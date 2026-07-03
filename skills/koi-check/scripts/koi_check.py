#!/usr/bin/env python3
"""检查 requirements.txt 中所有包的供应链安全状态（基于 Koi API）。

API 端点 (api.prod.koi.security/api/external/v2):
  GET  /koidex/risk-report?item_id=&marketplace=&version=
       → {risk, risk_level, findings:{findings:[...]}, risk_status, ...}
  POST /koidex/fetch  {items:[{item_id, marketplace, version, include_ai_insights}]}
       → 触发异步分析（新制品首次查询前调用）

裁定逻辑（与 koi_client.py 一致）:
  risk_level critical/high → BLOCK
  risk_level medium        → REQUEST_APPROVAL
  risk_level low           → PASS
  无 risk_level 按 risk 数值: >=7 BLOCK, >=4 REQUEST_APPROVAL, else PASS

用法:
  python koi_check.py [requirements.txt] [output.json]

退出码: 有 BLOCK 或 REQUEST_APPROVAL → 1，全部 PASS → 0。
stdlib only，py3.6+ 兼容。
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime

KOI_API_BASE = os.environ.get(
    "KOI_API_BASE", "https://api.prod.koi.security/api/external/v2"
).rstrip("/")

KOI_API_KEY = os.environ.get("KOI_API_KEY", "")
POLL_INTERVAL = 2   # 每次轮询间隔（秒）
POLL_RETRIES  = 3   # 触发 fetch 后最多轮询次数
HTTP_TIMEOUT  = 20


# ---------- 端点 ----------

def _auth_headers():
    key = os.environ.get("KOI_API_KEY", KOI_API_KEY)
    if not key:
        sys.exit("错误: 未提供 KOI_API_KEY，请通过环境变量传入。")
    return {"Authorization": "Bearer " + key}


def _get(url):
    req = urllib.request.Request(url, headers=_auth_headers())
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))


def _post(url, payload):
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=body,
        headers={**_auth_headers(), "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))


def _risk_report(marketplace, item_id, version=None):
    """GET /koidex/risk-report — 返回 (status_code, data|None)。"""
    params = {"item_id": item_id, "marketplace": marketplace}
    if version:
        params["version"] = version
    url = KOI_API_BASE + "/koidex/risk-report?" + urllib.parse.urlencode(params)
    try:
        code, data = _get(url)
        return code, data
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return 404, None
        raise


def _trigger_fetch(marketplace, item_id, version=None):
    """POST /koidex/fetch — 触发异步分析，忽略响应体。"""
    item = {"item_id": item_id, "marketplace": marketplace, "include_ai_insights": True}
    if version:
        item["version"] = version
    try:
        _post(KOI_API_BASE + "/koidex/fetch", {"items": [item]})
    except Exception:
        pass  # fetch 失败不阻断主流程，后续 GET 会兜底


# ---------- 裁定逻辑（同 koi_client.py _state_from） ----------

def _state_from(risk_level, risk):
    lvl = (risk_level or "").lower()
    if lvl in ("critical", "high"):
        return "BLOCK"
    if lvl == "medium":
        return "REQUEST_APPROVAL"
    if lvl == "low":
        return "PASS"
    if risk is None:
        return "PASS"
    if risk >= 7:
        return "BLOCK"
    if risk >= 4:
        return "REQUEST_APPROVAL"
    return "PASS"


# ---------- 单包检查（含轮询） ----------

def check_package(marketplace, item_id, version=None):
    """
    查询单个包的风险，参考 koi_client.py risk_report() 逻辑:
      1. GET risk-report
      2. 若 404 / 无 risk_level / status!=completed → 触发 fetch + 轮询
      3. 后端不可用 → fail-safe 返回 REQUEST_APPROVAL
    """
    try:
        code, data = _risk_report(marketplace, item_id, version)

        need_fetch = (
            code == 404
            or data is None
            or data.get("risk_level") is None
            or data.get("risk_status") not in (None, "completed")
        )

        if need_fetch:
            _trigger_fetch(marketplace, item_id, version)
            for _ in range(POLL_RETRIES):
                time.sleep(POLL_INTERVAL)
                code, data = _risk_report(marketplace, item_id, version)
                if data and data.get("risk_level") is not None:
                    break

        if not data:
            data = {}

        risk       = data.get("risk")
        risk_level = data.get("risk_level")
        raw_findings = (data.get("findings") or {}).get("findings") or []
        findings = [
            {
                "finding_name": f.get("finding_name") or f.get("finding_id") or "finding",
                "severity":     f.get("severity") or "info",
                "description":  (f.get("description") or "")[:800],
                "evidence":     (f.get("evidence") or "")[:400],
            }
            for f in raw_findings[:20]
        ]

        return {
            "state":            _state_from(risk_level, risk),
            "risk":             risk,
            "risk_level":       risk_level,
            "risk_status":      data.get("risk_status"),
            "ai_risk_summary":  data.get("ai_risk_summary"),
            "item_display_name": data.get("item_display_name") or data.get("package_name"),
            "version_resolved": data.get("version"),
            "findings_count":   len(findings),
            "findings":         findings,
            "source":           "koi",
            "note": None if data.get("risk_status") == "completed"
                    else "Koi 仍在分析，结果可能未就绪",
        }

    except (urllib.error.URLError, OSError, ValueError) as e:
        sys.stderr.write("  ! {0}/{1}: 连接失败 ({2}) — 按 REQUEST_APPROVAL 处理\n".format(
            marketplace, item_id, e))
        return {
            "state": "REQUEST_APPROVAL", "risk": None, "risk_level": None,
            "risk_status": None, "ai_risk_summary": None,
            "item_display_name": None, "version_resolved": None,
            "findings_count": 0, "findings": [], "source": "offline",
            "note": "API 不可用: " + str(e),
        }


# ---------- 解析 requirements.txt ----------

def parse_requirements(path):
    if not os.path.exists(path):
        sys.exit("错误: 找不到文件 " + path)
    packages = []
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            line = line.split("#")[0].strip()
            if not line:
                continue
            if re.match(r"^(https?://|git\+)", line, re.I):
                continue
            m = re.match(r"^([A-Za-z0-9]([A-Za-z0-9._-]*[A-Za-z0-9])?)", line)
            if not m:
                continue
            name = m.group(1)
            spec = line[len(name):].strip().split(";")[0].strip()
            # 尝试提取精确版本号（==x.y.z）
            vm = re.match(r"^==([^\s,;]+)", spec)
            version = vm.group(1) if vm else None
            packages.append((name, spec, version))
    return packages


# ---------- 主流程 ----------

def main():
    req_file = sys.argv[1] if len(sys.argv) > 1 else "requirements.txt"
    out_file = sys.argv[2] if len(sys.argv) > 2 else "koi_report.json"

    packages = parse_requirements(req_file)

    # 去重保序（包名不区分大小写）
    seen, uniq = set(), []
    for name, spec, version in packages:
        if name.lower() not in seen:
            seen.add(name.lower())
            uniq.append((name, spec, version))

    print("Koi 供应链扫描: {0} 个包 ({1})".format(len(uniq), req_file))
    print("API: {0}\n".format(KOI_API_BASE))

    items  = []
    counts = {"PASS": 0, "REQUEST_APPROVAL": 0, "BLOCK": 0}

    for idx, (name, spec, version) in enumerate(uniq):
        if idx > 0:
            time.sleep(5)
        sys.stdout.write("  检查 {0}{1} … ".format(name, spec or ""))
        sys.stdout.flush()

        r = check_package("pypi", name, version)
        state = r["state"]
        counts[state] = counts.get(state, 0) + 1

        label = {"PASS": "PASS", "BLOCK": "BLOCK", "REQUEST_APPROVAL": "REVIEW"}.get(state, state)
        note  = "  [{0}]".format(r["note"]) if r.get("note") else ""
        print("{0}  risk={1} ({2}){3}".format(
            label, r.get("risk"), r.get("risk_level"), note))

        items.append({
            "name":             name,
            "version_spec":     spec,
            "version_resolved": r["version_resolved"],
            "marketplace":      "pypi",
            "state":            state,
            "risk":             r.get("risk"),
            "risk_level":       r.get("risk_level"),
            "risk_status":      r.get("risk_status"),
            "ai_risk_summary":  r.get("ai_risk_summary"),
            "item_display_name": r.get("item_display_name"),
            "findings_count":   r["findings_count"],
            "findings":         r["findings"],
            "source":           r["source"],
            **({"note": r["note"]} if r.get("note") else {}),
        })

    blocked     = [r["name"] for r in items if r["state"] == "BLOCK"]
    need_review = [r["name"] for r in items if r["state"] == "REQUEST_APPROVAL"]

    report = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "source_file":  os.path.abspath(req_file),
        "api_base":     KOI_API_BASE,
        "total":        len(uniq),
        "counts":       counts,
        "blocked":      blocked,
        "needs_review": need_review,
        "passed":       [r["name"] for r in items if r["state"] == "PASS"],
        "items":        items,
    }

    with open(out_file, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)

    print("\n报告已写入: {0}".format(os.path.abspath(out_file)))
    print("\n结论: PASS={0}  REVIEW={1}  BLOCK={2}".format(
        counts["PASS"], counts["REQUEST_APPROVAL"], counts["BLOCK"]))
    if blocked:
        print("  BLOCK (高危): " + ", ".join(blocked))
    if need_review:
        print("  需人工审核:   " + ", ".join(need_review))

    sys.exit(1 if (blocked or need_review) else 0)


if __name__ == "__main__":
    main()
