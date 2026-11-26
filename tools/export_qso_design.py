#!/usr/bin/env python3
"""导出「通联卡片页」的单文件设计稿，供外部改 UI 布局。

和 export_design.py 的区别：
- 只导出 qso.html；
- 数据 = 真实日志（data/qso.csv）+ 演示日志（demo/qso.csv），
  这样既能看真实那张带长备注的 BG5BGO 卡片，也能看多条卡片的列表布局；
- 单文件内联 CSS / JS / 字体 / favicon，双击打开，不发网络请求；
- 搜索、波段/模式筛选、排序、主题切换都能直接操作。

用法：
    python tools/export_qso_design.py
    python tools/export_qso_design.py --out qso-card-design.html
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import export_design  # noqa: E402
from sitegen import build  # noqa: E402

OUT_DIR = ROOT / "preview"

BANNER = """<!--
  ────────────────────────────────────────────────────────────────
  BG5HLC · 通联记录页 单文件设计稿（qso.html）
  ────────────────────────────────────────────────────────────────
  · CSS / JS / 字体 / favicon 全部内联，双击就能打开，不依赖服务器。
  · 数据 = {real} 条真实通联 + {demo} 条演示通联：
      第一条 BG5BGO 是真实记录，备注很长，用来检查长文本布局；
      其余是演示记录，用来检查列表、两列/单列和筛选排序。
  · 搜索、波段/模式筛选、排序、主题切换（右上角按钮）都可以直接操作。
  · 想改布局，重点看 <style> 里这几段：
      .filter-bar                 搜索 / 波段 / 模式 / 排序
      .qso-grid                   卡片网格（默认 auto-fill，最窄 490px）
      .qso-card                   单张卡片
      .qso-top                    呼号 + 波段/模式/网格 + 时间
      .qso-metrics                频率 / 功率 / RST
      .qso-details                QTH / RIG / ANT
      .qso-note                   备注
    CSS 变量（配色、字体、圆角）在 <style> 最顶部。
  · 改完把这份 HTML 发回来，我按改动回填到
    sitegen/render.py、assets/css/site-v2.css 和 assets/js/site-v2.js。
  · 导航链接指向正式站点的其它页面，单文件里没有那些页面，点了会 404。
  ────────────────────────────────────────────────────────────────
-->
"""


def _read_rows(path: Path) -> tuple[list[str], list[dict]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def _write_rows(path: Path, fields: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _merged_rows(real: list[dict], demo: list[dict], fields: list[str]) -> list[dict]:
    """真实记录排前面；按 日期+时间+呼号 去重。"""
    merged: list[dict] = []
    seen: set[tuple[str, str, str]] = set()
    for row in real + demo:
        key = (row.get("date", ""), row.get("time", ""), row.get("call", ""))
        if key in seen:
            continue
        seen.add(key)
        merged.append({field: row.get(field, "") for field in fields})
    return merged


def main() -> int:
    parser = argparse.ArgumentParser(description="导出通联卡片页单文件设计稿")
    parser.add_argument("--out", default="qso-design.html", help="输出文件名（默认 qso-design.html）")
    args = parser.parse_args()

    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

    demo_path = ROOT / "demo" / "qso.csv"
    real_path = ROOT / "data" / "qso.csv"
    backup = demo_path.read_bytes()

    demo_fields, demo_rows = _read_rows(demo_path)
    real_fields, real_rows = _read_rows(real_path)
    fields = list(dict.fromkeys(demo_fields + real_fields))
    if not fields:
        raise SystemExit("两个 CSV 都没有表头，无法导出")
    merged = _merged_rows(real_rows, demo_rows, fields)

    try:
        print(f"· 合并数据：真实 {len(real_rows)} 条 + 演示 {len(demo_rows)} 条 → {len(merged)} 条")
        _write_rows(demo_path, fields, merged)

        print("· 用合并数据构建 …")
        build.main(ROOT, ["--demo"])

        dist = ROOT / "dist"
        source = dist / "qso.html"
        if not source.is_file():
            raise SystemExit("构建后找不到 dist/qso.html")

        html = source.read_text(encoding="utf-8")
        html = export_design.strip_demo_bar(html)
        html = export_design.inline_assets(html, dist)
        html = html.replace(
            "<!doctype html>\n",
            "<!doctype html>\n" + BANNER.format(real=len(real_rows), demo=len(demo_rows)),
            1,
        )

        OUT_DIR.mkdir(exist_ok=True)
        target = OUT_DIR / args.out
        target.write_text(html, encoding="utf-8")

        print(f"\n✓ 已导出：{target}")
        print(f"  体积：{target.stat().st_size / 1024:.0f} KB（字体、样式、脚本均已内联）")
        print("  双击打开即可改布局；搜索 / 筛选 / 排序 / 主题都能用。")
    finally:
        demo_path.write_bytes(backup)
        print("\n· 恢复真实内容构建 …")
        build.main(ROOT, [])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
