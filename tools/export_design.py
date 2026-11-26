#!/usr/bin/env python3
"""导出一份单文件静态 HTML（供外部改设计用）。

把首页渲染成独立文件：CSS、JS、图片、favicon 全部内联，
双击就能在浏览器打开，不依赖本地服务器，也不发任何网络请求。

用法：
    python tools/export_design.py                 # 导出首页
    python tools/export_design.py --page qso.html # 导出其它页面
"""

from __future__ import annotations

import argparse
import base64
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sitegen import build  # noqa: E402

OUT_DIR = ROOT / "preview"

MIME = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
    ".woff2": "font/woff2",
    ".woff": "font/woff",
}


def data_uri(path: Path) -> str:
    mime = MIME.get(path.suffix.lower(), "application/octet-stream")
    payload = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{payload}"


def _inline_css(css: str, dist: Path) -> str:
    """把 CSS 里的自托管字体换成 data URI。"""

    def swap_font(match: re.Match) -> str:
        name = Path(match.group(1)).name
        file = dist / "assets/fonts" / name
        if not file.is_file():
            return match.group(0)
        return f'url("{data_uri(file)}") format("woff2")'

    css = re.sub(r'url\("\.\./fonts/([^"]+)"\)\s*format\("woff2(?:-variations)?"\)', swap_font, css)
    css = re.sub(r'url\("\.\./fonts/([^"]+)"\)', swap_font, css)
    return css


def inline_assets(html: str, dist: Path) -> str:
    favicon = data_uri(dist / "assets/favicon.svg")

    # 页面实际引用哪个 CSS / JS 就内联哪个（旧版 style.css、新版 site-v2.css 都支持）
    def swap_css(match: re.Match) -> str:
        href = match.group(1).split("?")[0]
        file = dist / href
        if not file.is_file():
            return match.group(0)
        return f"<style>\n{_inline_css(file.read_text(encoding='utf-8'), dist)}\n</style>"

    def swap_js(match: re.Match) -> str:
        src = match.group(1).split("?")[0]
        file = dist / src
        if not file.is_file():
            return match.group(0)
        # 内联脚本放在 </body> 前，不需要 defer
        return f"<script>\n{file.read_text(encoding='utf-8')}\n</script>"

    html = re.sub(r'<link rel="stylesheet" href="([^"]+)">', swap_css, html)
    html = re.sub(r'<script src="([^"]+)"[^>]*></script>', swap_js, html)
    html = re.sub(r'<link rel="icon" href="[^"]*" type="image/svg\+xml">', f'<link rel="icon" href="{favicon}" type="image/svg+xml">', html)

    def swap(match: re.Match) -> str:
        attr, rel = match.group(1), match.group(2)
        file = dist / rel
        if not file.is_file():
            return match.group(0)
        return f'{attr}="{data_uri(file)}"'

    html = re.sub(r'(src|href)="(media/[^"]+)"', swap, html)
    # 单文件里不需要字体预加载
    html = re.sub(r'<link rel="preload"[^>]*>\s*', "", html)
    return html


def strip_demo_bar(html: str) -> str:
    return re.sub(r'<div class="demo-bar">.*?</div>\s*', "", html, flags=re.S)


def add_banner(html: str, page: str) -> str:
    banner = f"""<!--
  ────────────────────────────────────────────────────────────────
  BG5HLC 设计稿 · 单文件快照（{page}）
  ────────────────────────────────────────────────────────────────
  · 这是正式站点渲染出来的静态快照，CSS / JS / 图片全部内联，
    双击即可在浏览器打开，不依赖网络和本地服务器。
  · 直接在这份文件上改样式、调布局即可，改完把文件发回来，
    我会按改动回填到 Python 生成器（sitegen/ + assets/）。
  · 结构提示：
      <html data-theme="light|dark" data-theme-mode="auto|light|dark">
      CSS 变量在 <style> 顶部，两套主题各一组；
      导航链接指向正式站点的其它页面，本文件只包含 {page}。
  · 内容为演示数据（与真实日志无关），改版不用管文案。
  ────────────────────────────────────────────────────────────────
-->
"""
    return html.replace("<!doctype html>\n", "<!doctype html>\n" + banner, 1)


def main() -> int:
    parser = argparse.ArgumentParser(description="导出单文件静态 HTML 设计稿")
    parser.add_argument("--page", default="index.html", help="要导出的页面（默认 index.html）")
    parser.add_argument("--out", default="design.html", help="输出文件名（默认 design.html）")
    args = parser.parse_args()

    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("· 用演示数据构建 …")
    build.main(ROOT, ["--demo"])

    dist = ROOT / "dist"
    source = dist / args.page
    if not source.is_file():
        raise SystemExit(f"找不到 {args.page}，可选：{', '.join(p.name for p in dist.glob('*.html'))}")

    html = source.read_text(encoding="utf-8")
    html = strip_demo_bar(html)
    html = inline_assets(html, dist)
    html = add_banner(html, args.page)

    OUT_DIR.mkdir(exist_ok=True)
    target = OUT_DIR / args.out
    target.write_text(html, encoding="utf-8")

    print(f"\n✓ 已导出：{target}")
    print(f"  体积：{target.stat().st_size / 1024:.0f} KB（图片已内联）")
    print("  双击即可打开；改完把文件发回来即可回填。")

    # 复原真实内容，避免 dist/ 停留在演示数据
    print("\n· 恢复真实内容构建 …")
    build.main(ROOT, [])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
