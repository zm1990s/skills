#!/usr/bin/env python3
"""保存选中图标：取 SVG → 存工作目录 → 转 PNG（供 pptx 插图）。

用法：
    python save_icon.py "<关键词>" --id <图标id> [--source auto|iconfont|iconify|cncf]
                         [--type auto|icon|logo]
                         [--output-dir icons] [--out-name <文件名，不含扩展名>] [--size 512]
                         [--color "#RRGGBB"]

- 用与搜索相同的关键词 + id 精确定位候选（find_icons.py 打印的 id）。
- 默认存 icons/<name>.svg 和 icons/<name>.png（512×512 透明底）。
- 单独获取图片时，用 --output-dir . 直接保存到当前目录。
- 打印生成的 PNG 相对路径，Agent 生成 pptx 时用它 add_picture。
"""

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

try:
    import cairosvg
except ImportError:
    cairosvg = None

API = "http://localhost:8000/icons/search"
CNCF_BASE = "https://landscape.cncf.io"


def _slug(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9_-]+", "-", name).strip("-")
    return s or "icon"


def _request(url: str) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json,text/html,image/svg+xml,*/*",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read()


def _load_cncf_items() -> list[dict]:
    """Load CNCF Landscape items. The site may serve the data inline in HTML."""
    urls = [
        f"{CNCF_BASE}/data/items-export.json",
        f"{CNCF_BASE}/",
    ]
    last_error: Exception | None = None
    for url in urls:
        try:
            text = _request(url).decode("utf-8", "ignore")
            if text.lstrip().startswith(("{", "[")):
                data = json.loads(text)
            else:
                marker = "window.baseDS"
                marker_pos = text.find(marker)
                if marker_pos < 0:
                    continue
                start = text.find("{", marker_pos)
                if start < 0:
                    continue
                data, _ = json.JSONDecoder().raw_decode(text[start:])
            if isinstance(data, dict) and isinstance(data.get("items"), list):
                return data["items"]
            if isinstance(data, list):
                return data
        except Exception as e:  # noqa: BLE001
            last_error = e
    if last_error:
        raise last_error
    raise RuntimeError("CNCF Landscape data not found")


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def _cncf_score(item: dict, query: str) -> int:
    q = _norm(query)
    name = _norm(str(item.get("name", "")))
    item_id = _norm(str(item.get("id", "")))
    haystack = " ".join(
        [
            name,
            item_id,
            _norm(str(item.get("category", ""))),
            _norm(str(item.get("subcategory", ""))),
        ]
    )
    if not q:
        return 0
    if q == name:
        return 1000
    if q in name:
        return 800 - abs(len(name) - len(q))
    q_terms = q.split()
    hits = sum(1 for term in q_terms if term in haystack)
    return hits * 100 - abs(len(name) - len(q))


def search_cncf(query: str, limit: int) -> dict:
    matches = []
    for item in _load_cncf_items():
        if not item.get("logo"):
            continue
        score = _cncf_score(item, query)
        if score <= 0:
            continue
        logo = str(item["logo"])
        matches.append(
            {
                "source": "cncf",
                "id": str(item.get("id") or logo),
                "name": str(item.get("name") or item.get("id") or "logo"),
                "category": item.get("category", ""),
                "subcategory": item.get("subcategory", ""),
                "logo": logo,
                "svg_url": urllib.parse.urljoin(f"{CNCF_BASE}/", logo),
                "_score": score,
            }
        )
    matches.sort(key=lambda it: (-it["_score"], it["name"].lower()))
    for item in matches:
        item.pop("_score", None)
    return {"source_used": "cncf", "items": matches[:limit]}


def search_local_api(query: str, limit: int, source: str) -> dict:
    qs = urllib.parse.urlencode({"q": query, "limit": limit, "source": source})
    with urllib.request.urlopen(f"{API}?{qs}", timeout=15) as r:
        return json.loads(r.read())


def _logo_intent(query: str, icon_type: str) -> bool:
    if icon_type == "logo":
        return True
    if icon_type == "icon":
        return False
    q = query.lower()
    return any(word in q for word in (" logo", "logo ", "公司", "品牌", "商标"))


def _svg_from_match(match: dict) -> str:
    if match.get("source") == "cncf":
        url = match.get("svg_url") or urllib.parse.urljoin(f"{CNCF_BASE}/", str(match["logo"]))
        return _request(str(url)).decode("utf-8", "ignore")
    return str(match["svg"])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("--id", required=True, help="find_icons.py 打印的图标 id")
    ap.add_argument("--source", default="auto", choices=["auto", "iconfont", "iconify", "cncf"])
    ap.add_argument("--type", default="auto", choices=["auto", "icon", "logo"])
    ap.add_argument("--output-dir", default="icons", help="输出目录；默认 icons，传 . 则保存到当前目录")
    ap.add_argument("--out-name", default=None)
    ap.add_argument("--size", type=int, default=512)
    ap.add_argument("--color", default=None, help="替换 currentColor 的填充色，如 #2563eb")
    ap.add_argument("--limit", type=int, default=50)
    args = ap.parse_args()

    try:
        if args.source == "cncf":
            data = search_cncf(args.query, args.limit)
        elif args.source == "auto" and _logo_intent(args.query, args.type):
            data = search_cncf(args.query, args.limit)
            if not data.get("items"):
                data = search_local_api(args.query, args.limit, "auto")
        else:
            data = search_local_api(args.query, args.limit, args.source)
    except Exception as e:  # noqa: BLE001
        print(f"搜索失败: {e}", file=sys.stderr)
        return 1

    match = next((it for it in data.get("items", []) if str(it["id"]) == str(args.id)), None)
    if match is None:
        print(f"未找到 id={args.id} 的图标（请先用 find_icons.py 确认 id）", file=sys.stderr)
        return 1

    svg = _svg_from_match(match)
    # SVG 常用 currentColor 表示随文字色；转 PNG 前替换成指定色，否则默认黑
    fill = args.color or "#000000"
    svg = svg.replace("currentColor", fill)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(exist_ok=True)
    base = _slug(args.out_name or match["name"])
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
