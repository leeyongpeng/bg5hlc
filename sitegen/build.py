"""构建流程：读数据 → 拷贝资源 → 渲染页面 → 写入 dist/ →（可选）本地预览。"""

from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime, timedelta, timezone
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import config, data, images, render

TZ = timezone(timedelta(hours=8))


def _utf8_console() -> None:
    """Windows 控制台默认 GBK，打印中文/符号前先切到 UTF-8。"""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass



def _copy_assets(root: Path, out: Path) -> None:
    src = root / "assets"
    if src.is_dir():
        shutil.copytree(src, out / "assets", dirs_exist_ok=True)


def _attach_images(items: list[dict], source_dir: Path, out: Path, kind: str) -> None:
    """把条目引用的图片复制到 dist/media/<kind>/，顺手生成缩略图。"""
    for item in items:
        name = str(item["meta"].get("image", "") or "").strip()
        if not name:
            continue
        found = images.find(source_dir, name)
        if not found:
            print(f"  ! {item['slug']}：找不到图片 {name}，卡片会显示占位块")
            continue
        full, thumb = images.prepare(found, out / "media" / kind, item["slug"])
        item["image_url"] = full
        item["thumb_url"] = thumb


def _write(out: Path, relative: str, content: str) -> None:
    path = out / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class _PreviewHandler(SimpleHTTPRequestHandler):
    """本地预览用的静态服务器：不打印 200 日志，404 交给 404.html。"""

    def log_message(self, format: str, *args) -> None:  # noqa: A002 - 沿用父类签名
        message = format % args
        if " 200 " not in message:
            sys.stderr.write(f"{self.address_string()} - {message}\n")

    def guess_type(self, path):  # noqa: D401 - 覆盖父类
        guessed = super().guess_type(path)
        if isinstance(guessed, str) and not guessed.startswith(("image/", "font/")) and "charset" not in guessed:
            return f"{guessed}; charset=utf-8"
        return guessed

    def send_error(self, code, message=None, explain=None):
        if code == 404:
            page = Path(self.directory) / "404.html"
            if page.is_file():
                body = page.read_bytes()
                self.send_response(404)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                if self.command != "HEAD":
                    self.wfile.write(body)
                return
        super().send_error(code, message, explain)


def main(root: Path, argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="build.py", description="生成 BG5HLC 静态站点到 dist/")
    parser.add_argument("--serve", action="store_true", help="构建完成后启动本地预览服务器")
    parser.add_argument("--port", type=int, default=8080, help="本地预览端口（默认 8080）")
    parser.add_argument("--demo", action="store_true", help="用 demo/ 里的演示数据构建，仅用于本地看效果")
    args = parser.parse_args(argv)

    _utf8_console()
    cfg = config.load(root)
    out = root / "dist"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    built_at = datetime.now(TZ).strftime("%Y-%m-%d %H:%M")
    demo = args.demo

    if demo:
        source = root / "demo"
        qso_path = source / "qso.csv"
        content_dir = source
    else:
        source = root
        qso_path = root / "data" / "qso.csv"
        content_dir = root / "content"

    rows = data.load_qso(qso_path)
    stats = data.stats(rows)
    cards = data.load_entries(content_dir / "qsl")
    sstv = data.load_entries(content_dir / "sstv")
    notes = data.load_entries(content_dir / "notes")

    _copy_assets(root, out)
    _attach_images(cards, content_dir / "qsl", out, "qsl")
    _attach_images(sstv, content_dir / "sstv", out, "sstv")

    pages = {
        "index.html": render.page_home(
            cfg, rows=rows, stats=stats, cards=cards, sstv=sstv, built_at=built_at, demo=demo
        ),
        "qso.html": render.page_qso(cfg, rows=rows, stats=stats, built_at=built_at, demo=demo),
        "qsl.html": render.page_qsl(cfg, items=cards, built_at=built_at, demo=demo),
        "sstv.html": render.page_sstv(cfg, items=sstv, built_at=built_at, demo=demo),
        "notes.html": render.page_notes(cfg, items=notes, built_at=built_at, demo=demo),
        "station.html": render.page_station(cfg, stats=stats, built_at=built_at, demo=demo),
        "404.html": render.page_404(cfg, built_at=built_at, demo=demo),
    }
    for relative, html in pages.items():
        _write(out, relative, html)

    for note in notes:
        _write(out, f"notes/{note['slug']}.html", render.page_note(cfg, item=note, built_at=built_at, demo=demo))

    (out / "robots.txt").write_text("User-agent: *\nAllow: /\n", encoding="utf-8")
    (out / ".nojekyll").write_text("", encoding="utf-8")

    print(f"✓ 构建完成：{len(pages) + len(notes)} 个页面")
    print(f"  通联 {stats['total']} 条 · QSL {len(cards)} 张 · SSTV {len(sstv)} 张 · 随笔 {len(notes)} 篇")
    if demo:
        print("  注意：本次使用的是 demo/ 演示数据（--demo），没有写入真实内容")
    print(f"  输出目录：{out}")

    if args.serve:
        handler = partial(_PreviewHandler, directory=str(out))
        url = f"http://127.0.0.1:{args.port}/"
        print(f"\n本地预览：{url}    （Ctrl+C 停止）\n")
        try:
            with ThreadingHTTPServer(("127.0.0.1", args.port), handler) as httpd:
                httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n预览已停止。")
        return 0

    print("\n本地预览：python build.py --serve")
    return 0
