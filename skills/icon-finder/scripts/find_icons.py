#!/usr/bin/env python3
"""搜索图标/Logo，打印候选供选择。

用法：
    python scripts/find_icons.py "<关键词>" [--limit N]
                                 [--source auto|iconfont|iconify|dashboard|lobe|cncf]
                                 [--type auto|icon|logo]
"""

from __future__ import annotations

import argparse
import sys

from icon_sources import search_icons


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument(
        "--source",
        default="auto",
        choices=["auto", "iconfont", "iconify", "dashboard", "lobe", "cncf"],
    )
    parser.add_argument("--type", default="auto", choices=["auto", "icon", "logo"])
    args = parser.parse_args()

    try:
        data = search_icons(args.query, args.limit, args.source, args.type)
    except Exception as exc:  # noqa: BLE001
        print(f"搜索失败: {exc}", file=sys.stderr)
        return 1

    items = data.get("items", [])
    print(f"来源: {data.get('source_used')}  结果数: {len(items)}\n")
    for index, item in enumerate(items):
        extra = ""
        if item.get("source") == "cncf":
            bits = [item.get("category"), item.get("subcategory")]
            extra = "  " + " / ".join(str(bit) for bit in bits if bit)
        print(f"[{index}] {item['source']:9} id={item['id']:<52} name={item['name']}{extra}")

    for error in data.get("errors", []):
        print(f"警告: {error}", file=sys.stderr)

    if not items:
        print("（无结果，换个关键词试试，或用英文）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
