"""
SQLModel CRUD Pattern - Models

四层模型分离模式示例：
- Base: 共享属性（用于创建和更新）
- Create: 创建时的输入（继承 Base，可添加密码等额外字段）
- Update: 更新时的输入（字段全部可选）
- Table Model: 数据库表（继承 Base，添加 id、时间戳）
- Public: API 返回（继承 Base，添加 id）
- ListPublic: 分页列表返回（data + count）

使用方式：
    参考此模板定义你自己的模型，保持四层分离模式。
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlmodel import Field, SQLModel


def get_datetime_utc() -> datetime:
    """获取 UTC 当前时间。"""
    return datetime.now(timezone.utc)


# === 示例：Entity 模型 ===

class EntityBase(SQLModel):
    """共享属性，用于创建和读取。"""
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


class EntityCreate(EntityBase):
    """创建时的输入模型。直接继承 Base，可添加额外字段。"""
    pass


class EntityUpdate(EntityBase):
    """更新时的输入模型。所有字段可选（exclude_unset 模式）。"""
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore


class Entity(EntityBase, table=True):
    """数据库表模型。"""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


class EntityPublic(EntityBase):
    """API 返回模型。"""
    id: uuid.UUID
    created_at: datetime | None = None


class EntitiesPublic(SQLModel):
    """分页列表返回模型。"""
    data: list[EntityPublic]
    count: int


# === 通用响应模型 ===

class Message(SQLModel):
    """通用消息响应。"""
    message: str
