#!/usr/bin/env python3
"""搜索图标（iconfont 优先，自动降级 Iconify），打印候选供选择。

用法：
    python find_icons.py "<关键词>" [--limit N] [--source auto|iconfont|iconify|cncf]
                         [--type auto|icon|logo]

输出每个候选的 index / source / id / name（不打印完整 SVG，避免刷屏）。
选中后用 save_icon.py 保存并转 PNG。
"""

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request

# 本平台内网代理接口（容器内直连后端，无需鉴权）
API = "http://localhost:8000/icons/search"
CNCF_BASE = "https://landscape.cncf.io"


def _request(url: str) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json,text/html,*/*",
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--source", default="auto", choices=["auto", "iconfont", "iconify", "cncf"])
    ap.add_argument("--type", default="auto", choices=["auto", "icon", "logo"])
    args = ap.parse_args()

    try:
        if args.source == "cncf":
            data = search_cncf(args.query, args.limit)
        elif args.source == "auto" and _logo_intent(args.query, args.type):
            data = search_cncf(args.query, args.limit)
            if not data.get("items"):
                data = search_local_api(args.query, args.limit, "auto")
                data["source_used"] = f"cncf(no results) -> {data.get('source_used')}"
        else:
            data = search_local_api(args.query, args.limit, args.source)
    except Exception as e:  # noqa: BLE001
        print(f"搜索失败: {e}", file=sys.stderr)
        return 1

    items = data.get("items", [])
    print(f"来源: {data.get('source_used')}  结果数: {len(items)}\n")
    for i, it in enumerate(items):
        extra = ""
        if it.get("source") == "cncf":
            bits = [it.get("category"), it.get("subcategory")]
            extra = "  " + " / ".join(str(b) for b in bits if b)
        print(f"[{i}] {it['source']:8} id={it['id']:<48} name={it['name']}{extra}")
    if not items:
        print("（无结果，换个关键词试试，或用英文）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
