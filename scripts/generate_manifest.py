#!/usr/bin/env python3
"""
Scans the skills/ directory and generates skills.json for the Skill Hub frontend.

Supports two skill formats (both can coexist):
  1. Directory — skills/<name>/SKILL.md
     → zipped into dist/<name>.skill for download
  2. Zip file  — skills/<name>.skill  (or .zip)
     → copied as-is into dist/<name>.skill; SKILL.md is read in-memory, never extracted

Usage:
    python scripts/generate_manifest.py
"""

import json
import re
import shutil
import sys
import zipfile
from pathlib import Path
from datetime import datetime, timezone

SKILLS_DIR  = Path(__file__).parent.parent / "skills"
DIST_DIR    = Path(__file__).parent.parent / "dist"
OUTPUT_FILE = Path(__file__).parent.parent / "skills.json"

CATEGORY_ICONS = {
    "文档": "📄", "数据": "📈", "安全": "🛡️", "设计": "🎨",
    "工作流": "⚙️", "翻译": "🌐", "研究": "🔬", "代码": "💻",
    "写作": "✍️", "其他": "📦",
}
CATEGORY_COLORS = {
    "文档": "#141415", "数据": "#162A1E", "安全": "#1A1F2A", "设计": "#251E10",
    "工作流": "#1C2020", "翻译": "#1E2230", "研究": "#1A2025", "代码": "#1A1A2A",
    "写作": "#1F2220", "其他": "#1E1E1E",
}


# ── Helpers ────────────────────────────────────────────────────────────────

def parse_frontmatter(text: str) -> dict:
    """Return key/value pairs from the first --- block."""
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip().strip('"').strip("'")
    return fm


def extract_metadata(skill_md_text: str) -> tuple[dict, str]:
    """Return (frontmatter dict, description string) from SKILL.md text."""
    fm = parse_frontmatter(skill_md_text)
    desc = fm.get("description", "")
    if not desc:
        body = re.sub(r"^---.*?---\s*\n", "", skill_md_text, flags=re.DOTALL)
        paras = [p.strip() for p in body.split("\n\n")
                 if p.strip() and not p.strip().startswith("#")]
        desc = paras[0][:200] if paras else ""
    return fm, desc


def build_entry(name_stem: str, fm: dict, description: str,
                dist_file: Path, mtime: float) -> dict:
    cat = fm.get("category", "其他")
    size = dist_file.stat().st_size if dist_file.exists() else 0
    return {
        "id":          name_stem,
        "name":        fm.get("name", name_stem.replace("-", " ").title()),
        "icon":        fm.get("icon",   CATEGORY_ICONS.get(cat,  "📦")),
        "iconBg":      fm.get("iconBg", CATEGORY_COLORS.get(cat, "#1E1E1E")),
        "category":    cat,
        "description": description,
        "author":      fm.get("author",  "社区"),
        "trigger":     fm.get("trigger", f"/{name_stem}"),
        "file":        f"dist/{name_stem}.zip",
        "sourcePath":  f"skills/{name_stem}",
        "size":        _fmt(size),
        "updatedAt":   datetime.fromtimestamp(mtime, tz=timezone.utc).strftime("%Y-%m-%d"),
    }


def _fmt(n: int) -> str:
    if n < 1024:     return f"{n} B"
    if n < 1024**2:  return f"{n/1024:.1f} KB"
    return f"{n/1024**2:.1f} MB"


def zip_dir(src: Path, dest: Path) -> None:
    """Pack src/ directory into dest .zip, paths relative to src's parent."""
    dest = dest.with_suffix(".zip")
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(src.rglob("*")):
            if f.is_file():
                zf.write(f, f.relative_to(src.parent))


def read_skill_md_from_zip(zip_path: Path) -> str | None:
    """Read SKILL.md text from inside a zip — never extracts to disk."""
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            candidates = [n for n in zf.namelist() if n.endswith("SKILL.md")]
            if candidates:
                return zf.read(candidates[0]).decode("utf-8", errors="replace")
    except zipfile.BadZipFile:
        pass
    return None


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    if not SKILLS_DIR.exists():
        print(f"[error] skills/ not found at {SKILLS_DIR}", file=sys.stderr)
        sys.exit(1)

    DIST_DIR.mkdir(exist_ok=True)

    skills = []
    seen: set[str] = set()

    # ── 1. Directory-based: skills/<name>/SKILL.md ──────────────────────
    for skill_dir in sorted(d for d in SKILLS_DIR.iterdir() if d.is_dir()):
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            print(f"  –  {skill_dir.name}/  (no SKILL.md, skipped)")
            continue

        try:
            text = skill_md.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            print(f"  ✗  {skill_dir.name}/  (read error: {e})")
            continue

        fm, description = extract_metadata(text)
        dest = DIST_DIR / f"{skill_dir.name}.zip"
        zip_dir(skill_dir, dest)

        mtime = max(f.stat().st_mtime for f in skill_dir.rglob("*") if f.is_file())
        entry = build_entry(skill_dir.name, fm, description, dest, mtime)
        skills.append(entry)
        seen.add(skill_dir.name)
        print(f"  ✓  {skill_dir.name}/  ({entry['category']}) — {entry['name']}  [{entry['size']}]")

    # ── 2. Zip-based: skills/<name>.skill or skills/<name>.zip ──────────
    #    SKILL.md is read in-memory from the zip; the file is never extracted.
    for ext in ("*.skill", "*.zip"):
        for skill_file in sorted(SKILLS_DIR.glob(ext)):
            name_stem = skill_file.stem
            if name_stem in seen:
                continue  # directory version takes precedence

            text = read_skill_md_from_zip(skill_file)
            if text is None:
                print(f"  ✗  {skill_file.name}  (no SKILL.md inside, skipped)")
                continue

            fm, description = extract_metadata(text)
            dest = DIST_DIR / f"{name_stem}.zip"
            shutil.copy2(skill_file, dest)   # copy as-is, no extraction

            entry = build_entry(name_stem, fm, description, dest, skill_file.stat().st_mtime)
            skills.append(entry)
            seen.add(name_stem)
            print(f"  ✓  {skill_file.name}  ({entry['category']}) — {entry['name']}  [{entry['size']}]")

    manifest = {
        "generatedAt": datetime.now(tz=timezone.utc).isoformat(),
        "count":       len(skills),
        "skills":      skills,
    }
    OUTPUT_FILE.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n→ skills.json: {len(skills)} skills  |  dist/: {len(list(DIST_DIR.glob('*.zip')))} files")


if __name__ == "__main__":
    main()
