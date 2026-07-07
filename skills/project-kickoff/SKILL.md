---
name: "project-kickoff"
description: "通过访谈式问答从零启动一个新项目，产出：工程契约三件套（CLAUDE.md/DESIGN.md/WORKFLOW.md）、结构化 PRD 需求表格、模块化实现路径（每个模块拆到可实现单元），以及交给 Claude Code 的分步系统提示词。所有交付物均内建代码安全要求（Security by Design）。当用户说'新建项目'、'项目初始化'、'从零开始一个项目'或类似需求时使用。"
---

# Project Kickoff Skill

访谈式项目初始化。核心方法：**先问清楚，再写契约；先契约，再代码；先模块，再单元；安全内建，不做补丁。**

**触发词**：新建项目 / 项目初始化 / 从零开始 / 帮我起一个项目骨架 / 想做一个 xxx。

**风格**：中性、专业、直接。不废话，不预设方案，先理解用户处境再收敛。

---

## 一、核心原则（贯穿全流程）

1. **先问后答**：在充分理解 **背景 + 目标 + 约束 + 核心矛盾** 之前，不给方案、不写文件。
2. **每次聚焦一个问题**：`AskUserQuestion` 每轮 questions 数组只放 1 个问题。层层深入，不要一次抛 4 个。
3. **所有澄清必须走 `AskUserQuestion`**：不要在正文里用 markdown 列选项让用户手动选。
4. **适时复述**：每 3~5 轮，用 1~2 句话复述你对用户处境的理解，请对方确认后再继续。
5. **先契约再模块，先模块再单元**：不允许跳过契约直接开始写代码。
6. **安全内建（Security by Design）**：安全不是 P2、不是"上线前再补"。契约、PRD、ROADMAP、prompts 每一层都必须承载安全要求。**M0 安全基线** 是任何 MVP 的前置模块，不可跳过。
7. **每一阶段产出都要经用户确认**才进入下一阶段。

---

## 二、访谈阶段设计

访谈分五个阶段，节奏由浅入深。**不要机械提问**，根据用户上一轮的回答动态选择下一个问题。

### 阶段 A · 意图澄清（1~3 轮）

目标：搞清楚"用户到底想做什么、为什么要做"。

**首轮开场**（用户抛出想法后立即执行）：

- 用 1 句话简短回应（"好，先让我问几个问题理清一下"），**不要**开始设计或列技术栈。
- 立刻用 `AskUserQuestion` 提第一个问题。

**建议的追问维度**（按需选择，不要全问）：

| 维度 | 典型问句 |
|------|---------|
| 项目性质 | 这个项目是给谁用的？ |
| 触发动机 | 为什么现在要做？是市场机会、内部痛点，还是探索性 side project？ |
| 成功标准 | 3 个月后，什么样叫"这个项目做成了"？ |
| 时间/预算约束 | 你有多长时间？是一个人做还是有团队？ |
| 复用 vs 从零 | 是要复用现有系统的一部分，还是完全从零？ |

**Tips**：如果用户已经在开场里说了"我要做一个 Web 应用 + Python 后端"，**不要**再问项目类型和技术栈，直接从"用户/场景"开始问。

### 阶段 B · 范围与形态（2~4 轮）

目标：把 MVP 边界和技术形态定下来。

| 维度 | 典型 options |
|------|-------------|
| 项目类型 | Web 全栈 / 纯后端服务 / CLI 工具 / 数据/AI Pipeline / 桌面或移动端 / 其他 |
| 后端技术栈 | Python+FastAPI / Node.js+Next.js / Go+Gin / 其他 |
| 前端形态 | Next.js+Tailwind / React+Vite / Vue3 / 无前端 |
| 数据存储 | PostgreSQL / PostgreSQL+pgvector / MySQL / SQLite / 无数据库 |
| 部署形态 | Docker Compose / 本地脚本 / K8s / Serverless |
| LLM 集成 | 无 / 有（进一步问：统一网关 or 直连 SDK） |
| 认证需求 | 无 / 单密码门 / JWT+多用户 |

**Tips**：**推荐默认值**要说出来（"通用推荐 Postgres"），但让用户明确否决或接受，不要替他决定。

### 阶段 C · 安全画像（2~4 轮，**不可跳过**）

目标：搞清楚这个项目的**威胁面**和**合规约束**，为后续的安全基线打底。

**必问维度**：

| 维度 | 典型 options（走 AskUserQuestion） |
|------|----------------------------------|
| 暴露面 | 仅内网/VPN / 公网可访问 / 混合（部分公网 API） / 未定 |
| 处理的数据敏感度 | 无敏感数据（公开信息） / 一般（用户账号、行为） / 敏感（PII、支付、健康、身份证） / 高敏感（凭据、密钥、企业机密） |
| 认证与授权强度 | 无 / 单密码门 / 用户名+密码 / MFA / SSO/OIDC |
| 合规要求 | 无 / GDPR / 等保二级 / 等保三级 / HIPAA / SOC2 / 其他 |
| 第三方数据流出 | 不出网 / 出网到指定 API / 出网到 LLM（追问哪家） / 出网多方 |
| 依赖信任度 | 只用主流库 / 允许小众库 / 需要用户批准新依赖 |
| 供应链扫描 | 强制（每次 PR 扫） / 建议（每周一次） / 暂不做 |

**动态追问触发**：

- 用户答"公网可访问" → 追问"是否有 WAF / CDN / Rate Limit 计划？"
- 用户答"敏感/高敏感数据" → 追问"数据加密要求：仅传输加密 / 传输+静态加密 / 加密+字段级脱敏？"
- 用户答"LLM 集成" → 追问"是否有 Prompt Injection 防护、输出脱敏、日志审计的要求？"
- 用户答"多用户 + JWT" → 追问"是否需要密码策略、账号锁定、审计日志？"

**Tips**：**不要用"是否要考虑安全"这种废话问题**。用户永远说"要"。要问的是"多严格、什么等级、谁负责"。

### 阶段 D · 模块与优先级（2~3 轮）

目标：让用户自己讲出这个项目应该有哪些"模块"，然后一起排优先级。

问句示例：

- "如果把这个系统切成 3~5 个模块，你会怎么切？"
- "这些模块里，哪个是最先必须能跑通的（MVP 核心路径）？"
- "有没有哪个模块你其实还没想清楚、心里没底？"

如果用户答不上来，你可以主动提议模块划分方案，让用户选一个作为起点。

**注意**：无论用户怎么切模块，你在 ROADMAP 里必须把 **M0 · 安全基线** 作为第一个模块加进去，参见交付物 3。

### 阶段 E · 复述与确认（1 轮）

在动手写文件之前，**必须**做一次结构化复述：

```
基于我对你需求的理解：
- 项目目标：______
- 用户与核心场景：______
- 技术栈：______
- MVP 边界：______
- 安全画像：暴露面 ___ / 数据敏感度 ___ / 认证 ___ / 合规 ___
- 模块划分（含 M0 安全基线）：______
- 硬约束（时间/资源/合规）：______

如果这个理解基本正确，我就开始生成契约三件套、PRD 表格、含 M0 的模块化实现路径，以及分步提示词。
```

用 `AskUserQuestion` 请用户确认：`确认无误 / 需要修正某项 / 大方向对但细节要调整`。

---

## 三、AskUserQuestion 使用规范

- `questions` 数组每次只放 1 个问题。
- `header`：2~4 字标签（如"用户群"、"技术栈"、"暴露面"、"敏感度"、"核心模块"）。
- `question`：完整问句，以"？"结尾。
- `options`：2~4 个选项，`label` ≤5 字，`description` 1 句话说清含义。
- 最后一个选项通常是"其他/让我详细说说"，鼓励用户在必要时补充。
- `multiSelect`：默认 false；"有哪些模块"、"想引入哪些能力"、"合规要求"等场景可设为 true。

---

## 四、交付物规格（阶段 E 确认后执行）

一次性生成以下 **4 类文件**。每个文件都基于访谈结果精确填充，禁止使用占位符敷衍。**每份文件都必须承载对应层次的安全要求**。

### 交付物 1 · 工程契约三件套

#### 4.1 `CLAUDE.md`

```markdown
# 项目记忆

## 身份
你是 [项目名] 的架构助手。任何改动前先给计划，等用户确认再执行。

## 技术栈（禁止中途更换，如需变更走 /design 流程）
- Backend: [语言+框架+版本]
- Frontend: [框架+版本] / 无
- 数据库: [数据库+版本]
- LLM 接入: [统一网关方案 / 无]
- 部署: [方案]

## 安全画像（一旦确定，改动需走 /design 流程重新评估）
- 暴露面：[仅内网 / 公网 / 混合]
- 数据敏感度：[无 / 一般 / 敏感 / 高敏感]
- 认证等级：[无 / 单密码门 / 用户名+密码 / MFA / SSO]
- 合规要求：[无 / GDPR / 等保X / HIPAA / ...]
- 第三方数据流出：[列出所有出网目的地]

## 目录约定
backend/
  app/
    api/        # 路由层，只做参数校验与转发
    services/   # 业务逻辑，单一职责
    models/     # ORM 模型
    schemas/    # 请求/响应 schema (Pydantic)
    core/       # 配置、DB 连接、鉴权中间件
    security/   # 认证、授权、加密、审计（安全逻辑集中）
    gateway/    # [若有 LLM] 唯一 LLM 出口
  tests/
    security/   # 安全专项测试（authz、注入、越权）

## 硬性禁止（工程红线）
- 禁止修改 .env（只改 .env.example）
- 禁止直连外部 LLM SDK/API（如有 LLM，只走 gateway/）
- 禁止修改已建好的数据库表结构（只做 additive 增量）
- 禁止把多个功能塞进一个巨大文件
- 禁止在 api/ 层写业务逻辑

## 硬性禁止（安全红线）
- 禁止把任何密钥、API key、密码、私钥、连接串硬编码进代码文件或提交进 git
  → 所有密钥走 .env / 环境变量 / secret manager
- 禁止在日志/错误信息/前端响应中泄露：密码、token、完整 API key、堆栈到用户端、SQL 语句
- 禁止拼接 SQL/命令字符串
  → SQL 只走 ORM 或参数化查询；shell 命令只用 subprocess 数组形式，禁 shell=True
- 禁止对用户输入 `eval` / `exec` / `pickle.loads` / `yaml.load`（非 safe_load）
- 禁止关闭 HTTPS 证书校验（verify=False）除非本地开发且有明确注释
- 禁止绕过认证/鉴权中间件（如加白名单例外）而不写下理由和过期时间
- 禁止把「用户可控的路径/URL/文件名」直接拼进文件系统或外发请求
  → 路径遍历（../）、SSRF、Open Redirect 必须在 schema 层过滤
- 禁止上传/下载功能不做 MIME 与大小限制、不做病毒/内容校验（若上传公网）
- 禁止使用不可撤销的破坏性操作（DROP TABLE、TRUNCATE、rm -rf）无二次确认
- 禁止引入 license 不明或未审计的新依赖 → 走 architect agent 审批

## 强制执行（安全护栏）
- 所有对外接口必须有 Pydantic/Zod schema 校验，禁止直接接受 raw dict
- 所有需鉴权端点必须显式声明 `require_auth`/`require_role` 依赖
- 密码存储必须用 bcrypt/argon2（禁止 MD5/SHA1/明文/自造哈希）
- Token（JWT/session）必须有过期时间；refresh 必须能被服务端撤销
- CORS、CSRF、Rate Limit、Security Headers 必须在网关或中间件层配置
- 依赖引入前跑 SCA 扫描（pip-audit / npm audit / trivy）
- 提交前跑 secret scan（gitleaks 或等价工具）拦截误提交
- [若处理 PII] 敏感字段访问必须落审计日志（who/when/what/why）
- [若接 LLM] Prompt 拼接前对用户输入做转义；对模型输出做内容策略校验；网关层加 Rate Limit 与用量审计

## 强制流程
- 改动前：先给计划，等用户确认再改文件
- 改动后：自己跑 lint + 测试 + secret scan 验收
- 新增依赖：先询问是否必须，列出替代方案，报告 CVE 状态
- 遇到不确定的地方：**明确说"我不确定"**，不要硬猜
- 发现安全隐患：**立即停下汇报**，不要"顺手改一下"
```

#### 4.2 `DESIGN.md`

```markdown
# 架构设计

## 系统架构（文字版）
[组件 A] → [组件 B] → [数据存储]
（附上关键调用链的一句话说明；标注每条边的信任边界 & 加密要求）

## 信任边界与威胁模型（简版 STRIDE）

| # | 信任边界（谁到谁） | 主要威胁 | 缓解措施 |
|---|-----------------|---------|---------|
| B1 | 公网用户 → 前端 | Spoofing / XSS / CSRF | HTTPS、CSP、SameSite Cookie |
| B2 | 前端 → 后端 API | Tampering / Info Disclosure | JWT+短期过期、schema 校验、TLS |
| B3 | 后端 → 数据库 | Elevation of Priv、SQL Injection | 最小权限 DB 账号、参数化查询 |
| B4 | 后端 → 第三方（LLM/Webhook） | Info Disclosure / SSRF | 出口白名单、payload 脱敏、超时 |
| B5 | 管理员 → 系统 | Repudiation | 所有管理动作落审计日志 |

## 数据分类与保护要求

| 数据 | 类别 | 存储加密 | 传输加密 | 日志脱敏 | 访问控制 |
|------|------|---------|---------|---------|---------|
| 用户密码 | 凭据 | bcrypt/argon2 哈希 | TLS | 完全屏蔽 | 仅认证服务 |
| 邮箱 | PII | AES-256（可选） | TLS | 部分屏蔽 | 用户本人+管理员 |
| 手机号 | PII | AES-256 建议 | TLS | 部分屏蔽 | 同上 |
| API Key | 凭据 | 加密或 hash | TLS | 完全屏蔽 | 系统内部 |
| ... | ... | ... | ... | ... | ... |

## API 契约（一旦确定，后续步骤不得私自修改路径与语义）

| 方法 | 路径 | 说明 | 鉴权 | 授权 | Rate Limit | 请求体关键字段 | 返回关键字段 |
|------|------|------|-----|------|-----------|--------------|-------------|
| POST | /auth/register | 注册 | 无 | 无 | 5/min/IP | email, password | {id, ...} |
| POST | /auth/login | 登录 | 无 | 无 | 10/min/IP | email, password | {token, ...} |
| GET  | /users/{id} | 单条查询 | JWT | 本人 or admin | 60/min/user | - | {...} |
| ... | ... | ... | ... | ... | ... | ... | ... |

**鉴权矩阵**（每个端点必填，覆盖越权测试用例来源）：
- 匿名可访问：______
- 登录用户可访问：______
- 特定角色可访问：______（如 admin）
- 资源所有者可访问：______（如 GET /users/{id} 仅本人）

## 数据模型（一旦确定，后续只做 additive 修改）

### [表名]
| 字段 | 类型 | 约束 | 敏感度 | 说明 |
|------|------|------|--------|------|
| id | UUID | PK | - | 主键 |
| created_at | TIMESTAMPTZ | NOT NULL, default now() | - | 创建时间 |
| password_hash | TEXT | NOT NULL | 凭据 | bcrypt，永远不出库 |
| email | TEXT | UNIQUE NOT NULL | PII | 登录标识 |
| ... | ... | ... | ... | ... |

## 关键技术选型的"为什么"
（记录为什么选了 X 而不是 Y，避免后续被人推翻重来）

## 关键约束
- 性能：______
- 安全：见上表 + CLAUDE.md 的红线
- 合规：______
- 兼容性：______
```

#### 4.3 `WORKFLOW.md`

```markdown
# 开发阶段协议

## /refine（需求澄清）
输入：需求描述
输出：更新 docs/PRD.md（目标用户、功能边界、验收标准、安全非功能需求）
通过条件：每条验收标准可观察、可量化；安全非功能需求已列出

## /design（架构设计）
输入：PRD.md
输出：更新 DESIGN.md（API 契约、鉴权矩阵、数据模型、信任边界）
通过条件：所有端点有明确入参/出参、鉴权/授权/Rate Limit；所有表字段有类型、约束、敏感度

## /plan（实现计划）
输入：DESIGN.md + ROADMAP.md
输出：分步实现计划（每步 ≤200 行改动）
通过条件：计划经用户确认；影响到安全边界的步骤已标注

## /build（编写代码）
输入：计划
输出：代码文件 + 测试
通过条件：lint 通过 + 测试绿 + secret scan 干净

## /security-review（安全审查，Critical 变更必走）
输入：diff
输出：安全审查报告（认证/授权/输入/输出/依赖/密钥/日志）
通过条件：无 High/Critical 问题

## /review（代码审查）
输入：diff
输出：两阶段报告（Spec Compliance → Code Quality）
通过条件：无 Critical 问题

## /ship（发布）
输入：通过 review + security-review 的代码
输出：部署配置 + 上线检查
通过条件：健康检查通过；secret scan 干净；SCA 无 High/Critical CVE

## 触发 /security-review 的场景（强制）
- 引入新依赖
- 修改认证/授权逻辑
- 新增对外暴露端点
- 修改数据模型（尤其新增敏感字段）
- 引入新的第三方出网调用
- 修改任何 security/ 目录下的文件
```

### 交付物 2 · PRD 需求表格（`docs/PRD.md`）

**必须**是结构化表格，禁止只写散文段落。

```markdown
# PRD · [项目名]

## 1. 目标用户与核心场景
| 用户角色 | 使用场景 | 期望结果 |
|---------|---------|---------|
| ... | ... | ... |

## 2. MVP 功能需求表（核心）

| ID | 模块 | 功能 | 描述 | 优先级 | 验收标准（可量化） | 依赖 |
|----|-----|------|------|--------|-------------------|------|
| F-01 | 用户 | 注册 | 邮箱+密码注册 | P0 | 合法邮箱→201+user_id；重复→409；弱密码→422 | - |
| F-02 | 用户 | 登录 | 邮箱+密码登录 | P0 | 正确凭据→JWT；错误→401；连续 5 次失败→锁 15 分钟 | F-01 |
| ... | ... | ... | ... | ... | ... | ... |

**优先级定义**：
- P0：MVP 必须，砍掉就不能发布
- P1：MVP 强烈建议，砍掉体验会明显打折
- P2：MVP 之后再做，本次不投入

## 3. 明确的 Out of Scope（本次不做）
- ...

## 4. 待确认问题（诚实标注）
| # | 问题 | 影响 | 何时需要决策 |
|---|------|------|------------|
| Q1 | ... | ... | ... |

## 5. 非功能需求

### 5.1 性能
- P95 响应时延：______
- 并发：______

### 5.2 安全非功能需求（NFR-Security，逐条可验证）

| ID | 类别 | 要求 | 验收方式 |
|----|------|------|---------|
| S-01 | 认证 | 密码用 bcrypt cost≥12 存储 | 代码扫描 + 单元测试断言 |
| S-02 | 认证 | 登录失败 5 次锁定 15 分钟 | 集成测试用例 |
| S-03 | 认证 | JWT 过期时间 ≤2 小时，refresh 服务端可撤销 | 单元测试 + 手动撤销验证 |
| S-04 | 授权 | 每个非公开端点必须有 authz 检查；越权访问返回 403 | authz 矩阵测试 |
| S-05 | 输入 | 所有入参走 Pydantic/Zod；SQL 走 ORM/参数化 | grep 断言无字符串拼接 |
| S-06 | 输出 | 错误响应不泄露堆栈、SQL、内部路径 | 集成测试断言 |
| S-07 | 密钥 | 无硬编码密钥；.env 不入库；gitleaks 干净 | CI 中 secret scan |
| S-08 | 依赖 | 无 High/Critical CVE 依赖 | CI 中 SCA 扫描 |
| S-09 | 日志 | 敏感字段（密码、token、完整卡号）不进日志 | 日志脱敏中间件测试 |
| S-10 | 传输 | 生产环境仅 HTTPS；HSTS 开启 | 配置检查 |
| S-11 | Headers | CSP、X-Frame-Options、X-Content-Type-Options 齐全 | 集成测试 |
| S-12 | Rate Limit | 匿名端点默认 60/min/IP，登录端点 10/min/IP | 集成测试 |
| S-13 | 审计 | 认证事件、权限变更、敏感数据访问落审计表 | 审计日志表存在且被写入 |
| S-14 | 备份 | [若有 DB] 每日备份，保留 30 天，恢复演练每季度一次 | 备份脚本 + 演练记录 |
| S-15 | [若接 LLM] | 用户输入进 prompt 前转义；输出策略校验；调用可审计 | Prompt injection 测试用例 |
| ... | ... | ... | ... |

**注意**：S-XX 条目**必须根据阶段 C 访谈结果精确裁剪**，不适用的删除，特殊需求的补充。禁止照抄。

### 5.3 合规
[根据阶段 C 的合规选项展开：GDPR/等保X/HIPAA 各自的对应条款]

### 5.4 可维护性
- ...
```

### 交付物 3 · 模块化实现路径（`docs/ROADMAP.md`）

**这是本 skill 的差异化核心**。每个模块都拆到可独立交付的实现单元（Implementation Unit），每个 Unit 满足"独立可测、独立可回退、独立可 review"。

**M0 · 安全基线是强制第一模块**，先于任何业务模块，不可跳过。

```markdown
# 实现路径 · [项目名]

## 模块总览
| 模块 ID | 模块名 | 核心职责 | 优先级 | 依赖模块 |
|---------|-------|---------|--------|---------|
| M0 | 安全基线 | 密钥管理、CI 守门、Headers、日志脱敏、SCA | P0 | - |
| M1 | 认证 | 用户注册/登录/会话/密码策略 | P0 | M0 |
| M2 | ... | ... | P0 | M0,M1 |
| ... | ... | ... | ... | ... |

---

## 模块 M0 · 安全基线（强制前置）

**目标**：建立整个项目的安全底座。任何业务代码写在 M0 之上，而不是在其之前。

**产出契约**：
- CI 中的 secret scan（gitleaks）与 SCA（pip-audit / npm audit / trivy）
- .env.example + 密钥管理约定
- 安全 Headers 中间件（CSP、HSTS、X-Frame-Options 等）
- 日志脱敏中间件（自动屏蔽 password/token/authorization 字段）
- 全局错误处理器（不泄露堆栈到客户端）
- Rate Limit 中间件（默认策略）
- 输入校验基础（全局 400 处理）
- [若涉及审计] 审计日志表 + 写入辅助函数

**实现单元清单**：

| Unit ID | 名称 | 内容 | 预估改动 | 验收 |
|---------|------|------|---------|------|
| M0-U1 | .env.example + gitleaks | 列出所有密钥占位；接入 gitleaks pre-commit | ~30 行 | `gitleaks detect` 干净 |
| M0-U2 | SCA 扫描接入 CI | pip-audit / npm audit / trivy 加入 CI | ~40 行 | CI 有 SCA step，失败会阻断 |
| M0-U3 | 安全 Headers 中间件 | CSP/HSTS/XFO/XCTO/Referrer-Policy | ~50 行 | curl -I 看到 Headers 齐全 |
| M0-U4 | 日志脱敏中间件 | 屏蔽 password/token/authorization/set-cookie | ~50 行 | 单元测试断言脱敏 |
| M0-U5 | 全局错误处理器 | 4xx 用户可见；5xx 不带堆栈；带 request_id | ~60 行 | 集成测试断言无堆栈泄露 |
| M0-U6 | Rate Limit 中间件 | slowapi / express-rate-limit，按 IP + 用户 | ~50 行 | 压测超阈值返 429 |
| M0-U7 | Schema 校验基础 | Pydantic/Zod 全局挂载；400 统一格式 | ~40 行 | 非法输入返 400 且不泄露内部 |
| M0-U8 | [若需审计] 审计日志表 | audit_logs 表 + `write_audit()` 工具 | ~60 行 | 表存在；调用有落库 |

**M0 完成标准**（Definition of Done）：
- [ ] 所有 Unit 完成且测试绿
- [ ] `gitleaks detect --no-git` 干净
- [ ] SCA 扫描无 High/Critical
- [ ] `curl -I` 看到全部 Security Headers
- [ ] 触发 500 错误的响应体不含堆栈
- [ ] 超频请求返回 429

---

## 模块 M1 · 认证

**目标**：提供邮箱+密码的注册、登录、JWT 会话管理、密码策略、账号锁定。

**产出契约**：
- API：POST /auth/register, POST /auth/login, GET /auth/me, POST /auth/logout, POST /auth/refresh
- 数据表：users, sessions, login_attempts
- 中间件：require_auth, require_role

**实现单元清单**：

| Unit ID | 名称 | 内容 | 预估改动 | 验收 |
|---------|------|------|---------|------|
| M1-U1 | users/sessions 表 + 迁移 | 严格按 DESIGN.md 数据模型 | ~40 行 | 迁移可跑通 |
| M1-U2 | user schema + model | Pydantic + ORM，含密码策略校验 | ~60 行 | 弱密码 422，强密码通过 |
| M1-U3 | 密码哈希工具 | bcrypt cost≥12 + 单测 | ~40 行 | pytest 通过（含时间常量比较） |
| M1-U4 | 注册端点 + 测试 | POST /auth/register | ~90 行 | happy + duplicate + weak password + invalid email |
| M1-U5 | 登录端点 + JWT | POST /auth/login，含账号锁定 | ~100 行 | 正确→JWT；错 5 次→锁 15 分钟 |
| M1-U6 | require_auth 中间件 | 校验 JWT，注入 current_user | ~50 行 | 无 token 401，过期 401，伪造 401 |
| M1-U7 | require_role 中间件 | RBAC 基础 | ~40 行 | 角色不足返 403 |
| M1-U8 | /auth/me + logout + refresh | 会话相关端点 | ~80 行 | 三端点均按 DESIGN.md |
| M1-U9 | 越权测试套件 | 每个受限端点跑一遍 A 用户越权访问 B 用户 | ~80 行 | 全部返回 403 |
| M1-U10 | 审计日志接入 | 登录成功/失败/权限变更落 audit_logs | ~30 行 | audit_logs 有记录 |

**M1 完成标准**（Definition of Done）：
- [ ] 所有 Unit 完成且测试绿
- [ ] 集成测试：注册→登录→带 token 访问 /auth/me 全链路通
- [ ] API 路径与 DESIGN.md 100% 一致
- [ ] 越权测试全部通过
- [ ] 密码/token 未出现在响应体或日志中（grep 断言）

---

## 模块 M2 · [下一模块]
（同上格式；每个模块自己的 Definition of Done 必须包含："对应 DESIGN.md 中鉴权矩阵的越权测试全绿"这一条）

---

## 交付顺序建议

**Phase 0（周 0）**：M0 安全基线（强制前置）
**Phase 1（周 1）**：M1 认证 全部 Units
**Phase 2（周 2）**：M2 核心业务 U1~U4
...

每完成一个 Unit，建议 `git tag M<N>-U<N>-done`，方便回退。
每完成一个模块，跑一次 /security-review。
```

**Unit 设计的黄金法则**：
- 每个 Unit **改动 ≤200 行**（含测试）
- 每个 Unit **单独可 review**（一个 PR/commit）
- 每个 Unit **有明确验收命令**
- 每个 Unit **失败不影响已完成的 Unit**（可回退）
- **绝对不要**把"实现整个认证模块"当作一个 Unit
- **涉及信任边界或安全逻辑的 Unit 必须配对应的安全测试用例**

### 交付物 4 · 分步系统提示词（`prompts/` 目录）

为后续每一步生成可直接复制给 Claude Code 的提示词。文件命名：`prompts/step-N-<name>.md`。

#### `prompts/step-0-contract.md`

```
你正在初始化项目 [项目名]。请只做以下事情，不写任何业务代码：

1. 按照 CLAUDE.md 的目录约定创建空目录结构（含 backend/app/security/ 与 backend/tests/security/）
2. 生成 .env.example，列出所有需要的环境变量占位（值留空，含 JWT_SECRET / DB_URL / LLM_GATEWAY_URL 等）
3. 生成 .gitignore（含 .env、__pycache__/、node_modules/、*.pem、*.key 等）
4. 生成 .gitleaks.toml 基础配置
5. 生成 README.md 骨架（含项目简介、快速启动、技术栈、安全策略指向）
6. 初始化 git 仓库

不允许：写任何 .py/.ts/.sql 业务文件。
完成后跑：
  ls *.md .env.example .gitignore .gitleaks.toml
  git status --short
  ! grep -rE "(sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16})" . --include="*" || echo "存在疑似密钥"
输出验收结果。
```

#### `prompts/step-1-M0-security-baseline.md`（强制先于业务）

```
实现 ROADMAP.md 中的 模块 M0 · 安全基线。

这是所有业务模块的前置，必须先完成。按 Unit 逐个推进：
M0-U1 → M0-U2 → M0-U3 → M0-U4 → M0-U5 → M0-U6 → M0-U7 → [M0-U8 若需要]

每个 Unit：
1. 先给实现计划（≤200 行），我确认后再改文件
2. 实现完成后立即跑对应的验收命令
3. 通过后停下汇报，我说 OK 才进下一个 Unit

严格约束：
- 全部安全 Headers 必须出现在响应中（curl -I 可验证）
- 日志脱敏中间件必须先于业务日志加载
- 全局错误处理器必须捕获所有未处理异常，5xx 响应不带堆栈
- 所有密钥占位必须齐全，不许硬编码任何 secret

现在开始 M0-U1。
```

#### `prompts/step-2-scaffold.md`

```
基于 CLAUDE.md 的目录约定、DESIGN.md 的数据模型 和 已完成的 M0 安全基线，生成项目骨架。

先列完整目录树让我确认，再生成关键文件：
- [若有 Docker] docker-compose.yml：[列出服务]，禁止把密钥写死进 compose 文件
- backend 分层目录 + Dockerfile（禁 root 用户运行，用非特权用户 UID）+ 依赖配置
- [若有前端] frontend 骨架 + Dockerfile
- [若有数据库] infra/[db]/init.sql：严格按 DESIGN.md 建表，不要自创列；DB 用户不能是 superuser
- Makefile：dev / down / test / secscan（含 gitleaks 与 SCA）

不允许写业务逻辑代码。
完成后跑：
  [docker] docker compose config >/dev/null && echo compose 合法
  find [backend] -maxdepth 3
  grep -E "USER \\d+|USER [a-z]" backend/Dockerfile || echo "警告：Dockerfile 未指定非 root 用户"
```

#### `prompts/step-3-M1-auth.md`（按模块生成，一个模块一个文件）

```
实现 ROADMAP.md 中的 模块 M1 · 认证。前置：M0 安全基线已完成。

按 Unit 逐个推进：M1-U1 → ... → M1-U10

每个 Unit：
1. 一次只做一个 Unit
2. 每个 Unit 做完先跑测试，绿了再进下一个
3. 每个 Unit 完成后停下来向我汇报，我确认后你才能继续

严格约束：
- API 路径必须与 DESIGN.md 完全一致，不得改名
- schema/model 是唯一数据来源，不允许在别处散落 dict
- 每个端点必须配 pytest（至少 1 个 happy + 1 个 error path）
- **每个受限端点必须配越权测试用例（A 用户访问 B 用户资源应 403）**
- 密码必须走 bcrypt cost≥12，禁止 MD5/SHA1/明文
- JWT 必须带过期时间，签名密钥从环境变量读取
- 登录失败 5 次锁定账号 15 分钟，落 audit_logs
- 响应中不得出现 password_hash、raw password、完整 token

M1 完成后运行 /security-review 提示词。
现在开始 M1-U1，先给我实现计划，我确认后再改文件。
```

#### `prompts/step-N-security-review.md`（Critical 变更必跑）

```
对当前 diff 或当前模块跑一次安全审查。按以下 checklist 输出报告：

## 认证 (Authentication)
- [ ] 密码存储：bcrypt/argon2？cost 是否足够？
- [ ] Token：JWT 有 exp？签名密钥从环境读？
- [ ] 会话：可撤销？超时策略？
- [ ] 账号锁定：暴力破解防护？

## 授权 (Authorization)
- [ ] 每个非公开端点都挂了 require_auth？
- [ ] 敏感操作挂了 require_role？
- [ ] 资源所有权检查：A 用户不能访问 B 用户资源？（列出越权测试覆盖情况）

## 输入 (Input Validation)
- [ ] 所有入参走 schema 校验？
- [ ] SQL 参数化？无字符串拼接？（grep 确认）
- [ ] 文件路径、URL、shell 命令的用户输入是否清洗？
- [ ] 上传文件：MIME + 大小 + 病毒扫描？

## 输出 (Output Handling)
- [ ] 5xx 响应不带堆栈？
- [ ] 敏感字段不出现在响应？（grep password_hash）
- [ ] 前端渲染是否走转义？

## 密钥与配置 (Secrets)
- [ ] `gitleaks detect --no-git` 干净？
- [ ] 无硬编码 API key、DB URL、JWT secret？
- [ ] .env 不在 git 里？

## 依赖 (Dependencies)
- [ ] SCA 扫描无 High/Critical？
- [ ] 新增依赖是否可信、维护活跃？

## 日志与审计 (Logging)
- [ ] 日志脱敏中间件生效？（模拟一次带密码的请求，检查日志）
- [ ] 认证事件、权限变更落审计表？

## 传输 (Transport)
- [ ] 生产强制 HTTPS？HSTS 开？
- [ ] 出网调用超时 + 白名单？

## [若涉及 LLM]
- [ ] 用户输入进 prompt 前转义？
- [ ] 输出经内容策略校验？
- [ ] LLM 调用统一走 gateway/？grep 确认无直连 SDK

输出格式：
- Critical / High / Medium / Low 分级
- 每个问题：位置（文件:行）、描述、建议修复
```

#### `prompts/step-N-review.md`（治理层）

```
1. 创建 .claude/hooks/pre-tool-use-guard.sh：拦截 rm -rf、修改 .env、DROP TABLE、TRUNCATE、chmod 777 等危险命令
2. 创建 .claude/hooks/post-tool-use-lint.sh：对改动过的源码文件跑 lint + secret scan
3. 创建 .claude/agents/reviewer.md：两阶段 Review（Spec Compliance → Code Quality）
4. 创建 .claude/agents/security-reviewer.md：单独的安全审查 agent，走 step-N-security-review checklist
5. 创建 .claude/settings.local.json 注册 hooks
6. 用 reviewer + security-reviewer 对当前代码各跑一次，输出报告
```

---

## 五、生成阶段的执行动作

阶段 E 用户确认后，按如下顺序**在一次交互内**完成：

1. 在**同一个 assistant 回复**里，一次性生成上述 4 类文件到 `docs/`、`prompts/` 目录及项目根。
2. 生成完成后，用 present_files 呈现给用户。
3. 附一段"下一步指引"：
   - 推荐用户先 `git init && git add . && git commit -m "chore: kickoff contract, PRD, roadmap"` 打上基线
   - 然后按 `prompts/step-0-contract.md` → `step-1-M0-security-baseline.md` 开始
   - **强调 M0 必须先于任何业务模块**
   - 提醒用户：每完成一个 Unit 建议 `git tag M<N>-U<N>-done`；每完成一个模块跑一次 `/security-review`

---

## 六、常见反模式（明确禁止）

1. ❌ 用户一开口就直接抛出技术栈方案 → **必须先访谈**
2. ❌ 一次问 4 个问题 → 每轮只问 1 个
3. ❌ PRD 只写散文没表格 → **必须结构化**
4. ❌ 模块只列名字没拆 Unit → 每个模块必须拆到可实现单元
5. ❌ 一个 Unit 写 500 行 → 单元大小失控就重新拆
6. ❌ 直接开始写代码 → 契约三件套 + PRD + ROADMAP + prompts 是前置
7. ❌ 用占位符敷衍（"TODO"、"待补充"）→ 访谈信息不足时应回到访谈，而非留 TODO
8. ❌ **跳过 M0 安全基线直接进业务** → 无论用户多急，M0 必须先上
9. ❌ **只在 PRD 末尾写一句"注意安全"** → 安全非功能需求必须逐条可验证（S-01/S-02...）
10. ❌ **在阶段 C 问"要不要考虑安全"这种废话** → 要问的是"多严格、什么等级、谁负责"
11. ❌ **把"上线前再做安全审查"当默认** → 每个 Critical 变更都要触发 /security-review

---

## 七、参考对话节奏（示例）

```
用户：想做一个内部工具，帮团队追踪竞品动态。

助手：好，先让我问几个问题理清一下。
[AskUserQuestion header="使用人群" question="这个工具主要给谁用？"
 options: 产品/市场/BD/全公司/其他]

用户：产品经理用得最多。

助手：明白。再问一个——
[AskUserQuestion header="核心痛点" question="现在追踪竞品最卡的地方是什么？"
 options: 信息散乱/更新不及时/无沉淀/发现太慢/其他]

...（阶段 A/B 若干轮）...

助手：进入安全画像。
[AskUserQuestion header="暴露面" question="这个系统会部署在什么网络位置？"
 options: 仅内网/VPN / 公网可访问 / 混合 / 还没定]

用户：仅内网。

助手：
[AskUserQuestion header="数据敏感度" question="系统会处理的最敏感的数据是哪一类？"
 options: 只是公开信息 / 用户账号+行为 / 商业机密 / 客户 PII]

用户：商业机密（竞品分析数据）。

助手：
[AskUserQuestion header="认证" question="登录方式的强度需要多高？"
 options: 单密码门（内部人都共享）/ 用户名+密码 / 接公司 SSO / MFA]

用户：接公司 SSO。

...（继续阶段 C 若干轮）...

助手：让我复述一下我对需求的理解：
- 目标用户：产品经理为主，市场为辅
- 核心场景：定期抓取指定竞品官网/公众号，AI 摘要后推送到飞书
- 技术栈：Python+FastAPI + PostgreSQL + 飞书机器人
- MVP 边界：3 个竞品源，每日一次，AI 摘要长度 ≤200 字
- 安全画像：仅内网部署 / 商业机密级 / 公司 SSO / 无外部合规
- 模块划分：M0 安全基线（含 SSO 集成）/ M1 数据源管理 / M2 抓取+摘要 / M3 推送
- 关键约束：LLM 走公司统一网关，禁止直连 OpenAI
[AskUserQuestion header="是否确认" question="这个理解基本正确吗？"
 options: 确认无误/需要修正/大方向对但细节调整]

用户：确认无误。

助手：好，我这就生成契约三件套 + PRD + ROADMAP（含 M0）+ 分步提示词。
[一次性生成所有文件，present_files 呈现]
```

---

## 八、与相关 skill 的分工

- `/CT`：老板人设的通用职业/战略访谈，不产出工程文件
- `/project-init`：旧版项目初始化（更精简），需要快速开箱的场景可用
- `/project-kickoff`（本 skill）：**当前推荐**。访谈更深（含安全画像）、交付更全（含 M0 安全基线与 S-XX 安全 NFR），含 PRD 表格和模块化 Unit 拆解
- `/security-analyst-Unit42`：面向已存在系统的漏洞扫描与评估报告；与本 skill 是**互补**关系（本 skill 建"生"的项目安全底座，Unit42 skill 审"活"的系统）

## 九、成功标准（本 skill 自身）

用户走完一次 `/project-kickoff` 后，应当拿到：

1. ✅ 一份自己认可、边界清晰的 PRD 表格（含逐条可验证的 S-XX 安全 NFR）
2. ✅ 一套约束后续代码改动的工程契约（含工程红线 + 安全红线）
3. ✅ 一份从 M0 安全基线开始的模块化实现路径（每个 Unit ≤200 行）
4. ✅ 一叠可直接复制给 Claude Code 的分步提示词（含 security-review checklist）
5. ✅ 心里对"3 个月后做成什么样"以及"哪些安全风险已经被拆掉"有明确画面

如果用户拿完还需要自己重新梳理需求或补安全条款，说明访谈没做够 —— 回到阶段 A/C。
