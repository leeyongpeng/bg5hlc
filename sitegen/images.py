"""图片搬运：复制到 dist/media/ 下，并在装了 Pillow 时顺手生成缩略图。

Pillow 是可选的：装了就自动缩图（页面加载更快），没装就直接用原图。
安装方式：python -m pip install pillow
"""

from __future__ import annotations

import shutil
from pathlib import Path

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif", ".bmp"}
THUMB_WIDTH = 900
THUMB_QUALITY = 82

_pillow_ready: bool | None = None


def _pillow():
    """惰性导入 Pillow；不可用时返回 None。"""
    global _pillow_ready
    if _pillow_ready is False:
        return None
    try:
        from PIL import Image  # type: ignore

        _pillow_ready = True
        return Image
    except Exception:  # pragma: no cover - 取决于本机环境
        _pillow_ready = False
        return None


def find(folder: Path, name: str) -> Path | None:
    """在内容目录里按文件名找图片（大小写不敏感，容忍漏写扩展名）。"""
    if not name:
        return None
    candidate = folder / name
    if candidate.is_file():
        return candidate
    stem = Path(name).stem.lower()
    for path in folder.iterdir() if folder.is_dir() else []:
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES:
            if path.stem.lower() == stem:
                return path
    return None


def prepare(src: Path, dest_dir: Path, slug: str) -> tuple[str, str]:
    """把图片复制成 <slug>.<ext>，返回 (原图, 缩略图) 两个相对路径。"""
    dest_dir.mkdir(parents=True, exist_ok=True)
    suffix = src.suffix.lower()
    target = dest_dir / f"{slug}{suffix}"
    if src.resolve() != target.resolve():
        shutil.copyfile(src, target)

    thumb_name = f"{slug}.thumb.jpg"
    Image = _pillow()
    made_thumb = False
    if Image is not None and suffix != ".gif":
        try:
            with Image.open(target) as img:
                img = img.convert("RGB") if img.mode not in ("RGB", "L") else img
                if img.width > THUMB_WIDTH:
                    ratio = THUMB_WIDTH / img.width
                    img = img.resize((THUMB_WIDTH, max(1, round(img.height * ratio))), Image.LANCZOS)
                img.save(dest_dir / thumb_name, "JPEG", quality=THUMB_QUALITY, optimize=True, progressive=True)
            made_thumb = True
        except Exception as exc:  # 图片损坏时不要让整站构建失败
            print(f"  ! 缩略图生成失败 {src.name}: {exc}")

    return f"media/{dest_dir.name}/{target.name}", f"media/{dest_dir.name}/{thumb_name if made_thumb else target.name}"
