"""极简 Markdown 渲染器（无第三方依赖）。

支持：标题、段落、粗体、斜体、删除线、行内代码、代码块、链接、图片、
无序/有序列表、引用、分隔线。够写通联笔记和卡片背面故事了。
"""

from __future__ import annotations

import html
import re

_INLINE_CODE = re.compile(r"`([^`]+)`")
_IMAGE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"([^\"]*)\")?\)")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)(?:\s+\"([^\"]*)\")?\)")
_BOLD = re.compile(r"\*\*(.+?)\*\*")
_STRIKE = re.compile(r"~~(.+?)~~")
_ITALIC = re.compile(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?!\*)")

_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
_HR = re.compile(r"^\s*(-{3,}|\*{3,}|_{3,})\s*$")
_ULIST = re.compile(r"^\s*[-*+]\s+(.*)$")
_OLIST = re.compile(r"^\s*\d+[.)]\s+(.*)$")
_QUOTE = re.compile(r"^\s*>\s?(.*)$")


def _inline(text: str) -> str:
    """转义 HTML 后按 Markdown 规则加行内标记。"""
    text = html.escape(text, quote=False)

    stash: list[str] = []

    def keep(fragment: str) -> str:
        stash.append(fragment)
        return f"\x00{len(stash) - 1}\x00"

    text = _INLINE_CODE.sub(lambda m: keep(f"<code>{m.group(1)}</code>"), text)
    text = _IMAGE.sub(
        lambda m: keep(
            f'<img src="{m.group(2)}" alt="{m.group(1)}" loading="lazy"'
            + (f' title="{m.group(3)}"' if m.group(3) else "")
            + ">"
        ),
        text,
    )
    text = _LINK.sub(
        lambda m: keep(
            f'<a href="{m.group(2)}"'
            + (f' title="{m.group(3)}"' if m.group(3) else "")
            + f">{m.group(1)}</a>"
        ),
        text,
    )
    text = _BOLD.sub(r"<strong>\1</strong>", text)
    text = _STRIKE.sub(r"<del>\1</del>", text)
    text = _ITALIC.sub(r"<em>\1</em>", text)

    for index, fragment in enumerate(stash):
        text = text.replace(f"\x00{index}\x00", fragment)
    return text


def render(text: str) -> str:
    """把 Markdown 文本渲染成 HTML 片段。"""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    out: list[str] = []
    i, total = 0, len(lines)

    while i < total:
        line = lines[i]

        if line.lstrip().startswith("```"):
            i += 1
            buffer: list[str] = []
            while i < total and not lines[i].lstrip().startswith("```"):
                buffer.append(lines[i])
                i += 1
            i += 1
            out.append('<pre class="code"><code>' + html.escape("\n".join(buffer)) + "</code></pre>")
            continue

        if not line.strip():
            i += 1
            continue

        heading = _HEADING.match(line)
        if heading:
            level = len(heading.group(1))
            inner = _inline(heading.group(2).strip())
            out.append(f"<h{level}>{inner}</h{level}>")
            i += 1
            continue

        if _HR.match(line):
            out.append("<hr>")
            i += 1
            continue

        if _QUOTE.match(line):
            buffer = []
            while i < total:
                quoted = _QUOTE.match(lines[i])
                if quoted:
                    buffer.append(quoted.group(1))
                    i += 1
                elif buffer and lines[i].strip():
                    buffer.append(lines[i])
                    i += 1
                else:
                    break
            out.append("<blockquote><p>" + _inline(" ".join(x.strip() for x in buffer)) + "</p></blockquote>")
            continue

        m = _ULIST.match(line)
        if m:
            items = []
            while i < total:
                item = _ULIST.match(lines[i])
                if not item:
                    break
                items.append(f"<li>{_inline(item.group(1).strip())}</li>")
                i += 1
            out.append("<ul>" + "".join(items) + "</ul>")
            continue

        m = _OLIST.match(line)
        if m:
            items = []
            while i < total:
                item = _OLIST.match(lines[i])
                if not item:
                    break
                items.append(f"<li>{_inline(item.group(1).strip())}</li>")
                i += 1
            out.append("<ol>" + "".join(items) + "</ol>")
            continue

        buffer = [line]
        i += 1
        while i < total and lines[i].strip():
            nxt = lines[i]
            if _HEADING.match(nxt) or _ULIST.match(nxt) or _OLIST.match(nxt) or _QUOTE.match(nxt) or nxt.lstrip().startswith("```"):
                break
            buffer.append(nxt)
            i += 1
        out.append("<p>" + _inline(" ".join(x.strip() for x in buffer)) + "</p>")

    return "\n".join(out)


def plain(text: str, limit: int = 0) -> str:
    """取纯文本摘要（去掉 Markdown 标记），用于列表页和 meta description。"""
    cleaned = re.sub(r"```.*?```", " ", text, flags=re.S)
    cleaned = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", cleaned)
    cleaned = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", cleaned)
    cleaned = re.sub(r"[#>*_`~\-]+", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if limit and len(cleaned) > limit:
        return cleaned[: max(0, limit - 1)].rstrip() + "…"
    return cleaned
