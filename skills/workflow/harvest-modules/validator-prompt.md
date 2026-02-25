# Validator Subagent Prompt Template

Phase 2 候选验证子 agent 的提示词模板。每个子 agent 负责验证 1-3 个候选模块。

## 使用方式

```
task(
  category="deep",
  load_skills=[],
  run_in_background=true,
  description="验证候选模块: {candidate_paths}",
  prompt=<按下方模板填充>
)
```

## 提示词模板

```
你正在为一个代码知识库评估候选模块的复用价值。

## 候选模块

{对每个候选，列出：}
- 路径: {candidate.path}
- 扫描理由: {candidate.reason}
- 预估类型: {candidate.estimated_type}
- 语言: {candidate.lang}

## 仓库信息

- 仓库路径: {repo_path}
- 项目框架: {framework}（如 FastAPI、React、Express 等）

## 你的任务

对每个候选，执行以下评估：

### 1. 读取候选文件

- 只读候选路径下的文件（目录候选读取目录内所有文件）
- 追踪本地 import：如果候选文件 import 了同仓库内的其他文件，也读取那些文件
- 在第三方依赖处停止（不追踪 node_modules / site-packages 等）
- 总共不要读超过 15 个文件

### 2. 评估复用价值

判断标准：

| 维度 | 可复用 | 不可复用 |
|------|--------|----------|
| 业务耦合 | 通用逻辑，不依赖特定业务实体 | 引用具体业务模型（User、Order 等） |
| 接口清晰度 | 有明确的输入/输出，可独立使用 | 深度嵌入应用上下文，无法独立运行 |
| 泛化难度 | 少量参数化即可通用 | 需要大量重写才能通用 |
| 复用频率 | 跨项目常见需求（auth、http、cache） | 一次性或极小众需求 |

### 3. 确定模块边界

如果候选可复用，确定：
- 哪些文件属于这个模块（最小必要集合）
- 模块的 API 表面（导出了什么函数/类/类型）
- 第三方依赖列表
- 需要泛化的点（硬编码的配置、业务特定的类型名等）

### 4. 输出评估结果

对每个候选，返回以下 JSON：

```json
{
  "path": "原始候选路径",
  "reusable": true/false,
  "reason": "判断理由（1-2 句话）",
  "name": "建议的模块名（kebab-case）",
  "type": "utility / component / blueprint",
  "lang": "python / typescript / shared",
  "summary": "一句话描述（用于语义搜索）",
  "tags": ["关键词1", "关键词2"],
  "files": ["属于该模块的文件路径列表"],
  "dependencies": ["第三方依赖列表"],
  "api_surface": "主要导出的函数/类/类型（简要描述）",
  "generalization_notes": "需要泛化的点"
}
```

如果不可复用：

```json
{
  "path": "原始候选路径",
  "reusable": false,
  "reason": "不可复用的原因"
}
```

## 约束

- 不要读取候选路径之外的代码（除了追踪本地 import）
- 不要修改任何文件
- 不要运行任何命令
- 如果无法判断，标记为 reusable: false 并说明原因
- 宁可严格不要宽松 — 质量比数量重要
```
