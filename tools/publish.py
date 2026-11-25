#!/usr/bin/env python3
"""把构建结果发布到 gh-pages 分支（不依赖 GitHub Actions）。

用法：
    python tools/publish.py                 # 构建 + 发布
    python tools/publish.py --no-build      # 只把现有 dist/ 推上去
    python tools/publish.py -m "自定义提交说明"

前置条件（只需一次）：
    仓库 Settings → Pages → Source 选 "Deploy from a branch"
    → Branch 选 gh-pages → 目录选 /(root) → Save
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TZ = timezone(timedelta(hours=8))
BRANCH = "gh-pages"


def find_git() -> str:
    """优先用 PATH 里的 git；找不到就探常见安装位置。"""
    found = shutil.which("git")
    if found:
        return found
    candidates = [
        Path.home() / "AppData/Local/Programs/Git/cmd/git.exe",
        Path("C:/Program Files/Git/cmd/git.exe"),
        Path("C:/Program Files (x86)/Git/cmd/git.exe"),
        Path("D:/apps/Git/cmd/git.exe"),
    ]
    for path in candidates:
        if path.is_file():
            return str(path)
    raise SystemExit("找不到 git，请确认已安装 Git 并加入 PATH")


GIT = find_git()


def run(args: list[str], cwd: Path, check: bool = True, use_git: bool = True) -> subprocess.CompletedProcess:
    cmd = [GIT, *args] if use_git else list(args)
    result = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", errors="replace")
    if check and result.returncode != 0:
        sys.stderr.write(result.stdout + result.stderr)
        raise SystemExit(f"命令失败：{' '.join(cmd)}")
    return result


def cleanup_worktrees() -> None:
    """清掉可能残留的 gh-pages 工作区（上次中断时留下的）。"""
    listing = run(["worktree", "list", "--porcelain"], ROOT, check=False).stdout
    current_path = None
    for line in listing.splitlines():
        if line.startswith("worktree "):
            current_path = line[len("worktree "):].strip()
        elif line.strip() == f"branch refs/heads/{BRANCH}" and current_path:
            run(["worktree", "remove", "--force", current_path], ROOT, check=False)
            shutil.rmtree(current_path, ignore_errors=True)
            print(f"· 清理残留工作区 {current_path}")
    run(["worktree", "prune"], ROOT, check=False)


def git_ok() -> bool:
    try:
        run(["rev-parse", "--is-inside-work-tree"], ROOT)
        return True
    except SystemExit:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="构建并发布到 gh-pages 分支")
    parser.add_argument("--no-build", action="store_true", help="跳过构建，直接发布现有 dist/")
    parser.add_argument("-m", "--message", default="", help="提交说明")
    args = parser.parse_args()

    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

    if not git_ok():
        raise SystemExit("当前目录不是 git 仓库")

    dist = ROOT / "dist"
    if not args.no_build:
        print("· 构建站点 …")
        run([sys.executable, "build.py"], ROOT, use_git=False)
    if not (dist / "index.html").is_file():
        raise SystemExit("dist/index.html 不存在，先运行 python build.py")

    message = args.message or f"publish: {datetime.now(TZ).strftime('%Y-%m-%d %H:%M')}"
    cleanup_worktrees()
    worktree = Path(tempfile.mkdtemp(prefix="bg5hlc-pages-"))

    try:
        print(f"· 准备 {BRANCH} 工作区 …")
        run(["worktree", "add", "--force", "-B", BRANCH, str(worktree)], ROOT)

        # 清空工作区内容（保留 .git 指针文件）
        for entry in worktree.iterdir():
            if entry.name == ".git":
                continue
            if entry.is_dir():
                shutil.rmtree(entry)
            else:
                entry.unlink()

        print("· 复制 dist/ …")
        shutil.copytree(dist, worktree, dirs_exist_ok=True)

        # 保证 Pages 不走 Jekyll
        (worktree / ".nojekyll").write_text("", encoding="utf-8")

        run(["add", "-A"], worktree)
        status = run(["status", "--porcelain"], worktree).stdout.strip()
        if not status:
            print("· 内容没有变化，跳过提交")
        else:
            run(["commit", "-q", "-m", message], worktree)
            print(f"· 提交：{message}")

        current = run(["rev-parse", "--abbrev-ref", "HEAD"], ROOT).stdout.strip()
        print(f"· 推送 {BRANCH} …")
        run(["push", "-f", "origin", BRANCH], worktree)
        print(f"\n✓ 已发布到 {BRANCH} 分支（本地分支仍是 {current}）")
        print("  仓库 Settings → Pages → Source 选 Deploy from a branch → gh-pages / (root)")
    finally:
        run(["git", "worktree", "remove", "--force", str(worktree)], ROOT, check=False)
        shutil.rmtree(worktree, ignore_errors=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
