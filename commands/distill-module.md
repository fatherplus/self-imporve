---
description: 蒸馏本次对话中的可复用代码为 module，注册到知识库
argument-hint: <可选：模块描述>
---

# 蒸馏 Module

分析本次对话，提取可复用的代码模块，创建 manifest 并注册到知识库。

## 蒸馏流程

**第一步：识别可复用代码**

回顾本次对话中编写的代码，识别：
- 哪些代码是通用的、跨项目可复用的
- 不是业务特定的一次性代码
- 有清晰的输入输出接口

**第二步：判断模块类型**

| 类型 | 判断标准 |
|------|----------|
| utility | 单文件工具函数，无外部状态依赖 |
| component | 多文件业务模块，有适配点 |
| blueprint | 项目级架构模板，不含具体实现 |

**第三步：生成 manifest.json 草稿**

展示给用户确认。manifest 必须包含：

- `name`: kebab-case 模块名
- `type`: utility / component / blueprint
- `lang`: python / typescript / shared
- `summary`: 一句话描述（用于语义搜索）
- `tags`: 关键词数组（用于精准匹配）
- `api`: API 定义（utility/component 必填）
- `install.dependencies`: 第三方依赖列表
- `install.entry`: 导入语句示例

component 额外需要 `adapt_points` 数组。
blueprint 额外需要 `design_decisions` 数组。

**第四步：写入知识库**

确认后执行：

1. 创建模块目录：
   - utility: `__REPO_PATH__/modules/utilities/<lang>/<name>/`
   - component: `__REPO_PATH__/modules/components/<lang>/<name>/`
   - blueprint: `__REPO_PATH__/modules/blueprints/<lang>/<name>/`（跨语言模板用 `shared` 作为 lang）

2. 写入 `manifest.json` 和 `src/` 目录下的源码文件

3. 注册到 registry：
   ```bash
    python __REPO_PATH__/commands/register.py modules/<type>/<lang>/<name>
   ```


## tags 设计原则

tags 用于精准匹配，应包含：
- 核心功能词：auth, http, cache, log
- 框架名：fastapi, react, express
- 技术关键词：jwt, websocket, orm

不要放泛泛的词如 "tool", "helper", "utils"。

用户主题: $ARGUMENTS
