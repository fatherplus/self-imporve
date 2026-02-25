---
description: 读取 git-master skill 对当前仓库进行一次 commit
argument-hint: <可选：commit 补充说明>
---

# Commit

使用 git-master skill 对当前仓库执行一次规范的 commit。

## 执行流程

**第一步：加载 skill**

你必须先使用 Skill 工具加载 `git-master` skill，然后严格按照其流程执行。

**第二步：按 git-master 流程执行**

严格遵循 git-master skill 中定义的所有阶段：

1. **Phase 0** — 并行收集上下文（git status, git diff, git log 等）
2. **Phase 1** — 风格检测（语言、commit 风格），**必须输出检测结果**
3. **Phase 3** — 原子单元规划，**必须输出 commit 计划**
4. **Phase 4** — 策略决策（fixup / new commit / reset rebuild）
5. **Phase 5** — 执行 commit
6. **Phase 6** — 验证与报告

**第三步：报告结果**

输出最终的 commit 摘要。

## 注意事项

- 如果没有任何变更（git status 干净），直接告知用户，不要创建空 commit
- 遵循仓库现有的 commit 风格，不要自作主张用 conventional commits
- 多文件变更必须拆分为多个原子 commit，严格遵守 git-master 的拆分规则

用户补充说明: $ARGUMENTS
