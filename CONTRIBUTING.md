# 贡献 Skill

## 快速开始

1. Fork 本仓库
2. 在 `skills/` 目录下新建一个子目录，目录名即为 skill 的 ID（如 `skills/my-skill/`）
3. 在该目录内创建 `SKILL.md`，填写 frontmatter（见下）以及 skill 内容
4. 提交 Pull Request

合并后，GitHub Actions 会自动把目录打包为 `.zip` / `.skill`，更新 `skills.json`，页面立即显示你的 skill。

---

## SKILL.md frontmatter 字段

```yaml
---
name: 我的 Skill 名称       # 显示名称（必填）
description: 一句话描述功能  # 卡片描述（必填，建议 50–150 字）
category: 工作流             # 分类（见下方列表）
author: 你的名字             # 作者名
trigger: /my-skill           # 激活命令
icon: 🛠️                    # 卡片图标 emoji
---
```

## 可用分类

`文档` · `数据` · `安全` · `设计` · `工作流` · `翻译` · `研究` · `代码` · `写作` · `其他`

---

## 本地预览

```bash
# 先生成 skills.json
python scripts/generate_manifest.py

# 启动本地服务器（任选一）
python -m http.server 8000
npx serve .
```

然后访问 http://localhost:8000
