# 全栈 FastAPI 项目架构蓝图

## 项目结构

```
project/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py          # FastAPI 依赖注入（DB session, 认证）
│   │   │   ├── main.py          # API 路由注册
│   │   │   └── routes/          # 按领域分组的路由模块
│   │   │       ├── login.py     # 认证路由（token, 密码重置）
│   │   │       ├── users.py     # 用户管理路由
│   │   │       ├── items.py     # 业务实体路由（示例）
│   │   │       ├── utils.py     # 工具路由（健康检查, 测试邮件）
│   │   │       └── private.py   # 仅 local 环境的调试路由
│   │   ├── core/
│   │   │   ├── config.py        # Pydantic Settings 配置
│   │   │   ├── db.py            # 数据库引擎 + 初始化
│   │   │   └── security.py      # 密码哈希 + JWT
│   │   ├── alembic/             # 数据库迁移
│   │   ├── email-templates/     # 邮件模板（MJML → HTML）
│   │   ├── models.py            # SQLModel 模型（四层分离）
│   │   ├── crud.py              # CRUD 操作函数
│   │   ├── utils.py             # 邮件发送等工具
│   │   ├── main.py              # FastAPI app 入口
│   │   └── tests_pre_start.py   # 数据库连接重试
│   ├── tests/                   # Pytest 测试
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── client/              # 自动生成的 API 客户端
│   │   ├── components/
│   │   │   ├── ui/              # shadcn/ui 基础组件
│   │   │   ├── Common/          # 通用业务组件
│   │   │   └── [Feature]/       # 按功能分组的业务组件
│   │   ├── hooks/               # 自定义 hooks
│   │   ├── routes/              # TanStack Router 文件路由
│   │   │   ├── __root.tsx       # 根布局
│   │   │   ├── _layout.tsx      # 认证保护布局
│   │   │   ├── _layout/         # 受保护页面
│   │   │   ├── login.tsx        # 登录页
│   │   │   └── signup.tsx       # 注册页
│   │   ├── main.tsx             # 入口（QueryClient, Router, Theme）
│   │   └── utils.ts             # 工具函数
│   ├── tests/                   # Playwright E2E 测试
│   ├── Dockerfile
│   └── package.json
├── compose.yml                  # Docker Compose 生产配置
├── compose.override.yml         # 开发环境覆盖
├── compose.traefik.yml          # Traefik 配置
├── .env                         # 环境变量
└── .github/workflows/           # CI/CD
```

## Docker Compose 编排模式

```
db (PostgreSQL)
  ↓ healthcheck
prestart (运行迁移 + 种子数据)
  ↓ service_completed_successfully
backend (FastAPI)
  ↓
frontend (React + Nginx)
  ↓
traefik (反向代理 + HTTPS)
```

关键点：
- `prestart` 服务在 db 健康检查通过后运行 `alembic upgrade head` + `init_db`
- `backend` 在 prestart 成功完成后才启动
- Traefik 通过 Docker 标签自动发现服务并配置路由

## 认证流程

### 后端
1. 用户提交 email + password → `/login/access-token`
2. 验证密码（Argon2/Bcrypt，含防时序攻击）
3. 生成 JWT access token（HS256）
4. 后续请求通过 `Authorization: Bearer <token>` 认证
5. `get_current_user` 依赖解码 token 并查询用户

### 前端
1. 登录成功 → token 存入 localStorage
2. `OpenAPI.TOKEN` resolver 自动注入 token 到所有请求
3. QueryClient 全局拦截 401/403 → 清除 token → 跳转登录页
4. `useAuth` hook 提供 login/signup/logout + 当前用户状态

## 模型分层模式（SQLModel）

```python
# 1. Base - 共享属性
class EntityBase(SQLModel):
    title: str
    description: str | None = None

# 2. Create - 创建输入
class EntityCreate(EntityBase):
    pass  # 或添加 password 等额外字段

# 3. Update - 更新输入（字段可选）
class EntityUpdate(EntityBase):
    title: str | None = None  # type: ignore

# 4. Table - 数据库模型
class Entity(EntityBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime | None = Field(default_factory=get_datetime_utc)

# 5. Public - API 返回
class EntityPublic(EntityBase):
    id: uuid.UUID
    created_at: datetime | None = None

# 6. ListPublic - 分页列表
class EntitiesPublic(SQLModel):
    data: list[EntityPublic]
    count: int
```

## OpenAPI 客户端自动生成

```bash
# 1. 启动后端获取 OpenAPI schema
# 2. 运行生成命令
cd frontend && bun run generate-client
# 使用 @hey-api/openapi-ts 从 openapi.json 生成：
#   - types.gen.ts (TypeScript 类型)
#   - sdk.gen.ts (服务类)
#   - schemas.gen.ts (JSON Schema)
```

## CI/CD 工作流

- `test-backend.yml`: 后端 pytest
- `playwright.yml`: 前端 E2E 测试
- `test-docker-compose.yml`: Docker Compose 集成测试
- `deploy-staging.yml`: 部署到 staging
- `deploy-production.yml`: 部署到 production
- `pre-commit.yml`: 代码格式检查

## 技术栈

| 层 | 技术 |
|---|------|
| 后端框架 | FastAPI |
| ORM | SQLModel (SQLAlchemy + Pydantic) |
| 数据库 | PostgreSQL |
| 迁移 | Alembic |
| 认证 | JWT (PyJWT) + Argon2/Bcrypt (pwdlib) |
| 前端框架 | React 19 |
| 路由 | TanStack Router |
| 状态管理 | TanStack Query |
| UI 组件 | shadcn/ui (Radix + Tailwind) |
| 构建 | Vite |
| E2E 测试 | Playwright |
| 容器 | Docker Compose |
| 反向代理 | Traefik |
