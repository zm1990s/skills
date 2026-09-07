---
name: icon-finder
description: "Search and insert vector icons or company/product logos when building presentations or documents. Use this whenever a slide, PPT, or doc would benefit from an icon (e.g. a rocket for growth, a shield for security, a gear for settings) or a cloud-native/company logo. Generic icons can use iconfont.cn directly or Iconify; company/product logos can use CNCF Landscape, dashboard-icons, lobe-icons, or Iconify. Saves the asset as SVG + PNG into the working directory, ready to drop into a .pptx via add_picture."
---

# Icon Finder

搜索矢量图标或公司/产品 Logo，并保存为可直接插入 PPT 的图片。所有脚本都直连公开来源，不依赖本地后端服务。

## 图标来源

- 普通图标：`iconfont` 优先，失败或无结果时可用 `iconify`。
- 公司/产品 Logo：优先 `cncf`、`dashboard`、`lobe`，也可回退 `iconify`。
- `auto` 模式：
  - 普通图标按 `iconfont -> iconify` 搜索。
  - Logo 意图按 `cncf -> dashboard -> lobe -> iconfont -> iconify` 搜索。

## 何时使用

- 做 PPT / 幻灯片，某一页需要配图标（增长→火箭、安全→盾牌、数据→图表…）
- 做 PPT / 幻灯片，需要公司、产品、云原生项目 Logo（如 Kubernetes、Envoy、VMware vSphere、Terraform）
- 文档 / 网页需要一个矢量图标
- 用户明确说「加个图标」「配图」「icon」「logo」

## 工作流

脚本路径相对本 skill 目录。默认图标会落到当前工作目录的 `icons/` 子目录；如果用户只是要单独获取图片文件，不是为了后续组装 PPT，则保存到当前目录。

### 1. 搜索候选

```bash
python scripts/find_icons.py "rocket" --limit 20
```

- 关键词优先用英文；iconfont 也支持中文。
- 输出每个候选的 `[index] source id name`。挑一个记下它的 `id`。
- `--source auto|iconfont|iconify|dashboard|lobe|cncf` 可指定来源，默认 `auto`。
- `--type auto|icon|logo` 可指定图标意图。

按普通图标搜索：

```bash
python scripts/find_icons.py "rocket" --type icon --limit 20
python scripts/find_icons.py "火箭" --source iconfont --limit 20
python scripts/find_icons.py "shield" --source iconify --limit 20
```

按 Logo 搜索：

```bash
python scripts/find_icons.py "kubernetes" --type logo --limit 20
python scripts/find_icons.py "docker" --source dashboard --limit 20
python scripts/find_icons.py "claude" --source lobe --limit 20
python scripts/find_icons.py "envoy" --source cncf --limit 20
```

### 2. 保存并转 PNG

```bash
python scripts/save_icon.py "rocket" --id <上一步的id> --size 512 --color "#2563eb"
```

- `--id` 用 `find_icons.py` 打印的 id 精确定位。
- `dashboard:`、`lobe:`、`cncf:` 和 Iconify 的 `prefix:name` id 可自动判断来源。
- iconfont 的 id 通常是数字；如需避免歧义，可加 `--source iconfont`。
- `--output-dir` 指定输出目录，默认 `icons`；用户说「单独获取图片」「下载这个图标/Logo」「保存图片」时，用 `--output-dir .` 直接保存到当前目录。
- `--color` 会替换 SVG 中的 `currentColor`；不传时默认黑色。
- 生成 `<output-dir>/<name>.svg` 和 `<output-dir>/<name>.png`（默认 512×512，透明底）。

示例：

```bash
python scripts/save_icon.py "rocket" --source iconfont --id 4766778 --size 512 --color "#2563eb"
python scripts/save_icon.py "docker" --id dashboard:docker --type logo --size 512
python scripts/save_icon.py "claude" --id lobe:claude-color --type logo --output-dir . --size 512
python scripts/save_icon.py "kubernetes" --id cncf:kubernetes --type logo --size 512
python scripts/save_icon.py "shield" --id mdi:shield-check --source iconify --size 512
```

### 3. 插入 pptx

用 pptx skill 生成幻灯片时，对保存的 PNG 用 `add_picture`：

```python
slide.shapes.add_picture("icons/rocket.png", Inches(1), Inches(1), height=Inches(0.8))
```

## 注意

- iconfont 图标多为个人上传，商用请自行确认授权；对合规敏感的正式对外材料，优先在 `--source iconify` 里选开源图标（许可清晰）。
- Logo 来自对应项目/厂商公开仓库或 CNCF Landscape，使用前仍需遵守对应品牌/商标规范；对外商用材料要确认授权。
- 图标是单色矢量时，`--color` 选与主题协调的颜色；同一套 PPT 尽量用同源、同风格的图标保持统一。
- 公司/产品 Logo 尽量用官方英文名或产品名搜索；若某关键词无结果，换更通用的英文词（如 "analytics" 而非 "数据分析大屏"）。
