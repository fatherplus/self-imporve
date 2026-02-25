# Scanner Heuristics — Phase 1 启发式扫描规则

Phase 1 的目标是**不读源码**，仅通过文件结构和项目配置识别候选模块。

## 扫描步骤

### Step 1: 识别项目元信息

读取项目根目录的配置文件，确定：

| 配置文件 | 提取信息 |
|----------|----------|
| `package.json` | 语言=typescript/javascript，框架，依赖列表 |
| `pyproject.toml` / `setup.py` / `setup.cfg` | 语言=python，框架，依赖列表 |
| `go.mod` | 语言=go |
| `Cargo.toml` | 语言=rust |
| `tsconfig.json` | TypeScript 项目确认 |
| `docker-compose.yml` | 多服务项目，可能有 blueprint 价值 |

### Step 2: 扫描目录结构

运行 `tree -L 3 -d` 或 `find . -type d -maxdepth 3` 获取目录树。

### Step 3: 按规则匹配候选

## 候选识别规则

### 规则 1: 工具目录（高置信度 → utility）

以下目录名通常包含可复用工具函数：

```
utils/    helpers/    lib/    common/    shared/
tools/    core/       pkg/
```

**判断方式：** 目录内的文件是否命名清晰、自包含（如 `date.ts`、`http.ts`、`logger.py`）

### 规则 2: 独立业务模块目录（中置信度 → component）

目录结构暗示独立模块边界：

```
src/auth/          → 认证模块
src/email/         → 邮件模块
src/payments/      → 支付模块
services/cache/    → 缓存服务
middleware/        → 中间件集合
```

**信号：**
- 目录内有 `index.ts` / `__init__.py`（明确的模块入口）
- 目录内文件数 2-10 个（太少=不值得，太多=可能是整个子系统）
- 目录名是具体功能名（不是 `v1`、`old`、`temp`）

### 规则 3: React Hooks / Composables（高置信度 → utility/component）

```
hooks/use-*.ts       → React custom hooks
composables/use*.ts  → Vue composables
```

单个 hook 文件 → utility，hook + 配套组件 → component

### 规则 4: 配置/设置模式（中置信度 → utility）

```
config/settings.py      → 配置管理
src/config/             → 配置模块
*.config.ts             → 配置工具
```

### 规则 5: 项目级架构（低置信度 → blueprint）

整个项目的目录结构本身有参考价值：

**信号：**
- 有 `docker-compose.yml` + 多个服务目录
- 有 CI/CD 配置（`.github/workflows/`、`Dockerfile`）
- 前后端分离结构（`frontend/` + `backend/`）
- 有数据库迁移目录（`alembic/`、`migrations/`）

**注意：** blueprint 候选需要整个项目有清晰的架构模式，不是随便一个项目都值得提取。

## 排除规则（跳过这些）

| 跳过 | 原因 |
|------|------|
| `test/`、`tests/`、`__tests__/`、`spec/` | 测试代码不可复用 |
| `node_modules/`、`.venv/`、`vendor/` | 第三方依赖 |
| `dist/`、`build/`、`out/`、`.next/` | 构建产物 |
| `docs/`、`examples/`、`scripts/` | 文档和脚本通常不可复用 |
| `.git/`、`.idea/`、`.vscode/` | IDE/VCS 配置 |
| 文件名含 `mock`、`fixture`、`stub` | 测试辅助 |
| 超过 20 个文件的目录 | 可能是整个子系统，粒度太大 |

## 输出格式

扫描完成后，输出候选列表：

```json
[
  {
    "path": "src/utils/http-client.ts",
    "reason": "自包含工具文件，命名清晰",
    "estimated_type": "utility",
    "lang": "typescript",
    "confidence": "high"
  },
  {
    "path": "src/auth/",
    "reason": "独立模块目录，含 index.ts 入口，4 个文件",
    "estimated_type": "component",
    "lang": "typescript",
    "confidence": "medium"
  }
]
```

## 注意事项

- **宁可多选不要漏选** — Phase 2 的验证子 agent 会过滤掉不合适的
- **不要读源码** — 这一步只看文件名和目录结构
- **标注置信度** — 帮助用户在审批门做决策
- **monorepo 特殊处理** — 如果是 monorepo（`packages/`、`apps/`），对每个 package 单独扫描
