"""读取并规范化 site.config.json。

站点里的称呼、简介、设备清单、联系邮箱等都集中在这个文件里，
改配置不需要碰任何模板代码。
"""

from __future__ import annotations

import json
from pathlib import Path

DEFAULTS: dict = {
    "callsign": "BG5HLC",
    "operator": "",
    "tagline": "业余无线电 · HF / VHF · QSL via bureau",
    "tagline_en": "",
    "description": "记录我的业余无线电通联、收到的 QSL 卡片、SSTV 图像与设备笔记。",
    "description_en": "",
    "country": "",
    "country_en": "",
    "qth": "",
    "qth_en": "",
    "grid": "",
    "cq_zone": "",
    "itu_zone": "",
    "license": "",
    "license_en": "",
    "email": "",
    "qsl_address": "",
    "qsl_address_en": "",
    "github": "",
    "url": "",
    "since": "",
    "qsl_via": "",
    "qsl_via_en": "",
    "equipment": [],
    "antennas": [],
    "bands": [],
}

# 英文页缺字段时用中文配置兜底，这里只列出需要单独提供英文的项。
EN_PAIRS = ("tagline", "description", "license", "qsl_via", "country", "qth", "qsl_address")


def load(root: Path) -> dict:
    """读取 <root>/site.config.json，缺失的字段用默认值补齐。"""
    cfg = dict(DEFAULTS)
    path = root / "site.config.json"
    if path.exists():
        raw = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(raw, dict):
            raise SystemExit("site.config.json 必须是一个 JSON 对象")
        cfg.update(raw)

    # 统一去掉字符串两端空白，避免手写配置时多出来的空格影响显示。
    for key, value in list(cfg.items()):
        if isinstance(value, str):
            cfg[key] = value.strip()

    cfg["url"] = cfg["url"].rstrip("/")
    cfg["callsign"] = cfg["callsign"] or "N0CALL"
    cfg["site_name"] = cfg.get("site_name") or cfg["callsign"]
    return cfg


def absolute_url(cfg: dict, path: str) -> str:
    """把站内相对路径拼成绝对地址；没配置 url 时返回空串。"""
    if not cfg.get("url"):
        return ""
    return f"{cfg['url']}/{path.lstrip('/')}"
