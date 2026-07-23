# Layering And QA Reference

## Layer Ownership

| Layer | Include | Exclude |
| --- | --- | --- |
| Visual background | Waves, buildings, maps, gradients, complex shadows, decorative curves | Audience-facing text, data, duplicate card borders |
| Composite asset | Text-free section bars, decorative wedges, complex card chrome, process-strip background | Editable labels or values |
| Independent icon | Tight-cropped or transparent icon, badge artwork, currency symbol artwork | White crop rectangles, neighboring text |
| Native shape | Masks, simple dividers, hit areas, basic card geometry when not baked into another layer | Approximate redraws of complex art |
| Editable text | Titles, subtitles, section labels, body text, KPIs, units, process steps, footers | Decorative text baked into a visual asset unless explicitly accepted |

Each visible element must have one owner. If the background already contains a card outline and shadow, do not add another native card outline.

## Text Removal Strategy

Use these methods in descending order of preference:

1. Create a clean text-free background while preserving source decoration.
2. Rebuild the background from tightly cropped decorative assets when a clean full-frame background is unavailable.
3. Replace a complete component with a text-free composite asset and overlay editable text.
4. Use a local mask only inside a cropped component whose background is truly flat. Never mask a full-slide screenshot to simulate editability.

Do not create one mask per line of text when a single card-interior mask is possible. Recreate separators after masking if necessary.

## Full-Slide Image Gate

Reject an editable reconstruction when a reference screenshot or PDF page appears as an image covering most of the slide. A full-frame bitmap is allowed only after it has been verified to contain no source text, cards, icons, KPIs, or other editable content. Inspect image bounding boxes and the rendered slide before delivery.

## Icon Extraction

- Prefer SVG or transparent PNG from a trusted icon source when it visually matches.
- Prefer native shapes or SVG for simple rings, targets, shields, people, arrows, and document symbols.
- When extracting from a screenshot, crop the physical bitmap before inserting it into the deck.
- Keep neighboring labels and card text outside the crop.
- Use ellipse or round-rectangle image masks only after the crop is tight.
- For circular screenshot badges, rebuild the circle, outline, and shadow as native shapes and retain only a tightly cropped center glyph. This avoids blurry badge edges and square crop artifacts.
- Do not upscale a screenshot crop beyond its useful resolution.
- Verify that moving or deleting the icon does not reveal a duplicated icon underneath.

## Text Metric Safety

- Do not size a text box to the exact generated-preview bounds. Leave enough width and height for PowerPoint/WPS font substitution and line-height differences.
- Reduce font size or widen the text column before allowing a line to touch a card border or dashed divider.
- Recheck rich-text paragraphs because bold lead-ins can change wrapping even when the plain-text preview fits.
- Keep repeated titles and body columns on shared x/y anchors rather than aligning each one by eye.

## Section Bars And Process Strips

Treat a red bar plus gold wedge, folded corner, or complex arrow silhouette as one text-free visual component. Overlay only its text. Keep the full process strip as a background asset when its gradients and joins are complex; add independent editable labels and icons above it.

For native multi-step arrow strips:

- Match the reference topology before styling: a continuous chevron ribbon must remain continuous and must not be replaced with separated narrow arrows.
- Use one shared height, pitch, icon anchor, and text baseline for every step.
- Reserve the arrowhead area as non-text space; do not center text across the full arrow bounding box.
- Keep a real gap between adjacent arrows, or prove that any overlap affects only the arrowhead. A neighboring arrow must never cover the next step's icon or label box.
- Leave an explicit right-side safety margin on the final arrow because PowerPoint/WPS may render the last label wider than the generator preview.
- Use a transparent or vector pictogram. Do not place a white document rectangle or screenshot crop inside a red arrow.
- Give every icon its own fixed-size anchor box and verify all steps at full size; do not reuse uneven screenshot crops whose visible glyph sizes vary.
- When a long label cannot fit without touching the arrowhead, reduce the label font or widen all steps consistently.

For repeated footer bands:

- Implement the footer as one shared component across the deck. Derive icon, summary, and right-side report-label positions from the band centerline instead of hard-coding different vertical offsets per slide.
- Keep the footer band flush to the slide bottom, but allow its height to follow the reference page. Vertically center each footer object within that page's band.
- Preserve one shared left anchor for the summary and one shared right anchor for the report label. Verify their optical baselines in PowerPoint or WPS, not only in the generator preview.

## Comparison Checklist

For each slide compare:

- Canvas proportions and margins.
- Title icon size, title baseline, subtitle spacing.
- Card positions, widths, heights, corner radius, border weight, and shadow softness.
- Internal text anchors and line breaks.
- Icon crop, optical center, and distance to labels.
- Footer band height, summary baseline, and right-side report label.
- Source text removal and mask visibility at 100% zoom.

Render the final deck and inspect each slide, not only a montage. Search layout and inspection output for overflow, outside-canvas objects, warnings, `NaN`, and `Infinity`. When PowerPoint, WPS, Keynote, or the user's named target app is available, open the exported PPTX there and inspect every edited slide at normal zoom before delivery.
