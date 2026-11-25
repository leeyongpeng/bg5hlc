#!/usr/bin/env python3
"""生成 demo/ 用的演示图片：3 张 QSL 卡片 + 3 张 SSTV 帧。

这些图只是为了让本地预览（python build.py --demo）有内容可看，
真实使用时把它们替换成自己的卡片和收图。

需要 Pillow：python -m pip install pillow
    python tools/make_demo_images.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

# Windows 控制台默认 GBK，统一成 UTF-8 免得打印中文/符号时报错。
for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
QSL_DIR = ROOT / "demo" / "qsl"
SSTV_DIR = ROOT / "demo" / "sstv"
FONT_DIR = Path("C:/Windows/Fonts")

CARD_SIZE = (900, 600)
SSTV_SIZE = (640, 480)


def font(names: list[str], size: int) -> ImageFont.FreeTypeFont:
    for name in names:
        path = FONT_DIR / name
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size)
            except OSError:
                continue
    return ImageFont.load_default()


def bold(size: int):
    return font(["arialbd.ttf", "segoeuib.ttf", "msyhbd.ttc", "DejaVuSans-Bold.ttf"], size)


def regular(size: int):
    return font(["arial.ttf", "segoeui.ttf", "msyh.ttc", "DejaVuSans.ttf"], size)


def mono(size: int):
    return font(["consola.ttf", "cour.ttf", "DejaVuSansMono.ttf"], size)


def gradient(size: tuple[int, int], top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    width, height = size
    strip = Image.new("RGB", (1, height))
    pixels = strip.load()
    for y in range(height):
        t = y / max(1, height - 1)
        pixels[0, y] = tuple(round(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
    return strip.resize(size, Image.BILINEAR)


def radial_glow(size: tuple[int, int], center: tuple[float, float], radius: float, color, strength=0.55) -> Image.Image:
    """一圈柔和的辉光，用来给卡片增加一点“电台屏幕”的感觉。"""
    width, height = size
    glow = Image.new("RGB", (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(glow)
    steps = 26
    for i in range(steps, 0, -1):
        r = radius * i / steps
        alpha = strength * (1 - i / steps) ** 2
        box = [center[0] - r, center[1] - r, center[0] + r, center[1] + r]
        tint = tuple(round(c * alpha) for c in color)
        draw.ellipse(box, fill=tint)
    return glow.filter(ImageFilter.GaussianBlur(radius / 6))


def overlay_text(img: Image.Image, xy, text, fnt, fill, anchor=None, spacing=0) -> None:
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    draw.text(xy, text, font=fnt, fill=fill, anchor=anchor, spacing=spacing)
    img.paste(Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB"), (0, 0))


def save(img: Image.Image, path: Path, quality: int = 88) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(path, "JPEG", quality=quality, optimize=True, progressive=True)
    print(f"  ✓ {path.relative_to(ROOT)}  ({path.stat().st_size // 1024} KB)")


# ── QSL 卡片 ─────────────────────────────────────────────


def card_ja1kwf(path: Path) -> None:
    width, height = CARD_SIZE
    img = gradient(CARD_SIZE, (18, 58, 54), (7, 17, 20)).convert("RGBA")
    img.alpha_composite(radial_glow(CARD_SIZE, (690, 380), 340, (30, 120, 110), 0.5).convert("RGBA"))
    draw = ImageDraw.Draw(img)

    amber = (242, 163, 60)
    paper = (245, 240, 228)

    draw.rectangle([20, 20, width - 20, height - 20], outline=amber + (150,), width=2)
    draw.line([(20, 150), (width - 20, 150)], fill=amber + (90,), width=1)

    draw.text((56, 48), "JA1KWF", font=bold(86), fill=paper + (255,))
    draw.text((58, 146), "TOKYO · JAPAN · PM95", font=mono(20), fill=(150, 205, 195, 255))

    # 右侧巨大的 QSL 字样
    draw.text((620, 250), "QSL", font=bold(190), fill=(242, 163, 60, 42), anchor="mm")

    draw.text((58, 214), "TO RADIO", font=mono(17), fill=(140, 170, 175, 255))
    draw.text((58, 240), "BG5HLC", font=bold(44), fill=paper + (255,))

    rows = [("DATE", "2026-08-29"), ("BAND", "20m"), ("MODE", "SSB"), ("RST", "59 / 59")]
    for index, (key, value) in enumerate(rows):
        y = 350 + index * 40
        draw.text((58, y), key, font=mono(16), fill=(130, 160, 165, 255))
        draw.text((164, y - 3), value, font=mono(22), fill=paper + (235,))

    draw.text((58, height - 62), "CONFIRMING QSO WITH PLEASURE", font=mono(15), fill=(120, 150, 155, 255))
    draw.text((width - 60, height - 62), "73 DE JA1KWF", font=mono(15), fill=amber + (220,), anchor="ra")

    save(img, path)


def card_dl2xyz(path: Path) -> None:
    width, height = CARD_SIZE
    img = Image.new("RGB", CARD_SIZE, (242, 236, 220))
    draw = ImageDraw.Draw(img)

    red = (176, 42, 48)
    blue = (36, 62, 120)
    ink = (28, 28, 30)

    # 左侧红色竖条 + 底部蓝色带
    draw.rectangle([0, 0, 26, height], fill=red)
    draw.rectangle([0, height - 76, width, height], fill=blue)

    # 蓝白菱形（巴伐利亚风格）铺在右侧
    cell = 34
    for row in range(-2, 12):
        for col in range(-2, 12):
            cx = width - 250 + col * cell
            cy = 60 + row * cell
            if cx < width - 250:
                continue
            draw.polygon(
                [(cx, cy - cell // 2), (cx + cell // 2, cy), (cx, cy + cell // 2), (cx - cell // 2, cy)],
                fill=(232, 238, 249),
            )

    draw.text((72, 54), "QSL", font=bold(30), fill=red)
    draw.text((72, 104), "DL2XYZ", font=bold(92), fill=ink)
    draw.text((74, 210), "MÜNCHEN · JO58", font=mono(20), fill=(70, 70, 76))

    draw.text((74, 286), "TO", font=mono(16), fill=(120, 120, 126))
    draw.text((74, 312), "BG5HLC", font=bold(40), fill=blue)

    rows = [("DATE", "2026-10-12"), ("BAND", "20m"), ("MODE", "SSB"), ("RST", "59 / 58")]
    for index, (key, value) in enumerate(rows):
        y = 388 + index * 32
        draw.text((74, y), key, font=mono(15), fill=(130, 130, 136))
        draw.text((176, y - 3), value, font=mono(20), fill=ink)

    draw.text((74, height - 62), "ANTENNA: MULTIBAND VERTICAL · 100W", font=mono(15), fill=(226, 232, 245))
    draw.text((width - 60, height - 62), "73 · DL2XYZ", font=mono(15), fill=(236, 220, 180), anchor="ra")

    save(img, path)


def card_ja3abc(path: Path) -> None:
    """复古线稿风格：米色纸 + 深绿字 + 手绘铁塔。"""
    width, height = CARD_SIZE
    img = Image.new("RGB", CARD_SIZE, (236, 231, 216))
    draw = ImageDraw.Draw(img)

    green = (28, 72, 58)
    ink = (30, 32, 34)
    pencil = (122, 122, 110)

    draw.rectangle([18, 18, width - 18, height - 18], outline=green, width=3)
    draw.rectangle([26, 26, width - 26, height - 26], outline=green, width=1)

    draw.text((60, 50), "JA3ABC", font=bold(86), fill=green)
    draw.text((62, 148), "OSAKA · JAPAN · PM84", font=mono(19), fill=(70, 96, 84))

    # 右侧手绘铁塔
    cx = 700
    for index in range(9):
        y = 520 - index * 48
        half = 92 - index * 9
        draw.line([(cx - half, y), (cx + half, y)], fill=pencil, width=2)
    draw.line([(cx - 92, 520), (cx, 128)], fill=pencil, width=2)
    draw.line([(cx + 92, 520), (cx, 128)], fill=pencil, width=2)
    draw.line([(cx, 128), (cx, 62)], fill=pencil, width=2)
    draw.line([(cx - 60, 120), (cx - 150, 96)], fill=pencil, width=2)
    draw.line([(cx + 60, 120), (cx + 150, 96)], fill=pencil, width=2)

    draw.text((62, 210), "TO RADIO", font=mono(16), fill=(120, 128, 118))
    draw.text((62, 236), "BG5HLC", font=bold(42), fill=ink)

    rows = [("DATE", "2025-11-15"), ("BAND", "40m"), ("MODE", "CW"), ("RST", "579 / 569")]
    for index, (key, value) in enumerate(rows):
        y = 350 + index * 38
        draw.text((62, y), key, font=mono(15), fill=(126, 134, 124))
        draw.text((166, y - 3), value, font=mono(21), fill=ink)

    draw.text((62, height - 60), "TNX FER QSO · 73 DE JA3ABC", font=mono(15), fill=(110, 124, 112))

    save(img, path)


def card_vk3abc(path: Path) -> None:
    width, height = CARD_SIZE
    img = gradient(CARD_SIZE, (250, 158, 82), (58, 38, 74)).convert("RGBA")

    sun = Image.new("RGBA", CARD_SIZE, (0, 0, 0, 0))
    sun_draw = ImageDraw.Draw(sun)
    sun_draw.ellipse([540, 118, 716, 294], fill=(255, 228, 176, 228))
    img.alpha_composite(sun)

    draw = ImageDraw.Draw(img)
    paper = (250, 244, 232)

    draw.text((56, 48), "VK3ABC", font=bold(88), fill=paper + (255,))
    draw.text((58, 150), "MELBOURNE · QF21 · AUSTRALIA", font=mono(19), fill=(255, 236, 214, 235))

    # 信息面板：半透明压在夕阳上，保证文字始终读得清
    panel = Image.new("RGBA", CARD_SIZE, (0, 0, 0, 0))
    panel_draw = ImageDraw.Draw(panel)
    panel_draw.rounded_rectangle(
        [56, 212, 472, 444], radius=16, fill=(16, 13, 24, 168), outline=(242, 163, 60, 95), width=1
    )
    img.alpha_composite(panel)

    draw = ImageDraw.Draw(img)
    draw.text((82, 234), "TO", font=mono(15), fill=(230, 210, 182, 210))
    draw.text((82, 258), "BG5HLC", font=bold(40), fill=paper + (255,))

    rows = [("DATE", "2026-11-10"), ("BAND", "15m"), ("MODE", "SSB"), ("RST", "57 / 55")]
    for index, (key, value) in enumerate(rows):
        y = 330 + index * 30
        draw.text((82, y), key, font=mono(14), fill=(205, 186, 165, 215))
        draw.text((186, y - 3), value, font=mono(19), fill=paper + (255,))

    # 远山与海面
    draw.polygon(
        [(0, 500), (140, 458), (280, 492), (430, 450), (560, 488), (700, 462), (900, 494), (900, 600), (0, 600)],
        fill=(40, 30, 48, 255),
    )
    draw.rectangle([0, 512, width, height], fill=(26, 22, 40, 255))
    for i in range(12):
        y = 522 + i * 7
        draw.line([(40 + i * 10, y), (width - 70 - i * 16, y)], fill=(120, 96, 120, 36), width=2)

    draw.text((58, height - 58), "73 AND GOOD DX", font=mono(15), fill=(250, 240, 226, 210))
    draw.text((width - 58, height - 58), "VK3ABC", font=mono(15), fill=(250, 240, 226, 210), anchor="ra")

    save(img, path)


# ── SSTV 帧 ──────────────────────────────────────────────


def sstv_effects(img: Image.Image, seed: int, noise: float = 0.16) -> Image.Image:
    """加一点真实接收的味道：轻微斜纹、扫描线、噪点。"""
    width, height = img.size
    # 轻微倾斜（同步不稳）
    img = img.transform(
        (width, height), Image.AFFINE, (1, 0, 0, 0.035, 1, 0), resample=Image.BILINEAR, fillcolor=(0, 0, 0)
    )
    # 噪点
    grain = Image.effect_noise((width, height), 34).convert("RGB")
    img = Image.blend(img, grain, noise * 0.55)
    # 扫描线
    layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    for y in range(0, height, 3):
        draw.line([(0, y), (width, y)], fill=(0, 0, 0, 22))
    img = Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")
    return img


def sstv_frame(
    path: Path,
    *,
    call: str,
    freq: str,
    mode: str,
    stamp: str,
    sky: tuple[tuple[int, int, int], tuple[int, int, int]],
    seed: int,
    silhouette: str,
) -> None:
    width, height = SSTV_SIZE
    img = gradient(SSTV_SIZE, *sky).convert("RGBA")
    draw = ImageDraw.Draw(img)

    if silhouette == "hill":
        draw.polygon(
            [(0, 360), (90, 300), (190, 342), (300, 286), (420, 350), (520, 320), (640, 372), (640, 480), (0, 480)],
            fill=(16, 34, 38, 255),
        )
        draw.rectangle([0, 430, width, 480], fill=(10, 24, 28, 255))
    elif silhouette == "city":
        draw.rectangle([0, 400, width, 480], fill=(40, 24, 22, 255))
        for index, (x, w, h) in enumerate([(30, 46, 96), (92, 34, 140), (140, 58, 110), (212, 40, 72), (268, 62, 120), (346, 36, 88), (396, 54, 132), (466, 44, 100), (524, 60, 118)]):
            draw.rectangle([x, 402 - h, x + w, 402], fill=(34, 22, 22, 255))
            for row in range(3):
                for col in range(max(1, w // 16)):
                    if (index + row + col) % 3 == 0:
                        draw.rectangle(
                            [x + 6 + col * 14, 402 - h + 12 + row * 22, x + 11 + col * 14, 402 - h + 18 + row * 22],
                            fill=(240, 198, 120, 200),
                        )
    else:  # moon
        draw.ellipse([430, 70, 540, 180], fill=(238, 240, 226, 235))
        draw.polygon(
            [(0, 372), (120, 316), (240, 356), (360, 300), (500, 354), (640, 310), (640, 480), (0, 480)],
            fill=(12, 16, 30, 255),
        )

    img = sstv_effects(img.convert("RGB"), seed)
    draw = ImageDraw.Draw(img)

    # 顶部标签条
    draw.rectangle([0, 0, width, 26], fill=(6, 10, 14))
    draw.text((8, 5), f"{freq}  {mode}", font=mono(13), fill=(140, 220, 205))
    draw.text((width - 8, 5), stamp, font=mono(13), fill=(220, 190, 130), anchor="ra")

    # 呼号水印
    draw.text((12, height - 44), call, font=bold(30), fill=(250, 250, 245))
    draw.text((12, height - 14), "SSTV RECEIVED", font=mono(11), fill=(230, 230, 220))

    save(img, path, quality=86)


def main() -> None:
    print("生成 QSL 卡片 …")
    card_ja1kwf(QSL_DIR / "ja1kwf.jpg")
    card_dl2xyz(QSL_DIR / "dl2xyz.jpg")
    card_vk3abc(QSL_DIR / "vk3abc.jpg")
    card_ja3abc(QSL_DIR / "ja3abc.jpg")

    print("生成 SSTV 帧 …")
    sstv_frame(
        SSTV_DIR / "ja1kwf-scottie.jpg",
        call="JA1KWF",
        freq="14.230 MHz",
        mode="Scottie 1",
        stamp="2026-06-21 08:12 UTC",
        sky=((96, 150, 176), (26, 52, 64)),
        seed=1,
        silhouette="hill",
    )
    sstv_frame(
        SSTV_DIR / "dl2xyz-martin.jpg",
        call="DL2XYZ",
        freq="14.230 MHz",
        mode="Martin 1",
        stamp="2026-09-19 18:40 UTC",
        sky=((250, 176, 108), (86, 44, 60)),
        seed=2,
        silhouette="city",
    )
    sstv_frame(
        SSTV_DIR / "vk3abc-robot.jpg",
        call="VK3ABC",
        freq="21.340 MHz",
        mode="Robot 36",
        stamp="2026-11-08 11:26 UTC",
        sky=((58, 62, 118), (14, 16, 34)),
        seed=3,
        silhouette="moon",
    )
    print("完成。")


if __name__ == "__main__":
    main()
