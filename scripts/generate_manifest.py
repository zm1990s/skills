#!/usr/bin/env python3
"""
Scans the skills/ directory, reads each .skill file (zip archive containing SKILL.md),
and generates skills.json for the Skill Hub frontend.

Usage:
    python scripts/generate_manifest.py
"""

import json
import os
import re
import sys
import zipfile
from pathlib import Path
from datetime import datetime, timezone

SKILLS_DIR = Path(__file__).parent.parent / "skills"
OUTPUT_FILE = Path(__file__).parent.parent / "skills.json"

# Default category icons (used as fallback)
CATEGORY_ICONS = {
    "文档": "📄",
    "数据": "📈",
    "安全": "🛡️",
    "设计": "🎨",
    "工作流": "⚙️",
    "翻译": "🌐",
    "研究": "🔬",
    "代码": "💻",
    "写作": "✍️",
    "其他": "📦",
}

CATEGORY_COLORS = {
    "文档": "#1A2A40",
    "数据": "#162A1E",
    "安全": "#1A1F2A",
    "设计": "#251E10",
    "工作流": "#1C2020",
    "翻译": "#1E2230",
    "研究": "#1A2025",
    "代码": "#1A1A2A",
    "写作": "#1F2220",
    "其他": "#1E1E1E",
}


def parse_frontmatter(text: str) -> dict:
    """Extract YAML-like frontmatter between --- markers."""
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not match:
        return {}
    fm = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            fm[key.strip()] = value.strip().strip('"').strip("'")
    return fm


def read_skill_file(skill_path: Path) -> dict | None:
    """
    Read a .skill file (zip) and extract metadata from SKILL.md.
    Falls back to reading a plain SKILL.md if the .skill is not a zip.
    """
    name_stem = skill_path.stem  # filename without .skill

    # Try reading as zip first
    skill_md_text = None
    try:
        with zipfile.ZipFile(skill_path, "r") as zf:
            # Look for SKILL.md at any depth
            candidates = [n for n in zf.namelist() if n.endswith("SKILL.md")]
            if candidates:
                skill_md_text = zf.read(candidates[0]).decode("utf-8", errors="replace")
    except (zipfile.BadZipFile, KeyError):
        pass

    # If not a zip or no SKILL.md inside, treat file itself as text
    if skill_md_text is None:
        try:
            skill_md_text = skill_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return None

    fm = parse_frontmatter(skill_md_text)

    # Pull description from frontmatter or first non-header paragraph
    description = fm.get("description", "")
    if not description:
        # Grab first meaningful paragraph after frontmatter
        body = re.sub(r"^---.*?---\s*\n", "", skill_md_text, flags=re.DOTALL)
        paras = [p.strip() for p in body.split("\n\n") if p.strip() and not p.strip().startswith("#")]
        description = paras[0][:200] if paras else ""

    # Derive fields
    display_name = fm.get("name", name_stem.replace("-", " ").title())
    category = fm.get("category", "其他")
    author = fm.get("author", "社区")
    trigger = fm.get("trigger", f"/{name_stem}")
    icon = fm.get("icon", CATEGORY_ICONS.get(category, "📦"))
    icon_bg = fm.get("iconBg", CATEGORY_COLORS.get(category, "#1E1E1E"))

    # File size
    size_bytes = skill_path.stat().st_size
    if size_bytes < 1024:
        size_str = f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        size_str = f"{size_bytes / 1024:.1f} KB"
    else:
        size_str = f"{size_bytes / 1024 / 1024:.1f} MB"

    return {
        "id": name_stem,
        "name": display_name,
        "icon": icon,
        "iconBg": icon_bg,
        "category": category,
        "description": description,
        "author": author,
        "trigger": trigger,
        "file": f"skills/{skill_path.name}",
        "size": size_str,
        "updatedAt": datetime.fromtimestamp(
            skill_path.stat().st_mtime, tz=timezone.utc
        ).strftime("%Y-%m-%d"),
    }


def main():
    if not SKILLS_DIR.exists():
        print(f"[error] skills/ directory not found at {SKILLS_DIR}", file=sys.stderr)
        sys.exit(1)

    skill_files = sorted(SKILLS_DIR.glob("*.skill"))
    if not skill_files:
        print("[warn] No .skill files found in skills/")

    skills = []
    for sf in skill_files:
        data = read_skill_file(sf)
        if data:
            skills.append(data)
            print(f"  ✓  {sf.name}  ({data['category']}) — {data['name']}")
        else:
            print(f"  ✗  {sf.name}  (skipped, could not parse)")

    manifest = {
        "generatedAt": datetime.now(tz=timezone.utc).isoformat(),
        "count": len(skills),
        "skills": skills,
    }

    OUTPUT_FILE.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n→ skills.json written: {len(skills)} skills")


if __name__ == "__main__":
    main()
