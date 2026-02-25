"""
SQLModel CRUD Pattern - CRUD Functions

通用 CRUD 操作函数模式。

核心模式：
- model_validate + update: 创建时合并额外字段
- model_dump(exclude_unset=True) + sqlmodel_update: 部分更新
- select + func.count + offset/limit: 分页查询
"""
from typing import Any, TypeVar
from uuid import UUID

from sqlmodel import Session, col, func, select, SQLModel

T = TypeVar("T", bound=SQLModel)


def create_entity(
    *,
    session: Session,
    entity_create: SQLModel,
    model_class: type[T],
    extra_data: dict[str, Any] | None = None,
) -> T:
    """
    创建实体。

    Args:
        session: 数据库 session
        entity_create: 创建输入模型实例
        model_class: 目标 ORM 模型类
        extra_data: 额外字段（如 owner_id, hashed_password）

    示例:
        item = create_entity(
            session=session,
            entity_create=item_in,
            model_class=Item,
            extra_data={"owner_id": current_user.id},
        )
    """
    db_obj = model_class.model_validate(
        entity_create, update=extra_data or {}
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_entity(
    *,
    session: Session,
    db_entity: T,
    entity_update: SQLModel,
    extra_data: dict[str, Any] | None = None,
) -> T:
    """
    更新实体（仅更新传入的字段）。

    使用 exclude_unset=True 确保只更新显式传入的字段。

    示例:
        user = update_entity(
            session=session,
            db_entity=db_user,
            entity_update=user_in,
            extra_data={"hashed_password": new_hash},
        )
    """
    update_data = entity_update.model_dump(exclude_unset=True)
    if extra_data:
        update_data.update(extra_data)
    db_entity.sqlmodel_update(update_data)
    session.add(db_entity)
    session.commit()
    session.refresh(db_entity)
    return db_entity


def get_entity_by_field(
    *,
    session: Session,
    model_class: type[T],
    field_name: str,
    value: Any,
) -> T | None:
    """
    按字段查询单个实体。

    示例:
        user = get_entity_by_field(
            session=session,
            model_class=User,
            field_name="email",
            value="user@example.com",
        )
    """
    statement = select(model_class).where(
        getattr(model_class, field_name) == value
    )
    return session.exec(statement).first()


def list_entities(
    *,
    session: Session,
    model_class: type[T],
    skip: int = 0,
    limit: int = 100,
    order_by_field: str = "created_at",
    order_desc: bool = True,
    filter_field: str | None = None,
    filter_value: Any = None,
) -> tuple[list[T], int]:
    """
    分页列表查询。

    返回 (entities, total_count)。

    示例:
        items, count = list_entities(
            session=session,
            model_class=Item,
            skip=0,
            limit=10,
            filter_field="owner_id",
            filter_value=current_user.id,
        )
    """
    base_query = select(model_class)
    count_query = select(func.count()).select_from(model_class)

    if filter_field and filter_value is not None:
        condition = getattr(model_class, filter_field) == filter_value
        base_query = base_query.where(condition)
        count_query = count_query.where(condition)

    count = session.exec(count_query).one()

    if order_desc:
        base_query = base_query.order_by(
            col(getattr(model_class, order_by_field)).desc()
        )
    else:
        base_query = base_query.order_by(
            col(getattr(model_class, order_by_field)).asc()
        )

    entities = session.exec(base_query.offset(skip).limit(limit)).all()
    return list(entities), count
