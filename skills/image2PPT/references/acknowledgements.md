# Acknowledgements And Dependency Boundaries

## Companion Runtime

This skill expects a compatible `presentations` skill and its PowerPoint generation, rendering, overflow-detection, and visual-inspection toolchain. The exact packages and applications used by that companion toolchain are not vendored or pinned here.

This package contains instructions and reference material only. It does not directly bundle PptxGenJS, LibreOffice, PowerPoint, WPS, or another PPTX implementation.

## Methodology References

The workflow was informed by public presentation skills and by iterative visual QA on real reconstruction tasks:

- [OpenAI Skills](https://github.com/openai/skills): source-preserving slide generation, rendering, overflow checks, and editable generator workflows.
- [Anthropic PPTX Skill](https://github.com/anthropics/skills/tree/main/skills/pptx): structured PPTX creation, inspection, editing, and delivery practices.
- [Codex PPT Skill](https://github.com/ningzimu/codex-ppt-skill): screenshot- and PDF-driven style analysis and fidelity-first reconstruction.
- [Presentation Skill](https://github.com/sirilsengolraj-source/presentation-skill): source-first presentation generation, reusable layout systems, and QA gates.
- [pptx-from-layouts-skill](https://github.com/tristan-mcinnis/pptx-from-layouts-skill): slide-master, layout, and placeholder-aware generation.
- [PPT Agent Skills](https://github.com/sunbigfly/ppt-agent-skills): staged planning, per-slide generation, vector-oriented output, and visual QA.
- [MiniMax PPTX Generator](https://github.com/MiniMax-AI/skills/tree/main/skills/pptx-generator): combined PPTX inspection, template editing, generation, and design-system checks.
- [Guizang PPT Skill](https://github.com/op7418/guizang-ppt-skill): visual storytelling and editorial presentation composition.

These projects are references, not runtime dependencies. Users do not need to install them to use this skill.

## Attribution Status

No source code, scripts, templates, icons, or other assets from the projects above are currently vendored in this skill. The instructions are a synthesis of public workflow ideas and project-specific lessons learned during PPT reconstruction and review.

If upstream code or assets are introduced later, record the repository, file path, commit or release, license, local modifications, and destination file in this document before publishing.
