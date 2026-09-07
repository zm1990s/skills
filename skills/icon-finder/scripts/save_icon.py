#!/usr/bin/env python3
"""保存选中图标：取 SVG -> 存工作目录 -> 转 PNG（供 pptx 插图）。

用法：
    python scripts/save_icon.py "<关键词>" --id <图标id>
                                [--source auto|iconfont|iconify|dashboard|lobe|cncf]
                                [--type auto|icon|logo]
                                [--output-dir icons] [--out-name <文件名>] [--size 512]
                                [--color "#RRGGBB"]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    import cairosvg
except ImportError:
    cairosvg = None

from icon_sources import search_icons, source_from_id, svg_from_match


def slug(name: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9_-]+", "-", name).strip("-")
    return clean or "icon"


def strip_source_prefix(icon_id: str) -> str:
    if icon_id.startswith(("dashboard:", "lobe:", "cncf:")):
        return icon_id.split(":", 1)[1]
    return icon_id


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--id", required=True, help="find_icons.py 打印的图标 id")
    parser.add_argument(
        "--source",
        default="auto",
        choices=["auto", "iconfont", "iconify", "dashboard", "lobe", "cncf"],
    )
    parser.add_argument("--type", default="auto", choices=["auto", "icon", "logo"])
    parser.add_argument("--output-dir", default="icons", help="输出目录；默认 icons，传 . 则保存到当前目录")
    parser.add_argument("--out-name", default=None)
    parser.add_argument("--size", type=int, default=512)
    parser.add_argument("--color", default=None, help="替换 currentColor 的填充色，如 #2563eb")
    parser.add_argument("--limit", type=int, default=80)
    args = parser.parse_args()

    source = args.source
    inferred_source = source_from_id(args.id)
    if source == "auto" and inferred_source:
        source = inferred_source

    try:
        data = search_icons(args.query, args.limit, source, args.type)
    except Exception as exc:  # noqa: BLE001
        print(f"搜索失败: {exc}", file=sys.stderr)
        return 1

    wanted_ids = {args.id, strip_source_prefix(args.id)}
    match = next(
        (
            item
            for item in data.get("items", [])
            if str(item["id"]) in wanted_ids or strip_source_prefix(str(item["id"])) in wanted_ids
        ),
        None,
    )
    if match is None:
        print(f"未找到 id={args.id} 的图标（请先用 find_icons.py 确认 id）", file=sys.stderr)
        return 1

    try:
        svg = svg_from_match(match)
    except Exception as exc:  # noqa: BLE001
        print(f"获取 SVG 失败: {exc}", file=sys.stderr)
        return 1

    fill = args.color or "#000000"
    svg = svg.replace("currentColor", fill)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    base = slug(args.out_name or str(match["name"]))
    svg_path = out_dir / f"{base}.svg"
    png_path = out_dir / f"{base}.png"

    svg_path.write_text(svg, encoding="utf-8")
    if cairosvg is None:
        print(
            "已保存 SVG，但未生成 PNG：当前 Python 环境缺少 cairosvg。"
            "请安装 CairoSVG 后重试，或直接使用 SVG。",
            file=sys.stderr,
        )
        print(f"  SVG: {svg_path}")
        return 2

    cairosvg.svg2png(
        bytestring=svg.encode("utf-8"),
        write_to=str(png_path),
        output_width=args.size,
        output_height=args.size,
    )

    print(f"已保存:\n  SVG: {svg_path}\n  PNG: {png_path}  ({args.size}x{args.size})")
    print(f"\n在 pptx 中插入: slide.shapes.add_picture('{png_path}', left, top, ...)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
