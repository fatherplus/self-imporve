# OpenCode 集成配置

## 前置条件

- OpenCode + oh-my-opencode 已安装
- Python 3.11+
- `pip install mcp`

## 1. 注册 MCP Server

在 opencode 配置中添加 MCP server，让 agent 能调用模块检索工具。

编辑 `~/.config/opencode/opencode.json`，添加 `mcpServers` 字段：

```json
{
  "mcpServers": {
    "self-improve-modules": {
      "command": "python",
      "args": ["/path/to/self-imporve/mcp-server/server.py"]
    }
  }
}
```

将 `/path/to/self-imporve` 替换为仓库实际路径。

## 2. 同步 Skills

运行同步脚本，将 skills 链接到 opencode skills 目录：

```bash
cd /path/to/self-imporve
bash scripts/sync.sh
```

同步后 skills 出现在 `~/.config/opencode/skills/self-improve/` 下，
opencode 启动时自动发现并加载 description 到 system prompt。

## 3. 一键同步（Skills + Commands）

运行同步脚本会自动完成 AGENTS.md 注入、Skills 链接、Commands 链接：

```bash
cd /path/to/self-imporve
bash scripts/sync.sh
```

同步后可用的命令：
- `/distill-skill` — 蒸馏对话经验为 skill
- `/distill-module` — 蒸馏代码为 module

## 4. Git 版本管理

```bash
cd /path/to/self-imporve
git init
git add .
git commit -m "init: self-improve knowledge base"
git remote add origin <your-repo-url>
git push -u origin main
```

更新知识库后：
```bash
git add .
git commit -m "feat: add new module/skill"
git push
```

其他机器拉取更新：
```bash
cd /path/to/self-imporve
git pull
bash scripts/sync.sh
```
