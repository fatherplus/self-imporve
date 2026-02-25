"""
FastAPI DB Prestart

数据库预启动工具：
1. wait_for_db: 使用 tenacity 重试等待数据库就绪
2. init_db: 初始化种子数据（如创建超级管理员）

使用方式：
    from fastapi_db_prestart.prestart import wait_for_db, init_db

    # 等待数据库
    wait_for_db(engine)

    # 初始化种子数据
    with Session(engine) as session:
        init_db(session, ...)
"""
import logging
from typing import Any, Callable

from sqlalchemy import Engine
from sqlmodel import Session, select
from tenacity import after_log, before_log, retry, stop_after_attempt, wait_fixed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def wait_for_db(
    engine: Engine,
    max_tries: int = 60 * 5,
    wait_seconds: int = 1,
) -> None:
    """
    等待数据库就绪。

    使用 tenacity 重试机制，默认最多等待 5 分钟。

    Args:
        engine: SQLAlchemy engine
        max_tries: 最大重试次数（默认 300 = 5分钟）
        wait_seconds: 每次重试间隔秒数
    """

    @retry(
        stop=stop_after_attempt(max_tries),
        wait=wait_fixed(wait_seconds),
        before=before_log(logger, logging.INFO),
        after=after_log(logger, logging.WARN),
    )
    def _check() -> None:
        try:
            with Session(engine) as session:
                session.exec(select(1))
        except Exception as e:
            logger.error(e)
            raise e

    logger.info("Waiting for database to be ready...")
    _check()
    logger.info("Database is ready.")


def init_db(
    session: Session,
    *,
    superuser_email: str,
    superuser_password: str,
    user_model: type,
    create_user_fn: Callable[..., Any],
    email_field: str = "email",
) -> None:
    """
    初始化数据库种子数据。

    检查超级管理员是否存在，不存在则创建。

    Args:
        session: 数据库 session
        superuser_email: 超级管理员邮箱
        superuser_password: 超级管理员密码
        user_model: 用户 ORM 模型
        create_user_fn: 创建用户的函数
        email_field: 邮箱字段名

    示例:
        init_db(
            session,
            superuser_email="admin@example.com",
            superuser_password="changethis",
            user_model=User,
            create_user_fn=crud.create_user,
        )
    """
    user = session.exec(
        select(user_model).where(
            getattr(user_model, email_field) == superuser_email
        )
    ).first()

    if not user:
        logger.info(f"Creating superuser: {superuser_email}")
        create_user_fn(
            session=session,
            email=superuser_email,
            password=superuser_password,
            is_superuser=True,
        )
        logger.info("Superuser created.")
    else:
        logger.info("Superuser already exists, skipping.")
