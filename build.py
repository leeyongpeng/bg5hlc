#!/usr/bin/env python3
"""BG5HLC 个人站点生成器。

只依赖 Python 标准库（Pillow 可选，用于自动生成缩略图）。

用法：
    python build.py                 # 生成静态站点到 dist/
    python build.py --serve         # 生成后启动本地预览 http://127.0.0.1:8080
    python build.py --serve --port 4000
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from sitegen.build import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main(ROOT))
