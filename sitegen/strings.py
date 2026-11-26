"""界面文案（中文 / 英文）。

站点按语言生成两套页面：`/` 是中文，`/en/` 是英文。
每种语言只显示自己的文字，不再同屏并排。
"""

from __future__ import annotations

STRINGS: dict[str, tuple[str, str]] = {
    # ── 导航 ────────────────────────────────────────────────
    "nav.home": ("首页", "Home"),
    "nav.qso": ("通联记录", "QSO Log"),
    "nav.qsl": ("QSL 卡片", "QSL Cards"),
    "nav.sstv": ("SSTV 相册", "SSTV"),
    "nav.notes": ("随笔", "Notes"),
    "nav.station": ("电台室", "Station"),
    # ── 通用按钮 ────────────────────────────────────────────
    "btn.view_all": ("查看全部", "View all"),
    "btn.all_qso": ("全部通联记录", "All QSOs"),
    "btn.qsl_exchange": ("如何交换卡片", "How to exchange"),
    "btn.back_notes": ("返回随笔列表", "Back to notes"),
    "btn.reset": ("清空筛选", "Reset"),
    "btn.contact": ("写信给我", "Get in touch"),
    # ── 首页 ────────────────────────────────────────────────
    "home.meta_qth": ("QTH", "QTH"),
    "home.meta_grid": ("网格", "GRID"),
    "home.meta_license": ("操作证书", "LICENSE"),
    "home.meta_bands": ("常用频段", "BANDS"),
    "home.section_latest": ("最新通联", "Latest QSOs"),
    "home.section_qsl": ("最近的 QSL 卡片", "Recent QSL Cards"),
    "home.section_sstv": ("最近的 SSTV", "Recent SSTV"),
    "home.section_equip": ("设备速览", "Station at a glance"),
    "home.cta_title": ("想和我交换 QSL 卡片？", "Want to exchange a QSL card?"),
    "home.cta_body": (
        "卡片局（Bureau）优先，也可直寄。收到卡片的我都会回卡，通常两到三周内寄出。",
        "Bureau first, direct mail is fine too. Every card I receive gets one back, usually within two or three weeks.",
    ),
    # ── 统计标签 ────────────────────────────────────────────
    "stat.qso": ("通联", "QSO"),
    "stat.dxcc": ("DXCC", "DXCC"),
    "stat.qsl": ("QSL 卡片", "QSL"),
    "stat.sstv": ("SSTV", "SSTV"),
    "stat.bands": ("波段", "Bands"),
    "stat.first": ("首次通联", "First QSO"),
    "stat.last": ("最近通联", "Latest QSO"),
    "stat.months": ("最近 12 个月", "Last 12 months"),
    "stat.by_band": ("按波段分布", "By band"),
    # ── 表格表头 ────────────────────────────────────────────
    "th.date": ("日期", "Date"),
    "th.time": ("时间", "UTC"),
    "th.call": ("呼号", "Call"),
    "th.band": ("波段", "Band"),
    "th.mode": ("模式", "Mode"),
    "th.rst": ("RST", "RST"),
    "th.dxcc": ("地区", "DXCC"),
    "th.notes": ("备注", "Notes"),
    # ── 空状态 ──────────────────────────────────────────────
    "empty.qso_title": ("还没有通联记录", "No QSOs logged yet"),
    "empty.qso_lead": (
        "日志从零开始也没关系。照着下面的格式往 data/qso.csv 加一行，记录就会出现在这里。",
        "Starting from zero is fine. Add a row to data/qso.csv in the format below and it appears here.",
    ),
    "empty.qsl_title": ("还没有 QSL 卡片", "No QSL cards yet"),
    "empty.qsl_lead": (
        "收到卡片后拍张照，和一段文字一起放进 content/qsl/ 目录即可。",
        "Photograph a card, drop it into content/qsl/ with a short note, and it appears here.",
    ),
    "empty.sstv_title": ("还没有 SSTV 图像", "No SSTV pictures yet"),
    "empty.sstv_lead": (
        "把收到的图像存进 content/sstv/，加上频率和模式信息就能归档。",
        "Save a decoded picture into content/sstv/ with its frequency and mode to archive it.",
    ),
    "empty.notes_title": ("还没有随笔", "No notes yet"),
    "empty.notes_lead": (
        "野外架台、设备折腾、天线 DIY，都值得记一笔。",
        "Field operations, gear tweaks, antenna builds — all worth writing down.",
    ),
    "empty.qso_hint": (
        "日志就是一张表格，照着表头加一行即可（用 Excel 或记事本打开 data/qso.csv）：",
        "The log is just a table. Add a row like this in data/qso.csv:",
    ),
    "empty.qso_note": (
        "时间一律用 UTC；波段写 20m、70cm 这种形式；模式写 SSB、FT8、CW。",
        "Times are UTC. Bands look like 20m or 70cm, modes like SSB, FT8, CW.",
    ),
    "empty.card_hint": (
        "在该目录下新建一个 .md（可复制 _template.md），把图片放在同一目录。",
        "Create a .md in that folder (copy _template.md) and put the image next to it.",
    ),
    "empty.notes_hint": (
        "在 content/notes/ 新建一个 .md，写上 title 和 date 即可。",
        "Create a .md in content/notes/ with a title and a date.",
    ),
    "empty.home_hint": ("在 data/qso.csv 里照着表头加一行：", "Add a row to data/qso.csv:"),
    # ── 页面标题与导语 ──────────────────────────────────────
    "page.qso_lead": (
        "按时间倒序排列的全部通联。可以按呼号、地区搜索，也可以只看某个波段或模式。",
        "Every QSO, newest first. Search by callsign or country, or narrow down by band and mode.",
    ),
    "page.qsl_lead": (
        "从各个国家寄来的卡片，按收到年份归档。点开可以看大图。",
        "Cards from around the world, grouped by year. Click any card for the full size.",
    ),
    "page.sstv_lead": (
        "在 HF 和 VHF 上收到的 SSTV 图像，保留了原始的画质和噪点。",
        "SSTV pictures received on HF and VHF, kept exactly as they came out of the decoder.",
    ),
    "page.notes_lead": (
        "架台记录、设备评测、天线实验，以及一些和无线电有关的碎碎念。",
        "Field reports, gear reviews, antenna experiments, and radio-related notes.",
    ),
    "page.station_lead": (
        "我的电台室、天线，以及怎么和我交换卡片。",
        "My shack, my antennas, and how to exchange a card with me.",
    ),
    # ── 筛选器 ──────────────────────────────────────────────
    "filter.search": ("搜索呼号 / 地区 / 备注", "Search call, country, notes"),
    "filter.band": ("波段", "Band"),
    "filter.mode": ("模式", "Mode"),
    "filter.year": ("年份", "Year"),
    "filter.all_bands": ("全部波段", "All bands"),
    "filter.all_modes": ("全部模式", "All modes"),
    "filter.all_years": ("全部年份", "All years"),
    "filter.count": ("共 {n} 条", "{n} QSOs"),
    "filter.count_cards": ("共 {n} 张", "{n} cards"),
    "filter.none": ("没有匹配的记录", "Nothing matches those filters"),
    "filter.swipe": ("左右滑动可查看其余列", "Swipe sideways for more columns"),
    # ── 电台室 ──────────────────────────────────────────────
    "op.title": ("个人信息 · 操作员", "Station card"),
    "op.callsign": ("呼号 / CALLSIGN", "Callsign"),
    "op.country": ("国家", "Country"),
    "op.qth": ("QTH", "QTH"),
    "op.grid": ("网格坐标", "Grid"),
    "op.cq": ("CQ 分区", "CQ zone"),
    "op.itu": ("ITU 分区", "ITU zone"),
    "op.email": ("邮箱", "Email"),
    "op.qsl_address": ("收卡地址 / QSL VIA", "QSL address"),
    "op.missing": ("待填写", "To be added"),
    "op.license": ("操作证书", "License"),
    "station.qth": ("QTH 与执照", "QTH & license"),
    "station.equipment": ("设备", "Equipment"),
    "station.antennas": ("天线", "Antennas"),
    "station.software": ("软件", "Software"),
    "station.qsl": ("QSL 政策", "QSL policy"),
    "station.contact": ("联系方式", "Contact"),
    "station.col_item": ("名称", "Item"),
    "station.col_role": ("类别", "Role"),
    "station.col_note": ("备注", "Note"),
    "station.empty_item": ("待补充", "To be added"),
    "station.contact_lead": ("通过邮件或 GitHub 都能找到我。", "Email or GitHub both reach me."),
    # ── 页脚 ────────────────────────────────────────────────
    "footer.nav": ("导航", "Navigate"),
    "footer.more": ("其它", "More"),
    "footer.site": ("站点", "Site"),
    "footer.contact": ("联系", "Contact"),
    "footer.made": ("由 Python 生成 · 托管于 GitHub Pages", "Generated with Python · Hosted on GitHub Pages"),
    "footer.built": ("最近构建", "Built"),
    # ── 其它 ────────────────────────────────────────────────
    "a11y.skip": ("跳到主要内容", "Skip to content"),
    "a11y.home": ("返回首页", "Back to home"),
    "a11y.theme": ("切换主题（自动 / 浅色 / 深色）", "Cycle theme (auto / light / dark)"),
    "theme.auto": ("自动 · 跟随系统", "Auto · follow system"),
    "theme.light": ("浅色", "Light"),
    "theme.dark": ("深色", "Dark"),
    "theme.label": ("主题", "Theme"),
    "marquee": (
        "BG5HLC ✺ 通联记录 ✺ QSL 卡片 ✺ SSTV 接收 ✺ 73 DE BG5HLC ✺ CQ CQ CQ",
        "BG5HLC ✺ QSO Log ✺ QSL Cards ✺ SSTV RX ✺ 73 DE BG5HLC ✺ CQ CQ CQ",
    ),
    "a11y.to_en": ("切换到英文", "Switch to English"),
    "a11y.to_zh": ("切换到中文", "Switch to Chinese"),
    "misc.demo": ("演示数据 · 不代表真实通联记录", "Demo data · not a real logbook"),
    "misc.demo_badge": ("示例", "DEMO"),
    "404.title": ("页面不存在", "Page not found"),
    "404.lead": (
        "这个地址上没有内容。可能是链接过期了，也可能是呼号听错了。",
        "Nothing lives at this address. The link may be stale, or the call was misheard.",
    ),
    "404.btn": ("回到首页", "Back to home"),
}

LANGS = ("zh", "en")


def tr(lang: str, key: str) -> str:
    """按语言取文案：zh 取第一个，en 取第二个。"""
    zh, en = STRINGS[key]
    return en if lang == "en" else zh


def fmt(lang: str, key: str, **kwargs) -> str:
    return tr(lang, key).format(**kwargs)


def other(lang: str) -> str:
    return "en" if lang == "zh" else "zh"
