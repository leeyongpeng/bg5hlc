"""数据层：通联日志（CSV）与内容条目（Markdown）的读取、归一化和统计。

内容条目支持 `.en.md` 后缀的英文版本：
    content/qsl/ja1kwf.md      ← 中文
    content/qsl/ja1kwf.en.md   ← 英文（可选，缺字段就回退到中文）
"""

from __future__ import annotations

import csv
from collections import Counter
from datetime import date, datetime
from pathlib import Path

from . import frontmatter, markdown

# 波段从低到高排列，界面上的色标也按这个顺序取色。
BAND_LIST = [
    "160m", "80m", "60m", "40m", "30m", "20m", "17m", "15m", "12m", "10m",
    "6m", "4m", "2m", "70cm", "23cm", "13cm",
]

# 统计时把 USB/LSB 归到 SSB，显示仍用原始值。
MODE_GROUPS = {"USB": "SSB", "LSB": "SSB", "PHONE": "SSB", "FT4": "FT8"}

# 模式标签配色分组（见 style.css 的 .mode-*）
MODE_CLASSES = {
    "SSB": "ssb", "USB": "ssb", "LSB": "ssb", "AM": "ssb",
    "CW": "cw",
    "FT8": "ft8", "FT4": "ft8", "JT65": "ft8", "WSPR": "ft8",
    "SSTV": "sstv",
    "FM": "fm",
    "RTTY": "rtty",
    "PSK31": "psk", "PSK63": "psk",
}

CSV_ALIASES = {
    "qso_date": "date",
    "date_utc": "date",
    "utc_date": "date",
    "time_on": "time",
    "utc": "time",
    "callsign": "call",
    "call_sign": "call",
    "frequency": "freq",
    "freq_mhz": "freq",
    "tx_freq": "freq",
    "downlink": "freq",
    "downlink_freq": "freq",
    "uplink": "uplink",
    "uplink_freq": "uplink",
    "uplink_mhz": "uplink",
    "offset": "offset",
    "freq_offset": "offset",
    "shift": "offset",
    "ctcss": "ctcss",
    "ctcss_tone": "ctcss",
    "tone": "ctcss",
    "freq_band": "band",
    "mode_type": "mode",
    "rst_tx": "rst_sent",
    "rstsent": "rst_sent",
    "rst_rx": "rst_rcvd",
    "rstrcvd": "rst_rcvd",
    "tx_power": "power",
    "power_w": "power",
    "pwr": "power",
    "watts": "power",
    "my_qth": "my_qth",
    "station_qth": "my_qth",
    "own_qth": "my_qth",
    "their_rig": "their_rig",
    "dx_rig": "their_rig",
    "other_rig": "their_rig",
    "their_power": "their_power",
    "dx_power": "their_power",
    "other_power": "their_power",
    "their_antenna": "their_antenna",
    "dx_antenna": "their_antenna",
    "other_antenna": "their_antenna",
    "their_height": "their_height",
    "their_alt": "their_height",
    "their_altitude": "their_height",
    "dx_height": "their_height",
    "other_height": "their_height",
    "my_height": "my_height",
    "my_alt": "my_height",
    "my_altitude": "my_height",
    "station_height": "my_height",
    "own_height": "my_height",
    "country": "dxcc",
    "gridsquare": "grid",
    "equipment": "rig",
    "radio": "rig",
    "transceiver": "rig",
    "tx": "rig",
    "antenna_type": "antenna",
    "ant": "antenna",
    "aerial": "antenna",
    "comment": "notes",
    "note": "notes",
    "remark": "notes",
}


def _text(value) -> str:
    return ("" if value is None else str(value)).strip()


def parse_date(raw) -> date | None:
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
    if text in BAND_LIST:
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
    row["freq"] = _text(row.get("freq"))
    row["uplink"] = _text(row.get("uplink"))
    row["offset"] = _text(row.get("offset"))
    row["ctcss"] = _text(row.get("ctcss"))
    row["power"] = _text(row.get("power"))
    row["dxcc"] = _text(row.get("dxcc"))
    row["qth"] = _text(row.get("qth"))
    row["my_qth"] = _text(row.get("my_qth"))
    row["grid"] = _text(row.get("grid"))
    row["rig"] = _text(row.get("rig"))
    row["antenna"] = _text(row.get("antenna"))
    row["their_rig"] = _text(row.get("their_rig"))
    row["their_power"] = _text(row.get("their_power"))
    row["their_antenna"] = _text(row.get("their_antenna"))
    row["their_height"] = _text(row.get("their_height"))
    row["my_height"] = _text(row.get("my_height"))
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

    band_index = {band: i for i, band in enumerate(BAND_LIST)}
    bands = sorted(band_counter.items(), key=lambda kv: (band_index.get(kv[0], 99), -kv[1]))
    modes = sorted(mode_counter.items(), key=lambda kv: (-kv[1], kv[0]))

    dates = [row["date_obj"] for row in rows if row["date_obj"]]
    first, last = min(dates), max(dates)

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


# ── 内容条目 ─────────────────────────────────────────────


def _variant(meta: dict, body: str) -> dict:
    return {
        "title": _text(meta.get("title")),
        "summary": _text(meta.get("summary")) or markdown.plain(body, 120),
        "note": _text(meta.get("note")),
        "body_html": markdown.render(body),
        "meta": meta,
    }


def load_entries(folder: Path) -> list[dict]:
    """读取 content/qsl、content/sstv、content/notes 下的条目，中英版本合并成一条。

    以 `_` 开头的文件是模板/草稿，会被跳过；`xxx.en.md` 是 xxx.md 的英文版本。
    """
    groups: dict[str, dict[str, dict]] = {}

    if not folder.is_dir():
        return []

    for path in sorted(folder.glob("*.md")):
        if path.name.startswith("_"):
            continue
        stem = path.stem
        if stem.endswith(".en"):
            lang, slug = "en", stem[:-3]
        else:
            lang, slug = "zh", stem
        try:
            raw = path.read_text(encoding="utf-8-sig")
        except OSError as exc:
            print(f"  ! 无法读取 {path.name}：{exc}")
            continue
        meta, body = frontmatter.parse(raw)
        groups.setdefault(slug, {})[lang] = _variant(meta, body)

    entries: list[dict] = []
    for slug, variants in groups.items():
        primary = variants.get("zh") or variants.get("en") or {}
        # 语言无关的字段（call / band / mode / via / freq / image）两边互补
        meta: dict = {}
        for lang in ("en", "zh"):
            meta.update({k: v for k, v in (variants.get(lang, {}).get("meta") or {}).items() if k not in meta})
        parsed = parse_date(meta.get("date"))
        entries.append(
            {
                "slug": slug,
                "date": parsed,
                "meta": meta,
                "variants": variants,
                "is_placeholder": slug.lower().startswith("sample"),
                "image_name": _text(meta.get("image")),
                "image_url": "",
                "thumb_url": "",
            }
        )

    entries.sort(key=lambda item: (item["date"] or date.min), reverse=True)
    return entries


def pick(entry: dict, lang: str, field: str, default: str = "") -> str:
    """取某语言的字段，缺了回退到另一种语言。"""
    variants = entry.get("variants") or {}
    current = variants.get(lang) or {}
    value = current.get(field)
    if value:
        return value
    fallback = variants.get("zh") or variants.get("en") or {}
    return fallback.get(field) or default


def pick_meta(entry: dict, lang: str, field: str, default=None):
    """取某语言 frontmatter 里的字段（例如 tags），缺了回退到另一种语言。"""
    variants = entry.get("variants") or {}
    value = ((variants.get(lang) or {}).get("meta") or {}).get(field)
    if value:
        return value
    fallback = variants.get("zh") or variants.get("en") or {}
    return ((fallback.get("meta") or {}).get(field)) or default


def group_by_year(items: list[dict]) -> list[tuple[str, list[dict]]]:
    buckets: dict[str, list[dict]] = {}
    for item in items:
        key = str(item["date"].year) if item["date"] else "—"
        buckets.setdefault(key, []).append(item)
    return sorted(buckets.items(), key=lambda kv: kv[0], reverse=True)
