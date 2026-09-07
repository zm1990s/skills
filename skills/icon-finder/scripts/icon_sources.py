#!/usr/bin/env python3
"""Public icon source helpers for icon-finder.

All sources are queried directly from public endpoints. No private service is
required.
"""

from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request

ICONFONT_API = "https://www.iconfont.cn/api/icon/search.json"
ICONIFY_API = "https://api.iconify.design"
CNCF_BASE = "https://landscape.cncf.io"
DASHBOARD_REPO = "walkxcode/dashboard-icons"
LOBE_REPO = "lobehub/lobe-icons"


class SourceError(RuntimeError):
    """Raised when a source cannot be queried or parsed."""


def request_bytes(url: str, data: bytes | None = None, accept: str = "*/*") -> bytes:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
        ),
        "Accept": accept,
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    if data is not None:
        headers.update(
            {
                "Content-Type": "application/x-www-form-urlencoded",
                "Referer": "https://www.iconfont.cn/",
                "Origin": "https://www.iconfont.cn",
            }
        )
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=25) as response:
        return response.read()


def request_json(url: str, data: bytes | None = None) -> object:
    raw = request_bytes(url, data=data, accept="application/json,*/*")
    return json.loads(raw.decode("utf-8", "ignore"))


def norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def score_name(name: str, query: str, extra: str = "") -> int:
    q = norm(query)
    n = norm(name)
    haystack = " ".join(part for part in [n, norm(extra)] if part)
    if not q:
        return 0
    if q == n:
        return 1000
    if q in n:
        return 800 - abs(len(n) - len(q))
    terms = q.split()
    hits = sum(1 for term in terms if term in haystack)
    return hits * 100 - abs(len(n) - len(q))


def source_from_id(icon_id: str) -> str | None:
    if icon_id.startswith("dashboard:"):
        return "dashboard"
    if icon_id.startswith("lobe:"):
        return "lobe"
    if icon_id.startswith("cncf:"):
        return "cncf"
    if ":" in icon_id:
        return "iconify"
    return None


def logo_intent(query: str, icon_type: str) -> bool:
    if icon_type == "logo":
        return True
    if icon_type == "icon":
        return False
    q = query.lower()
    return any(word in q for word in (" logo", "logo ", "公司", "品牌", "商标"))


def search_iconfont(query: str, limit: int) -> dict:
    form = {
        "q": query,
        "sortType": "recommend",
        "page": "1",
        "pageSize": str(min(max(limit, 1), 100)),
        "sType": "",
        "fromCollection": "-1",
        "fills": "",
        "t": str(int(time.time() * 1000)),
        "ctoken": "null",
    }
    data = request_json(ICONFONT_API, data=urllib.parse.urlencode(form).encode())
    if not isinstance(data, dict) or data.get("code") != 200:
        raise SourceError(f"iconfont returned unexpected response: {data!r}")

    icons = data.get("data", {}).get("icons", [])
    items = []
    for icon in icons[:limit]:
        svg = icon.get("show_svg")
        if not svg:
            continue
        name = str(icon.get("name") or icon.get("font_class") or icon.get("slug") or icon.get("id"))
        items.append(
            {
                "source": "iconfont",
                "id": str(icon.get("id")),
                "name": name,
                "svg": svg,
                "preview": icon.get("preview_image", ""),
            }
        )
    return {"source_used": "iconfont", "items": items}


def search_iconify(query: str, limit: int) -> dict:
    qs = urllib.parse.urlencode({"query": query, "limit": max(limit, 1)})
    data = request_json(f"{ICONIFY_API}/search?{qs}")
    if not isinstance(data, dict):
        raise SourceError("iconify returned unexpected response")
    icons = data.get("icons", [])
    items = [
        {
            "source": "iconify",
            "id": str(icon_id),
            "name": str(icon_id).split(":", 1)[-1],
            "svg_url": f"{ICONIFY_API}/{urllib.parse.quote(str(icon_id), safe=':')}.svg",
        }
        for icon_id in icons[:limit]
    ]
    return {"source_used": "iconify", "items": items}


def load_cncf_items() -> list[dict]:
    urls = [
        f"{CNCF_BASE}/data/items-export.json",
        f"{CNCF_BASE}/",
    ]
    last_error: Exception | None = None
    for url in urls:
        try:
            text = request_bytes(url, accept="application/json,text/html,*/*").decode("utf-8", "ignore")
            if text.lstrip().startswith(("{", "[")):
                data = json.loads(text)
            else:
                marker_pos = text.find("window.baseDS")
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
        except Exception as exc:  # noqa: BLE001
            last_error = exc
    if last_error:
        raise SourceError(f"CNCF data unavailable: {last_error}") from last_error
    raise SourceError("CNCF data not found")


def search_cncf(query: str, limit: int) -> dict:
    matches = []
    for item in load_cncf_items():
        logo = item.get("logo")
        if not logo:
            continue
        name = str(item.get("name") or item.get("id") or "logo")
        score = score_name(
            name,
            query,
            " ".join(
                str(item.get(key, ""))
                for key in ("id", "category", "subcategory")
            ),
        )
        if score <= 0:
            continue
        item_id = str(item.get("id") or name)
        matches.append(
            {
                "source": "cncf",
                "id": f"cncf:{item_id}",
                "name": name,
                "category": item.get("category", ""),
                "subcategory": item.get("subcategory", ""),
                "svg_url": urllib.parse.urljoin(f"{CNCF_BASE}/", str(logo)),
                "_score": score,
            }
        )
    matches.sort(key=lambda item: (-item["_score"], item["name"].lower()))
    for item in matches:
        item.pop("_score", None)
    return {"source_used": "cncf", "items": matches[:limit]}


def github_tree(repo: str, branch: str = "main") -> list[dict]:
    url = f"https://api.github.com/repos/{repo}/git/trees/{branch}?recursive=1"
    data = request_json(url)
    if not isinstance(data, dict) or not isinstance(data.get("tree"), list):
        raise SourceError(f"GitHub tree unavailable for {repo}")
    return data["tree"]


def search_dashboard(query: str, limit: int) -> dict:
    matches = []
    for entry in github_tree(DASHBOARD_REPO):
        path = str(entry.get("path", ""))
        if not path.startswith("svg/") or not path.endswith(".svg"):
            continue
        slug = path.rsplit("/", 1)[-1][:-4]
        score = score_name(slug, query)
        if score <= 0:
            continue
        matches.append(
            {
                "source": "dashboard",
                "id": f"dashboard:{slug}",
                "name": slug,
                "svg_url": f"https://raw.githubusercontent.com/{DASHBOARD_REPO}/main/{path}",
                "_score": score,
            }
        )
    matches.sort(key=lambda item: (-item["_score"], item["name"]))
    for item in matches:
        item.pop("_score", None)
    return {"source_used": "dashboard", "items": matches[:limit]}


def search_lobe(query: str, limit: int) -> dict:
    matches = []
    for entry in github_tree(LOBE_REPO, branch="master"):
        path = str(entry.get("path", ""))
        if not path.startswith("packages/static-svg/icons/") or not path.endswith(".svg"):
            continue
        slug = path.rsplit("/", 1)[-1][:-4]
        score = score_name(slug, query)
        if score <= 0:
            continue
        matches.append(
            {
                "source": "lobe",
                "id": f"lobe:{slug}",
                "name": slug,
                "svg_url": f"https://raw.githubusercontent.com/{LOBE_REPO}/master/{path}",
                "_score": score,
            }
        )
    matches.sort(key=lambda item: (-item["_score"], item["name"]))
    for item in matches:
        item.pop("_score", None)
    return {"source_used": "lobe", "items": matches[:limit]}


def search_one_source(source: str, query: str, limit: int) -> dict:
    if source == "iconfont":
        return search_iconfont(query, limit)
    if source == "iconify":
        return search_iconify(query, limit)
    if source == "cncf":
        return search_cncf(query, limit)
    if source == "dashboard":
        return search_dashboard(query, limit)
    if source == "lobe":
        return search_lobe(query, limit)
    raise ValueError(f"unknown source: {source}")


def search_icons(query: str, limit: int, source: str = "auto", icon_type: str = "auto") -> dict:
    if source != "auto":
        return search_one_source(source, query, limit)

    ordered_sources = (
        ["cncf", "dashboard", "lobe", "iconfont", "iconify"]
        if logo_intent(query, icon_type)
        else ["iconfont", "iconify"]
    )
    items = []
    used = []
    errors = []
    per_source_limit = max(limit, 10)

    for current_source in ordered_sources:
        try:
            data = search_one_source(current_source, query, per_source_limit)
            source_items = data.get("items", [])
            used.append(f"{current_source}({len(source_items)})")
            items.extend(source_items)
            if len(items) >= limit and not logo_intent(query, icon_type):
                break
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{current_source}: {exc}")

    result = {"source_used": "auto: " + " -> ".join(used), "items": items[:limit]}
    if errors:
        result["errors"] = errors
    return result


def svg_from_match(match: dict) -> str:
    if match.get("svg"):
        return str(match["svg"])
    svg_url = match.get("svg_url")
    if not svg_url:
        raise SourceError(f"no SVG URL for {match.get('source')}:{match.get('id')}")
    return request_bytes(str(svg_url), accept="image/svg+xml,text/plain,*/*").decode("utf-8", "ignore")
