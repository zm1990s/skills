---
name: "project-init"
description: "新建项目时，通过问答收集关键信息，输出工程契约文件（CLAUDE.md/DESIGN.md/WORKFLOW.md）和每一步的系统提示词，遵循\"先计划后执行、先契约后代码\"的最佳实践。"
---

# Project Init Skill

当用户说"新建一个项目"、"帮我初始化项目"、"项目从零开始"或类似需求时，执行此 Skill。

---

## 第一步：问答收集（AskUserQuestion）

在做任何事之前，先用 `AskUserQuestion` 工具连续问以下关键信息（最多分 2 轮，每轮 ≤4 个问题）。

### 第一轮提问（必问）

```
问题1: header="项目类型"
  - Web 全栈应用（前后端分离）
  - 纯后端服务 / API
  - CLI 工具 / 脚本
  - 数据分析 / AI Pipeline
  - 其他（用户填写）

问题2: header="核心技术栈"
  - Python + FastAPI（推荐，适合 AI/数据密集型）
  - Node.js / Next.js 全栈
  - Go + Gin/Echo
  - 用户自定义

问题3: header="前端需求"（若问题1选了"纯后端"则跳过）
  - Next.js 14 + Tailwind（推荐）
  - React + Vite
  - Vue 3 + Vite
  - 无前端

问题4: header="数据存储"
  - PostgreSQL（推荐，通用首选）
  - PostgreSQL + pgvector（有向量/RAG 需求）
  - MySQL / MariaDB
  - SQLite（轻量/本地）
  - 无数据库
```

### 第二轮提问（按需，若上轮信息不足）

```
问题1: header="部署方式"
  - Docker Compose（推荐，开发友好）
  - 纯本地运行
  - Kubernetes
  - 云函数/Serverless

问题2: header="LLM 集成"
  - 有（需要 AI 能力）→ 追问：走统一网关还是直连 SDK
  - 无

问题3: header="认证需求"
  - 无认证（内部工具/demo）
  - 简单密码门（单密码环境变量）
  - JWT / Session（多用户）

问题4: header="CI/CD"
  - GitHub Actions（推荐）
  - GitLab CI
  - Jenkins
  - 暂不需要
```

---

## 第二步：最佳实践设计（在回复中输出，不写文件）

收到问答结果后，**先在对话中输出一段"设计决策摘要"**，包含：

1. **技术栈确认** — 列出选定的每层技术及版本
2. **目录约定** — 后端分几层、前端结构约定
3. **API 契约草案** — 列出核心端点（≤10 个，附 HTTP 方法和简述）
4. **数据模型草案** — 列出核心表/集合（附关键字段）
5. **关键约束** — 禁止项（如禁直连 LLM SDK、禁改 .env、禁删表）
6. **分步计划** — 告知将分几步生成文件，每步产出什么

**等用户确认后，再进入第三步。**

---

## 第三步：逐步输出文件和系统提示词

每次只生成一步的内容，附验收命令，等用户执行并确认后再继续。

---

### Step 0 · 工程契约（先于一切代码）

**目标**：生成"项目记忆三件套"，约束后续所有改动。

**生成以下文件**（根据问答结果填充，不含任何业务代码）：

#### CLAUDE.md 模板
```markdown
# 项目记忆

## 身份
你是 [项目名] 的架构助手。

## 技术栈（禁止中途更换）
- Backend: [语言+框架+版本]
- Frontend: [框架+版本] / 无
- 数据库: [数据库+版本]
- LLM 接入: [网关方案 / 无]
- 部署: [方案]

## 目录约定
[根据项目类型生成，如：]
backend/
  app/
    api/        # 路由层
    services/   # 业务逻辑
    models/     # 数据模型
    schemas/    # 请求/响应 schema
    core/       # 配置、数据库连接等

## 禁止事项
- 禁止修改 .env（只改 .env.example）
- 禁止直连外部 LLM SDK/API（如有 LLM，只走统一网关）
- 禁止修改已建好的数据库表结构（只做 additive 增量）
- 禁止把 API key 硬编码进任何代码文件

## 必须执行
- 改动前：先给计划，等用户确认再改文件
- 改动后：自己跑 lint + 测试验收
- 新增依赖：先询问是否必须，列出替代方案
```

#### DESIGN.md 模板
```markdown
# 架构设计

## 架构图（文字版）
[组件 A] → [组件 B] → [数据库]

## API 契约（此表一旦确定，后续步骤不得私自修改端点路径）
| 方法 | 路径 | 说明 | 返回 |
|------|------|------|------|
| POST | /[资源] | 创建 | {id, ...} |
| GET  | /[资源]/{id} | 查询单条 | {...} |
| GET  | /[资源] | 查询列表 | [...] |

## 数据模型（此表一旦确定，后续只做 additive 修改）
### [表名]
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PK | 主键 |
| created_at | TIMESTAMPTZ | 创建时间 |

## 关键约束
- [技术选型约束]
- [安全约束]
```

#### WORKFLOW.md 模板
```markdown
# 开发阶段协议

## /refine（需求澄清）
输入：需求描述
输出：PRD.md（目标用户、功能边界、验收标准）
通过条件：每条验收标准可观察、可量化

## /design（架构设计）
输入：PRD.md
输出：更新 DESIGN.md（API 契约、数据模型）
通过条件：所有端点有明确入参/出参

## /plan（实现计划）
输入：DESIGN.md
输出：分步实现计划（每步 ≤200 行改动）
通过条件：计划经用户确认

## /build（编写代码）
输入：计划
输出：代码文件 + 测试
通过条件：lint 通过 + 测试绿

## /review（代码审查）
输入：diff
输出：两阶段报告（Spec Compliance → Code Quality）
通过条件：无 Critical 问题

## /ship（发布）
输入：通过 review 的代码
输出：部署配置 + 上线检查
通过条件：健康检查通过
```

**Step 0 验收命令**：
```bash
ls *.md .env.example && echo "契约文件生成完毕"
# 检查无业务代码
git status --short  # 只应看到 .md 和 .env.example
```

**🔍 核验清单**：
- [ ] CLAUDE.md 含技术栈、目录约定、禁止事项、必须执行
- [ ] DESIGN.md 含 API 契约表（真实端点，非占位）
- [ ] .env.example 含所有需要的环境变量占位（值为空）
- [ ] 无任何 .py / .ts / .sql 文件（只写文档）

---

### Step 1 · PRD（需求澄清）

**输出给 Claude Code 的系统提示词**：

```
基于 CLAUDE.md，你现在是产品与架构助手。请不要写代码。
先输出计划，再生成 docs/PRD.md，内容包含：
1. 目标用户与核心场景
2. MVP 功能边界（明确 in scope / out of scope）
3. 数据流与模块划分
4. 验收标准（每条必须可观察、可验证，不要"流畅"这种主观词）
5. 风险与待确认问题
生成后告诉我怎么验收。
```

**验收命令**：
```bash
grep -c "验收标准\|acceptance" docs/PRD.md
```

**🔍 核验清单**：
- [ ] 验收标准每条可量化（有数字或可 yes/no 判断）
- [ ] 有"out of scope"部分
- [ ] 有"待确认问题"（AI 诚实标注自己不知道的）

---

### Step 2 · 项目骨架

**输出给 Claude Code 的系统提示词**（根据技术栈替换 `[...]`）：

```
基于 docs/PRD.md 和 CLAUDE.md 的目录约定，生成项目骨架。
先列完整目录树让我确认，再生成关键文件，最后给验收命令。

要求：
- [若有 Docker] docker-compose.yml：[列出所有服务]
- backend 分层目录 + Dockerfile + 依赖配置文件
- [若有前端] frontend 骨架 + Dockerfile
- [若有数据库] infra/[db]/init.sql：建库建表，严格按 DESIGN.md 的数据模型，不要自创列
- Makefile：dev / down / test 目标
- 不要把逻辑塞进一个大文件；严格按分层目录
```

**验收命令**：
```bash
# 根据技术栈替换
[docker] docker compose config >/dev/null && echo "compose 合法"
tree -L 3 [backend目录] 2>/dev/null || find [backend目录] -maxdepth 3
```

**🔍 核验清单**：
- [ ] 目录结构与 CLAUDE.md 约定一致
- [ ] 数据库表字段与 DESIGN.md 精确匹配（无自创列）
- [ ] 无业务逻辑代码（只有骨架和配置）

---

### Step 3 · 核心实现

**输出给 Claude Code 的系统提示词**（量大，要求分 sub-step）：

```
基于骨架实现核心功能。先给实现计划（分几个 PR/几步），我确认后逐步改，每步跑测试。

Backend：
- [schemas/models 文件]：Pydantic/ORM 模型唯一来源
- [api 层文件]：实现 DESIGN.md 中的全部端点
- [services 层]：业务逻辑，每个服务单一职责
- [若有 LLM] [gateway/client 文件]：唯一 LLM 入口，禁止其他模块 import LLM SDK
- 每个 API 配 pytest

[若有前端]
Frontend：
- src/lib/api.ts：API client 单独封装
- 核心页面组件：含 Loading/Error 状态
- 响应式设计

约束：任何 LLM 调用必须经过 gateway/client；不改已建好的表结构。
```

**验收命令**：
```bash
cd [backend] && python -m pytest -q
# 若有 LLM，检查无直连
! grep -rE "^(from|import) (openai|anthropic|dashscope)" [backend]/[app] --include=*.py | grep -v gateway/
```

**🔍 核验清单**（重点防漂移）：
- [ ] API 端点路径与 DESIGN.md 完全一致（没有私自改路径）
- [ ] schema/models 是唯一数据模型来源（没有散落的 dict）
- [ ] 测试覆盖核心 happy path + 一个 error path
- [ ] [若有 LLM] grep 确认无直连 SDK

---

### Step 4 · 测试 + CI

**输出给 Claude Code 的系统提示词**：

```
先给计划，再实现，最后跑一遍测试。
1. 补齐测试：
   - 输入校验测试（边界值、非法输入）
   - "禁止直连 LLM SDK"守门测试（若有 LLM）
   - 关键业务逻辑单测
2. [若有数据] testdata/ 或 scripts/seed.sh：生成测试数据
3. .github/workflows/ci.yml（或其他 CI 配置）：
   安装依赖 → lint → pytest → 守门检查（必备文件存在）
要求：测试要测"行为"不是"调一次返回非空"。
```

**验收命令**：
```bash
cd [backend] && python -m pytest -q
[若有 seed] bash scripts/seed.sh && echo "seed ok"
```

---

### Step 5 · Hooks + Review（治理层）

**输出给 Claude Code 的系统提示词**：

```
先给计划再实现。
1. .claude/hooks/pre-tool-use-guard.sh：PreToolUse 拦截危险命令
   （rm -rf、修改 .env、删库语句）
2. .claude/hooks/post-tool-use-lint.sh：PostToolUse 对改动的源码文件跑 lint
3. .claude/agents/：
   - reviewer.md：两阶段 Review（先 Spec Compliance，再 Code Quality）
   - architect.md：决定是否引入新依赖
4. .claude/settings.local.json：注册上面的 hooks
5. 用 reviewer 跑一次当前代码，输出报告
```

**验收命令**：
```bash
ls .claude/hooks .claude/agents
bash .claude/hooks/pre-tool-use-guard.sh <<<'{"tool_name":"Bash","tool_input":{"command":"rm -rf /"}}'; echo "exit=$?"  # 期望 exit 1
```

---

## 关键原则（每步都要遵守）

1. **每步必须先给计划，等用户确认再改文件**
2. **契约文件（CLAUDE.md/DESIGN.md）一旦确定，后续步骤不得私自修改核心约定**
3. **验收命令必须是可直接复制粘贴到终端的 bash**
4. **每步产出必须有"🔍 核验清单"，含具体可 yes/no 判断的检查项**
5. **漂移防护**：每步开始前先检查 DESIGN.md 的 API 端点和表结构，防止 AI 私自重命名
6. **兜底**：每步完成后建议用户 `git tag step-N`，卡住可以回退

---

## 输出格式约定

- 每个系统提示词用代码块包裹（可直接复制给 Claude Code）
- 验收命令独立代码块
- 核验清单用 `- [ ]` 格式（可在聊天中手动勾选）
- 设计决策摘要用表格形式，清晰对比各层技术选型

