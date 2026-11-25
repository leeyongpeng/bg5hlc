"""数据层：通联日志（CSV）与内容条目（Markdown）的读取、归一化和统计。"""

from __future__ import annotations

import csv
from collections import Counter
from datetime import date, datetime
from pathlib import Path

from . import frontmatter, markdown

# 波段从高到低排序，界面上的色标也按这个顺序取色。
BAND_ORDER = [
    "160m", "80m", "60m", "40m", "30m", "20m", "17m", "15m", "12m", "10m",
    "6m", "4m", "2m", "70cm", "23cm", "13cm",
]

# 统计时把 USB/LSB 归到 SSB，显示仍用原始值。
MODE_GROUPS = {
    "USB": "SSB",
    "LSB": "SSB",
    "PHONE": "SSB",
    "PSK": "PSK31",
    "FT4": "FT8",
    "RTTY": "RTTY",
}

CSV_ALIASES = {
    "qso_date": "date",
    "date_utc": "date",
    "utc_date": "date",
    "time_on": "time",
    "utc": "time",
    "callsign": "call",
    "call_sign": "call",
    "freq_band": "band",
    "mode_type": "mode",
    "rst_tx": "rst_sent",
    "rstsent": "rst_sent",
    "rst_rx": "rst_rcvd",
    "rstrcvd": "rst_rcvd",
    "country": "dxcc",
    "gridsquare": "grid",
    "comment": "notes",
    "note": "notes",
    "remark": "notes",
}


def _text(value) -> str:
    return ("" if value is None else str(value)).strip()


def parse_date(raw) -> date | None:
    """尽量把各种写法的日期解析成 date。"""
    text = _text(raw)
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%Y%m%d", "%Y/%m/%d", "%Y.%m.%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def normalize_band(raw) -> str:
    text = _text(raw).lower().replace(" ", "")
    if not text:
        return ""
    if text in BAND_ORDER:
        return text
    if text.endswith("cm") or text.endswith("m"):
        return text
    if text.isdigit():
        return f"{text}m"
    return text


def normalize_mode(raw) -> str:
    text = _text(raw).upper()
    return MODE_GROUPS.get(text, text)


def _canonical_row(raw: dict) -> dict:
    """把 CSV 的列名映射成内部统一的字段名。"""
    row: dict[str, str] = {}
    for key, value in raw.items():
        name = _text(key).lower().replace(" ", "_")
        name = CSV_ALIASES.get(name, name)
        if name and name not in row:
            row[name] = _text(value)

    parsed = parse_date(row.get("date"))
    row["date_obj"] = parsed
    row["date"] = parsed.isoformat() if parsed else _text(row.get("date"))
    row["time"] = _text(row.get("time"))[:5]
    row["call"] = _text(row.get("call")).upper()
    row["band"] = normalize_band(row.get("band"))
    row["mode"] = _text(row.get("mode")).upper()
    row["mode_group"] = normalize_mode(row.get("mode"))
    row["rst_sent"] = _text(row.get("rst_sent"))
    row["rst_rcvd"] = _text(row.get("rst_rcvd"))
    row["dxcc"] = _text(row.get("dxcc"))
    row["qth"] = _text(row.get("qth"))
    row["grid"] = _text(row.get("grid"))
    row["notes"] = _text(row.get("notes"))
    return row


def load_qso(path: Path) -> list[dict]:
    """读取通联 CSV；文件不存在、只有表头或格式有误都返回空列表。"""
    if not path.is_file():
        return []

    rows: list[dict] = []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            for raw in reader:
                if not any(_text(v) for v in raw.values()):
                    continue
                row = _canonical_row(raw)
                if not row["call"] or not row["date_obj"]:
                    continue
                rows.append(row)
    except (csv.Error, UnicodeDecodeError) as exc:
        print(f"  ! 读取 {path.name} 失败：{exc}")
        return []

    rows.sort(key=lambda r: (r["date_obj"], r["time"]), reverse=True)
    return rows


def next_month(day: date) -> date:
    return date(day.year + (day.month == 12), day.month % 12 + 1, 1)


def stats(rows: list[dict]) -> dict:
    """汇总首页与日志页要用到的所有数字。"""
    if not rows:
        today = date.today().replace(day=1)
        months = []
        cursor = today
        for _ in range(12):
            months.append((f"{cursor.year}-{cursor.month:02d}", 0))
            cursor = date(cursor.year - (cursor.month == 1), cursor.month - 1 or 12, 1)
        months.reverse()
        return {
            "total": 0, "dxcc": 0, "bands": [], "modes": [], "months": months,
            "first": "", "last": "", "band_count": 0, "dxcc_set": set(),
        }

    band_counter = Counter(row["band"] for row in rows if row["band"])
    mode_counter = Counter(row["mode_group"] or row["mode"] for row in rows if row["mode_group"] or row["mode"])
    dxcc_set = {row["dxcc"] for row in rows if row["dxcc"]}

    band_index = {band: i for i, band in enumerate(BAND_ORDER)}
    bands = sorted(band_counter.items(), key=lambda kv: (band_index.get(kv[0], 99), -kv[1]))
    modes = sorted(mode_counter.items(), key=lambda kv: (-kv[1], kv[0]))

    dates = [row["date_obj"] for row in rows if row["date_obj"]]
    first, last = min(dates), max(dates)

    # 以最近一次通联所在月份为终点，往前数 12 个月。
    end = last.replace(day=1)
    month_keys: list[str] = []
    cursor = end
    for _ in range(12):
        month_keys.append(f"{cursor.year}-{cursor.month:02d}")
        cursor = date(cursor.year - (cursor.month == 1), cursor.month - 1 or 12, 1)
    month_keys.reverse()
    month_counter = Counter(row["date"][:7] for row in rows if row["date"])
    months = [(key, month_counter.get(key, 0)) for key in month_keys]

    return {
        "total": len(rows),
        "dxcc": len(dxcc_set),
        "dxcc_set": dxcc_set,
        "bands": bands,
        "modes": modes,
        "months": months,
        "first": first.isoformat(),
        "last": last.isoformat(),
        "band_count": len(band_counter),
    }


def load_entries(folder: Path) -> list[dict]:
    """读取 content/qsl、content/sstv、content/notes 下的 Markdown 条目。

    以 `_` 开头的文件是模板/草稿，会被跳过。
    """
    items: list[dict] = []
    if not folder.is_dir():
        return items

    for path in sorted(folder.glob("*.md")):
        if path.name.startswith("_"):
            continue
        try:
            raw = path.read_text(encoding="utf-8-sig")
        except OSError as exc:
            print(f"  ! 无法读取 {path.name}：{exc}")
            continue

        meta, body = frontmatter.parse(raw)
        parsed = parse_date(meta.get("date"))
        items.append(
            {
                "slug": path.stem,
                "meta": meta,
                "body": body,
                "body_html": markdown.render(body),
                "summary": _text(meta.get("summary")) or markdown.plain(body, 120),
                "summary_en": _text(meta.get("summary_en")),
                "title": _text(meta.get("title")) or path.stem,
                "title_en": _text(meta.get("title_en")),
                "date": parsed,
                "source": path,
                "is_placeholder": path.stem.lower().startswith("sample"),
            }
        )

    items.sort(key=lambda item: (item["date"] or date.min), reverse=True)
    return items


def group_by_year(items: list[dict]) -> list[tuple[str, list[dict]]]:
    """按年份分组，年份倒序；没有日期的归到「未标注」。"""
    buckets: dict[str, list[dict]] = {}
    for item in items:
        key = str(item["date"].year) if item["date"] else "—"
        buckets.setdefault(key, []).append(item)
    return sorted(buckets.items(), key=lambda kv: kv[0], reverse=True)
