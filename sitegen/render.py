"""页面渲染：按语言生成单语页面。

中文站：/            英文站：/en/
每种语言只出现自己的文字，不再同屏双语。
"""

from __future__ import annotations

import html
import math
import random
import re
from datetime import datetime, timedelta, timezone

from . import __version__, data
from . import strings as S

TZ = timezone(timedelta(hours=8))

NAV = [
    ("index.html", "nav.home", "home"),
    ("qso.html", "nav.qso", "qso"),
    ("qsl.html", "nav.qsl", "qsl"),
    ("sstv.html", "nav.sstv", "sstv"),
    ("notes.html", "nav.notes", "notes"),
    ("station.html", "nav.station", "station"),
]

KICKERS = {
    "qso": "QSO LOG",
    "qsl": "QSL CARDS",
    "sstv": "SSTV",
    "notes": "NOTES",
    "station": "STATION",
    "notfound": "404",
}

ICONS = {
    "qso": '<svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M4 7h16M4 12h16M4 17h10"/></svg>',
    "qsl": '<svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="6" width="18" height="12" rx="2"/><path d="M7 10h4M7 14h6"/><circle cx="17" cy="10.5" r="1.6"/></svg>',
    "sstv": '<svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="8.5" cy="10" r="1.6"/><path d="M21 16l-5-5-7 7"/></svg>',
    "notes": '<svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M6 3h9l4 4v14H6z"/><path d="M14 3v5h5M9 13h7M9 17h5"/></svg>',
    "wave": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M2 12h3l2-6 3 12 3-9 2 6h3l2-4h2"/></svg>',
    "sun": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><circle cx="12" cy="12" r="4.2"/><path d="M12 2.6v2.2M12 19.2v2.2M2.6 12h2.2M19.2 12h2.2M5.4 5.4l1.6 1.6M17 17l1.6 1.6M18.6 5.4L17 7M7 17l-1.6 1.6"/></svg>',
    "moon": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M20 14.5A8.2 8.2 0 1 1 9.5 4a6.6 6.6 0 0 0 10.5 10.5z"/></svg>',
    "auto": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="12" cy="12" r="7"/><path d="M12 5a7 7 0 0 1 0 14z" fill="currentColor" stroke="none"/></svg>',
}


def esc(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def t(lang: str, key: str) -> str:
    return S.tr(lang, key)


def url(prefix: str, path: str) -> str:
    """把站点内相对路径拼上当前页面前缀。"""
    if not path:
        return prefix or "./"
    return prefix + path


class Ctx:
    """一次构建里所有页面共享的数据。"""

    def __init__(self, cfg: dict, *, rows, stats, cards, sstv, notes, built_at: str, demo: bool):
        self.cfg = cfg
        self.rows = rows
        self.stats = stats
        self.cards = cards
        self.sstv = sstv
        self.notes = notes
        self.built_at = built_at
        self.demo = demo
        # 资源版本号：每次构建都会变，避免 CDN / 浏览器缓存旧样式
        self.build_id = re.sub(r"[^0-9]", "", built_at) or __version__

    def description(self, lang: str) -> str:
        if lang == "en":
            return self.cfg.get("description_en") or self.cfg.get("description") or ""
        return self.cfg.get("description") or ""

    def tagline(self, lang: str) -> str:
        if lang == "en":
            return self.cfg.get("tagline_en") or self.cfg.get("tagline") or ""
        return self.cfg.get("tagline") or ""

    def license(self, lang: str) -> str:
        if lang == "en":
            return self.cfg.get("license_en") or self.cfg.get("license") or ""
        return self.cfg.get("license") or ""

    def qsl_note(self, lang: str) -> str:
        if lang == "en":
            return self.cfg.get("qsl_via_en") or self.cfg.get("qsl_via") or ""
        return self.cfg.get("qsl_via") or ""


# ── 小标签 ───────────────────────────────────────────────


def _band_class(band: str) -> str:
    return "band-" + re.sub(r"[^a-z0-9]+", "-", band.lower()).strip("-")


def band_chip(band: str, extra: str = "") -> str:
    if not band:
        return ""
    return f'<span class="chip band {_band_class(band)} {extra}">{esc(band)}</span>'


def mode_chip(mode: str, lang: str, extra: str = "") -> str:
    if not mode:
        return ""
    cls = data.MODE_CLASSES.get(mode, "other")
    return f'<span class="chip mode mode-{cls} {extra}">{esc(mode)}</span>'


def chip(text, variant: str = "") -> str:
    if not text:
        return ""
    return f'<span class="chip {variant}">{esc(text)}</span>'


def dash(value, tone: str = "muted") -> str:
    text = "" if value is None else str(value).strip()
    return esc(text) if text else f'<span class="{tone}">—</span>'


# ── 版面 ─────────────────────────────────────────────────


def _header_tools(ctx: Ctx, lang: str, prefix: str, page_path: str) -> str:
    other = S.other(lang)
    switch_target = url(prefix, ("en/" if lang == "zh" else "") + page_path)
    switch_label = "EN" if lang == "zh" else "中文"
    switch_aria = t(lang, "a11y.to_en") if lang == "zh" else t(lang, "a11y.to_zh")

    github = ""
    if ctx.cfg.get("github"):
        github = (
            f'<a class="tool tool-gh" href="{esc(ctx.cfg["github"])}" target="_blank" rel="noopener">'
            "GitHub</a>"
        )

    return (
        '<div class="header-tools">'
        f'<a class="tool tool-lang" href="{esc(switch_target)}" hreflang="{other}" '
        f'title="{esc(switch_aria)}" aria-label="{esc(switch_aria)}">{esc(switch_label)}</a>'
        f'<button class="tool tool-icon theme-toggle" id="theme-toggle" type="button" '
        f'aria-label="{esc(t(lang, "a11y.theme"))}" title="{esc(t(lang, "theme.auto"))}" '
        f'data-label-auto="{esc(t(lang, "theme.auto"))}" '
        f'data-label-light="{esc(t(lang, "theme.light"))}" '
        f'data-label-dark="{esc(t(lang, "theme.dark"))}">'
        f'<span class="icon icon-auto">{ICONS["auto"]}</span>'
        f'<span class="icon icon-sun">{ICONS["sun"]}</span>'
        f'<span class="icon icon-moon">{ICONS["moon"]}</span>'
        "</button>"
        f"{github}"
        "</div>"
    )


def _nav_html(ctx: Ctx, lang: str, active: str, prefix: str) -> str:
    items = []
    for href, key, key_active in NAV:
        current = ' aria-current="page"' if active == key_active else ""
        cls = "nav-link is-active" if active == key_active else "nav-link"
        items.append(
            f'<a class="{cls}" href="{url(prefix, href)}"{current}>{esc(t(lang, key))}</a>'
        )
    return "".join(items)


def layout(
    ctx: Ctx,
    lang: str,
    *,
    prefix: str,
    page_path: str,
    active: str,
    title: str,
    description: str,
    body: str,
) -> str:
    cfg = ctx.cfg
    callsign = cfg.get("callsign", "")
    tagline = ctx.tagline(lang) or "Amateur Radio"
    nav_items = _nav_html(ctx, lang, active, prefix)
    tools = _header_tools(ctx, lang, prefix, page_path)
    lang_attr = "zh-CN" if lang == "zh" else "en"

    demo_bar = ""
    if ctx.demo:
        demo_bar = f'<div class="demo-bar">{esc(t(lang, "misc.demo"))}</div>'

    alternates = ""
    if cfg.get("url"):
        base = cfg["url"].rstrip("/")
        alternates = (
            f'<link rel="alternate" hreflang="zh-CN" href="{esc(base + "/" + page_path)}">'
            f'<link rel="alternate" hreflang="en" href="{esc(base + "/en/" + page_path)}">'
        )

    footer_links = "".join(
        f'<li><a href="{url(prefix, href)}">{esc(t(lang, key))}</a></li>' for href, key, _ in NAV
    )
    contact_items = []
    if cfg.get("email"):
        contact_items.append(f'<li><a href="mailto:{esc(cfg["email"])}">{esc(cfg["email"])}</a></li>')
    if cfg.get("github"):
        contact_items.append(
            f'<li><a href="{esc(cfg["github"])}" target="_blank" rel="noopener">GitHub</a></li>'
        )
    contact_items.append(f'<li><a href="{url(prefix, "station.html")}#qsl">QSL</a></li>')

    return f"""<!doctype html>
<html lang="{lang_attr}" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<meta name="color-scheme" content="light dark">
<meta name="theme-color" content="#0f1a14">
<meta name="generator" content="bg5hlc-sitegen {__version__}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{esc(callsign)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
{alternates}
<link rel="icon" href="{url(prefix, "assets/favicon.svg")}" type="image/svg+xml">
<script>
(function () {{
  var root = document.documentElement;
  var saved = null;
  try {{ saved = localStorage.getItem("bg5hlc-theme"); }} catch (e) {{}}
  var mode = (saved === "light" || saved === "dark" || saved === "auto") ? saved : "auto";
  var dark = window.matchMedia ? window.matchMedia("(prefers-color-scheme: dark)").matches : true;
  root.setAttribute("data-theme-mode", mode);
  root.setAttribute("data-theme", mode === "auto" ? (dark ? "dark" : "light") : mode);
}})();
</script>
<link rel="stylesheet" href="{url(prefix, "assets/css/style.css")}?v={ctx.build_id}">
</head>
<body class="page-{esc(active)}">
{demo_bar}
<a class="skip-link" href="#main">{esc(t(lang, "a11y.skip"))}</a>
<header class="site-header">
  <div class="wrap header-inner">
    <a class="brand" href="{url(prefix, "index.html")}" aria-label="{esc(callsign)} — {esc(t(lang, "a11y.home"))}">
      <span class="brand-mark" aria-hidden="true">{ICONS["wave"]}</span>
      <span class="brand-text"><strong>{esc(callsign)}</strong><small>{esc(tagline)}</small></span>
    </a>
    <nav class="site-nav" aria-label="nav">{nav_items}</nav>
    {tools}
  </div>
</header>
<main id="main" class="wrap">
{body}
</main>
<footer class="site-footer">
  <div class="wrap footer-grid">
    <div class="footer-col footer-about">
      <span class="footer-call">{esc(callsign)}</span>
      <p>{esc(ctx.description(lang))}</p>
    </div>
    <div class="footer-col">
      <h2>{esc(t(lang, "footer.nav"))}</h2>
      <ul class="footer-links">{footer_links}</ul>
    </div>
    <div class="footer-col">
      <h2>{esc(t(lang, "footer.contact"))}</h2>
      <ul class="footer-links">{"".join(contact_items)}</ul>
    </div>
  </div>
  <div class="footer-big" aria-hidden="true">73 DE {esc(callsign)}</div>
  <div class="wrap footer-bottom">
    <span>© {datetime.now(TZ).year} {esc(callsign)}</span>
    <span>{esc(t(lang, "footer.made"))}</span>
    <span>{esc(t(lang, "footer.built"))} {esc(ctx.built_at)}</span>
  </div>
</footer>
<div class="lightbox" id="lightbox" hidden>
  <button class="lightbox-close" type="button" aria-label="close">×</button>
  <figure class="lightbox-figure">
    <img id="lightbox-img" src="" alt="">
    <figcaption id="lightbox-cap"></figcaption>
  </figure>
</div>
<script src="{url(prefix, "assets/js/app.js")}?v={ctx.build_id}" defer></script>
</body>
</html>"""


def page_head(*, kicker: str, title: str, lead: str) -> str:
    return (
        '<section class="page-head">'
        f'<p class="kicker">{esc(kicker)}</p>'
        f'<h1 class="page-title">{esc(title)}</h1>'
        f'<p class="page-lead">{esc(lead)}</p>'
        "</section>"
    )


def section_head(title: str, href: str = "", label: str = "") -> str:
    more = (
        f'<a class="section-more" href="{esc(href)}">{esc(label)}<span aria-hidden="true">→</span></a>'
        if href
        else ""
    )
    return f'<div class="section-head"><h2 class="section-title">{esc(title)}</h2>{more}</div>'


def stat_block(value: str, label: str, empty: bool = False, compact: bool = False) -> str:
    cls = "stat-value"
    if empty:
        cls += " is-empty"
    if compact:
        cls += " is-compact"
    return (
        f'<div class="stat"><span class="{cls}">{esc(value)}</span>'
        f'<span class="stat-label">{esc(label)}</span></div>'
    )


def empty_state(*, kind: str, title: str, lead: str, extra: str = "") -> str:
    return (
        '<div class="empty-state">'
        f'{ICONS.get(kind, ICONS["notes"])}'
        f'<h3 class="empty-title">{esc(title)}</h3>'
        f'<p class="empty-lead">{esc(lead)}</p>'
        f"{extra}"
        "</div>"
    )


# ── 通联表格 ─────────────────────────────────────────────


def _rst(row: dict) -> str:
    sent, rcvd = row.get("rst_sent", ""), row.get("rst_rcvd", "")
    if sent and rcvd:
        return f'{esc(sent)}<span class="sep">/</span>{esc(rcvd)}'
    return esc(sent or rcvd)


def _row_html(row: dict, lang: str) -> str:
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
        f'<td class="cell-mode">{mode_chip(row.get("mode", ""), lang)}</td>'
        f'<td class="cell-rst">{_rst(row)}</td>'
        f'<td class="cell-place">{esc(place)}</td>'
        f'<td class="cell-notes">{esc(row.get("notes", ""))}</td>'
        "</tr>"
    )


def _thead(lang: str, sortable: bool = True) -> str:
    heads = [
        ("date", "th.date", "descending"),
        ("time", "th.time", ""),
        ("call", "th.call", ""),
        ("band", "th.band", ""),
        ("mode", "th.mode", ""),
        ("rst", "th.rst", ""),
        ("place", "th.dxcc", ""),
        ("notes", "th.notes", ""),
    ]
    cells = []
    for key, label, aria in heads:
        text = esc(t(lang, label))
        aria_attr = f' aria-sort="{aria}"' if aria else ""
        if sortable and key in ("date", "time", "call", "band", "mode"):
            cells.append(
                f'<th scope="col" class="sortable th-{key}" data-key="{key}"{aria_attr}>'
                f'<button type="button" class="th-btn">{text}</button></th>'
            )
        else:
            cells.append(f'<th scope="col" class="th-{key}"><span class="th-static">{text}</span></th>')
    return f'<thead><tr>{"".join(cells)}</tr></thead>'


def qso_table(rows: list[dict], lang: str, *, limit: int | None = None, table_id: str = "log", sortable: bool = True) -> str:
    shown = rows if limit is None else rows[:limit]
    body = "".join(_row_html(row, lang) for row in shown)
    return (
        '<div class="table-wrap">'
        f'<table class="log" id="{table_id}">{_thead(lang, sortable)}'
        f'<tbody id="{table_id}-body">{body}</tbody></table>'
        f'<p class="log-empty" id="{table_id}-empty" hidden>{esc(t(lang, "filter.none"))}</p>'
        "</div>"
        f'<p class="table-hint">{esc(t(lang, "filter.swipe"))}</p>'
    )


def log_tools(rows: list[dict], stats: dict, lang: str) -> str:
    bands = sorted(
        {row["band"] for row in rows if row["band"]},
        key=lambda b: (data.BAND_LIST.index(b) if b in data.BAND_LIST else 99, b),
    )
    modes = sorted({row["mode"] for row in rows if row["mode"]})
    band_opts = "".join(f'<option value="{esc(b)}">{esc(b)}</option>' for b in bands)
    mode_opts = "".join(f'<option value="{esc(m)}">{esc(m)}</option>' for m in modes)
    template = t(lang, "filter.count")
    total = S.fmt(lang, "filter.count", n=stats["total"])
    return (
        f'<div class="log-tools" data-count="{esc(template)}">'
        '<label class="field field-search">'
        f'<span class="field-label sr-only">{esc(t(lang, "filter.search"))}</span>'
        f'<input type="search" id="qso-search" placeholder="{esc(t(lang, "filter.search"))}" autocomplete="off">'
        "</label>"
        '<label class="field">'
        f'<span class="field-label">{esc(t(lang, "filter.band"))}</span>'
        f'<select id="qso-band"><option value="">{esc(t(lang, "filter.all_bands"))}</option>{band_opts}</select>'
        "</label>"
        '<label class="field">'
        f'<span class="field-label">{esc(t(lang, "filter.mode"))}</span>'
        f'<select id="qso-mode"><option value="">{esc(t(lang, "filter.all_modes"))}</option>{mode_opts}</select>'
        "</label>"
        f'<button type="button" class="btn btn-ghost btn-sm" id="qso-reset">{esc(t(lang, "btn.reset"))}</button>'
        f'<span class="log-count" id="qso-count">{esc(total)}</span>'
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
            f'<span class="spark-bar{empty_cls}" style="height:{height}%" title="{esc(key)} · {count}"></span>'
            f'<span class="spark-x">{esc(label)}</span></div>'
        )
    return f'<div class="spark">{"".join(cols)}</div>'


# ── 卡片 ─────────────────────────────────────────────────


def _media(entry: dict, kind: str, prefix: str, caption: str) -> str:
    full = entry.get("image_url", "")
    thumb = entry.get("thumb_url", "")
    if not thumb:
        return '<span class="card-media is-empty"><span class="media-hint">no image</span></span>'
    alt = f"{entry['meta'].get('call', '')} {kind}".strip()
    return (
        f'<a class="card-media" href="{url(prefix, full or thumb)}" data-lightbox data-caption="{esc(caption)}">'
        f'<img src="{url(prefix, thumb)}" alt="{esc(alt)}" loading="lazy" decoding="async">'
        "</a>"
    )


def qsl_card(entry: dict, lang: str, prefix: str) -> str:
    meta = entry["meta"]
    call = str(meta.get("call", "") or "")
    date_txt = entry["date"].isoformat() if entry["date"] else ""
    caption = " · ".join(x for x in (call, date_txt) if x)
    chips = "".join(
        [
            band_chip(str(meta.get("band", "") or "")),
            mode_chip(str(meta.get("mode", "") or "").upper(), lang),
            chip(str(meta.get("via", "") or ""), "via"),
        ]
    )
    body = data.pick(entry, lang, "body_html")
    body_html = f'<div class="card-text">{body}</div>' if body else ""
    sample = f'<span class="card-flag">{esc(t(lang, "misc.demo_badge"))}</span>' if entry.get("is_placeholder") else ""
    return (
        '<article class="card">'
        f"{_media(entry, 'qsl', prefix, caption)}{sample}"
        '<div class="card-body">'
        f'<div class="card-head"><h3 class="card-call">{esc(call)}</h3>'
        f'<time class="card-date" datetime="{esc(date_txt)}">{esc(date_txt)}</time></div>'
        f'<div class="card-chips">{chips}</div>{body_html}'
        "</div></article>"
    )


def sstv_card(entry: dict, lang: str, prefix: str) -> str:
    meta = entry["meta"]
    call = str(meta.get("call", "") or "")
    date_txt = entry["date"].isoformat() if entry["date"] else ""
    freq = str(meta.get("freq", "") or "")
    caption = " · ".join(x for x in (call, freq, date_txt) if x)
    chips = "".join([chip(freq, "freq"), mode_chip(str(meta.get("mode", "") or "").upper(), lang)])
    body = data.pick(entry, lang, "body_html")
    note = data.pick(entry, lang, "note")
    body_html = f'<div class="card-text">{body}</div>' if body else ""
    if note:
        body_html += f'<p class="card-note">{esc(note)}</p>'
    return (
        '<article class="card card-sstv">'
        f"{_media(entry, 'sstv', prefix, caption)}"
        '<div class="card-body">'
        f'<div class="card-head"><h3 class="card-call">{esc(call)}</h3>'
        f'<time class="card-date" datetime="{esc(date_txt)}">{esc(date_txt)}</time></div>'
        f'<div class="card-chips">{chips}</div>{body_html}'
        "</div></article>"
    )


def card_grid(items: list[dict], kind: str, lang: str, prefix: str) -> str:
    render_one = qsl_card if kind == "qsl" else sstv_card
    return f'<div class="card-grid">{"".join(render_one(item, lang, prefix) for item in items)}</div>'


def gallery(items: list[dict], kind: str, lang: str, prefix: str, empty_key: str) -> str:
    if not items:
        return empty_state(
            kind=kind,
            title=t(lang, empty_key + "_title"),
            lead=t(lang, empty_key + "_lead"),
            extra=f'<p class="empty-hint">{esc(t(lang, "empty.card_hint"))}</p>',
        )

    blocks = []
    for year, group in data.group_by_year(items):
        blocks.append(
            f'<section class="year-group" data-year="{esc(year)}">'
            f'<h2 class="year-title">{esc(year)}<small>{len(group)}</small></h2>'
            f"{card_grid(group, kind, lang, prefix)}</section>"
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


def page_home(ctx: Ctx, lang: str, prefix: str, page_path: str) -> str:
    cfg, stats = ctx.cfg, ctx.stats
    callsign = cfg.get("callsign", "")

    stat_items = [
        (str(stats["total"]) if stats["total"] else "—", t(lang, "stat.qso")),
        (str(stats["dxcc"]) if stats["dxcc"] else "—", t(lang, "stat.dxcc")),
        (str(len(ctx.cards)) if ctx.cards else "—", t(lang, "stat.qsl")),
        (str(len(ctx.sstv)) if ctx.sstv else "—", t(lang, "stat.sstv")),
        (str(stats["band_count"]) if stats["band_count"] else "—", t(lang, "stat.bands")),
    ]
    stats_html = "".join(stat_block(v, label, empty=(v == "—")) for v, label in stat_items)

    meta_items = [
        (t(lang, "home.meta_qth"), cfg.get("qth")),
        (t(lang, "home.meta_grid"), cfg.get("grid")),
        (t(lang, "home.meta_license"), ctx.license(lang)),
    ]
    meta_items = [(k, v) for k, v in meta_items if str(v or "").strip()]
    meta_block = ""
    if meta_items:
        meta_block = '<ul class="hero-meta">' + "".join(
            f"<li><span>{esc(k)}</span><b>{esc(v)}</b></li>" for k, v in meta_items
        ) + "</ul>"

    if ctx.rows:
        latest = section_head(
            t(lang, "home.section_latest"), url(prefix, "qso.html"), t(lang, "btn.view_all")
        ) + qso_table(ctx.rows, lang, limit=5, table_id="latest", sortable=False)
    else:
        latest = section_head(t(lang, "home.section_latest")) + empty_state(
            kind="qso",
            title=t(lang, "empty.qso_title"),
            lead=t(lang, "empty.qso_lead"),
            extra=(
                f'<p class="empty-hint">{esc(t(lang, "empty.home_hint"))}</p>'
                '<pre class="snippet">2026-03-14,08:42,JA1KWF,20m,SSB,59,59,Japan,Tokyo,PM95,first QSO</pre>'
            ),
        )
        latest += (
            '<p class="section-foot">'
            f'<a class="link-arrow" href="{url(prefix, "qso.html")}">{esc(t(lang, "btn.all_qso"))}'
            '<span aria-hidden="true">→</span></a></p>'
        )

    def preview(items, kind, section_key, page_href, empty_key):
        head = section_head(t(lang, section_key), url(prefix, page_href), t(lang, "btn.view_all"))
        if items:
            return head + card_grid(items[:3], kind, lang, prefix)
        return head + empty_state(
            kind=kind,
            title=t(lang, empty_key + "_title"),
            lead=t(lang, empty_key + "_lead"),
            extra=f'<p class="empty-hint">{esc(t(lang, "empty.card_hint"))}</p>',
        )

    equip = ""
    names = [
        item.get("name", "")
        for item in (cfg.get("equipment") or []) + (cfg.get("antennas") or [])
        if item.get("name")
    ]
    if names:
        equip = section_head(
            t(lang, "home.section_equip"), url(prefix, "station.html"), t(lang, "btn.view_all")
        )
        equip += '<ul class="equip-list">' + "".join(f"<li>{esc(n)}</li>" for n in names) + "</ul>"

    cta = (
        '<section class="cta">'
        '<div class="cta-inner">'
        f'<h2>{esc(t(lang, "home.cta_title"))}</h2>'
        f'<p>{esc(ctx.qsl_note(lang) or t(lang, "home.cta_body"))}</p>'
        f'<a class="btn btn-primary" href="{url(prefix, "station.html")}#qsl">{esc(t(lang, "btn.qsl_exchange"))}</a>'
        "</div></section>"
    )

    equipment = cfg.get("equipment") or []
    rig_name = (equipment[0].get("name") if equipment else "") or "IC-7300"
    marquee = t(lang, "marquee")

    body = f"""
<section class="hero">
  <div class="hero-copy">
    <p class="kicker">CQ CQ CQ · DE <b>{esc(callsign)}</b> · PSE K</p>
    <h1 class="hero-call">{esc(callsign)}</h1>
    <p class="hero-tag">{esc(ctx.tagline(lang))}</p>
    <p class="hero-desc">{esc(ctx.description(lang))}</p>
    <div class="hero-actions">
      <a class="btn btn-primary" href="{url(prefix, "qso.html")}">{esc(t(lang, "btn.all_qso"))}</a>
      <a class="btn btn-ghost" href="{url(prefix, "station.html")}">{esc(t(lang, "nav.station"))}</a>
    </div>
    {meta_block}
  </div>
  <aside class="hero-panel" aria-hidden="true">
    <div class="panel-bar panel-bar-top">
      <span class="panel-status"><i class="live-dot"></i>{esc(rig_name)} · RX</span>
      <span class="panel-freq">14.074.000</span>
    </div>
    <div class="spectrum">{spectrum_bars()}</div>
    <div class="panel-bar panel-bar-bottom">
      <span class="morse">-... --. ..... .... .-.. -.-.</span>
      <span>USB · 20m</span>
    </div>
  </aside>
</section>

<div class="marquee" aria-hidden="true">
  <div class="marquee-track">
    <span>{esc(marquee)} ✺ </span><span>{esc(marquee)} ✺ </span>
  </div>
</div>

<section class="stats-row">{stats_html}</section>

<section class="section">{latest}</section>
<section class="section">{preview(ctx.cards, "qsl", "home.section_qsl", "qsl.html", "empty.qsl")}</section>
<section class="section">{preview(ctx.sstv, "sstv", "home.section_sstv", "sstv.html", "empty.sstv")}</section>
{f'<section class="section">{equip}</section>' if equip else ''}
{cta}
"""
    return layout(
        ctx,
        lang,
        prefix=prefix,
        page_path=page_path,
        active="home",
        title=f"{callsign} · {t(lang, 'nav.home')}",
        description=ctx.description(lang),
        body=body,
    )


# ── 通联记录 ─────────────────────────────────────────────


def page_qso(ctx: Ctx, lang: str, prefix: str, page_path: str) -> str:
    head = page_head(
        kicker=KICKERS["qso"],
        title=t(lang, "nav.qso"),
        lead=t(lang, "page.qso_lead"),
    )

    if not ctx.rows:
        empty = empty_state(
            kind="qso",
            title=t(lang, "empty.qso_title"),
            lead=t(lang, "empty.qso_lead"),
            extra=(
                '<div class="empty-guide">'
                f'<p class="empty-hint">{esc(t(lang, "empty.qso_hint"))}</p>'
                '<pre class="snippet">date,time,call,band,mode,rst_sent,rst_rcvd,dxcc,qth,grid,notes\n'
                "2026-03-14,08:42,JA1KWF,20m,SSB,59,59,Japan,Tokyo,PM95,first QSO</pre>"
                f'<p class="empty-hint">{esc(t(lang, "empty.qso_note"))}</p>'
                "</div>"
            ),
        )
        body = head + f'<section class="section">{empty}</section>'
    else:
        stats = ctx.stats
        values = [
            (str(stats["total"]), t(lang, "stat.qso"), False),
            (str(stats["dxcc"]), t(lang, "stat.dxcc"), False),
            (stats["first"], t(lang, "stat.first"), True),
            (stats["last"], t(lang, "stat.last"), True),
        ]
        stat_html = "".join(
            stat_block(value, label, compact=compact) for value, label, compact in values
        )
        charts = (
            '<div class="chart-grid">'
            f'<div class="panel"><h3 class="panel-title">{esc(t(lang, "stat.by_band"))}</h3>'
            f'{bar_chart(stats["bands"], kind="band")}</div>'
            f'<div class="panel"><h3 class="panel-title">{esc(t(lang, "stat.months"))}</h3>'
            f'{month_spark(stats["months"])}</div>'
            "</div>"
        )
        body = (
            head
            + f'<section class="stats-row stats-row-4">{stat_html}</section>'
            + f'<section class="section">{charts}</section>'
            + f'<section class="section">{log_tools(ctx.rows, stats, lang)}{qso_table(ctx.rows, lang, table_id="log")}</section>'
        )

    return layout(
        ctx,
        lang,
        prefix=prefix,
        page_path=page_path,
        active="qso",
        title=f"{t(lang, 'nav.qso')} — {ctx.cfg.get('callsign')}",
        description=t(lang, "page.qso_lead"),
        body=body,
    )


# ── 相册 ─────────────────────────────────────────────────


def _gallery_page(ctx: Ctx, lang: str, prefix: str, page_path: str, kind: str) -> str:
    is_qsl = kind == "qsl"
    items = ctx.cards if is_qsl else ctx.sstv
    nav_key = "nav.qsl" if is_qsl else "nav.sstv"
    lead_key = "page.qsl_lead" if is_qsl else "page.sstv_lead"
    empty_key = "empty.qsl" if is_qsl else "empty.sstv"

    head = page_head(kicker=KICKERS[kind], title=t(lang, nav_key), lead=t(lang, lead_key))
    title = t(lang, nav_key) if not items else f"{t(lang, nav_key)} ({len(items)})"

    if items:
        years = sorted({str(item["date"].year) for item in items if item["date"]}, reverse=True)
        year_opts = "".join(f'<option value="{y}">{y}</option>' for y in years)
        template = t(lang, "filter.count_cards")
        total = S.fmt(lang, "filter.count_cards", n=len(items))
        toolbar = (
            f'<div class="gallery-tools" data-count="{esc(template)}">'
            '<label class="field">'
            f'<span class="field-label">{esc(t(lang, "filter.year"))}</span>'
            f'<select id="gallery-year"><option value="">{esc(t(lang, "filter.all_years"))}</option>{year_opts}</select>'
            "</label>"
            f'<span class="log-count" id="gallery-count">{esc(total)}</span>'
            "</div>"
        )
        content = gallery(items, kind, lang, prefix, empty_key)
    else:
        toolbar = ""
        content = gallery(items, kind, lang, prefix, empty_key)

    body = head + f'<section class="section">{toolbar}{content}</section>'
    return layout(
        ctx,
        lang,
        prefix=prefix,
        page_path=page_path,
        active=kind,
        title=f"{title} — {ctx.cfg.get('callsign')}",
        description=t(lang, lead_key),
        body=body,
    )


def page_qsl(ctx: Ctx, lang: str, prefix: str, page_path: str) -> str:
    return _gallery_page(ctx, lang, prefix, page_path, "qsl")


def page_sstv(ctx: Ctx, lang: str, prefix: str, page_path: str) -> str:
    return _gallery_page(ctx, lang, prefix, page_path, "sstv")


# ── 随笔 ─────────────────────────────────────────────────


def page_notes(ctx: Ctx, lang: str, prefix: str, page_path: str) -> str:
    head = page_head(kicker=KICKERS["notes"], title=t(lang, "nav.notes"), lead=t(lang, "page.notes_lead"))

    if not ctx.notes:
        content = empty_state(
            kind="notes",
            title=t(lang, "empty.notes_title"),
            lead=t(lang, "empty.notes_lead"),
            extra=f'<p class="empty-hint">{esc(t(lang, "empty.notes_hint"))}</p>',
        )
    else:
        rows = []
        for item in ctx.notes:
            date_txt = item["date"].isoformat() if item["date"] else ""
            raw_tags = data.pick_meta(item, lang, "tags") or []
            tags = [raw_tags] if isinstance(raw_tags, str) else raw_tags
            tag_html = "".join(chip(str(tag), "tag") for tag in tags)
            title = data.pick(item, lang, "title") or item["slug"]
            summary = data.pick(item, lang, "summary")
            rows.append(
                f'<li class="note-item"><a class="note-link" href="{url(prefix, "notes/" + item["slug"] + ".html")}">'
                f'<time class="note-date" datetime="{esc(date_txt)}">{esc(date_txt)}</time>'
                f'<span class="note-main"><span class="note-title">{esc(title)}</span>'
                f'<span class="note-sum">{esc(summary)}</span></span>'
                '<span class="note-arrow" aria-hidden="true">→</span></a>'
                f'<span class="note-tags">{tag_html}</span></li>'
            )
        content = f'<ul class="note-list">{"".join(rows)}</ul>'

    body = head + f'<section class="section">{content}</section>'
    return layout(
        ctx,
        lang,
        prefix=prefix,
        page_path=page_path,
        active="notes",
        title=f"{t(lang, 'nav.notes')} — {ctx.cfg.get('callsign')}",
        description=t(lang, "page.notes_lead"),
        body=body,
    )


def page_note(ctx: Ctx, lang: str, prefix: str, page_path: str, item: dict) -> str:
    date_txt = item["date"].isoformat() if item["date"] else ""
    raw_tags = data.pick_meta(item, lang, "tags") or []
    tags = [raw_tags] if isinstance(raw_tags, str) else raw_tags
    tag_html = "".join(chip(str(tag), "tag") for tag in tags)
    title = data.pick(item, lang, "title") or item["slug"]
    summary = data.pick(item, lang, "summary")
    body_html = data.pick(item, lang, "body_html")

    body = f"""
<article class="prose">
  <header class="note-head">
    <p class="kicker">NOTES</p>
    <h1 class="page-title">{esc(title)}</h1>
    <p class="note-meta"><time datetime="{esc(date_txt)}">{esc(date_txt)}</time>{tag_html}</p>
  </header>
  {body_html}
  <footer class="note-foot">
    <a class="link-arrow" href="{url(prefix, "notes.html")}"><span aria-hidden="true">←</span>{esc(t(lang, "btn.back_notes"))}</a>
  </footer>
</article>
"""
    return layout(
        ctx,
        lang,
        prefix=prefix,
        page_path=page_path,
        active="notes",
        title=f"{title} — {ctx.cfg.get('callsign')}",
        description=summary or title,
        body=body,
    )


# ── 电台室 ───────────────────────────────────────────────


def _spec_table(rows: list[dict], lang: str) -> str:
    if not rows:
        return f'<p class="muted">{esc(t(lang, "station.empty_item"))}</p>'
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
        f'<th scope="col">{esc(t(lang, "station.col_item"))}</th>'
        f'<th scope="col">{esc(t(lang, "station.col_role"))}</th>'
        f'<th scope="col">{esc(t(lang, "station.col_note"))}</th>'
        "</tr></thead>"
    )
    return f'<table class="spec-table">{head}<tbody>{body}</tbody></table>'


def page_station(ctx: Ctx, lang: str, prefix: str, page_path: str) -> str:
    cfg = ctx.cfg
    rows = "".join(
        f"<div><dt>{esc(label)}</dt><dd>{dash(value)}</dd></div>"
        for label, value in (
            ("QTH", cfg.get("qth")),
            ("Grid", cfg.get("grid")),
            (t(lang, "home.meta_license"), ctx.license(lang)),
            ("Since", cfg.get("since")),
        )
    )

    contact = []
    if cfg.get("email"):
        contact.append(f'<a class="btn btn-primary" href="mailto:{esc(cfg["email"])}">{esc(cfg["email"])}</a>')
    if cfg.get("github"):
        contact.append(
            f'<a class="btn btn-ghost" href="{esc(cfg["github"])}" target="_blank" rel="noopener">GitHub</a>'
        )

    body = f"""
{page_head(kicker=KICKERS["station"], title=t(lang, "nav.station"), lead=t(lang, "page.station_lead"))}
<section class="station-grid">
  <div class="panel">
    <h2 class="panel-title">{esc(t(lang, "station.qth"))}</h2>
    <dl class="kv">{rows}</dl>
  </div>
  <div class="panel" id="qsl">
    <h2 class="panel-title">{esc(t(lang, "station.qsl"))}</h2>
    <p>{esc(ctx.qsl_note(lang))}</p>
  </div>
  <div class="panel">
    <h2 class="panel-title">{esc(t(lang, "station.equipment"))}</h2>
    {_spec_table(cfg.get("equipment") or [], lang)}
  </div>
  <div class="panel">
    <h2 class="panel-title">{esc(t(lang, "station.antennas"))}</h2>
    {_spec_table(cfg.get("antennas") or [], lang)}
  </div>
  <div class="panel">
    <h2 class="panel-title">{esc(t(lang, "station.software"))}</h2>
    {_spec_table(cfg.get("software") or [], lang)}
  </div>
  <div class="panel">
    <h2 class="panel-title">{esc(t(lang, "station.contact"))}</h2>
    <p>{esc(t(lang, "station.contact_lead"))}</p>
    <div class="contact-actions">{"".join(contact) or f'<span class="muted">{esc(t(lang, "station.empty_item"))}</span>'}</div>
  </div>
</section>
"""
    return layout(
        ctx,
        lang,
        prefix=prefix,
        page_path=page_path,
        active="station",
        title=f"{t(lang, 'nav.station')} — {cfg.get('callsign')}",
        description=t(lang, "page.station_lead"),
        body=body,
    )


# ── 404 ──────────────────────────────────────────────────


def page_404(ctx: Ctx, lang: str, prefix: str, page_path: str) -> str:
    body = f"""
<section class="notfound">
  <p class="kicker">404</p>
  <h1 class="page-title">{esc(t(lang, "404.title"))}</h1>
  <p class="page-lead">{esc(t(lang, "404.lead"))}</p>
  <a class="btn btn-primary" href="{url(prefix, "index.html")}">{esc(t(lang, "404.btn"))}</a>
</section>
"""
    return layout(
        ctx,
        lang,
        prefix=prefix,
        page_path=page_path,
        active="404",
        title=f"404 — {ctx.cfg.get('callsign')}",
        description=t(lang, "404.lead"),
        body=body,
    )
