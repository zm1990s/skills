---
name: icon-finder
description: "Search and insert vector icons or company/product logos when building presentations or documents. Use this whenever a slide, PPT, or doc would benefit from an icon (e.g. a rocket for growth, a shield for security, a gear for settings) or a cloud-native/company logo. For company/product logos, search CNCF Landscape first because it hosts many SVG logos; for generic icons, search iconfont.cn (preferred) with automatic fallback to Iconify's open-source icons. Saves the asset as SVG + PNG into the working directory, ready to drop into a .pptx via add_picture."
---

# Icon Finder

搜索矢量图标或公司/产品 Logo，并保存为可直接插入 PPT 的图片。图标源：普通图标 **iconfont.cn 优先**，请求失败/超时自动降级 **Iconify**（20 万+ 开源图标）；公司/产品 Logo **优先查 CNCF Landscape**（`https://landscape.cncf.io`，大量 SVG Logo）。

## 何时使用

- 做 PPT / 幻灯片，某一页需要配图标（增长→火箭、安全→盾牌、数据→图表…）
- 做 PPT / 幻灯片，需要公司、产品、云原生项目 Logo（如 Kubernetes、Envoy、VMware vSphere、Terraform）
- 文档 / 网页需要一个矢量图标
- 用户明确说「加个图标」「配图」「icon」「logo」

## 工作流

脚本路径相对本 skill 目录。默认图标会落到**当前工作目录**的 `icons/` 子目录；如果用户只是要单独获取图片文件，不是为了后续组装 PPT，则保存到当前目录。

### 1. 搜索候选

```bash
python scripts/find_icons.py "rocket" --limit 20
```

- 关键词**优先用英文**（两个源的英文命中率都更高）；也支持中文。
- 输出每个候选的 `[index] source id name`。挑一个记下它的 **id**。
- `--source auto|iconfont|iconify|cncf` 可指定源，默认 `auto`（普通图标：iconfont 优先降级 iconify）。
- **找公司/产品 Logo 时，先用 CNCF Landscape**：

```bash
python scripts/find_icons.py "kubernetes" --type logo --limit 20
# 或强制只查 CNCF:
python scripts/find_icons.py "kubernetes" --source cncf --limit 20
```

- `--type logo` 会先查 CNCF Landscape；无结果时回退原来的 iconfont/Iconify。`--type icon` 可强制按普通图标查找。

### 2. 保存并转 PNG

```bash
python scripts/save_icon.py "rocket" --id <上一步的id> --size 512 --color "#2563eb"
```

- `--id` 用 find_icons.py 打印的 id 精确定位。
- `--output-dir` 指定输出目录，默认 `icons`；用户说「单独获取图片」「下载这个图标/Logo」「保存图片」时，用 `--output-dir .` 直接保存到当前目录。
- 如果上一步用了 `--type logo` 或 `--source cncf`，保存时也带上相同参数：

```bash
python scripts/save_icon.py "kubernetes" --id <上一步的id> --type logo --size 512
```

单独获取图片时：

```bash
python scripts/save_icon.py "kubernetes" --id <上一步的id> --type logo --output-dir . --size 512
```

- `--color` 把图标染成指定色（SVG 里的 `currentColor` 会被替换；不传默认黑）。
- 生成 `<output-dir>/<name>.svg` 和 `<output-dir>/<name>.png`（默认 512×512，透明底）。

### 3. 插入 pptx

用 pptx skill 生成幻灯片时，对保存的 PNG 用 `add_picture`：

```python
slide.shapes.add_picture("icons/rocket.png", Inches(1), Inches(1), height=Inches(0.8))
```

## 注意

- **合规**：iconfont 图标多为个人上传，**商用请自行确认授权**；对合规敏感的正式对外材料，优先在 `--source iconify` 里选开源图标（许可清晰）。
- **Logo**：CNCF Landscape 的 Logo 多来自对应项目/厂商，使用前仍需遵守对应品牌/商标规范；对外商用材料要确认授权。
- 图标是单色矢量，`--color` 选与主题协调的颜色；同一套 PPT 尽量用同源、同风格的图标保持统一。
- 公司/产品 Logo 尽量用官方英文名或产品名搜索；若某关键词无结果，换更通用的英文词（如 "analytics" 而非 "数据分析大屏"）。
