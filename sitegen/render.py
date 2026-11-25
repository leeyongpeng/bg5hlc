"""页面渲染：把数据拼成 HTML 字符串。

刻意不引入模板引擎——所有结构都在这个文件里，看得见、改得动。
每个 page_* 函数返回一整页 HTML；组件函数负责重复出现的碎片。
"""

from __future__ import annotations

import html
import math
import random
import re
from datetime import date, datetime, timedelta, timezone

from . import __version__, data
from . import strings as S
from .config import absolute_url

TZ = timezone(timedelta(hours=8))

NAV = [
    ("index.html", "nav.home", "home"),
    ("qso.html", "nav.qso", "qso"),
    ("qsl.html", "nav.qsl", "qsl"),
    ("sstv.html", "nav.sstv", "sstv"),
    ("notes.html", "nav.notes", "notes"),
    ("station.html", "nav.station", "station"),
]

ICONS = {
    "qso": '<svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"><path d="M4 7h16M4 12h16M4 17h10"/></svg>',
    "qsl": '<svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="6" width="18" height="12" rx="2"/><path d="M7 10h4M7 14h6"/><circle cx="17" cy="10.5" r="1.6"/></svg>',
    "sstv": '<svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="8.5" cy="10" r="1.6"/><path d="M21 16l-5-5-7 7"/></svg>',
    "notes": '<svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><path d="M6 3h9l4 4v14H6z"/><path d="M14 3v5h5M9 13h7M9 17h5"/></svg>',
    "wave": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M2 12h3l2-6 3 12 3-9 2 6h3l2-4h2"/></svg>',
}


def esc(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


# ── 小标签与色标 ──────────────────────────────────────────


def _band_class(band: str) -> str:
    return "band-" + re.sub(r"[^a-z0-9]+", "-", band.lower()).strip("-")


def band_chip(band: str, extra: str = "") -> str:
    if not band:
        return ""
    return f'<span class="chip band {_band_class(band)} {extra}">{esc(band)}</span>'


def chip(text, variant: str = "") -> str:
    if not text:
        return ""
    return f'<span class="chip {variant}">{esc(text)}</span>'


def mode_chip(mode: str) -> str:
    return chip(mode, "mode") if mode else ""


def dash(value, fallback: str = "—") -> str:
    text = "" if value is None else str(value).strip()
    return esc(text) if text else f'<span class="muted">{fallback}</span>'


# ── 通用版式 ──────────────────────────────────────────────


def _nav_html(cfg: dict, active: str, prefix: str) -> str:
    items = []
    for href, key, key_active in NAV:
        zh, en = S.pair(key)
        current = ' aria-current="page"' if active == key_active else ""
        cls = "nav-link is-active" if active == key_active else "nav-link"
        items.append(
            f'<a class="{cls}" href="{prefix}{href}"{current}>'
            f'<span class="nav-zh">{esc(zh)}</span>'
            f'<span class="nav-en">{esc(en)}</span></a>'
        )
    github = ""
    if cfg.get("github"):
        github = (
            f'<a class="nav-gh" href="{esc(cfg["github"])}" target="_blank" rel="noopener">'
            'GitHub<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" '
            'stroke-linecap="round" aria-hidden="true"><path d="M7 17L17 7M9 7h8v8"/></svg></a>'
        )
    return "".join(items), github


def layout(
    cfg: dict,
    *,
    prefix: str,
    active: str,
    title: str,
    description: str,
    body: str,
    built_at: str,
    demo: bool = False,
) -> str:
    nav_items, github = _nav_html(cfg, active, prefix)
    tagline = cfg.get("tagline") or "Amateur Radio"
    callsign = cfg.get("callsign", "")

    demo_bar = ""
    if demo:
        zh, en = S.pair("misc.demo")
        demo_bar = f'<div class="demo-bar"><span>{esc(zh)}</span><span class="demo-en">{esc(en)}</span></div>'

    og_url = absolute_url(cfg, "")
    og_meta = f'<meta property="og:url" content="{esc(og_url)}">' if og_url else ""

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<meta name="color-scheme" content="dark">
<meta name="theme-color" content="#0a0d12">
<meta name="generator" content="bg5hlc-sitegen {__version__}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{esc(cfg.get('site_name') or callsign)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
{og_meta}
<link rel="icon" href="{prefix}assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{prefix}assets/css/style.css">
</head>
<body class="page-{esc(active)}">
{demo_bar}
<a class="skip-link" href="#main">{esc(S.zh('a11y.skip'))}</a>
<header class="site-header">
  <div class="wrap header-inner">
    <a class="brand" href="{prefix}index.html" aria-label="{esc(callsign)} — {esc(S.zh('a11y.home'))}">
      <span class="brand-mark" aria-hidden="true">{ICONS['wave']}</span>
      <span class="brand-text"><strong>{esc(callsign)}</strong><small>{esc(tagline)}</small></span>
    </a>
    <nav class="site-nav" aria-label="主导航">{nav_items}</nav>
    {github}
  </div>
</header>
<main id="main" class="wrap">
{body}
</main>
<footer class="site-footer">
  <div class="wrap footer-grid">
    <div class="footer-col footer-about">
      <span class="footer-call">{esc(callsign)}</span>
      <p>{esc(cfg.get('description') or '')}</p>
    </div>
    <div class="footer-col">
      <h2><span>{esc(S.zh('footer.nav'))}</span><small>{esc(S.en('footer.nav'))}</small></h2>
      <ul class="footer-links">
        {''.join(f'<li><a href="{prefix}{href}">{esc(S.zh(key))}</a></li>' for href, key, _ in NAV)}
      </ul>
    </div>
    <div class="footer-col">
      <h2><span>{esc(S.zh('footer.contact'))}</span><small>{esc(S.en('footer.contact'))}</small></h2>
      <ul class="footer-links">
        {f'<li><a href="mailto:{esc(cfg["email"])}">{esc(cfg["email"])}</a></li>' if cfg.get('email') else ''}
        {f'<li><a href="{esc(cfg["github"])}" target="_blank" rel="noopener">GitHub</a></li>' if cfg.get('github') else ''}
        <li><a href="{prefix}station.html#qsl">QSL</a></li>
      </ul>
    </div>
  </div>
  <div class="wrap footer-bottom">
    <span>© {datetime.now(TZ).year} {esc(callsign)}</span>
    <span>{esc(S.zh('footer.made'))}</span>
    <span>{esc(S.zh('footer.built'))} {esc(built_at)}</span>
  </div>
</footer>
<div class="lightbox" id="lightbox" hidden>
  <button class="lightbox-close" type="button" aria-label="关闭">×</button>
  <figure class="lightbox-figure">
    <img id="lightbox-img" src="" alt="">
    <figcaption id="lightbox-cap"></figcaption>
  </figure>
</div>
<script src="{prefix}assets/js/app.js" defer></script>
</body>
</html>"""


def page_head(*, kicker: str, title: str, lead: str, lead_en: str = "") -> str:
    en = f'<p class="page-lead-en">{esc(lead_en)}</p>' if lead_en else ""
    return (
        '<section class="page-head">'
        f'<p class="kicker">{esc(kicker)}</p>'
        f'<h1 class="page-title">{esc(title)}</h1>'
        f'<p class="page-lead">{esc(lead)}</p>{en}'
        "</section>"
    )


def section_head(zh: str, en: str, href: str = "", label: str = "") -> str:
    more = (
        f'<a class="section-more" href="{esc(href)}">{esc(label)}<span aria-hidden="true">→</span></a>'
        if href
        else ""
    )
    return (
        '<div class="section-head">'
        f'<h2 class="section-title"><span>{esc(zh)}</span><small>{esc(en)}</small></h2>'
        f"{more}</div>"
    )


def stat_block(value: str, zh: str, en: str, empty: bool = False, compact: bool = False) -> str:
    cls = "stat-value"
    if empty:
        cls += " is-empty"
    if compact:
        cls += " is-compact"
    return (
        f'<div class="stat"><span class="{cls}">{esc(value)}</span>'
        f'<span class="stat-label"><span>{esc(zh)}</span><small>{esc(en)}</small></span></div>'
    )


def _empty_icon(kind: str) -> str:
    return ICONS.get(kind, ICONS["notes"])


def empty_state(*, kind: str, title_zh: str, title_en: str, lead_zh: str, lead_en: str, extra: str = "") -> str:
    return (
        '<div class="empty-state">'
        f'{_empty_icon(kind)}'
        f'<h3 class="empty-title"><span>{esc(title_zh)}</span><small>{esc(title_en)}</small></h3>'
        f'<p class="empty-lead">{esc(lead_zh)}</p>'
        f'<p class="empty-lead-en">{esc(lead_en)}</p>'
        f"{extra}"
        "</div>"
    )


# ── 通联表格 ──────────────────────────────────────────────


def _rst(row: dict) -> str:
    sent, rcvd = row.get("rst_sent", ""), row.get("rst_rcvd", "")
    if sent and rcvd:
        return f"{esc(sent)}<span class=\"sep\">/</span>{esc(rcvd)}"
    return esc(sent or rcvd)


def _row_html(row: dict) -> str:
    search = " ".join(
        [row.get("call", ""), row.get("dxcc", ""), row.get("qth", ""), row.get("notes", ""), row.get("grid", "")]
    ).lower()
    place = " · ".join(x for x in (row.get("dxcc"), row.get("qth")) if x)
    date_txt = row.get("date", "")
    return (
        f'<tr class="log-row" data-search="{esc(search)}" data-band="{esc(row.get("band", ""))}" '
        f'data-mode="{esc(row.get("mode", ""))}" data-date="{esc(date_txt)}" data-time="{esc(row.get("time", ""))}" '
        f'data-call="{esc(row.get("call", ""))}">'
        f'<td class="cell-date"><time datetime="{esc(date_txt)}">{esc(date_txt)}</time></td>'
        f'<td class="cell-time">{esc(row.get("time", ""))}</td>'
        f'<td class="cell-call">{esc(row.get("call", ""))}</td>'
        f'<td class="cell-band">{band_chip(row.get("band", ""))}</td>'
        f'<td class="cell-mode">{mode_chip(row.get("mode", ""))}</td>'
        f'<td class="cell-rst">{_rst(row)}</td>'
        f'<td class="cell-place">{esc(place)}</td>'
        f'<td class="cell-notes">{esc(row.get("notes", ""))}</td>'
        "</tr>"
    )


def _thead(sortable: bool = True) -> str:
    heads = [
        ("date", "th.date", "text", "descending"),
        ("time", "th.time", "text", ""),
        ("call", "th.call", "text", ""),
        ("band", "th.band", "text", ""),
        ("mode", "th.mode", "text", ""),
        ("rst", "th.rst", "text", ""),
        ("place", "th.dxcc", "text", ""),
        ("notes", "th.notes", "text", ""),
    ]
    cells = []
    for key, label, dtype, aria in heads:
        zh, en = S.pair(label)
        aria_attr = f' aria-sort="{aria}"' if aria else ""
        if sortable and key in ("date", "time", "call", "band", "mode"):
            cells.append(
                f'<th scope="col" class="sortable th-{key}" data-key="{key}" data-type="{dtype}"{aria_attr}>'
                f'<button type="button" class="th-btn">{esc(zh)}<small>{esc(en)}</small></button></th>'
            )
        else:
            cells.append(
                f'<th scope="col" class="th-{key}"><span class="th-static">{esc(zh)}<small>{esc(en)}</small></span></th>'
            )
    return f'<thead><tr>{"".join(cells)}</tr></thead>'


def qso_table(rows: list[dict], *, limit: int | None = None, table_id: str = "log", sortable: bool = True) -> str:
    shown = rows if limit is None else rows[:limit]
    body = "".join(_row_html(row) for row in shown)
    return (
        '<div class="table-wrap">'
        f'<table class="log" id="{table_id}">{_thead(sortable)}'
        f'<tbody id="{table_id}-body">{body}</tbody></table>'
        '<p class="log-empty" id="' + table_id + '-empty" hidden>'
        f'{esc(S.zh("filter.none"))} <small>{esc(S.en("filter.none"))}</small></p>'
        "</div>"
        f'<p class="table-hint">{esc(S.zh("filter.swipe"))}<span>{esc(S.en("filter.swipe"))}</span></p>'
    )


def log_tools(rows: list[dict], stats: dict) -> str:
    bands = sorted({row["band"] for row in rows if row["band"]}, key=lambda b: (data.BAND_ORDER.index(b) if b in data.BAND_ORDER else 99, b))
    modes = sorted({row["mode"] for row in rows if row["mode"]})
    band_opts = "".join(f'<option value="{esc(b)}">{esc(b)}</option>' for b in bands)
    mode_opts = "".join(f'<option value="{esc(m)}">{esc(m)}</option>' for m in modes)
    # 模板里保留 {n}，由前端脚本替换成筛选后的条数
    zh_tpl, en_tpl = S.pair("filter.count")
    zh_count = zh_tpl.format(n=stats["total"])
    return (
        f'<div class="log-tools" data-count-zh="{esc(zh_tpl)}" data-count-en="{esc(en_tpl)}">'
        '<label class="field field-search">'
        f'<span class="field-label sr-only">{esc(S.zh("filter.search"))}</span>'
        f'<input type="search" id="qso-search" placeholder="{esc(S.zh("filter.search"))}" autocomplete="off">'
        "</label>"
        '<label class="field">'
        f'<span class="field-label">{esc(S.zh("filter.band"))}</span>'
        f'<select id="qso-band"><option value="">{esc(S.zh("filter.all_bands"))}</option>{band_opts}</select>'
        "</label>"
        '<label class="field">'
        f'<span class="field-label">{esc(S.zh("filter.mode"))}</span>'
        f'<select id="qso-mode"><option value="">{esc(S.zh("filter.all_modes"))}</option>{mode_opts}</select>'
        "</label>"
        f'<button type="button" class="btn btn-ghost btn-sm" id="qso-reset">{esc(S.zh("btn.reset"))}</button>'
        f'<span class="log-count" id="qso-count">{esc(zh_count)}</span>'
        "</div>"
    )


# ── 图表 ─────────────────────────────────────────────────


def bar_chart(items: list[tuple[str, int]], *, kind: str = "band") -> str:
    if not items:
        return ""
    top = max(count for _, count in items) or 1
    rows = []
    for label, count in items:
        width = max(4, round(count / top * 100))
        cls = "bar-fill" + (f" {_band_class(label)}" if kind == "band" else "")
        rows.append(
            '<div class="bar-row">'
            f'<span class="bar-label">{esc(label)}</span>'
            f'<span class="bar-track"><span class="{cls}" style="width:{width}%"></span></span>'
            f'<span class="bar-value">{count}</span>'
            "</div>"
        )
    return f'<div class="bars">{"".join(rows)}</div>'


def month_spark(months: list[tuple[str, int]]) -> str:
    top = max((count for _, count in months), default=0) or 1
    cols = []
    for key, count in months:
        height = 6 if count == 0 else max(10, round(count / top * 100))
        label = key[5:].lstrip("0") or key[5:]
        empty_cls = " is-zero" if count == 0 else ""
        cols.append(
            '<div class="spark-col">'
            f'<span class="spark-bar{empty_cls}" style="height:{height}%" '
            f'title="{esc(key)} · {count}"></span>'
            f'<span class="spark-x">{esc(label)}</span></div>'
        )
    return f'<div class="spark">{"".join(cols)}</div>'


# ── 卡片（QSL / SSTV）────────────────────────────────────


def _card_media(item: dict, kind: str, caption: str) -> str:
    full = item.get("image_url", "")
    thumb = item.get("thumb_url", "")
    if not thumb:
        return (
            '<span class="card-media is-empty">'
            f'<span class="media-hint">{esc("等待放入图片")}</span></span>'
        )
    alt = f"{item['meta'].get('call', '')} {'QSL 卡片' if kind == 'qsl' else 'SSTV 图像'}".strip()
    return (
        f'<a class="card-media" href="{esc(full or thumb)}" data-lightbox data-caption="{esc(caption)}">'
        f'<img src="{esc(thumb)}" alt="{esc(alt)}" loading="lazy" decoding="async">'
        "</a>"
    )


def qsl_card(item: dict) -> str:
    meta = item["meta"]
    call = str(meta.get("call", "") or "")
    date_txt = item["date"].isoformat() if item["date"] else ""
    caption = " · ".join(x for x in (call, date_txt) if x)
    chips = "".join(
        [
            band_chip(str(meta.get("band", "") or "")),
            mode_chip(str(meta.get("mode", "") or "").upper()),
            chip(str(meta.get("via", "") or ""), "via"),
        ]
    )
    body = f'<div class="card-text">{item["body_html"]}</div>' if item.get("body_html") else ""
    sample = '<span class="card-flag">示例</span>' if item.get("is_placeholder") else ""
    return (
        '<article class="card">'
        f"{_card_media(item, 'qsl', caption)}{sample}"
        '<div class="card-body">'
        f'<div class="card-head"><h3 class="card-call">{esc(call)}</h3>'
        f'<time class="card-date" datetime="{esc(date_txt)}">{esc(date_txt)}</time></div>'
        f'<div class="card-chips">{chips}</div>{body}'
        "</div></article>"
    )


def sstv_card(item: dict) -> str:
    meta = item["meta"]
    call = str(meta.get("call", "") or "")
    date_txt = item["date"].isoformat() if item["date"] else ""
    freq = str(meta.get("freq", "") or "")
    caption = " · ".join(x for x in (call, freq, date_txt) if x)
    chips = "".join([chip(freq, "freq"), mode_chip(str(meta.get("mode", "") or "").upper())])
    note = str(meta.get("note", "") or "")
    body = f'<div class="card-text">{item["body_html"]}</div>' if item.get("body_html") else ""
    if note:
        body += f'<p class="card-note">{esc(note)}</p>'
    return (
        '<article class="card card-sstv">'
        f"{_card_media(item, 'sstv', caption)}"
        '<div class="card-body">'
        f'<div class="card-head"><h3 class="card-call">{esc(call)}</h3>'
        f'<time class="card-date" datetime="{esc(date_txt)}">{esc(date_txt)}</time></div>'
        f'<div class="card-chips">{chips}</div>{body}'
        "</div></article>"
    )


def card_grid(items: list[dict], kind: str) -> str:
    render_one = qsl_card if kind == "qsl" else sstv_card
    return f'<div class="card-grid">{"".join(render_one(item) for item in items)}</div>'


def gallery(items: list[dict], kind: str, *, empty_kind: str, empty_key: str) -> str:
    if not items:
        zh, en = S.pair(empty_key + "_lead")
        t_zh, t_en = S.pair(empty_key + "_title")
        return empty_state(kind=empty_kind, title_zh=t_zh, title_en=t_en, lead_zh=zh, lead_en=en)

    groups = data.group_by_year(items)
    blocks = []
    for year, group in groups:
        blocks.append(
            f'<section class="year-group" data-year="{esc(year)}">'
            f'<h2 class="year-title">{esc(year)}<small>{len(group)}</small></h2>'
            f"{card_grid(group, kind)}</section>"
        )
    return "".join(blocks)


# ── 首页 ─────────────────────────────────────────────────


def spectrum_bars(count: int = 46) -> str:
    rnd = random.Random(20260314)
    bars = []
    for i in range(count):
        h = 10 + 80 * abs(math.sin(i * 0.63 + 0.4)) * (0.5 + 0.5 * rnd.random())
        bars.append(f'<span style="height:{h:.0f}%"></span>')
    return "".join(bars)


def page_home(cfg: dict, *, rows: list[dict], stats: dict, cards: list[dict], sstv: list[dict], built_at: str, demo: bool) -> str:
    callsign = cfg.get("callsign", "")
    desc_zh = cfg.get("description", "")
    desc_en = cfg.get("description_en", "")

    stats_empty = stats["total"] == 0
    stat_items = [
        (str(stats["total"]) if stats["total"] else "—", "stat.qso"),
        (str(stats["dxcc"]) if stats["dxcc"] else "—", "stat.dxcc"),
        (str(len(cards)) if cards else "—", "stat.qsl"),
        (str(len(sstv)) if sstv else "—", "stat.sstv"),
        (str(stats["band_count"]) if stats["band_count"] else "—", "stat.bands"),
    ]
    stats_html = "".join(
        stat_block(value, *S.pair(key), empty=(value == "—")) for value, key in stat_items
    )

    meta_items = [
        (key, value)
        for key, value in (
            ("home.meta_qth", cfg.get("qth")),
            ("home.meta_grid", cfg.get("grid")),
            ("home.meta_license", cfg.get("license")),
        )
        if str(value or "").strip()
    ]
    meta_block = ""
    if meta_items:
        meta_block = '<ul class="hero-meta">' + "".join(
            f'<li><span>{esc(S.zh(key))}</span><b>{esc(value)}</b></li>' for key, value in meta_items
        ) + "</ul>"

    if rows:
        latest = section_head(
            *S.pair("home.section_latest"), href="qso.html", label=S.zh("btn.view_all")
        ) + qso_table(rows, limit=5, table_id="latest", sortable=False)
    else:
        latest = section_head(*S.pair("home.section_latest")) + empty_state(
            kind="qso",
            title_zh=S.zh("empty.qso_title"),
            title_en=S.en("empty.qso_title"),
            lead_zh=S.zh("empty.qso_lead"),
            lead_en=S.en("empty.qso_lead"),
            extra=(
                '<p class="empty-hint">在 <code>data/qso.csv</code> 里照着表头加一行：</p>'
                '<pre class="snippet">2026-03-14,08:42,JA1KWF,20m,SSB,59,59,Japan,Tokyo,PM95,首次通联</pre>'
            ),
        )
        latest += f'<p class="section-foot"><a class="link-arrow" href="qso.html">{esc(S.zh("btn.all_qso"))}<span>→</span></a></p>'

    def preview(items, kind, section_key, page_href, empty_key):
        head = section_head(*S.pair(section_key), href=page_href, label=S.zh("btn.view_all"))
        if items:
            return head + card_grid(items[:3], kind)
        return head + empty_state(
            kind=kind,
            title_zh=S.zh(empty_key + "_title"),
            title_en=S.en(empty_key + "_title"),
            lead_zh=S.zh(empty_key + "_lead"),
            lead_en=S.en(empty_key + "_lead"),
        )

    equip = ""
    names = [item.get("name", "") for item in (cfg.get("equipment") or []) + (cfg.get("antennas") or []) if item.get("name")]
    if names:
        equip = section_head(*S.pair("home.section_equip"), href="station.html", label=S.zh("btn.view_all"))
        equip += '<ul class="equip-list">' + "".join(f"<li>{esc(n)}</li>" for n in names) + "</ul>"

    cta = (
        '<section class="cta">'
        '<div class="cta-inner">'
        f'<h2>{esc(S.zh("home.cta_title"))}<small>{esc(S.en("home.cta_title"))}</small></h2>'
        f'<p>{esc(S.zh("home.cta_body") or cfg.get("qsl_via", ""))}</p>'
        f'<p class="cta-en">{esc(S.en("home.cta_body"))}</p>'
        f'<a class="btn btn-primary" href="station.html#qsl">{esc(S.zh("btn.qsl_exchange"))}</a>'
        "</div></section>"
    )

    body = f"""
<section class="hero">
  <div class="hero-copy">
    <p class="kicker">{esc(S.zh("home.kicker"))} <b>{esc(callsign)}</b> · PSE K</p>
    <h1 class="hero-call">{esc(callsign)}</h1>
    <p class="hero-tag">{esc(cfg.get("tagline") or "")}</p>
    <p class="hero-desc">{esc(desc_zh)}</p>
    <p class="hero-desc-en">{esc(desc_en)}</p>
    <div class="hero-actions">
      <a class="btn btn-primary" href="qso.html">{esc(S.zh("btn.all_qso"))}<span class="btn-en">{esc(S.en("btn.all_qso"))}</span></a>
      <a class="btn btn-ghost" href="station.html">{esc(S.zh("nav.station"))}<span class="btn-en">{esc(S.en("nav.station"))}</span></a>
    </div>
    {meta_block}
  </div>
  <aside class="hero-panel" aria-hidden="true">
    <div class="panel-head"><span>20m · 14.074</span><i class="live-dot"></i></div>
    <div class="spectrum">{spectrum_bars()}</div>
    <div class="panel-foot"><span>FT8</span><span>−18 dB</span><span>RX</span></div>
  </aside>
</section>

<section class="stats-row">{stats_html}</section>

<section class="section">{latest}</section>
<section class="section">{preview(cards, "qsl", "home.section_qsl", "qsl.html", "empty.qsl")}</section>
<section class="section">{preview(sstv, "sstv", "home.section_sstv", "sstv.html", "empty.sstv")}</section>
{f'<section class="section">{equip}</section>' if equip else ''}
{cta}
"""
    return layout(
        cfg,
        prefix="",
        active="home",
        title=f"{callsign} · {S.zh('nav.home')}",
        description=desc_zh,
        body=body,
        built_at=built_at,
        demo=demo,
    )


# ── 通联记录页 ───────────────────────────────────────────

def page_qso(cfg: dict, *, rows: list[dict], stats: dict, built_at: str, demo: bool) -> str:
    if not rows:
        empty = empty_state(
            kind="qso",
            title_zh=S.zh("empty.qso_title"),
            title_en=S.en("empty.qso_title"),
            lead_zh=S.zh("empty.qso_lead"),
            lead_en=S.en("empty.qso_lead"),
            extra=(
                '<div class="empty-guide">'
                '<p class="empty-hint">日志就是一张表格，照着表头加一行即可（用 Excel 或记事本打开 <code>data/qso.csv</code>）：</p>'
                '<pre class="snippet">date,time,call,band,mode,rst_sent,rst_rcvd,dxcc,qth,grid,notes\n'
                "2026-03-14,08:42,JA1KWF,20m,SSB,59,59,Japan,Tokyo,PM95,首次通联</pre>"
                '<p class="empty-hint">时间一律用 UTC；波段写 <code>20m</code>、<code>70cm</code> 这种形式；模式写 <code>SSB</code>、<code>FT8</code>、<code>CW</code>。</p>'
                "</div>"
            ),
        )
        body = page_head(
            kicker="QSO LOG · 通联记录",
            title=S.zh("nav.qso"),
            lead=S.zh("page.qso_lead"),
            lead_en=S.en("page.qso_lead"),
        ) + f'<section class="section">{empty}</section>'
    else:
        stat_items = [
            (str(stats["total"]), *S.pair("stat.qso"), False),
            (str(stats["dxcc"]), *S.pair("stat.dxcc"), False),
            (stats["first"], *S.pair("stat.first"), True),
            (stats["last"], *S.pair("stat.last"), True),
        ]
        stat_html = "".join(stat_block(value, zh, en, compact=compact) for value, zh, en, compact in stat_items)

        charts = (
            '<div class="chart-grid">'
            '<div class="panel"><h3 class="panel-title">'
            f'{esc(S.zh("stat.by_band"))}<small>{esc(S.en("stat.by_band"))}</small></h3>'
            f'{bar_chart(stats["bands"], kind="band")}</div>'
            '<div class="panel"><h3 class="panel-title">'
            f'{esc(S.zh("stat.months"))}<small>{esc(S.en("stat.months"))}</small></h3>'
            f'{month_spark(stats["months"])}</div>'
            "</div>"
        )

        body = (
            page_head(
                kicker="QSO LOG · 通联记录",
                title=S.zh("nav.qso"),
                lead=S.zh("page.qso_lead"),
                lead_en=S.en("page.qso_lead"),
            )
            + f'<section class="stats-row stats-row-4">{stat_html}</section>'
            + f'<section class="section">{charts}</section>'
            + f'<section class="section">{log_tools(rows, stats)}{qso_table(rows, table_id="log")}</section>'
        )

    return layout(
        cfg,
        prefix="",
        active="qso",
        title=f"{S.zh('nav.qso')} · {S.en('nav.qso')} — {cfg.get('callsign')}",
        description=S.zh("page.qso_lead"),
        body=body,
        built_at=built_at,
        demo=demo,
    )


# ── QSL / SSTV 页 ────────────────────────────────────────

def _gallery_page(cfg, *, kind: str, items: list[dict], built_at: str, demo: bool) -> str:
    is_qsl = kind == "qsl"
    nav_key = "nav.qsl" if is_qsl else "nav.sstv"
    lead_key = "page.qsl_lead" if is_qsl else "page.sstv_lead"
    empty_key = "empty.qsl" if is_qsl else "empty.sstv"
    kicker = "QSL CARDS · 交换卡片" if is_qsl else "SSTV · 慢扫描电视"

    head = page_head(kicker=kicker, title=S.zh(nav_key), lead=S.zh(lead_key), lead_en=S.en(lead_key))
    title = S.zh(nav_key) if not items else f"{S.zh(nav_key)}（{len(items)}）"

    if items:
        years = sorted({str(item["date"].year) for item in items if item["date"]}, reverse=True)
        year_opts = "".join(f'<option value="{y}">{y}</option>' for y in years)
        zh_tpl, en_tpl = S.pair("filter.count_cards")
        zh_count = zh_tpl.format(n=len(items))
        toolbar = (
            f'<div class="gallery-tools" data-count-zh="{esc(zh_tpl)}" data-count-en="{esc(en_tpl)}">'
            + '<label class="field"><span class="field-label">'
            + esc(S.zh("filter.year"))
            + f'</span><select id="gallery-year"><option value="">{esc(S.zh("filter.all_years"))}</option>{year_opts}</select></label>'
            + f'<span class="log-count" id="gallery-count">{esc(zh_count)}</span>'
            + "</div>"
        )
        gallery_html = gallery(items, kind, empty_kind=kind, empty_key=empty_key)
    else:
        toolbar = ""
        extra = (
            '<p class="empty-hint">在 <code>content/'
            + kind
            + '/</code> 里新建一个 .md（可复制 <code>_template.md</code>），把图片放在同一目录。</p>'
        )
        gallery_html = empty_state(
            kind=kind,
            title_zh=S.zh(empty_key + "_title"),
            title_en=S.en(empty_key + "_title"),
            lead_zh=S.zh(empty_key + "_lead"),
            lead_en=S.en(empty_key + "_lead"),
            extra=extra,
        )

    body = head + f'<section class="section">{toolbar}{gallery_html}</section>'

    return layout(
        cfg,
        prefix="",
        active=kind,
        title=f"{S.zh(nav_key)} · {S.en(nav_key)} — {cfg.get('callsign')}",
        description=S.zh(lead_key),
        body=body,
        built_at=built_at,
        demo=demo,
    )


def page_qsl(cfg, *, items, built_at, demo):
    return _gallery_page(cfg, kind="qsl", items=items, built_at=built_at, demo=demo)


def page_sstv(cfg, *, items, built_at, demo):
    return _gallery_page(cfg, kind="sstv", items=items, built_at=built_at, demo=demo)


# ── 随笔 ─────────────────────────────────────────────────

def page_notes(cfg, *, items: list[dict], built_at: str, demo: bool) -> str:
    head = page_head(
        kicker="NOTES · 随笔",
        title=S.zh("nav.notes"),
        lead=S.zh("page.notes_lead"),
        lead_en=S.en("page.notes_lead"),
    )

    if not items:
        content = empty_state(
            kind="notes",
            title_zh=S.zh("empty.notes_title"),
            title_en=S.en("empty.notes_title"),
            lead_zh=S.zh("empty.notes_lead"),
            lead_en=S.en("empty.notes_lead"),
            extra='<p class="empty-hint">在 <code>content/notes/</code> 新建一个 .md，写上 <code>title</code> 和 <code>date</code> 即可。</p>',
        )
    else:
        rows = []
        for item in items:
            date_txt = item["date"].isoformat() if item["date"] else ""
            tags = item["meta"].get("tags") or []
            if isinstance(tags, str):
                tags = [tags]
            tag_html = "".join(chip(str(tag), "tag") for tag in tags)
            sub = item.get("title_en") or ""
            rows.append(
                f'<li class="note-item"><a class="note-link" href="notes/{esc(item["slug"])}.html">'
                f'<time class="note-date" datetime="{esc(date_txt)}">{esc(date_txt)}</time>'
                f'<span class="note-main"><span class="note-title">{esc(item["title"])}</span>'
                f'<span class="note-sum">{esc(item["summary"])}</span></span>'
                f'<span class="note-arrow" aria-hidden="true">→</span></a>'
                f'<span class="note-tags">{tag_html}</span></li>'
            )
        content = f'<ul class="note-list">{"".join(rows)}</ul>'

    body = head + f'<section class="section">{content}</section>'
    return layout(
        cfg,
        prefix="",
        active="notes",
        title=f"{S.zh('nav.notes')} · {S.en('nav.notes')} — {cfg.get('callsign')}",
        description=S.zh("page.notes_lead"),
        body=body,
        built_at=built_at,
        demo=demo,
    )


def page_note(cfg, *, item: dict, built_at: str, demo: bool) -> str:
    date_txt = item["date"].isoformat() if item["date"] else ""
    tags = item["meta"].get("tags") or []
    if isinstance(tags, str):
        tags = [tags]
    tag_html = "".join(chip(str(tag), "tag") for tag in tags)
    sub = f'<p class="note-sub">{esc(item["title_en"])}</p>' if item.get("title_en") else ""
    body = f"""
<article class="prose">
  <header class="note-head">
    <p class="kicker">NOTES · 随笔</p>
    <h1 class="page-title">{esc(item["title"])}</h1>
    {sub}
    <p class="note-meta"><time datetime="{esc(date_txt)}">{esc(date_txt)}</time>{tag_html}</p>
  </header>
  {item["body_html"]}
  <footer class="note-foot"><a class="link-arrow" href="../notes.html"><span aria-hidden="true">←</span>{esc(S.zh("btn.back_notes"))}</a></footer>
</article>
"""
    return layout(
        cfg,
        prefix="../",
        active="notes",
        title=f"{item['title']} — {cfg.get('callsign')}",
        description=item["summary"] or item["title"],
        body=body,
        built_at=built_at,
        demo=demo,
    )


# ── 电台室 ───────────────────────────────────────────────

def _spec_table(rows: list[dict], empty_hint: str) -> str:
    if not rows:
        return f'<p class="muted">{esc(empty_hint)}</p>'
    body = "".join(
        "<tr>"
        f'<td class="spec-name">{esc(item.get("name", ""))}</td>'
        f'<td>{esc(item.get("role", ""))}</td>'
        f'<td class="muted">{esc(item.get("note", ""))}</td>'
        "</tr>"
        for item in rows
    )
    head = (
        "<thead><tr>"
        f'<th scope="col">{esc(S.zh("station.col_item"))}</th>'
        f'<th scope="col">{esc(S.zh("station.col_role"))}</th>'
        f'<th scope="col">{esc(S.zh("station.col_note"))}</th>'
        "</tr></thead>"
    )
    return f'<table class="spec-table">{head}<tbody>{body}</tbody></table>'


def page_station(cfg: dict, *, stats: dict, built_at: str, demo: bool) -> str:
    qth_rows = "".join(
        f"<div><dt>{esc(label)}</dt><dd>{dash(value)}</dd></div>"
        for label, value in (
            ("QTH", cfg.get("qth")),
            ("网格 / Grid", cfg.get("grid")),
            ("操作证书 / License", cfg.get("license")),
            ("入坑年份 / Since", cfg.get("since")),
        )
    )

    contact_links = []
    if cfg.get("email"):
        contact_links.append(f'<a class="btn btn-primary" href="mailto:{esc(cfg["email"])}">{esc(cfg["email"])}</a>')
    if cfg.get("github"):
        contact_links.append(
            f'<a class="btn btn-ghost" href="{esc(cfg["github"])}" target="_blank" rel="noopener">GitHub</a>'
        )

    qsl_zh = S.zh("home.cta_body")
    qsl_en = S.en("home.cta_body")
    qsl_note = cfg.get("qsl_via")
    qsl_note_en = cfg.get("qsl_via_en")

    intro = ""

    body = f"""
{page_head(kicker="STATION · 电台室", title=S.zh("nav.station"), lead=S.zh("page.station_lead"), lead_en=S.en("page.station_lead"))}
{intro}
<section class="station-grid">
  <div class="panel">
    <h2 class="panel-title">{esc(S.zh("station.qth"))}<small>{esc(S.en("station.qth"))}</small></h2>
    <dl class="kv">{qth_rows}</dl>
  </div>
  <div class="panel" id="qsl">
    <h2 class="panel-title">{esc(S.zh("station.qsl"))}<small>{esc(S.en("station.qsl"))}</small></h2>
    <p>{esc(qsl_note or qsl_zh)}</p>
    {f'<p class="muted">{esc(qsl_note_en)}</p>' if qsl_note_en else f'<p class="muted">{esc(qsl_en)}</p>'}
  </div>
  <div class="panel">
    <h2 class="panel-title">{esc(S.zh("station.equipment"))}<small>{esc(S.en("station.equipment"))}</small></h2>
    {_spec_table(cfg.get("equipment") or [], S.zh("station.empty_item"))}
  </div>
  <div class="panel">
    <h2 class="panel-title">{esc(S.zh("station.antennas"))}<small>{esc(S.en("station.antennas"))}</small></h2>
    {_spec_table(cfg.get("antennas") or [], S.zh("station.empty_item"))}
  </div>
  <div class="panel">
    <h2 class="panel-title">{esc(S.zh("station.software"))}<small>{esc(S.en("station.software"))}</small></h2>
    {_spec_table(cfg.get("software") or [], S.zh("station.empty_item"))}
  </div>
  <div class="panel">
    <h2 class="panel-title">{esc(S.zh("station.contact"))}<small>{esc(S.en("station.contact"))}</small></h2>
    <p>{esc(S.zh("station.contact_lead"))}</p>
    <div class="contact-actions">{''.join(contact_links) or f'<span class="muted">{esc(S.zh("station.empty_item"))}</span>'}</div>
  </div>
</section>
"""
    return layout(
        cfg,
        prefix="",
        active="station",
        title=f"{S.zh('nav.station')} · {S.en('nav.station')} — {cfg.get('callsign')}",
        description=S.zh("page.station_lead"),
        body=body,
        built_at=built_at,
        demo=demo,
    )


# ── 404 ──────────────────────────────────────────────────

def page_404(cfg: dict, *, built_at: str, demo: bool = False) -> str:
    body = f"""
<section class="notfound">
  <p class="kicker">404</p>
  <h1 class="page-title">{esc(S.zh("404.title"))}</h1>
  <p class="page-lead">{esc(S.zh("404.lead"))}</p>
  <p class="page-lead-en">{esc(S.en("404.lead"))}</p>
  <a class="btn btn-primary" href="index.html">{esc(S.zh("404.btn"))}</a>
</section>
"""
    return layout(
        cfg,
        prefix="",
        active="404",
        title=f"404 — {cfg.get('callsign')}",
        description=S.zh("404.lead"),
        body=body,
        built_at=built_at,
        demo=demo,
    )
