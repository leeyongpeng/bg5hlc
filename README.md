# BG5HLC · 个人业余无线电主页

呼号 **BG5HLC** 的静态站点：通联记录、QSL 卡片、SSTV 相册、随笔、电台室。

- 线上地址：<https://leeyongpeng.github.io/bg5hlc/>
- 技术栈：Python 标准库（零第三方依赖）+ GitHub Pages + GitHub Actions
- 工作流：本地写内容 → `git push` → Actions 自动构建 → 刷新网页即更新

> 产品设计与功能规划见 [docs/网站策划.md](docs/网站策划.md)。

---

## 一、快速开始

```powershell
# 本地预览（改完内容刷新浏览器即可）
python build.py --serve

# 用演示数据预览（网站现在还没有真实内容时，先看看长什么样）
python build.py --demo --serve
```

打开 <http://127.0.0.1:8080>。构建产物在 `dist/`，不提交到仓库。

要求：Python 3.10+，无需安装任何包。装了 Pillow 会自动生成缩略图（可选）：

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
├── tools/
│   └── make_demo_images.py # 生成 demo 图片（需要 Pillow）
├── sitegen/                # 生成器源码
├── build.py                # 入口
└── dist/                   # 构建产物（不入库）
```

`content/` 下以 `_` 开头的文件是模板，不会被发布。

---

## 三、怎么加内容

### 3.1 通联记录

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
- `date` 只认日期，别把时间写进去；
- Excel 保存时选 **CSV UTF-8**（带 BOM），中文才不会乱码；
- 列的顺序无所谓，列名认 `date`、`call`、`band`、`mode` 这些关键词。

### 3.2 QSL 卡片

1. 把卡片拍照/扫描后放进 `content/qsl/`，建议长边 ≤ 1600px、单张 ≤ 300KB；
2. 复制 `content/qsl/_template.md` 改个名字（例如 `2026-03-14-ja1kwf.md`），填字段：

```yaml
---
call: JA1KWF
date: 2026-03-14
band: 20m
mode: SSB
via: 卡片局          # 卡片局 / 直寄 / eQSL / LoTW
image: ja1kwf.jpg    # 与 .md 同目录的图片文件名
note_en: First card from Japan.
---
这里写卡片背后的故事，支持 Markdown。
```

### 3.3 SSTV 图像

和 QSL 一样，模板是 `content/sstv/_template.md`：

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

### 3.4 随笔

复制 `content/notes/_template.md`：

```yaml
---
title: 周末在江边架台
title_en: A weekend activation   # 可选
date: 2026-09-13
tags: [POTA, 便携]
summary: 列表页显示的摘要。
summary_en: Optional English summary.
---
正文用 Markdown 写。
```

### 3.5 呼号、设备、天线、联系方式

改 `site.config.json`：`callsign`、`description`、`qth`、`grid`、`email`、`equipment`、`antennas`、`software`、`qsl_via` 等。改完刷新即可。

> `url` 字段要和实际部署地址一致（现在是 `https://leeyongpeng.github.io/bg5hlc`）。如果以后换成自定义域名，记得一起改。

---

## 四、发布到 GitHub Pages

### 4.1 首次配置（只做一次）

1. 打开仓库 <https://github.com/leeyongpeng/bg5hlc> → **Settings** → **Pages**；
2. **Source** 选 **GitHub Actions**（不要选 Deploy from a branch）；
3. 不用手动创建任何 workflow，`.github/workflows/pages.yml` 已经就位。

### 4.2 日常更新

```powershell
git add -A
git commit -m "新增一张 JA1KWF 的 QSL 卡片"
git push
```

推送后 GitHub 会自动构建并发布，通常 1 分钟内生效。刷新页面就能看到新内容。

### 4.3 怎么知道发布成功了

- 仓库顶部 **Actions** 标签页，看 `Build & Deploy` 是否变绿；
- 网页页脚右下角有「最近构建 2026-11-26 10:24」，时间变了就说明是新版本；
- 没变化先 `Ctrl + F5` 强制刷新（GitHub Pages 有 1～2 分钟 CDN 缓存）。

---

## 五、可选：自定义域名

1. 域名 DNS 添加 `CNAME` 记录指向 `leeyongpeng.github.io`；
2. 仓库 Settings → Pages → Custom domain 填入域名；
3. 在 `site.config.json` 把 `url` 改成新域名。

想用根地址 `https://leeyongpeng.github.io/` 而不是 `/bg5hlc/`：把仓库改名成 `leeyongpeng.github.io` 即可，代码里的链接都是相对路径，不需要改。

---

## 六、常见问题

**Q：push 之后网站没更新？**
先看 Actions 是否成功。红色 × 表示构建或部署失败，点进去看日志；常见原因是 CSV 格式写坏（比如某行少了一列）或 frontmatter 少了 `---`。

**Q：本地 `python` 找不到？**
装 Python 3.10+ 并勾选 "Add python.exe to PATH"。本项目只用到标准库。

**Q：中文在 Excel 里乱码？**
保存时选「CSV UTF-8（逗号分隔）」。构建时兼容带 BOM 的文件。

**Q：图片太大，页面很慢？**
单张压到 300KB 以内、长边 ≤ 1600px。装了 Pillow 后构建会自动生成 900px 缩略图，列表页只加载缩略图。

**Q：`--demo` 会不会把演示数据发布出去？**
不会。`--demo` 只读 `demo/` 目录，GitHub Actions 跑的是 `python build.py`，只读真实内容。

**Q：想换配色/字体？**
改 `assets/css/style.css` 顶部的 CSS 变量（`--amber`、`--cyan`、`--bg` 等）即可。

---

## 七、后续计划

- **M2**：命令行录入 `tools/add_qso.py`、ADIF 日志导入 `tools/import_adif.py`、图片批量压缩
- **M3**：随笔 RSS、相册更细致的归档
- **M4**：DXCC 世界地图、Open Graph 分享图、性能与 SEO 打磨

---

## 八、许可

站点内容（通联记录、卡片照片、图像与文字）版权归 BG5HLC 所有，转载请联系。
生成器代码可自由取用。
