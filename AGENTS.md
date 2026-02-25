# Self-Improve 知识库

**语言规则：始终使用中文回答用户问题。**

你有一个个人知识库可用，包含可复用的代码模块，通过 MCP 服务 `self-improve-modules` 按需检索。

## 模块检索

当你需要实现某个功能时，先检索是否有现成模块：

```
1. search_modules(query)            → 返回匹配模块的 name + type + summary
2. get_module_api(name)             → 返回 API 文档（不含源码）
3. install_module(name, target_dir) → 安装到指定路径，返回导入方式
```

模块是黑盒依赖。不要读源码，只看 API，直接安装使用。

## 模块类型

| 类型 | 说明 | 使用方式 |
|------|------|----------|
| utility | 单文件工具函数 | install 后直接 import |
| component | 多文件业务模块 | install 后按 adapt_points 适配 |
| blueprint | 项目架构模板 | 不安装，用 get_module_api 查看架构指导后按蓝图生成 |

## 蒸馏命令

对话结束时，用户可能使用以下命令将经验沉淀到知识库：

- `/distill-skill` — 提炼可复用的经验为 skill，写入知识库仓库
- `/distill-module` — 提炼可复用的代码为 module，注册到知识库仓库

执行时按命令中的指引操作。

## 知识库路径

__REPO_PATH__
