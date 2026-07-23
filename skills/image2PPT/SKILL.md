---
name: 通过图片反向绘制 PPT
description: 根据屏幕截图、幻灯片图像、PDF 或视觉参考资料，重建高保真且可编辑的 PowerPoint 演示文稿。此功能适用于以下场景：既要求保持视觉外观高度一致，又需确保标题、正文、KPI、标签及流程文本可编辑；需将仅含图像的 PPTX 页面转换为包含可编辑元素的混合型幻灯片；或在以往基于原生形状的重建过程中出现了双重边框、裁剪框错位、间距偏差或装饰元素重绘保真度低等问题。
tags: [PPT,办公,效率]
category: PPT
author: Joy
---

# 通过图片反向绘制 PPT

Use this skill together with the `presentations` skill. Follow the presentation toolchain, workspace, rendering, and overflow requirements from that skill.

## Default Contract

Use this priority unless the user specifies otherwise:

1. Visual fidelity.
2. Editable text and data.
3. Replaceable icons and small visual assets.
4. Editable decorative elements.

Keep titles, subtitles, section labels, body copy, KPIs, units, process labels, and audience-facing footer text editable. Do not force buildings, waves, watermarks, gradients, shadows, and complex ornament into native PowerPoint shapes.

## Choose The Reconstruction Route

- Use **native reconstruction** only for visually simple slides whose fidelity can be preserved with text, basic shapes, tables, charts, and connectors.
- Use **hybrid reconstruction** by default for screenshot- or PDF-driven branded slides with complex chrome, illustration, gradients, shadows, or decorative geometry.
- Use **image-only slides** only when the user explicitly prioritizes pixel fidelity over editability.

Read [references/layering-and-qa.md](references/layering-and-qa.md) before implementing hybrid reconstruction.

Read [references/acknowledgements.md](references/acknowledgements.md) only when maintaining or publishing this skill, or when reviewing its dependency and attribution boundaries.

## Workflow

1. Audit every source page at full resolution. Record the slide size, text regions, decorative regions, repeated components, icons, and structural boundaries.
2. Build a layer map before coding. Assign each visible element to exactly one owner: background image, composite asset, independent icon, native shape, or editable text.
3. Prepare a text-free visual base. Preserve gradients, watermarks, waves, buildings, shadows, and complex curves only after removing all source text and content structures.
4. If a clean background cannot be produced reliably, reconstruct the global background from tightly cropped decorative assets and native structural shapes. Do not use the source screenshot or PDF page as a full-slide image and do not conceal it with masks.
5. Extract icons as tight physical crops or use transparent SVG/PNG replacements. Prefer native PowerPoint shapes or SVG for rings, shields, targets, people, arrows, and other simple symbols. Insert each icon as an independent object. Do not rely on PowerPoint crop metadata unless the rendered preview proves it works.
6. When a screenshot-derived badge has a soft or blurry outer circle, split it into a native shape background plus a tightly cropped transparent center glyph. Never upscale the complete raster badge to simulate a crisp icon.
7. Normalize icons by visual bounds, not by source canvas size. Define one badge diameter and one glyph safe zone for each repeated set such as KPIs, cards, process steps, or footers, then optically center every glyph inside that set.
8. Recreate all required text as native text boxes. Match the source baseline, width, wrapping, typeface, weight, line spacing, and alignment. Reserve extra width and height for PowerPoint/WPS font metrics instead of fitting text exactly to the generated preview.
9. Give repeated card bodies the same top coordinate, width, line spacing, and vertical alignment. Use top alignment for multi-line body copy unless the reference clearly centers it.
10. When a card contains four or more stacked items, divide the available content region into explicit equal-height cells. Give every item a full-cell text box and vertically center it; place dividers on the shared cell boundaries.
11. Give same-level section labels on one slide the same left coordinate, width, and total visual bounds unless the reference clearly distinguishes them. Measure the composite through the decorative tail, not only the red rectangle.
12. Put repeated peer cards on an explicit grid. Use one column width, one gutter, and one inset system for every card; derive header arrows, number badges, icons, and body boxes from those shared dimensions.
13. For repeated icon-and-label rows, use a fixed icon cell, a fixed gap, and a left-aligned label box on a shared vertical centerline. Do not center labels inside oversized boxes because visual icon-to-text spacing will vary with label length.
14. When a circular badge straddles a card border, set the badge centerline exactly equal to the border coordinate. Derive the card position from the badge center instead of tuning the two objects independently.
15. Build repeated footer bands from a shared vertical centerline. Center the icon, summary, and report label independently on that line; do not align them by unrelated top offsets. Keep footer icon color, ring treatment, and apparent scale consistent across the deck.
16. Keep native shapes limited to masks, simple separators, editable hit areas, and genuinely resizable structural elements.
17. Export the `.pptx`, retain the editable `.mjs` source, render every slide, and run the QA gate below.
18. When the user's target presentation app is available, open the exported deck in that app and inspect the real rendering. Generator previews are not sufficient for final text wrapping and image-crop decisions.

## Non-Negotiable Rules

- Never draw the same border, shadow, title bar, arrow, or icon in both the background and native layers.
- Never use a screenshot or PDF page containing source text, cards, icons, or data as a full-slide background in an editable reconstruction.
- Never implement editability as a full-slide reference image plus white masks and replacement text.
- Never place editable text directly over baked source text. Remove or fully mask the baked text first.
- Never leave a white rectangular crop around an icon. Use a transparent asset, tight crop, or shape mask and verify it at full size.
- Never use an opaque raster tile for an icon placed on a colored footer or badge. Use transparent SVG/PNG or construct the badge from native shapes plus a vector glyph.
- Never enlarge a low-resolution screenshot crop when the same badge can be built as a native circle plus a transparent glyph or SVG.
- Never use placeholder characters such as `盾`, `群`, or `图` when the reference contains a recognizable icon.
- Never reconstruct complex decoration with many approximate native shapes merely to claim full editability.
- Never accept a title component with visible textbox boundaries, misaligned icon baseline, or an oversized masking rectangle.
- Never add an overview or marketing slide that is absent from the source unless the user requests it.

## QA Gate

Inspect every slide individually at full size and compare it side by side with the source. Reject the output if any of these are present:

- Original and editable text both visible, even faintly.
- Any full-slide reference image that still contains source text, cards, icons, or data.
- Small white mask blocks, patchwork masks, or obvious rectangular content plates.
- Double borders, duplicated card outlines, or repeated shadows.
- Whole-slide thumbnails appearing inside icon frames because crop metadata failed.
- Icon background squares, clipping seams, or inconsistent icon centering.
- Repeated icons with inconsistent apparent scale, stroke weight, or safe-zone padding even when their image boxes have equal dimensions.
- Section bars whose decorative wedge or cut corner is detached.
- Same-level section bars with drifting widths or decorative tails whose top and bottom edges do not align with the main bar.
- Titles, subtitles, and title icons on different baselines.
- KPI values with inconsistent font size, weight, or unit spacing.
- Repeated card copy with different top baselines or mixed top/middle vertical alignment.
- Dense stacked lists whose text boxes have different heights or are not centered inside equal row cells.
- Peer cards with drifting widths, uneven gutters, or header and badge geometry that is not derived from the same grid.
- Repeated icon-and-label rows whose apparent gap changes because the labels are centered in differently filled text boxes.
- Circular badges that straddle a card border without sharing the border's exact centerline.
- Footer icons, summaries, and report labels that do not share the footer band's visual centerline.
- Footer icons that switch color, ring treatment, or apparent scale without a semantic reason.
- Overlap, clipping, wrapping regressions, unresolved placeholders, or text outside the slide.
- Text that fits in the generator preview but wraps, clips, or crosses a divider in PowerPoint, WPS, or the user's named target app.

Allow at least a small font-metric safety margin around dense text, especially bold Chinese text and rich-text runs. When a mask remains visible, replace several small masks with one content-region mask, use a sampled visual patch, or prepare a clean background asset. Do not hide the problem by adding more borders or containers.

## Deliverables

Name the primary output with an `_editable` or `_hybrid_editable` suffix. Preserve the prior version when iterating. Deliver the final PPTX and retain the generator source and intermediate assets in the presentation workspace.
