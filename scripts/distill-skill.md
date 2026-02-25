---
description: 蒸馏本次对话经验为可复用的 skill
argument-hint: <可选：主题描述>
---

# 蒸馏 Skill

分析本次对话，提取可复用的经验，生成 SKILL.md 并注册到知识库。

## 蒸馏流程

**第一步：分析对话**

回顾本次对话，识别：
- 解决了什么核心问题
- 哪些经验是跨项目可复用的（不是一次性方案）
- 踩了什么坑、总结了什么最佳实践

**第二步：判断分类**

| 分类 | 适用场景 |
|------|----------|
| python | Python 语言相关经验 |
| typescript | TypeScript/前端相关经验 |
| devops | 部署、CI/CD、Docker 相关 |
| general | 跨语言通用经验 |

**第三步：生成 SKILL.md 草稿**

展示给用户确认，格式：

```markdown
---
name: <kebab-case-name>
description: Use when <触发条件，不描述内容>
---

# <标题>

## 核心原则
<1-2 句话>

## 具体做法
<步骤或模式>

## 常见错误
<踩坑点>
```

**第四步：写入知识库**

确认后执行：
1. 写入 `__REPO_PATH__/skills/<category>/<skill-name>/SKILL.md`
2. 运行 `bash __REPO_PATH__/scripts/sync.sh` 同步到 opencode
3. git add + commit

## 不值得蒸馏的内容

- 一次性的项目特定方案
- 标准文档已有的内容
- 过于简单无需记录的操作

用户主题: $ARGUMENTS
