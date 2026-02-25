---
description: 从外部仓库中批量识别和提取可复用代码模块到知识库
argument-hint: <仓库路径>
---

# Harvest Modules

从外部仓库中批量提取可复用代码模块，注册到知识库。

## 执行流程

**第一步：加载 skill**

你必须先使用 Skill 工具加载 `harvest-modules` skill，然后严格按照其 4 阶段流水线执行。

**第二步：确定目标仓库**

- 如果用户提供了路径，直接使用
- 如果用户提供了 git URL，先 `git clone --depth 1` 到临时目录
- 如果都没提供，询问用户

**第三步：按 harvest-modules skill 流程执行**

严格遵循 skill 中定义的 4 个阶段：

1. **Phase 1** — 结构扫描（主 agent 直接执行，参考 scanner-heuristics.md）
2. **Phase 2** — 候选验证（子 agent 并行，参考 validator-prompt.md）
3. **用户审批门** — 展示候选列表 + 去重结果，等待用户确认
4. **Phase 3** — 并行提取（子 agent 并行，参考 extractor-prompt.md）
5. **Phase 4** — 顺序注册 + 最终报告

**第四步：报告结果**

输出最终的收割摘要。

## 注意事项

- 大仓库不要试图在一个上下文中读完，严格按阶段拆分
- Phase 1 不读源码，只看文件结构
- 子 agent 只读候选文件，不读整个仓库
- register.py 必须顺序执行，不要并行
- 用户审批门是唯一的交互点，不要在每个模块提取后再问

用户指定的仓库路径: $ARGUMENTS
