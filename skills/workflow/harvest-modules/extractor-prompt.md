# Extractor Subagent Prompt Template

Phase 3 提取子 agent 的提示词模板。每个子 agent 负责提取一个已批准的模块。

## 使用方式

```
task(
  category="unspecified-low",
  load_skills=[],
  run_in_background=true,
  description="提取模块: {module.name}",
  prompt=<按下方模板填充>
)
```

## 提示词模板

```
你正在从一个外部仓库中提取可复用代码模块，写入知识库。

## 模块信息（来自验证阶段）

- 模块名: {module.name}
- 类型: {module.type} (utility / component / blueprint)
- 语言: {module.lang}
- 摘要: {module.summary}
- 标签: {module.tags}
- 源文件: {module.files}
- 第三方依赖: {module.dependencies}
- API 表面: {module.api_surface}
- 需要泛化的点: {module.generalization_notes}

## 仓库路径

- 源仓库: {repo_path}
- 知识库: {kb_repo_path}  (即 __REPO_PATH__)

## 你的任务

### 1. 读取源文件

读取上面列出的所有源文件。

### 2. 泛化代码

将业务特定的代码转化为通用可复用模块：

| 泛化操作 | 示例 |
|----------|------|
| 硬编码配置 → 参数/adapt_point | `API_URL = "https://myapp.com"` → 提取为配置参数 |
| 业务模型名 → 通用名 | `UserOrder` → 泛化或标记为 adapt_point |
| 项目特定 import → 相对 import | `from myapp.utils` → 调整为模块内部引用 |
| 删除无关代码 | 移除与模块核心功能无关的业务逻辑 |

**泛化原则：**
- 保留核心功能逻辑不变
- 只修改业务耦合的部分
- 不要过度抽象 — 保持代码可读
- 如果某处无法简单泛化，标记为 adapt_point

### 3. 生成 manifest.json

按以下 schema 生成：

```json
{
  "name": "{module.name}",
  "type": "{module.type}",
  "lang": "{module.lang}",
  "summary": "{module.summary}",
  "tags": ["{tag1}", "{tag2}"],
  "api": {
    "模块分组名": {
      "function_signature": "功能描述"
    }
  },
  "install": {
    "dependencies": ["dep1>=version"],
    "entry": "from module_name import xxx"
  }
}
```

component 类型额外添加 `adapt_points` 数组。
blueprint 类型额外添加 `design_decisions` 数组。

### 4. 写入知识库

目标目录结构：

```
{kb_repo_path}/modules/{type}s/{lang}/{name}/
├── manifest.json
└── src/
    ├── {泛化后的源文件}
    └── ...
```

注意目录层级：
- utility → `modules/utilities/{lang}/{name}/`
- component → `modules/components/{lang}/{name}/`
- blueprint → `modules/blueprints/{lang}/{name}/`

### 5. 报告结果

完成后返回：

```json
{
  "name": "模块名",
  "status": "success / failed",
  "path": "写入的目录路径",
  "files_written": ["文件列表"],
  "generalization_changes": ["做了哪些泛化修改"],
  "adapt_points": ["需要用户适配的点"],
  "notes": "其他备注"
}
```

## 约束

- 不要运行 register.py（主 agent 会顺序执行）
- 不要修改源仓库的任何文件
- 不要添加源文件中没有的功能
- manifest.json 的 tags 不要放泛泛的词（tool、helper、utils）
- summary 要具体，用于语义搜索
- 如果遇到无法处理的情况，返回 status: "failed" 并说明原因
```
