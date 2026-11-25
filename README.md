# BG5HLC · 个人业余无线电主页

呼号 **BG5HLC** 的静态站点：通联记录、QSL 卡片、SSTV 相册、随笔、电台室。

- 线上地址：<https://leeyongpeng.github.io/bg5hlc/>（中文）· <https://leeyongpeng.github.io/bg5hlc/en/>（English）
- 技术栈：Python 标准库（零第三方依赖）+ GitHub Pages + GitHub Actions
- 工作流：本地写内容 → `git push` → Actions 自动构建 → 刷新网页即更新

> 产品设计与功能规划见 [docs/网站策划.md](docs/网站策划.md)。

---

## 一、快速开始

```powershell
# 本地预览（改完内容刷新浏览器即可）
python build.py --serve

# 用演示数据预览（网站还没有真实内容时，先看看长什么样）
python build.py --demo --serve
```

打开 <http://127.0.0.1:8080>。构建产物在 `dist/`，不提交到仓库。

要求：Python 3.10+，不装任何包也能跑。装了 Pillow 会自动生成缩略图（可选）：

```powershell
python -m pip install pillow
```

---

## 二、目录结构

```
.
├── site.config.json        # 呼号、简介、QTH、设备、天线、联系方式
├── data/
│   └── qso.csv             # 通联记录（Excel 可直接编辑）
├── content/
│   ├── qsl/                # QSL 卡片：一个 .md + 一张图
│   ├── sstv/               # SSTV 图像：一个 .md + 一张图
│   └── notes/              # 随笔
├── assets/                 # CSS / JS / favicon
├── demo/                   # 演示数据，只在 --demo 时使用
├── sitegen/                # 生成器源码
├── build.py                # 入口
└── dist/                   # 构建产物（不入库）
    ├── *.html              # 中文
    └── en/*.html           # 英文
```

`content/` 下以 `_` 开头的文件是模板，不会被发布。

---

## 三、语言与主题

### 3.1 中英切换

站点不是同屏双语，而是**两套独立页面**：

| 地址 | 语言 |
|---|---|
| `/`、`/qso.html`、`/qsl.html` … | 中文 |
| `/en/`、`/en/qso.html` … | English |

右上角的 `EN` / `中文` 按钮会跳到当前页面的另一种语言版本，链接是自动算好的，不用手写。

内容也一样：给某个条目再建一个同名的 `.en.md`，英文页就会用它。

```
content/qsl/ja1kwf.md        ← 中文正文
content/qsl/ja1kwf.en.md     ← 英文正文（可选）
content/notes/pota-2026.md
content/notes/pota-2026.en.md
```

`.en.md` 里没写的字段（call、date、band、image、tags…）会自动回退到中文版本，所以英文文件通常只需要写一段英文正文，最多再补个 `title` / `summary` / `tags`。

界面文案（导航、按钮、空状态）在 `sitegen/strings.py` 里集中维护，每条都是 `(中文, 英文)` 一对。

### 3.2 日夜主题

右上角的太阳/月亮按钮切换明暗，选择存在浏览器 `localStorage` 里；第一次访问跟随系统设置。

配色（纸张米色 + 森林绿 + 焦橙）在 `assets/css/style.css` 顶部的变量里，两套主题各自一组：

```css
html[data-theme="dark"] { --bg: #0f1a14; --text: #f2e6ce; --accent: #f3a24e; … }
html[data-theme="light"] { --bg: #f6ecd9; --text: #16241c; --accent: #e8751a; … }
```

改一个变量就能整体换色。

---

## 四、怎么加内容

### 4.1 通联记录

用 Excel 或记事本打开 `data/qso.csv`，照着表头加行：

| 字段 | 必填 | 说明 | 示例 |
|---|---|---|---|
| `date` | ✓ | UTC 日期 | `2026-03-14` |
| `time` | | UTC 开始时间 | `08:42` |
| `call` | ✓ | 对方呼号 | `JA1KWF` |
| `band` | ✓ | 波段 | `20m` / `70cm` |
| `mode` | ✓ | 模式 | `SSB` / `FT8` / `CW` / `FM` / `SSTV` |
| `rst_sent` / `rst_rcvd` | | 收发信号报告 | `59` / `579` |
| `dxcc` | | DXCC 实体 | `Japan` |
| `qth` | | 对方城市 | `Tokyo` |
| `grid` | | 网格 | `PM95` |
| `notes` | | 备注 | `首次通联` |

注意：

- 时间统一用 **UTC**；
- `date` 只写日期，别把时间塞进去；
- Excel 保存时选 **CSV UTF-8**（带 BOM），中文才不会乱码；
- 列的顺序无所谓，认 `date`、`call`、`band`、`mode` 这些列名。

### 4.2 QSL 卡片

1. 卡片拍照/扫描后放进 `content/qsl/`，建议长边 ≤ 1600px、单张 ≤ 300KB；
2. 复制 `content/qsl/_template.md` 改名（例如 `2026-03-14-ja1kwf.md`），填字段：

```yaml
---
call: JA1KWF
date: 2026-03-14
band: 20m
mode: SSB
via: 卡片局          # 卡片局 / 直寄 / eQSL / LoTW
image: ja1kwf.jpg    # 与 .md 同目录的图片文件名
---
卡片背后的故事，支持 Markdown。
```

### 4.3 SSTV 图像

模板是 `content/sstv/_template.md`：

```yaml
---
call: JA1KWF
date: 2026-06-21
freq: 14.230 MHz
mode: Scottie 1
image: ja1kwf-scottie.jpg
note: 20m 段收到的第一张。
---
```

### 4.4 随笔

复制 `content/notes/_template.md`：

```yaml
---
title: 周末在江边架台
date: 2026-09-13
tags: [POTA, 便携]
summary: 列表页显示的摘要。
---
正文用 Markdown 写。
```

### 4.5 呼号、设备、联系方式

改 `site.config.json`。和英文页相关的字段都以 `_en` 结尾，缺省时英文页显示中文值：

| 字段 | 用途 |
|---|---|
| `callsign` / `tagline` / `tagline_en` | 呼号与品牌标语 |
| `description` / `description_en` | 首页与页脚的简介 |
| `qth` / `grid` / `license` / `license_en` | 电台室信息 |
| `qsl_via` / `qsl_via_en` | QSL 政策 |
| `equipment` / `antennas` / `software` | 设备、天线、软件表 |
| `url` | 部署地址，用于 hreflang 备用链接 |

---

## 五、发布到 GitHub Pages

### 5.1 首次配置（只做一次）

1. 仓库必须是**公开**的（免费账号的 Pages 不支持私有仓库）；
2. 打开仓库 → **Settings** → **Pages**；
3. **Source** 选 **GitHub Actions**（不要选 Deploy from a branch）。

不用手动创建 workflow，`.github/workflows/pages.yml` 已经就位。

### 5.2 日常更新

```powershell
git add -A
git commit -m "新增一张 JA1KWF 的 QSL 卡片"
git push
```

推送后 GitHub 自动构建发布，通常 1 分钟内生效。

### 5.3 怎么确认发布成功

- 仓库 **Actions** 标签页看 `Build & Deploy` 是否变绿；
- 页脚右下角的「最近构建 / Built」时间变了就是新版本；
- 没变化先 `Ctrl + F5` 强刷（GitHub Pages 有 1～2 分钟 CDN 缓存）。

---

## 六、国内访问说明

`*.github.io` 在中国大陆**没有保证**：多数时候能打开，但会遇到 DNS 污染、连接重置、加载慢，不同运营商和时段差别很大。GitHub 本身不属于在国内有稳定接入的服务。

如果想更稳，可以按顺序考虑：

1. **换 Cloudflare Pages**：免费、支持 Git 自动部署，绑定自己的域名后国内一般能访问，仍会波动；
2. **国内对象存储 + CDN**（阿里云 OSS / 腾讯云 COS）：最稳，但域名需要 ICP 备案；
3. **双部署**：GitHub Pages 主站 + Cloudflare Pages 镜像，用同一个域名切换。

本站是纯静态的，迁移成本很低——同一份 `dist/` 放到任何静态托管都能跑。

---

## 七、常见问题

**Q：push 之后网站没更新？**
先看 Actions 是否成功。红色 × 表示构建或部署失败，点进去看日志；常见原因是 CSV 写坏（某行少列）或 frontmatter 少 `---`。

**Q：本地 `python` 找不到？**
装 Python 3.10+ 并勾选 "Add python.exe to PATH"。本项目只用标准库。

**Q：中文在 Excel 里乱码？**
保存时选「CSV UTF-8（逗号分隔）」，构建时兼容带 BOM 的文件。

**Q：英文页有中文？**
说明该条目还没有 `.en.md`，或英文文件里缺字段导致回退到中文。补一个同名 `.en.md` 即可。

**Q：图片太大？**
单张压到 300KB 以内、长边 ≤ 1600px。装了 Pillow 后构建会自动生成 900px 缩略图。

**Q：`--demo` 会不会把演示数据发布出去？**
不会。`--demo` 只读 `demo/` 目录，Actions 跑的是 `python build.py`，只读真实内容。

**Q：想换配色？**
改 `assets/css/style.css` 顶部两套主题的 CSS 变量即可。

---

## 八、后续计划

- **M2**：命令行录入 `tools/add_qso.py`、ADIF 日志导入、图片批量压缩
- **M3**：随笔 RSS、相册归档细化
- **M4**：DXCC 世界地图、Open Graph 分享图、性能与 SEO

---

## 九、许可

站点内容（通联记录、卡片照片、图像与文字）版权归 BG5HLC 所有，转载请联系。
生成器代码可自由取用。
