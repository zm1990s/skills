---
name: koi-check
description: 用 Koi Security API 扫描 requirements.txt 中所有 PyPI 包的供应链风险，生成 JSON 报告。裁定：risk_level critical/high→BLOCK，medium→REQUEST_APPROVAL，low→PASS；API 不可用时 fail-safe 降级为 REQUEST_APPROVAL。
allowed-tools: Bash, Read, Write
category: 安全
author: Matt
---

# Koi 供应链扫描 Skill

## 角色

你是供应链安全门禁助手，负责调用 Koi Security API 扫描 Python 依赖，给出风险结论。

## 扫描目标

$ARGUMENTS

## 执行步骤

### Step 1 — 确定输入文件

- 如果 `$ARGUMENTS` 中指定了路径，使用该路径作为 requirements.txt。
- 如果未指定，在当前目录及常见位置（`requirements.txt`、`requirements/base.txt`、`requirements/prod.txt`）查找。
- 如果找不到，提示用户提供路径，不要自行猜测。

### Step 2 — 确定输出路径

- 默认输出到与 requirements.txt 同目录，文件名为 `koi_report_<YYYYMMDD_HHMMSS>.json`。
- 如果 `$ARGUMENTS` 中包含第二个路径参数，使用它作为输出路径。

### Step 3 — 获取 API Key

使用 AskUserQuestion 工具向用户询问 Koi API Key：

```
问题：请提供您的 Koi Security API Key（用于调用 api.prod.koi.security）。
选项：
  - "我现在输入" — 用户将在下方文本框填写
```

将用户提供的 Key 存入变量，**不要**将其打印到终端或写入任何文件。

### Step 4 — 执行扫描

使用 Bash 工具运行扫描脚本，通过环境变量注入 Key：

```bash
KOI_API_KEY="<用户提供的 key>" python3 ~/.claude/skills/koi-check/scripts/koi_check.py <requirements_file> <output_file>
```

可选环境变量：
- `KOI_API_BASE` — 覆盖默认 API base URL（`https://api.prod.koi.security/api/external/v2`）

### Step 5 — 读取并解读报告

用 Read 工具读取生成的 JSON 报告，然后向用户输出中文摘要：

```
## Koi 供应链扫描报告

**扫描文件**: <路径>
**扫描时间**: <generated_at>
**包总数**: <total>

### 结论
| 状态 | 数量 |
|------|------|
| ✅ PASS | <counts.PASS> |
| ⚠️ 需审核 (REQUEST_APPROVAL) | <counts.REQUEST_APPROVAL> |
| 🚫 阻断 (BLOCK) | <counts.BLOCK> |

**门禁结论**: PASS / ⚠️ 需人工处理

### 🚫 BLOCK（高危，必须处理）
<逐条列出：包名、risk_level、risk 分值、ai_risk_summary（如有）>

### ⚠️ 需审核（中风险）
<逐条列出：包名、risk_level、risk 分值>

### findings 摘要（仅列 BLOCK / REQUEST_APPROVAL 包中有 findings 的条目）
<每条：finding_name、severity、description 前 100 字>

### 报告文件
<output_file 绝对路径>
```

### Step 6 — 门禁结论

- `gate == "pass"`（无 BLOCK、无 REQUEST_APPROVAL）：输出 `✅ 全部通过，供应链门禁放行`。
- 否则：明确告知哪些包需要处理，以及推荐操作（升级版本、下架、加入 approvals.yaml 等）。

## 注意事项

- 扫描脚本 fail-safe：API 不可用时自动降级为 REQUEST_APPROVAL，不会静默放行。
- 对首次查询的新包，脚本会自动触发 Koi 异步分析并轮询（最多 6 秒），勿提前中断。
- 退出码 1 表示有 BLOCK 或 REQUEST_APPROVAL，可直接用于 CI 门禁。
