---
name: "ppt-spec-to-pptx"
description: "根据《幻灯片生成规格说明文件》（Markdown）生成正式、可编辑的 PowerPoint / PPTX 幻灯片。当用户提供规格 Markdown 文件并要求\"生成 PPT\"、\"按规格做幻灯片\"、\"把这份规格说明转成 PPTX\"或类似需求时使用。"
---

# 幻灯片生成 Skill（规格 Markdown → PPTX）

本 Skill 指导 Agent 将《幻灯片生成规格说明文件》（Markdown）转化为正式、可编辑的 PowerPoint / PPTX 文件。

## 关键定位

- **输入**：一份 Markdown 规格说明文件，已包含完整页面结构、标题、副标题、内容、Speaker Notes、页面草图、设计说明、注意事项。
- **任务**：根据该文件生成对应的 `.pptx` 文件。**不是重新创作内容，不是改写故事，不是优化结构**。
- **唯一权威输入**：规格 Markdown 文件。如果不存在或缺失，先要求用户提供。

## 一、内容执行硬约束（不得违反）

1. 严格按 Markdown 中的页面标题、副标题、内容、Speaker Notes、顺序、结构、角色生成幻灯片
2. **不得**修改页面标题或副标题
3. **不得**改写、扩写、删减、合并、重排页面内容
4. **不得**修改、删减、重写 Speaker Notes
5. **不得**调整页面顺序
6. **不得**添加新页面
7. **不得**将已有页面拆分
8. **不得**把页面写成普通文章
9. **不得**用整页图片替代可编辑页面
10. 每页 Speaker Notes **必须**写入演讲者备注区（notes_slide）
11. 如规格文件本身有问题，输出"建议调整项"，**不要**直接修改正式幻灯片

页数、顺序、标题、副标题、内容、Speaker Notes 是硬约束。不能因"看起来更合理""内容太多""版式更美观"而自行修改。

## 二、视觉与格式要求

**允许优化**：页面布局、视觉层级、图标风格、对齐、留白、字号层级、色块/卡片/流程/表格的视觉表达。

**不得改变**：页面标题、副标题、内容、Speaker Notes、顺序、角色、核心观点、故事结构。

**通用格式**：
- 16:9 宽屏（幻灯片尺寸 13.333 × 7.5 英寸）
- 浅色背景（除非规格另有指定）
- 微软雅黑字体（除非规格另有指定）
- 必须可编辑 `.pptx`，不得是 PDF 或整页图片
- 页面草图仅表达结构，不要求逐像素照搬
- 排版清晰、专业，适合商务/咨询/客户沟通/管理层汇报
- 每页 Speaker Notes 写入备注区
- 第一页隐藏说明页保留在文件中，**设置为隐藏幻灯片**（`slide.show = False` 或 XML 设置 `show="0"`）
- 最后一页为 Thank You / 感谢页

## 三、表格要求

页面有表格时**必须使用 PowerPoint 原生表格**（`shapes.add_table`）。

**禁止**：
- 多个文本框拼接
- 多个形状拼接
- 多条线条拼接
- 截图或图片模拟表格
- 字符排版模拟表格

表格必须可编辑（行列、文字、样式可改）。

## 四、PPTX 输出要求

1. 必须是可编辑 `.pptx`
2. 不要生成 PDF
3. 不要把页面做成整张图片
4. 16:9
5. 浅色背景
6. 微软雅黑（除非另有指定）
7. 表格使用原生表格
8. 不用文本框/形状/线条伪造表格
9. 排版专业
10. 第一页隐藏说明页设为隐藏幻灯片
11. 最后一页 Thank You

## 五、待确认信息处理

规格中标注【待确认】的内容（产品名称、产品组合、伙伴关系、客户案例、外部数据、对外口径、商务承诺等），**保留"待确认"标记，不要自行替换、补充、猜测或编造**。如发现关键信息缺失但未标注，列入"建议调整项"，不要私自补全。

## 工作流程

### 1. 读取并理解规格文件
- 用 Read 工具读取 Markdown 规格文件
- 解析每页：标题 / 副标题 / 内容 / Speaker Notes / Wireframe / 注意事项
- 列出页面清单确认无遗漏

### 2. 准备环境
- 优先调用 pptx skill（如果在 available_skills 中）：`Skill: "pptx"` 或读取 SKILL.md
- 否则使用 python-pptx：`pip install python-pptx --break-system-packages`

### 3. 生成 PPTX

使用 python-pptx 时的关键代码模式：

```python
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor
from pptx.oxml.ns import qn
from copy import deepcopy

prs = Presentation()
# 16:9
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

# 添加幻灯片（使用空白版式 layout 6）
blank = prs.slide_layouts[6]
slide = prs.slides.add_slide(blank)

# 文本框
tb = slide.shapes.add_textbox(Inches(0.5), Inches(0.4), Inches(12.3), Inches(1.0))
tf = tb.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
run = p.add_run()
run.text = "页面标题"
run.font.name = "微软雅黑"
run.font.size = Pt(32)
run.font.bold = True
run.font.color.rgb = RGBColor(0x1F, 0x2A, 0x44)

# 设置东亚字体（让中文也使用微软雅黑）
rPr = run._r.get_or_add_rPr()
ea = rPr.find(qn('a:ea'))
if ea is None:
    from lxml import etree
    ea = etree.SubElement(rPr, qn('a:ea'))
ea.set('typeface', '微软雅黑')

# 原生表格
rows, cols = 3, 4
tbl_shape = slide.shapes.add_table(rows, cols, Inches(0.5), Inches(2.0), Inches(12.3), Inches(4.5))
table = tbl_shape.table
table.cell(0, 0).text = "列1"
# ...

# Speaker Notes
notes_tf = slide.notes_slide.notes_text_frame
notes_tf.text = "讲稿内容..."

# 隐藏第一页（隐藏说明页）
from pptx.oxml.ns import qn
sld = prs.slides[0]._element  # 第一张
sld.set('show', '0')

prs.save("output.pptx")
```

### 4. 关键实现要点

**字体**：中文需要在 run 的 rPr 中同时设置 `latin` 和 `ea` typeface 为"微软雅黑"，否则 PowerPoint 会用默认字体渲染中文。

**隐藏幻灯片**：python-pptx 没有直接 API。使用：
```python
slide_element = prs.slides._sldIdLst[0]  # 或对应索引
slide_element.set('show', '0')
```
更稳妥的做法是给 `<p:sld>` 根元素加 `show="0"`：
```python
prs.slides[0]._element.set('show', '0')
```

**16:9 尺寸**：`prs.slide_width = Inches(13.333); prs.slide_height = Inches(7.5)`

**浅色背景**：默认白色即可；如需指定主色调，使用淡色（#F5F7FA、#FFFFFF、浅灰等）。

**视觉层级**：
- 标题 28-36pt 加粗
- 副标题 16-20pt
- 正文 14-16pt
- 注释 10-12pt
- 留白充足，对齐统一

**Wireframe 处理**：把 ASCII 框图转化为合理的视觉布局（左右分栏、三段式、流程箭头、卡片网格、能力地图等）。**不要**把 ASCII 字符直接当文本放进幻灯片。

**Speaker Notes**：完整、原样写入 `slide.notes_slide.notes_text_frame.text`。不要省略、改写。

### 5. 自检（生成前）
- [ ] 页数与规格文件一致
- [ ] 页面顺序与规格一致
- [ ] 每页标题、副标题、内容与规格逐字一致
- [ ] 每页 Speaker Notes 已写入备注区
- [ ] 第一页设置为隐藏
- [ ] 最后一页是 Thank You
- [ ] 所有表格使用原生表格
- [ ] 16:9，浅色背景，微软雅黑（含中文）
- [ ] 没有整页图片替代内容
- [ ] 【待确认】标记保留

### 6. 交付
- 保存到 outputs 目录
- 用 `computer://` 链接分享 `.pptx` 文件
- 如有"建议调整项"，单独列出（在聊天里，不写入 PPT）

## 重要提示

- **永远不要**主动"优化"规格文件中的内容措辞，即使它读起来啰嗦或不通顺
- **永远不要**因为某页"内容太少"就增加内容，或"内容太多"就拆页
- **永远不要**用图片代替文字（除非规格明确要求图片）
- **永远不要**省略 Speaker Notes
- 如果规格文件本身有结构或内容问题，先生成 PPT，再在聊天里提出"建议调整项"供用户决策
