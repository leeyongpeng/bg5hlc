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


def page_url(lang: str, prefix: str, path: str) -> str:
    """站内页面链接：英文页保持在 /en/ 下，不跳回中文页。"""
    lang_root = "en/" if lang == "en" else ""
    return url(prefix, lang_root + path)


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

    def country(self, lang: str) -> str:
        if lang == "en":
            return self.cfg.get("country_en") or self.cfg.get("country") or ""
        return self.cfg.get("country") or ""

    def qth(self, lang: str) -> str:
        if lang == "en":
            return self.cfg.get("qth_en") or self.cfg.get("qth") or ""
        return self.cfg.get("qth") or ""

    def qsl_address(self, lang: str) -> str:
        if lang == "en":
            return self.cfg.get("qsl_address_en") or self.cfg.get("qsl_address") or ""
        return self.cfg.get("qsl_address") or ""

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

    other = S.other(lang)
    switch_target = url(prefix, ("en/" if lang == "zh" else "") + page_path)
    switch_label = "EN" if lang == "zh" else "中文"

    site_links = "".join(
        f'<a href="{url(prefix, href)}">{esc(t(lang, key))}</a>' for href, key, _ in NAV[:4]
    )
    more_links = "".join(
        f'<a href="{url(prefix, href)}">{esc(t(lang, key))}</a>' for href, key, _ in NAV[4:]
    )
    more_links += (
        f'<a href="{esc(switch_target)}" hreflang="{other}">{esc(switch_label)}</a>'
        f'<a href="{url(prefix, "station.html")}">QSL</a>'
    )
    if cfg.get("email"):
        more_links += f'<a href="mailto:{esc(cfg["email"])}">{esc(cfg["email"])}</a>'
    if cfg.get("github"):
        more_links += f'<a href="{esc(cfg["github"])}" target="_blank" rel="noopener">GitHub</a>'

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
<link rel="preload" href="{url(prefix, "assets/fonts/archivo-black-latin-400.woff2")}" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="{url(prefix, "assets/fonts/space-grotesk-latin-var.woff2")}" as="font" type="font/woff2" crossorigin>
<script>
(function () {{
  var root = document.documentElement;
  var saved = null;
  try {{ saved = localStorage.getItem("bg5hlc-theme"); }} catch (e) {{}}
  root.classList.add("js");
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
  <div class="wrap">
    <div class="footer-grid">
      <div class="footer-about">
        <div class="footer-call">{esc(callsign)}</div>
        <p>{esc(ctx.description(lang))}</p>
      </div>
      <div class="footer-col">
        <h2>{esc(t(lang, "footer.site"))}</h2>
        <div class="footer-links">{site_links}</div>
      </div>
      <div class="footer-col">
        <h2>{esc(t(lang, "footer.more"))}</h2>
        <div class="footer-links">{more_links}</div>
      </div>
    </div>
    <div class="footer-big" aria-hidden="true">73 DE {esc(callsign)}</div>
    <div class="footer-bottom">
      <span>© {datetime.now(TZ).year} {esc(callsign)}</span>
      <span>73 DE {esc(callsign)} · CQ CQ CQ</span>
      <span>{esc(t(lang, "footer.built"))} {esc(ctx.built_at)}</span>
    </div>
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


def _freq_parts(raw: str) -> tuple[str, str]:
    """把 145.400 / 14.230 MHz 拆成数字和单位，卡片里好排版。"""
    text = (raw or "").strip()
    if not text:
        return "", ""
    match = re.match(r"^(\d[\d.,]*)\s*(ghz|mhz|khz|hz)?$", text, re.IGNORECASE)
    if match:
        unit = (match.group(2) or "mhz").upper()
        return match.group(1), {"GHZ": "GHz", "MHZ": "MHz", "KHZ": "kHz", "HZ": "Hz"}[unit]
    return text, ""


def _power_parts(raw: str) -> tuple[str, str]:
    text = (raw or "").strip()
    if not text:
        return "", ""
    match = re.match(r"^(\d[\d.]*)\s*(kw|mw|w)?$", text, re.IGNORECASE)
    if match:
        unit = (match.group(2) or "W").lower()
        return match.group(1), {"kw": "kW", "mw": "mW"}.get(unit, "W")
    return text, ""


def _readout(label: str, value_html: str, unit: str = "", tone: str = "") -> str:
    if not value_html:
        return ""
    cls = "qso-readout" + (f" is-{tone}" if tone else "")
    unit_html = f"<small>{esc(unit)}</small>" if unit else ""
    return (
        f'<div class="{cls}">'
        f'<span class="qso-readout-label">{esc(label)}</span>'
        f'<span class="qso-readout-value">{value_html}{unit_html}</span>'
        "</div>"
    )


def _qso_meta(label: str, value: str) -> str:
    if not value:
        return ""
    return f'<div><dt>{esc(label)}</dt><dd>{esc(value)}</dd></div>'


def _row_html(row: dict, lang: str) -> str:
    search = " ".join(
        [
            row.get("call", ""), row.get("dxcc", ""), row.get("qth", ""), row.get("rig", ""),
            row.get("antenna", ""), row.get("notes", ""), row.get("grid", ""),
            row.get("freq", ""), row.get("power", ""),
        ]
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
        f'<td class="cell-rig">{esc(row.get("rig", ""))}</td>'
        f'<td class="cell-antenna">{esc(row.get("antenna", ""))}</td>'
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
        ("rig", "th.rig", ""),
        ("antenna", "th.antenna", ""),
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


def qso_card(row: dict, lang: str) -> str:
    """一张通联卡：呼号、时间、频率/功率/RST、QTH/设备/天线和完整备注。"""
    call = row.get("call", "")
    date_txt = row.get("date", "")
    time_txt = row.get("time", "")
    when = " · ".join(x for x in (date_txt, f"{time_txt} UTC" if time_txt else "") if x)

    chips = band_chip(row.get("band", "")) + mode_chip(row.get("mode", ""), lang)
    tags_html = f'<div class="qso-card-tags">{chips}</div>' if chips else ""

    freq_value, freq_unit = _freq_parts(row.get("freq", ""))
    power_value, power_unit = _power_parts(row.get("power", ""))
    readouts = "".join(
        item
        for item in (
            _readout(t(lang, "qso.freq"), esc(freq_value), freq_unit, "freq"),
            _readout(t(lang, "qso.power"), esc(power_value), power_unit),
            _readout(t(lang, "qso.rst"), _rst(row)),
        )
        if item
    )
    readouts_html = f'<div class="qso-card-readouts">{readouts}</div>' if readouts else ""

    place = " · ".join(x for x in (row.get("dxcc"), row.get("qth")) if x)
    meta = "".join(
        item
        for item in (
            _qso_meta(t(lang, "qso.qth"), place),
            _qso_meta(t(lang, "qso.rig"), row.get("rig", "")),
            _qso_meta(t(lang, "qso.antenna"), row.get("antenna", "")),
        )
        if item
    )
    meta_html = f'<dl class="qso-card-meta">{meta}</dl>' if meta else ""

    notes = row.get("notes", "")
    notes_html = ""
    if notes:
        notes_html = (
            '<p class="qso-card-notes">'
            f'<span class="qso-notes-label">{esc(t(lang, "qso.notes"))}</span>'
            f"{esc(notes)}</p>"
        )

    search = " ".join(
        [
            row.get("call", ""), row.get("dxcc", ""), row.get("qth", ""), row.get("rig", ""),
            row.get("antenna", ""), row.get("notes", ""), row.get("grid", ""),
            row.get("freq", ""), row.get("power", ""), row.get("band", ""), row.get("mode", ""),
        ]
    ).lower()

    return (
        '<article class="qso-card" data-qso'
        f' data-search="{esc(search)}" data-band="{esc(row.get("band", ""))}"'
        f' data-mode="{esc(row.get("mode", ""))}" data-date="{esc(date_txt)}"'
        f' data-time="{esc(time_txt)}" data-call="{esc(call)}">'
        '<header class="qso-card-head">'
        f'<span class="qso-card-call">{esc(call)}</span>'
        f'<span class="qso-card-when">{esc(when)}</span>'
        "</header>"
        '<div class="qso-card-body">'
        f"{tags_html}{readouts_html}{meta_html}{notes_html}"
        "</div></article>"
    )


def qso_cards(rows: list[dict], lang: str) -> str:
    cards = "".join(qso_card(row, lang) for row in rows)
    return (
        f'<div class="qso-cards" id="log">{cards}</div>'
        f'<p class="log-empty" id="log-empty" hidden>{esc(t(lang, "filter.none"))}</p>'
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
    sort_opts = "".join(
        f'<option value="{value}">{esc(t(lang, key))}</option>'
        for value, key in (
            ("date-desc", "sort.newest"),
            ("date-asc", "sort.oldest"),
            ("call", "sort.call"),
            ("band", "sort.band"),
        )
    )
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
        '<label class="field">'
        f'<span class="field-label">{esc(t(lang, "sort.label"))}</span>'
        f'<select id="qso-sort">{sort_opts}</select>'
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

VIA_LABELS = {
    "卡片局": "BUREAU",
    "直寄": "DIRECT",
    "卡片局（bureau）": "BUREAU",
    "eqsl": "EQSL",
    "lotw": "LOTW",
    "bureau": "BUREAU",
    "direct": "DIRECT",
}


def via_label(raw: str) -> str:
    text = (raw or "").strip()
    return VIA_LABELS.get(text.lower(), VIA_LABELS.get(text, text.upper()))


def _art(entry: dict) -> str:
    """没有图片时的 CSS 卡面（QSL 稿纸风格）。"""
    meta = entry["meta"]
    call = str(meta.get("call", "") or "")
    band = str(meta.get("band", "") or "")
    mode = str(meta.get("mode", "") or "").upper()
    via = via_label(str(meta.get("via", "") or ""))
    sub = " · ".join(x for x in (band, mode) if x)
    mark = f"VIA {via}" if via else ""
    return (
        '<div class="qsl-art">'
        f'<span class="qsl-call">{esc(call)}</span>'
        f'<span class="qsl-sub">{esc(sub)}</span>'
        f'<span class="qsl-mark">{esc(mark)}</span>'
        "</div>"
    )


def _media(entry: dict, kind: str, prefix: str, caption: str) -> str:
    full = entry.get("image_url", "")
    thumb = entry.get("thumb_url", "")
    flag = "QSL" if kind == "qsl" else "SSTV"

    if not thumb:
        target = url(prefix, f"{kind}.html")
        body = _art(entry) if kind == "qsl" else '<span class="media-hint">SSTV</span>'
        cls = "card-media" if kind == "qsl" else "card-media is-empty"
        return (
            f'<a class="{cls}" href="{esc(target)}">'
            f'<span class="card-flag">{flag}</span>{body}</a>'
        )

    alt = f"{entry['meta'].get('call', '')} {kind}".strip()
    return (
        f'<a class="card-media" href="{url(prefix, full or thumb)}" data-lightbox data-caption="{esc(caption)}">'
        f'<span class="card-flag">{flag}</span>'
        f'<img src="{url(prefix, thumb)}" alt="{esc(alt)}" loading="lazy" decoding="async">'
        "</a>"
    )


def qsl_content(entry: dict, lang: str, prefix: str) -> str:
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
    return (
        '<article class="card">'
        f"{_media(entry, 'qsl', prefix, caption)}"
        '<div class="card-body">'
        f'<div class="card-head"><span class="card-call">{esc(call)}</span>'
        f'<time class="card-date" datetime="{esc(date_txt)}">{esc(date_txt)}</time></div>'
        f'<div class="card-chips">{chips}</div>{body_html}'
        "</div></article>"
    )


def sstv_content(entry: dict, lang: str, prefix: str) -> str:
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
        f'<div class="card-head"><span class="card-call">{esc(call)}</span>'
        f'<time class="card-date" datetime="{esc(date_txt)}">{esc(date_txt)}</time></div>'
        f'<div class="card-chips">{chips}</div>{body_html}'
        "</div></article>"
    )


def card_grid(items: list[dict], kind: str, lang: str, prefix: str) -> str:
    render_one = qsl_content if kind == "qsl" else sstv_content
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

WATERFALL_RAMP = " .·:-=+*#%@"
WATERFALL_PEAKS = [
    (0.16, 0.030, 1.00, 0.0),
    (0.44, 0.046, 0.85, 1.4),
    (0.74, 0.028, 0.95, 2.6),
    (0.90, 0.055, 0.55, 3.8),
]


def waterfall(rows: int = 13, cols: int = 42, seed: int = 7) -> str:
    """ASCII 频谱瀑布的首帧（JS 会接着往下滚）。"""
    rnd = random.Random(seed)
    lines = []
    for index in range(rows):
        moment = index * 0.28
        chars = []
        for x in range(cols):
            p = x / (cols - 1)
            value = 0.04 + rnd.random() * 0.07
            for freq, width, amp, phase in WATERFALL_PEAKS:
                distance = abs(p - freq)
                distance = min(distance, 1 - distance)
                value += amp * math.exp(-(distance * distance) / (2 * width * width)) * (
                    0.65 + 0.35 * math.sin(moment * 0.9 + phase)
                )
            idx = min(len(WATERFALL_RAMP) - 1, max(0, int(value * len(WATERFALL_RAMP))))
            chars.append(WATERFALL_RAMP[idx])
        opacity = 0.28 + 0.72 * (index / max(1, rows - 1))
        lines.append(f'<span style="opacity:{opacity:.2f}">{esc("".join(chars))}</span>')
    return "".join(lines)


def bands_text(ctx: Ctx, lang: str) -> str:
    """常用频段：优先取配置，其次取通联最多的三个波段。"""
    raw = ctx.cfg.get("bands")
    items: list[str] = []
    if isinstance(raw, str):
        items = [x.strip() for x in raw.replace("，", ",").split(",") if x.strip()]
    elif isinstance(raw, (list, tuple)):
        items = [str(x).strip() for x in raw if str(x).strip()]
    if not items and ctx.stats["bands"]:
        busiest = sorted(ctx.stats["bands"], key=lambda pair: -pair[1])
        items = [band for band, _ in busiest[:3]]
    return " / ".join(items)


def _page_home_legacy(ctx: Ctx, lang: str, prefix: str, page_path: str) -> str:
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
        (t(lang, "home.meta_license"), ctx.license(lang)),
        (t(lang, "home.meta_bands"), bands_text(ctx, lang)),
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
                '<pre class="snippet">2026-03-14,08:42,JA1KWF,14.270,20m,SSB,59,59,100,Japan,Tokyo,PM95,IC-7300,DP,first QSO</pre>'
            ),
        )

    def preview(items, kind, section_key, page_href, empty_key, foot_label):
        head = section_head(t(lang, section_key), url(prefix, page_href), t(lang, "btn.view_all"))
        if items:
            body = head + card_grid(items[:3], kind, lang, prefix)
            body += (
                '<div class="section-foot">'
                f'<a class="link-arrow" href="{url(prefix, page_href)}">{esc(foot_label)} '
                '<span aria-hidden="true">→</span></a></div>'
            )
            return body
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
        '<section class="section reveal">'
        '<div class="cta"><div class="cta-inner">'
        f'<h2>{esc(t(lang, "home.cta_title"))}</h2>'
        f'<p>{esc(ctx.qsl_note(lang) or t(lang, "home.cta_body"))}</p>'
        f'<a class="btn btn-primary" href="{url(prefix, "station.html")}">{esc(t(lang, "btn.qsl_exchange"))}</a>'
        "</div></div></section>"
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
    <pre class="waterfall" id="waterfall">{waterfall()}</pre>
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

<section class="section reveal">{latest}</section>
<section class="section reveal">{preview(ctx.cards, "qsl", "home.section_qsl", "qsl.html", "empty.qsl", t(lang, "btn.view_all"))}</section>
<section class="section reveal">{preview(ctx.sstv, "sstv", "home.section_sstv", "sstv.html", "empty.sstv", t(lang, "btn.view_all"))}</section>
{f'<section class="section reveal">{equip}</section>' if equip else ''}
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


# ── 首页（v2 清爽版） ────────────────────────────────────

V2_WAVE_ICON = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" '
    'stroke-linecap="round"><path d="M2 12h3l2-6 3 12 3-9 2 6h3l2-4h2"/></svg>'
)


def _v2_nav(active: str, lang: str, prefix: str) -> str:
    items = []
    for href, key, key_active in NAV:
        cls = "nav-tab is-active" if active == key_active else "nav-tab"
        current = ' aria-current="page"' if active == key_active else ""
        items.append(
            f'<a class="{cls}" href="{page_url(lang, prefix, href)}"{current}>{esc(t(lang, key))}</a>'
        )
    return "".join(items)


def _v2_header(ctx: Ctx, lang: str, active: str, prefix: str, page_path: str) -> str:
    cfg = ctx.cfg
    callsign = cfg.get("callsign", "")
    grid = cfg.get("grid", "")
    qth = ctx.qth(lang)
    subtitle = " · ".join(x for x in ("HF / VHF", f"GRID {grid}" if grid else "", qth) if x)
    other = S.other(lang)
    switch_target = url(prefix, ("en/" if lang == "zh" else "") + page_path)
    switch_label = "EN" if lang == "zh" else "中文"
    theme_label = t(lang, "theme.v2_light")
    return (
        '<header class="site-header">'
        '<div class="wrap header-inner">'
        f'<a class="brand" href="{page_url(lang, prefix, "index.html")}" aria-label="{esc(callsign)} — {esc(t(lang, "a11y.home"))}">'
        f'<span class="brand-badge" aria-hidden="true">{V2_WAVE_ICON}</span>'
        f'<span class="brand-title"><strong>{esc(callsign)}</strong><span>{esc(subtitle)}</span></span>'
        "</a>"
        f'<nav class="nav-tabs" aria-label="nav">{_v2_nav(active, lang, prefix)}</nav>'
        '<div class="header-actions">'
        f'<a class="lang-btn" href="{switch_target}" hreflang="{other}">{esc(switch_label)}</a>'
        '<button type="button" class="theme-btn" id="theme-toggle" '
        f'data-label-light="{esc(t(lang, "theme.v2_light"))}" '
        f'data-label-dark="{esc(t(lang, "theme.v2_dark"))}" '
        f'aria-label="{esc(theme_label)}">'
        f'<span class="theme-icon theme-icon-moon" aria-hidden="true">{ICONS["moon"]}</span>'
        f'<span class="theme-icon theme-icon-sun" aria-hidden="true">{ICONS["sun"]}</span>'
        "</button>"
        "</div>"
        "</div></header>"
    )


def _v2_lightbox(close_label: str) -> str:
    return (
        '<div class="lightbox-v2" id="lightbox-v2" hidden>'
        f'<button type="button" class="lightbox-v2-close" aria-label="{esc(close_label)}">×</button>'
        '<img id="lightbox-v2-img" alt="">'
        '<p class="lightbox-v2-cap" id="lightbox-v2-cap"></p>'
        "</div>"
    )


def layout_v2(
    ctx: Ctx,
    lang: str,
    *,
    prefix: str,
    page_path: str,
    active: str,
    title: str,
    description: str,
    body: str,
    with_lightbox: bool = False,
) -> str:
    cfg = ctx.cfg
    callsign = cfg.get("callsign", "")
    lang_attr = "zh-CN" if lang == "zh" else "en"
    year = datetime.now(TZ).year
    grid = cfg.get("grid", "")
    qth = ctx.qth(lang)
    close_label = "关闭" if lang == "zh" else "Close"

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

    github = ""
    if cfg.get("github"):
        github = (
            f' · <a href="{esc(cfg["github"])}" target="_blank" rel="noopener">GitHub</a>'
        )

    return f"""<!doctype html>
<html lang="{lang_attr}" data-theme="light" data-theme-mode="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<meta name="color-scheme" content="light dark">
<meta name="theme-color" content="#f6f4ef">
<meta name="generator" content="bg5hlc-sitegen {__version__}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{esc(callsign)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
{alternates}
<link rel="icon" href="{url(prefix, "assets/favicon.svg")}" type="image/svg+xml">
<link rel="preload" href="{url(prefix, "assets/fonts/archivo-black-latin-400.woff2")}" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="{url(prefix, "assets/fonts/space-grotesk-latin-var.woff2")}" as="font" type="font/woff2" crossorigin>
<script>
(function () {{
  var root = document.documentElement;
  var saved = null;
  try {{ saved = localStorage.getItem("bg5hlc-theme"); }} catch (e) {{}}
  var systemDark = window.matchMedia ? window.matchMedia("(prefers-color-scheme: dark)").matches : false;
  var mode = "light";
  if (saved === "light" || saved === "dark") mode = saved;
  else if (saved === "auto") mode = systemDark ? "dark" : "light";
  root.setAttribute("data-theme", mode);
  root.setAttribute("data-theme-mode", mode);
}})();
</script>
<link rel="stylesheet" href="{url(prefix, "assets/css/site-v2.css")}?v={ctx.build_id}">
</head>
<body class="page-{esc(active)} skin-v2">
{demo_bar}
<a class="skip-link" href="#main">{esc(t(lang, "a11y.skip"))}</a>
{_v2_header(ctx, lang, active, prefix, page_path)}
<main id="main" class="wrap">
{body}
</main>
<footer class="site-footer">
  <div class="wrap footer-inner">
    <span>© {year} <code>{esc(callsign)}</code> · Amateur Radio Station ({esc(qth)} · {esc(grid)})</span>
    <span><code>73 &amp; GOOD DX · PSE QSL VIA BUREAU / LOTW</code></span>
    <span>{esc(t(lang, "footer.built"))} {esc(ctx.built_at)}{github}</span>
  </div>
</footer>
{_v2_lightbox(close_label) if with_lightbox else ""}
<script src="{url(prefix, "assets/js/site-v2.js")}?v={ctx.build_id}" defer></script>
</body>
</html>
"""


def _v2_spec(label: str, value: str) -> str:
    if not value:
        return ""
    return f"<div><span>{esc(label)}</span><strong>{esc(value)}</strong></div>"


def _v2_info_line(label: str, value: str) -> str:
    if not value:
        return ""
    return f'<div class="info-line"><span>{esc(label)}</span><strong>{esc(value)}</strong></div>'


def _v2_info_strip(ctx: Ctx, lang: str, prefix: str) -> str:
    cfg = ctx.cfg
    grid = cfg.get("grid", "")
    cq = cfg.get("cq_zone", "")
    itu = cfg.get("itu_zone", "")
    zone = " · ".join(
        x for x in (grid, f"CQ {cq}" if cq else "", f"ITU {itu}" if itu else "") if x
    )
    station = "".join(
        [
            _v2_info_line(t(lang, "op.country"), ctx.country(lang)),
            _v2_info_line(t(lang, "op.qth"), ctx.qth(lang)),
            _v2_info_line(t(lang, "op.grid"), zone),
            _v2_info_line(t(lang, "op.license"), ctx.license(lang)),
        ]
    )

    stats = ctx.stats
    pills = "".join(
        f'<span class="s-pill">{esc(label)} <b>{value}</b></span>'
        for label, value in (
            (t(lang, "stat.qso"), stats["total"]),
            (t(lang, "stat.dxcc"), stats["dxcc"]),
            (t(lang, "stat.qsl"), len(ctx.cards)),
            (t(lang, "stat.sstv"), len(ctx.sstv)),
        )
    )

    contact = ""
    if cfg.get("email"):
        contact += f'<a href="mailto:{esc(cfg["email"])}">{esc(cfg["email"])}</a>'
    if ctx.qsl_address(lang):
        contact += (
            f'<span class="contact-line"><span>{esc(t(lang, "op.qsl_address"))}</span>'
            f"{esc(ctx.qsl_address(lang))}</span>"
        )

    return (
        '<section class="console-strip" aria-label="station overview">'
        '<div class="strip-card">'
        f'<div class="strip-head">{esc(t(lang, "home.v2_station"))} <span>STATION</span></div>'
        f'<div class="info-lines">{station}</div>'
        "</div>"
        '<div class="strip-card">'
        f'<div class="strip-head">{esc(t(lang, "home.v2_logbook"))} <span>LOGBOOK</span></div>'
        f'<div class="solar-pills logbook-pills">{pills}</div>'
        "</div>"
        '<div class="strip-card">'
        f'<div class="strip-head">{esc(t(lang, "home.v2_contact"))} <span>QSL &amp; CONTACT</span></div>'
        '<div class="strip-card-body">'
        f'<p class="strip-text">{esc(ctx.qsl_note(lang))}</p>'
        f'<div class="contact-links">{contact}</div>'
        "</div>"
        "</div>"
        "</section>"
    )


def _v2_qsl_art(entry: dict) -> str:
    meta = entry["meta"]
    call = str(meta.get("call", "") or "")
    band = str(meta.get("band", "") or "")
    mode = str(meta.get("mode", "") or "").upper()
    sub = " · ".join(x for x in (band, mode) if x)
    return (
        '<div class="qsl-art-v2">'
        f'<span class="qsl-art-call">{esc(call or "QSL")}</span>'
        f'<span class="qsl-art-sub">{esc(sub)}</span>'
        '<span class="qsl-art-mark">QSL</span>'
        "</div>"
    )


def _v2_qsl_card(entry: dict, lang: str, prefix: str, *, lightbox: bool = False) -> str:
    meta = entry["meta"]
    call = str(meta.get("call", "") or "")
    date_txt = entry["date"].isoformat() if entry["date"] else ""
    band = str(meta.get("band", "") or "")
    mode = str(meta.get("mode", "") or "").upper()
    via = via_label(str(meta.get("via", "") or ""))
    thumb = entry.get("thumb_url") or ""
    full = entry.get("image_url") or thumb
    target = page_url(lang, prefix, "qsl.html")

    if thumb:
        if lightbox and full:
            caption = " · ".join(x for x in (call, date_txt) if x)
            media = (
                f'<a class="qsl-media" href="{url(prefix, full)}" data-lightbox '
                f'data-caption="{esc(caption)}">'
                f'<img src="{url(prefix, thumb)}" alt="{esc(call)} QSL" loading="lazy" decoding="async">'
                "</a>"
            )
        else:
            media = (
                f'<a class="qsl-media" href="{target}">'
                f'<img src="{url(prefix, thumb)}" alt="{esc(call)} QSL" loading="lazy" decoding="async">'
                "</a>"
            )
    else:
        media = f'<a class="qsl-media" href="{target}">{_v2_qsl_art(entry)}</a>'

    tags = ""
    if band:
        tags += f'<span class="qsl-tag is-band">{esc(band)}</span>'
    if mode:
        tags += f'<span class="qsl-tag is-mode">{esc(mode)}</span>'
    if via:
        tags += f'<span class="qsl-tag is-via">{esc(via)}</span>'

    summary = data.pick(entry, lang, "summary")
    summary_html = f'<p class="qsl-note">{esc(summary)}</p>' if summary else ""
    date_html = (
        f'<time class="qsl-date" datetime="{esc(date_txt)}">{esc(date_txt)}</time>'
        if date_txt
        else ""
    )
    return (
        '<article class="qsl-card">'
        f"{media}"
        '<div class="qsl-body">'
        f'<div class="qsl-head"><span class="qsl-call">{esc(call or "QSL")}</span>{date_html}</div>'
        f'<div class="qsl-tags">{tags}</div>{summary_html}'
        "</div></article>"
    )


def _v2_qsl_section(ctx: Ctx, lang: str, prefix: str) -> str:
    cards = ctx.cards[:6]
    count = S.fmt(lang, "filter.count_cards", n=len(ctx.cards))
    head = (
        '<div class="section-bar">'
        '<div class="section-heading">'
        f'<h2>{esc(t(lang, "home.section_qsl"))}</h2><span>{esc(count)}</span>'
        "</div>"
        f'<a class="text-link" href="{page_url(lang, prefix, "qsl.html")}">{esc(t(lang, "btn.view_all"))} <span aria-hidden="true">→</span></a>'
        "</div>"
    )
    if cards:
        grid = f'<div class="qsl-grid">{"".join(_v2_qsl_card(card, lang, prefix) for card in cards)}</div>'
    else:
        grid = (
            '<div class="qsl-empty">'
            '<div class="qsl-empty-art" aria-hidden="true"><span>BG5HLC</span><small>QSL</small></div>'
            '<div class="qsl-empty-copy">'
            f'<h3>{esc(t(lang, "home.v2_qsl_empty_title"))}</h3>'
            f'<p>{esc(t(lang, "home.v2_qsl_empty_lead"))}</p>'
            f'<a class="btn-v2" href="{page_url(lang, prefix, "qsl.html")}">{esc(t(lang, "home.v2_qsl_open"))}</a>'
            "</div></div>"
        )
    return f'<section class="section-block" id="qsl">{head}{grid}</section>'


def page_head_v2(kicker: str, title: str, lead: str = "") -> str:
    lead_html = f'<p class="page-lead">{esc(lead)}</p>' if lead else ""
    # SSTV 页的 kicker 与标题同为 SSTV，不必重复显示
    kicker_html = f'<p class="kicker">{esc(kicker)}</p>' if kicker != title else ""
    return (
        '<section class="page-head">'
        f"{kicker_html}"
        f'<h1 class="page-title">{esc(title)}</h1>'
        f"{lead_html}"
        "</section>"
    )


def empty_v2(kind: str, title: str, lead: str, extra: str = "") -> str:
    icon = ICONS.get(kind, ICONS["qso"])
    return (
        '<div class="empty-v2">'
        f'<div class="empty-v2-icon" aria-hidden="true">{icon}</div>'
        f'<h2>{esc(title)}</h2><p>{esc(lead)}</p>{extra}'
        "</div>"
    )


def page_home(ctx: Ctx, lang: str, prefix: str, page_path: str) -> str:
    cfg = ctx.cfg
    callsign = cfg.get("callsign", "")
    grid = cfg.get("grid", "")
    cq = cfg.get("cq_zone", "")
    itu = cfg.get("itu_zone", "")
    zone = " · ".join(
        x for x in (grid, f"CQ {cq}" if cq else "", f"ITU {itu}" if itu else "") if x
    )
    equipment = cfg.get("equipment") or []
    antennas = cfg.get("antennas") or []
    main_rig = ""
    if equipment:
        first = equipment[0]
        main_rig = " · ".join(
            x for x in (first.get("name", ""), first.get("role", "")) if x
        )
    main_ant = ""
    if antennas:
        first_ant = antennas[0]
        main_ant = " · ".join(
            x for x in (first_ant.get("name", ""), first_ant.get("role", "")) if x
        )

    specs = "".join(
        [
            _v2_spec(t(lang, "home.v2_spec_grid"), zone),
            _v2_spec(t(lang, "home.v2_spec_rig"), main_rig),
            _v2_spec(t(lang, "home.v2_spec_ant"), main_ant),
            _v2_spec(t(lang, "home.v2_spec_qsl"), t(lang, "home.v2_qsl_short")),
        ]
    )

    terminal = (
        '<div class="ascii-terminal">'
        '<div class="terminal-header">'
        '<div class="terminal-dots"><i></i><i></i><i></i>'
        '<span style="margin-left:6px;">CW QSO MONITOR · 7.030 MHz</span></div>'
        '<div class="terminal-actions">'
        '<button type="button" class="t-btn" id="ascii-pause" '
        f'data-pause="{esc(t(lang, "home.v2_pause"))}" data-play="{esc(t(lang, "home.v2_play"))}">'
        f'{esc(t(lang, "home.v2_pause"))}</button>'
        f'<button type="button" class="t-btn" id="ascii-step">{esc(t(lang, "home.v2_step"))}</button>'
        "</div></div>"
        '<div class="ascii-viewport"><pre class="ascii-canvas" id="ascii-canvas"></pre></div>'
        '<div class="terminal-footer">'
        '<span id="ascii-status">1/4 · CQ CQ DE BG5HLC K</span>'
        "<strong>RST 599 / 599</strong>"
        "</div></div>"
    )

    station_block = (
        '<section class="section-block" id="station">'
        '<div class="section-bar"><div class="section-heading">'
        f'<h2>{esc(t(lang, "home.station_gear"))}</h2><span>STATION</span>'
        "</div></div>"
        f"{station_gear(ctx, lang)}"
        "</section>"
    )

    body = (
        '<section class="hero">'
        '<div class="hero-copy">'
        f'<div class="hero-status"><i class="pulse-dot"></i>{esc(t(lang, "home.v2_status"))}</div>'
        f'<h1 class="hero-call">{esc(callsign)}</h1>'
        f'<p class="hero-subtitle">{esc(ctx.tagline(lang))}</p>'
        f'<div class="hero-specs">{specs}</div>'
        "</div>"
        f"{terminal}"
        "</section>"
        f"{_v2_info_strip(ctx, lang, prefix)}"
        f"{station_block}"
        f"{_v2_qsl_section(ctx, lang, prefix)}"
    )

    return layout_v2(
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


def _page_qso_legacy(ctx: Ctx, lang: str, prefix: str, page_path: str) -> str:
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
                '<pre class="snippet">date,time,call,freq,band,mode,rst_sent,rst_rcvd,power,dxcc,qth,grid,rig,antenna,notes\n'
                "2026-03-14,08:42,JA1KWF,14.270,20m,SSB,59,59,100,Japan,Tokyo,PM95,IC-7300,DP,first QSO</pre>"
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
            + f'<section class="section">{log_tools(ctx.rows, stats, lang)}{qso_cards(ctx.rows, lang)}</section>'
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
    head = page_head_v2(KICKERS["qsl"], t(lang, "nav.qsl"))
    cards = ctx.cards

    if cards:
        years = sorted({str(item["date"].year) for item in cards if item["date"]}, reverse=True)
        year_opts = "".join(f'<option value="{y}">{y}</option>' for y in years)
        template = t(lang, "filter.count_cards")
        total = S.fmt(lang, "filter.count_cards", n=len(cards))
        toolbar = (
            f'<div class="filter-bar" data-count="{esc(template)}">'
            f'<label class="filter-label" for="gallery-year">{esc(t(lang, "filter.year"))}</label>'
            f'<select class="filter-select" id="gallery-year">'
            f'<option value="">{esc(t(lang, "filter.all_years"))}</option>{year_opts}</select>'
            f'<span class="filter-summary" id="gallery-count">{esc(total)}</span>'
            "</div>"
        )
        blocks = []
        for year, group in data.group_by_year(cards):
            grid = "".join(
                _v2_qsl_card(item, lang, prefix, lightbox=True) for item in group
            )
            blocks.append(
                f'<section class="year-group" data-year="{esc(year)}">'
                f'<h2 class="year-title">{esc(year)}<small>{len(group)}</small></h2>'
                f'<div class="qsl-grid">{grid}</div></section>'
            )
        content = toolbar + "".join(blocks)
    else:
        content = (
            '<div class="qsl-empty is-qsl-page">'
            '<div class="qsl-empty-art" aria-hidden="true"><span>BG5HLC</span><small>QSL</small></div>'
            '<div class="qsl-empty-copy">'
            f'<h3>{esc(t(lang, "empty.qsl_title"))}</h3>'
            f'<p>{esc(t(lang, "empty.qsl_lead"))}</p>'
            f'<p class="empty-hint-v2">{esc(t(lang, "empty.card_hint"))}</p>'
            "</div></div>"
        )

    body = head + f'<section class="section-block">{content}</section>'
    title = t(lang, "nav.qsl")
    if cards:
        title = f"{title} ({len(cards)})"
    return layout_v2(
        ctx,
        lang,
        prefix=prefix,
        page_path=page_path,
        active="qsl",
        title=f"{title} — {ctx.cfg.get('callsign')}",
        description=t(lang, "page.qsl_lead"),
        body=body,
        with_lightbox=True,
    )


def _page_sstv_legacy(ctx: Ctx, lang: str, prefix: str, page_path: str) -> str:
    return _gallery_page(ctx, lang, prefix, page_path, "sstv")


# ── 通联记录 / SSTV（v2） ────────────────────────────────


def _with_unit(raw, unit: str) -> str:
    text = str(raw or "").strip()
    if not text:
        return ""
    if re.search(r"[a-zA-Z]", text):
        return text
    return f"{text} {unit}"


def _repeater_cell(label: str, value: str) -> str:
    if not value:
        return ""
    return (
        f'<div class="repeater-cell"><span>{esc(label)}</span>'
        f"<strong>{esc(value)}</strong></div>"
    )


def _qso_detail(label: str, value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    return (
        f'<div class="detail-row"><dt>{esc(label)}</dt>'
        f'<dd title="{esc(text)}">{esc(text)}</dd></div>'
    )


def _qso_when(date_txt: str, time_txt: str, lang: str) -> str:
    """通联时间：CSV 里统一存 UTC，中文页面换算成北京时间显示。"""
    if not time_txt:
        return date_txt
    if date_txt:
        try:
            moment = datetime.strptime(f"{date_txt} {time_txt}", "%Y-%m-%d %H:%M")
        except ValueError:
            moment = None
        if moment:
            if lang == "zh":
                local = moment.replace(tzinfo=timezone.utc).astimezone(TZ)
                return f"{local:%Y-%m-%d} · {local:%H:%M} 北京时间"
            return f"{moment:%Y-%m-%d} · {moment:%H:%M} UTC"
    return " · ".join(x for x in (date_txt, time_txt) if x)


def _v2_qso_card(row: dict, lang: str) -> str:
    call = row.get("call", "")
    date_txt = row.get("date", "")
    time_txt = row.get("time", "")
    band = row.get("band", "")
    mode = row.get("mode", "")
    grid = row.get("grid", "")

    freq_value, freq_unit = _freq_parts(row.get("freq", ""))
    freq_html = f"{esc(freq_value)}<small>{esc(freq_unit)}</small>" if freq_value else "—"
    rst_html = _rst(row) or "—"

    badges = ""
    if band:
        badges += f'<span class="badge badge-band">{esc(band)}</span>'
    if mode:
        badges += f'<span class="badge badge-mode">{esc(mode)}</span>'
    if grid:
        badges += f'<span class="badge badge-grid">{esc(grid)}</span>'

    when = _qso_when(date_txt, time_txt, lang)
    place = " · ".join(x for x in (row.get("dxcc", ""), row.get("qth", "")) if x)
    my_qth = row.get("my_qth", "")
    my_height = row.get("my_height", "")
    rig = row.get("rig", "")
    antenna = row.get("antenna", "")
    their_rig = row.get("their_rig", "")
    their_power = _with_unit(row.get("their_power", ""), "W")
    their_antenna = row.get("their_antenna", "")
    their_height = row.get("their_height", "")

    repeater_cells = "".join(
        item
        for item in (
            _repeater_cell("UPLINK", _with_unit(row.get("uplink", ""), "MHz")),
            _repeater_cell("DOWNLINK", _with_unit(row.get("freq", ""), "MHz")),
            _repeater_cell("OFFSET", _with_unit(row.get("offset", ""), "MHz")),
            _repeater_cell("CTCSS", _with_unit(row.get("ctcss", ""), "Hz")),
        )
        if item
    )
    repeater_html = (
        '<div class="qso-repeater">'
        '<div class="repeater-head">REPEATER</div>'
        f'<div class="repeater-grid">{repeater_cells}</div></div>'
        if repeater_cells
        else ""
    )

    my_station = "".join(
        item
        for item in (
            _qso_detail("QTH", my_qth),
            _qso_detail("RIG", rig),
            _qso_detail("PWR", _with_unit(row.get("power", ""), "W")),
            _qso_detail("ANT", antenna),
            _qso_detail("ALT", my_height),
        )
        if item
    )
    their_station = "".join(
        item
        for item in (
            _qso_detail("QTH", place),
            _qso_detail("RIG", their_rig),
            _qso_detail("PWR", their_power),
            _qso_detail("ANT", their_antenna),
            _qso_detail("ALT", their_height),
        )
        if item
    )
    my_block = (
        '<div class="station-block">'
        '<div class="station-label">MY STATION</div>'
        f'<dl class="qso-details">{my_station}</dl></div>'
        if my_station
        else ""
    )
    their_block = (
        '<div class="station-block">'
        '<div class="station-label">THEIR STATION</div>'
        f'<dl class="qso-details">{their_station}</dl></div>'
        if their_station
        else ""
    )
    stations_html = (
        f'<div class="qso-stations">{my_block}{their_block}</div>'
        if (my_block or their_block)
        else ""
    )

    notes = row.get("notes", "")
    note_html = f'<p class="qso-note">{esc(notes)}</p>' if notes else ""

    search = " ".join(
        [
            call, row.get("dxcc", ""), row.get("qth", ""), my_qth, my_height, rig, antenna,
            their_rig, row.get("their_power", ""), their_antenna, their_height, notes,
            row.get("grid", ""), row.get("freq", ""), row.get("uplink", ""),
            row.get("offset", ""), row.get("ctcss", ""), row.get("power", ""),
            band, mode,
        ]
    ).lower()

    return (
        '<article class="qso-card" data-qso'
        f' data-search="{esc(search)}" data-band="{esc(band)}" data-mode="{esc(mode)}"'
        f' data-date="{esc(date_txt)}" data-time="{esc(time_txt)}" data-call="{esc(call)}">'
        '<div class="qso-top"><div class="qso-call-group">'
        f'<div class="qso-call-row"><span class="qso-call">{esc(call)}</span>{badges}</div>'
        f'<span class="qso-time">{esc(when)}</span>'
        "</div>"
        '<div class="qso-metrics">'
        '<div class="metric-cell"><span class="metric-label">FREQUENCY</span>'
        f'<span class="metric-val is-freq">{freq_html}</span></div>'
        '<div class="metric-cell"><span class="metric-label">RST (S/R)</span>'
        f'<span class="metric-val">{rst_html}</span></div>'
        "</div></div>"
        f"{repeater_html}{stations_html}{note_html}"
        "</article>"
    )


def _v2_qso_summary(stats: dict, lang: str) -> str:
    pills = "".join(
        f'<span class="s-pill">{esc(label)} <b>{esc(value)}</b></span>'
        for label, value in (
            (t(lang, "stat.qso"), str(stats["total"])),
            (t(lang, "stat.dxcc"), str(stats["dxcc"])),
            (t(lang, "stat.first"), stats["first"]),
            (t(lang, "stat.last"), stats["last"]),
        )
    )
    return f'<div class="qso-summary solar-pills">{pills}</div>'


def _v2_qso_filter_bar(rows: list[dict], lang: str) -> str:
    bands = sorted(
        {row["band"] for row in rows if row["band"]},
        key=lambda b: (data.BAND_LIST.index(b) if b in data.BAND_LIST else 99, b),
    )
    modes = sorted({row["mode"] for row in rows if row["mode"]})
    band_opts = "".join(f'<option value="{esc(b)}">{esc(b)}</option>' for b in bands)
    mode_opts = "".join(f'<option value="{esc(m)}">{esc(m)}</option>' for m in modes)
    sort_opts = "".join(
        f'<option value="{value}">{esc(t(lang, key))}</option>'
        for value, key in (
            ("date-desc", "sort.newest"),
            ("date-asc", "sort.oldest"),
            ("call", "sort.call"),
        )
    )
    template = t(lang, "filter.showing")
    initial = S.fmt(lang, "filter.showing", n=len(rows), total=len(rows))
    return (
        f'<div class="filter-bar is-qso" data-count="{esc(template)}">'
        f'<input type="search" class="filter-input" id="qso-search" '
        f'placeholder="{esc(t(lang, "filter.search"))}" autocomplete="off">'
        f'<select class="filter-select" id="qso-band">'
        f'<option value="">{esc(t(lang, "filter.all_bands"))}</option>{band_opts}</select>'
        f'<select class="filter-select" id="qso-mode">'
        f'<option value="">{esc(t(lang, "filter.all_modes"))}</option>{mode_opts}</select>'
        f'<select class="filter-select" id="qso-sort">{sort_opts}</select>'
        f'<button type="button" class="filter-reset" id="qso-reset">{esc(t(lang, "btn.reset"))}</button>'
        f'<span class="filter-summary" id="qso-count">{esc(initial)}</span>'
        "</div>"
    )


def page_qso(ctx: Ctx, lang: str, prefix: str, page_path: str) -> str:
    head = page_head_v2(KICKERS["qso"], t(lang, "nav.qso"))

    if not ctx.rows:
        extra = (
            f'<p class="empty-hint-v2">{esc(t(lang, "empty.qso_hint"))}</p>'
            '<pre class="empty-code">date,time,call,freq,uplink,offset,ctcss,band,mode,rst_sent,rst_rcvd,power,dxcc,qth,my_qth,grid,rig,antenna,their_rig,their_power,their_antenna,their_height,my_height,notes\n'
            "2026-03-14,08:42,JA1KWF,14.270,,,,20m,SSB,59,59,100,Japan,Tokyo,Hangzhou,PM95,IC-7300,DP,,,,,,\"交换 QSL 卡片\"</pre>"
            f'<p class="empty-hint-v2">{esc(t(lang, "empty.qso_note"))}</p>'
        )
        content = empty_v2("qso", t(lang, "empty.qso_title"), t(lang, "empty.qso_lead"), extra)
    else:
        cards = "".join(_v2_qso_card(row, lang) for row in ctx.rows)
        content = (
            f"{_v2_qso_summary(ctx.stats, lang)}"
            f"{_v2_qso_filter_bar(ctx.rows, lang)}"
            f'<div class="qso-grid" id="qso-grid">{cards}</div>'
        )

    body = head + f'<section class="section-block">{content}</section>'
    return layout_v2(
        ctx,
        lang,
        prefix=prefix,
        page_path=page_path,
        active="qso",
        title=f"{t(lang, 'nav.qso')} — {ctx.cfg.get('callsign')}",
        description=t(lang, "page.qso_lead"),
        body=body,
    )


def _v2_sstv_card(entry: dict, lang: str, prefix: str) -> str:
    meta = entry["meta"]
    call = str(meta.get("call", "") or "")
    freq = str(meta.get("freq", "") or "")
    mode = str(meta.get("mode", "") or "")
    date_txt = entry["date"].isoformat() if entry["date"] else ""
    thumb = entry.get("thumb_url") or ""
    full = entry.get("image_url") or thumb

    caption = " · ".join(x for x in (call, freq, date_txt) if x)
    if thumb:
        screen_cls = "sstv-screen"
        media = (
            f'<a href="{url(prefix, full)}" data-lightbox data-caption="{esc(caption)}">'
            f'<img src="{url(prefix, thumb)}" alt="{esc((call + " " + mode).strip())}" '
            'loading="lazy" decoding="async"></a>'
        )
    else:
        screen_cls = "sstv-screen is-empty"
        media = "<span>SSTV</span>"

    mode_tag = f'<span class="sstv-mode-tag">{esc(mode)}</span>' if mode else ""
    freq_html = f"<span>{esc(freq)}</span>" if freq else ""
    date_html = f'<div class="sstv-meta">{esc(date_txt)}</div>' if date_txt else ""
    desc = data.pick(entry, lang, "note") or data.pick(entry, lang, "summary")
    desc_html = f'<p class="sstv-desc">{esc(desc)}</p>' if desc else ""

    return (
        '<article class="sstv-card">'
        f'<div class="{screen_cls}">{mode_tag}{media}</div>'
        '<div class="sstv-body">'
        f'<div class="sstv-head"><strong>{esc(call or "SSTV")}</strong>{freq_html}</div>'
        f"{date_html}{desc_html}"
        "</div></article>"
    )


def page_sstv(ctx: Ctx, lang: str, prefix: str, page_path: str) -> str:
    head = page_head_v2(KICKERS["sstv"], t(lang, "nav.sstv"))
    items = ctx.sstv

    if items:
        years = sorted({str(item["date"].year) for item in items if item["date"]}, reverse=True)
        year_opts = "".join(f'<option value="{y}">{y}</option>' for y in years)
        template = t(lang, "filter.count_cards")
        total = S.fmt(lang, "filter.count_cards", n=len(items))
        toolbar = (
            f'<div class="filter-bar" data-count="{esc(template)}">'
            f'<label class="filter-label" for="gallery-year">{esc(t(lang, "filter.year"))}</label>'
            f'<select class="filter-select" id="gallery-year">'
            f'<option value="">{esc(t(lang, "filter.all_years"))}</option>{year_opts}</select>'
            f'<span class="filter-summary" id="gallery-count">{esc(total)}</span>'
            "</div>"
        )
        blocks = []
        for year, group in data.group_by_year(items):
            grid = "".join(_v2_sstv_card(item, lang, prefix) for item in group)
            blocks.append(
                f'<section class="year-group" data-year="{esc(year)}">'
                f'<h2 class="year-title">{esc(year)}<small>{len(group)}</small></h2>'
                f'<div class="sstv-grid">{grid}</div></section>'
            )
        content = toolbar + "".join(blocks)
    else:
        content = empty_v2(
            "sstv",
            t(lang, "empty.sstv_title"),
            t(lang, "empty.sstv_lead"),
            extra=f'<p class="empty-hint-v2">{esc(t(lang, "empty.card_hint"))}</p>',
        )

    body = head + f'<section class="section-block">{content}</section>'
    title = t(lang, "nav.sstv")
    if items:
        title = f"{title} ({len(items)})"
    return layout_v2(
        ctx,
        lang,
        prefix=prefix,
        page_path=page_path,
        active="sstv",
        title=f"{title} — {ctx.cfg.get('callsign')}",
        description=t(lang, "page.sstv_lead"),
        body=body,
        with_lightbox=True,
    )


# ── 随笔 ─────────────────────────────────────────────────


def page_notes(ctx: Ctx, lang: str, prefix: str, page_path: str) -> str:
    head = page_head_v2(KICKERS["notes"], t(lang, "nav.notes"))

    if not ctx.notes:
        content = empty_v2(
            "notes",
            t(lang, "empty.notes_title"),
            t(lang, "empty.notes_lead"),
            extra=f'<p class="empty-hint-v2">{esc(t(lang, "empty.notes_hint"))}</p>',
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
                f'<li class="note-item"><a class="note-link" href="{page_url(lang, prefix, "notes/" + item["slug"] + ".html")}">'
                f'<time class="note-date" datetime="{esc(date_txt)}">{esc(date_txt)}</time>'
                f'<span class="note-main"><span class="note-title">{esc(title)}</span>'
                f'<span class="note-sum">{esc(summary)}</span></span>'
                '<span class="note-arrow" aria-hidden="true">→</span></a>'
                f'<span class="note-tags">{tag_html}</span></li>'
            )
        content = f'<ul class="note-list">{"".join(rows)}</ul>'

    body = head + f'<section class="section-block">{content}</section>'
    return layout_v2(
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
<article class="note-detail">
  <header class="note-head">
    <p class="kicker">NOTES</p>
    <h1 class="page-title">{esc(title)}</h1>
    <p class="note-meta"><time datetime="{esc(date_txt)}">{esc(date_txt)}</time>{tag_html}</p>
  </header>
  <div class="prose">{body_html}</div>
  <footer class="note-foot">
    <a class="link-arrow" href="{page_url(lang, prefix, "notes.html")}"><span aria-hidden="true">←</span>{esc(t(lang, "btn.back_notes"))}</a>
  </footer>
</article>
"""
    return layout_v2(
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


def operator_card(ctx: Ctx, lang: str) -> str:
    """操作员信息卡片：国家、呼号、QTH、网格、CQ/ITU 分区、邮箱、收卡地址。"""
    cfg = ctx.cfg

    def missing() -> str:
        return f'<span class="op-missing">{esc(t(lang, "op.missing"))}</span>'

    def cell(value, *, link: bool = False) -> str:
        text = str(value or "").strip()
        if not text:
            return missing()
        if link:
            return f'<a href="mailto:{esc(text)}">{esc(text)}</a>'
        return esc(text)

    def field(label_key: str, value, *, link: bool = False) -> str:
        return (
            f"<div><dt>{esc(t(lang, label_key))}</dt>"
            f"<dd>{cell(value, link=link)}</dd></div>"
        )

    email = str(cfg.get("email") or "").strip()
    address = ctx.qsl_address(lang).strip()
    license_text = ctx.license(lang)
    since = str(cfg.get("since") or "").strip()
    license_line = ""
    if license_text or since:
        parts = [x for x in (license_text, since) if x]
        license_line = (
            f'<span class="op-license">{esc(t(lang, "op.license"))} · {esc(" · ".join(parts))}</span>'
        )

    address_html = (
        f'<p class="op-address">{esc(address)}</p>'
        if address
        else f'<p class="op-address">{missing()}</p>'
    )

    return f"""
<article class="op-card reveal" id="card">
  <div class="op-bar">
    <span class="op-bar-label">{esc(t(lang, "op.title"))}</span>
    <span class="op-stamp">QSL</span>
  </div>
  <div class="op-main">
    <div class="op-identity">
      <span class="op-kicker">{esc(t(lang, "op.callsign"))}</span>
      <span class="op-call">{esc(cfg.get("callsign") or "")}</span>
      <span class="op-country">{cell(ctx.country(lang))}</span>
      {license_line}
    </div>
    <dl class="op-fields">
      {field("op.qth", ctx.qth(lang))}
      {field("op.grid", cfg.get("grid"))}
      {field("op.cq", cfg.get("cq_zone"))}
      {field("op.itu", cfg.get("itu_zone"))}
      {field("op.email", email, link=True)}
    </dl>
    <div class="op-qsl">
      <span class="op-label">{esc(t(lang, "op.qsl_address"))}</span>
      {address_html}
    </div>
  </div>
</article>
"""


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


def operator_card_v2(ctx: Ctx, lang: str) -> str:
    cfg = ctx.cfg

    def cell(value, *, link: bool = False) -> str:
        text = str(value or "").strip()
        if not text:
            return f'<span class="info-missing">{esc(t(lang, "op.missing"))}</span>'
        if link:
            return f'<a href="mailto:{esc(text)}">{esc(text)}</a>'
        return esc(text)

    fields = "".join(
        f'<div class="info-line"><span>{esc(t(lang, key))}</span><strong>{value}</strong></div>'
        for key, value in (
            ("op.qth", cell(ctx.qth(lang))),
            ("op.grid", cell(cfg.get("grid"))),
            ("op.cq", cell(cfg.get("cq_zone"))),
            ("op.itu", cell(cfg.get("itu_zone"))),
            ("op.license", cell(ctx.license(lang))),
            ("op.email", cell(cfg.get("email"), link=True)),
        )
    )

    address = cell(ctx.qsl_address(lang))
    return (
        '<article class="operator-card">'
        '<div class="operator-head">'
        '<div class="operator-id">'
        f'<p class="kicker">{esc(t(lang, "op.title"))}</p>'
        f'<h2>{esc(cfg.get("callsign") or "")}</h2>'
        f'<p class="operator-sub">{esc(ctx.country(lang))} · {esc(ctx.license(lang))}</p>'
        "</div>"
        '<span class="qsl-stamp-v2" aria-hidden="true">QSL</span>'
        "</div>"
        f'<div class="info-lines operator-lines">{fields}</div>'
        f'<p class="operator-address"><span>{esc(t(lang, "op.qsl_address"))}</span>{address}</p>'
        "</article>"
    )


def station_gear(ctx: Ctx, lang: str) -> str:
    cfg = ctx.cfg
    return (
        '<section class="station-grid">'
        '<div class="panel">'
        f'<h2 class="panel-title">{esc(t(lang, "station.equipment"))}</h2>'
        f'{_spec_table(cfg.get("equipment") or [], lang)}'
        "</div>"
        '<div class="panel">'
        f'<h2 class="panel-title">{esc(t(lang, "station.antennas"))}</h2>'
        f'{_spec_table(cfg.get("antennas") or [], lang)}'
        "</div>"
        "</section>"
    )


def station_sections(ctx: Ctx, lang: str) -> str:
    cfg = ctx.cfg

    contact = []
    if cfg.get("email"):
        contact.append(f'<a class="btn-v2" href="mailto:{esc(cfg["email"])}">{esc(cfg["email"])}</a>')
    if cfg.get("github"):
        contact.append(
            f'<a class="btn-v2 btn-v2-ghost" href="{esc(cfg["github"])}" target="_blank" rel="noopener">GitHub</a>'
        )
    contact_html = "".join(contact) or f'<span class="info-missing">{esc(t(lang, "station.empty_item"))}</span>'

    return (
        operator_card_v2(ctx, lang)
        + '<section class="station-grid">'
        '<div class="panel">'
        f'<h2 class="panel-title">{esc(t(lang, "station.equipment"))}</h2>'
        f'{_spec_table(cfg.get("equipment") or [], lang)}'
        "</div>"
        '<div class="panel">'
        f'<h2 class="panel-title">{esc(t(lang, "station.antennas"))}</h2>'
        f'{_spec_table(cfg.get("antennas") or [], lang)}'
        "</div>"
        '<div class="panel">'
        f'<h2 class="panel-title">{esc(t(lang, "station.contact"))}</h2>'
        f'<p class="panel-text">{esc(t(lang, "station.contact_lead"))}</p>'
        f'<div class="contact-actions">{contact_html}</div>'
        "</div>"
        "</section>"
    )


def page_station(ctx: Ctx, lang: str, prefix: str, page_path: str) -> str:
    cfg = ctx.cfg
    body = (
        page_head_v2(KICKERS["station"], t(lang, "nav.station"), t(lang, "page.station_lead"))
        + station_sections(ctx, lang)
    )
    return layout_v2(
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
    body = (
        '<section class="notfound-v2">'
        '<p class="kicker">404</p>'
        f'<h1 class="page-title">{esc(t(lang, "404.title"))}</h1>'
        f'<p class="page-lead">{esc(t(lang, "404.lead"))}</p>'
        f'<a class="btn-v2" href="{page_url(lang, prefix, "index.html")}">{esc(t(lang, "404.btn"))}</a>'
        "</section>"
    )
    return layout_v2(
        ctx,
        lang,
        prefix=prefix,
        page_path=page_path,
        active="404",
        title=f"404 — {ctx.cfg.get('callsign')}",
        description=t(lang, "404.lead"),
        body=body,
    )
