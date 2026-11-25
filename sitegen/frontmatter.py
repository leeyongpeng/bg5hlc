"""极简 YAML frontmatter 解析器。

内容文件的格式：

    ---
    title: 标题
    date: 2026-03-14
    tags: [SSTV, 20m]
    featured: true
    ---
    正文（Markdown）
"""

from __future__ import annotations


def _scalar(raw: str):
    text = raw.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        return text[1:-1]
    low = text.lower()
    if low in ("true", "yes", "on"):
        return True
    if low in ("false", "no", "off"):
        return False
    if text.startswith("[") and text.endswith("]"):
        inner = text[1:-1].strip()
        if not inner:
            return []
        return [_scalar(part) for part in inner.split(",") if part.strip()]
    return text


def parse(text: str) -> tuple[dict, str]:
    """返回 (元数据字典, 正文)。没有 frontmatter 时元数据为空。"""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if not text.startswith("---"):
        return {}, text

    lines = text.split("\n")
    end = None
    for index in range(1, len(lines)):
        if lines[index].strip() in ("---", "..."):
            end = index
            break
    if end is None:
        return {}, text

    meta: dict = {}
    for line in lines[1:end]:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip().lower()] = _scalar(value)

    body = "\n".join(lines[end + 1:]).strip("\n")
    return meta, body
