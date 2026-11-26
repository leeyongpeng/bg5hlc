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
├── assets/                 # CSS / JS / favicon（site-v2.css = 当前；style.css = 旧版遗留）
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

全站使用新版清爽皮肤：`assets/css/site-v2.css` + `assets/js/site-v2.js`。

右上角是**太阳 / 月亮图标按钮**，切换浅色 / 深色；选择存在浏览器 `localStorage` 的 `bg5hlc-theme` 里，没有手动选择时默认浅色。按钮本身不显示文字，只在 `aria-label` 里保留读屏提示。

配色在 `assets/css/site-v2.css` 顶部，两套主题各一组：

```css
html[data-theme="light"] { --bg: #f6f4ef; --brand: #234d36; --accent: #d96b18; … }
html[data-theme="dark"]  { --bg: #111614; --brand: #52a375; --accent: #f08c3a; … }
```

> `assets/css/style.css` 和 `assets/js/app.js` 是上一版纸张风的遗留文件，页面已不再加载，保留仅作参考。

### 3.3 首页结构

- 顶部：呼号 + 导航 tab + `EN` + 日夜切换；
- 首屏：个人信息（呼号、标语、网格/分区、主力设备、主力天线、QSL 政策）+ 固定 9 行的 ASCII 双人通联动画，可暂停 / 单步；
- 信息条：台站信息、日志概况（QSO / DXCC / QSL / SSTV 数量）、QSL 政策与联系方式；
- 电台室：首页直接展示设备和天线表（导航里的「电台室」tab 已移除）；
- QSL 卡片：最近 6 张，按时间倒序；有图显示大图，没图用 CSS 画卡面；点开进 QSL 页；
- 页脚：呼号、QTH、构建时间、GitHub。

### 3.4 字体

`Archivo Black`（标题）和 `Space Grotesk`（正文）是**自托管**的，放在 `assets/fonts/`，不依赖 Google Fonts——国内访问不会被字体域名拖慢或卡住。中文仍然用系统字体（苹方 / 微软雅黑）。

换字体：把 woff2 放进 `assets/fonts/`，改 `assets/css/site-v2.css` 顶部的 `@font-face` 和 `--display` / `--sans` 变量。

---

## 四、怎么加内容

### 4.1 通联记录

用 Excel 或记事本打开 `data/qso.csv`，照着表头加行：

| 字段 | 必填 | 说明 | 示例 |
|---|---|---|---|
| `date` | ✓ | UTC 日期 | `2026-03-14` |
| `time` | | UTC 开始时间 | `08:42` |
| `call` | ✓ | 对方呼号 | `JA1KWF` |
| `freq` | | QSO 频率 / 中继下行频率（不带单位按 MHz） | `14.270` / `145.400` |
| `uplink` | | 中继上行频率（MHz） | `144.800` |
| `offset` | | 中继频差（MHz） | `-0.6` |
| `ctcss` | | 发射亚音（Hz） | `107.2` |
| `band` | ✓ | 波段 | `20m` / `70cm` |
| `mode` | ✓ | 模式 | `SSB` / `FT8` / `CW` / `FM` / `SSTV` |
| `rst_sent` / `rst_rcvd` | | 收发信号报告 | `59` / `579` |
| `power` | | 本台功率（W） | `100` / `5` |
| `dxcc` | | DXCC 实体 | `Japan` |
| `qth` | | 对方 QTH | `Tokyo` |
| `my_qth` | | 本台 QTH | `Hangzhou` |
| `grid` | | 网格 | `PM95` |
| `rig` | | 本台设备（可留空） | `IC-7300` |
| `antenna` | | 本台天线（可留空） | `20m 偶极` |
| `their_rig` | | 对方设备（可留空） | `FT-7500 车台` |
| `their_power` | | 对方功率（W，可留空） | `8` |
| `their_antenna` | | 对方天线（可留空） | `八木天线` |
| `their_height` | | 对方天线架设高度 / 楼层（可留空） | `四楼` / `20m` |
| `my_height` | | 本台天线架设高度 / 楼层（可留空） | `六楼` |
| `notes` | | 备注：只写要做的事（如交换 QSL 卡片） | `交换 QSL 卡片` |

通联记录页把每条通联渲染成一张卡片：呼号右侧是频率和 RST 读数，中继参数（上行 / 下行 / 频差 / 亚音）单独一块，本台和对方的 QTH / 设备 / 功率 / 天线 / 架设高度分两栏展示；`notes` 只显示动作、提醒这类真正的备注。中文页面的时间自动换算成北京时间，英文页面显示 UTC。支持搜索、波段/模式筛选和排序；首页不再放通联列表，只有个人信息和 QSL 展示。

注意：

- 时间统一用 **UTC** 填写；中文页面的卡片会自动换算成北京时间（UTC+8），跨零点时日期一起变，英文页面仍显示 UTC；
- `date` 只写日期，别把时间塞进去；
- 中继信息填 `uplink`、`offset`、`ctcss`，不要塞进 `notes`；
- 本台设备填 `rig` / `antenna`，本台架设高度填 `my_height`（如 `六楼`）；对方设备填 `their_rig` / `their_power` / `their_antenna`，对方架设高度填 `their_height`（如 `四楼`）。两栏都会显示 `ALT` 一行；
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
| `description` / `description_en` | 首页的 meta 描述（搜索引擎摘要） |
| `country` / `country_en` | 国家（个人信息卡片） |
| `qth` / `grid` | QTH 与网格坐标 |
| `cq_zone` / `itu_zone` | CQ / ITU 分区 |
| `qsl_address` / `qsl_address_en` | 收卡地址（可多行） |
| `license` / `license_en` / `since` | 操作证书与入坑年份 |
| `email` | 邮箱（卡片与联系区） |
| `qsl_via` / `qsl_via_en` | QSL 政策 |
| `equipment` / `antennas` | 设备、天线表 |
| `url` | 部署地址，用于 hreflang 备用链接 |

> 首页的「台站信息 / QSL 联系」区块，以及 `/station.html` 顶部的「个人信息卡片」，都会读这些字段：国家、呼号、QTH、网格、CQ/ITU 分区、邮箱、收卡地址。没填的会显示「待填写」，不会报错。电台室 tab 已从导航移除，设备和天线直接放在首页。

### 4.6 导出单文件 HTML（给外部改版）

把页面打包成一个不依赖服务器、双击就能打开的 HTML，方便发给别人调 UI：

```powershell
python tools/export_qso_design.py                    # 通联卡片页，含真实 + 演示数据
python tools/export_design.py --page qso.html       # 任意页面，只用演示数据
```

输出在 `preview/`。CSS、JS、字体、favicon 全部内联，搜索、筛选、排序、主题切换都能直接用；文件开头的注释标了 CSS 变量和 `.qso-card` 相关样式的位置。改完把 HTML 发回来，再按改动回填到 `sitegen/` 和 `assets/`。

---

## 五、发布到 GitHub Pages

站点支持两种发布方式，选一种即可。

### 方式 A：GitHub Actions（自动化，推荐）

**首次配置**

1. 仓库必须是**公开**的（免费账号的 Pages 不支持私有仓库）；
2. 仓库 → **Settings** → **Pages** → **Source** 选 **GitHub Actions**。

之后每次 `git push` 都会自动构建部署。

### 方式 B：发布到 gh-pages 分支（Actions 不可用时）

如果 Actions 因为账号限制、额度或设置问题跑不起来，用这个方式：

```powershell
python tools/publish.py          # 构建 + 发布到 gh-pages 分支
```

**首次配置**：仓库 → **Settings** → **Pages** → **Source** 选 **Deploy from a branch** → Branch 选 `gh-pages` → 目录选 `/(root)` → Save。

提交 history 不变，构建产物单独放在 `gh-pages` 分支里，主分支保持干净。

### 日常更新

```powershell
# 方式 A
git add -A; git commit -m "新增一张 QSL 卡片"; git push

# 方式 B
git add -A; git commit -m "新增一张 QSL 卡片"; git push
python tools/publish.py
```

### 怎么确认发布成功

- 仓库 **Actions** 标签页看 `Build & Deploy` 是否变绿（方式 A）；
- 页脚右下角的「最近构建 / Built」时间变了就是新版本；
- 没变化先 `Ctrl + F5` 强刷（GitHub Pages 有 1～2 分钟 CDN 缓存）。

### 如果 Actions 一直不跑

表现：`Actions` 页显示 "There are no workflow runs yet."，即使反复 push 也没有任何运行记录。这通常是账号或仓库层面禁用了 Actions，检查：

- 仓库 **Settings → Actions → General**，确认 **Allow all actions** 且没有被 Disable；
- 账号的 **Settings → Billing** 是否有异常；
- 邮箱是否已验证。

在修好之前，用方式 B 发布即可，站点内容完全一样。

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
