"""
FastAPI JWT Auth - Authentication Module

用户认证（含防时序攻击）和密码重置 token。
"""
from datetime import datetime, timedelta, timezone

import jwt
from jwt.exceptions import InvalidTokenError
from sqlmodel import Session, select

from .security import verify_password, ALGORITHM

# 防时序攻击的虚拟哈希值
# 当用户不存在时，仍然执行密码验证以保持响应时间一致
DUMMY_HASH = "$argon2id$v=19$m=65536,t=3,p=4$MjQyZWE1MzBjYjJlZTI0Yw$YTU4NGM5ZTZmYjE2NzZlZjY0ZWY3ZGRkY2U2OWFjNjk"


def authenticate(
    *,
    session: Session,
    email: str,
    password: str,
    user_model: type,
    email_field: str = "email",
) -> object | None:
    """
    认证用户，含防时序攻击保护。

    当用户不存在时，仍执行密码验证以防止通过响应时间枚举用户。

    Args:
        session: 数据库 session
        email: 用户邮箱
        password: 明文密码
        user_model: 用户 ORM 模型
        email_field: 邮箱字段名
    """
    statement = select(user_model).where(
        getattr(user_model, email_field) == email
    )
    db_user = session.exec(statement).first()

    if not db_user:
        # 防时序攻击：即使用户不存在也执行密码验证
        verify_password(password, DUMMY_HASH)
        return None

    verified, updated_password_hash = verify_password(
        password, db_user.hashed_password
    )
    if not verified:
        return None

    # 如果哈希算法升级，自动更新存储的哈希
    if updated_password_hash:
        db_user.hashed_password = updated_password_hash
        session.add(db_user)
        session.commit()
        session.refresh(db_user)

    return db_user


def generate_password_reset_token(
    email: str,
    secret_key: str,
    algorithm: str = ALGORITHM,
    expire_hours: int = 48,
) -> str:
    """生成密码重置 JWT token。"""
    now = datetime.now(timezone.utc)
    expires = now + timedelta(hours=expire_hours)
    return jwt.encode(
        {"exp": expires.timestamp(), "nbf": now, "sub": email},
        secret_key,
        algorithm=algorithm,
    )


def verify_password_reset_token(
    token: str,
    secret_key: str,
    algorithm: str = ALGORITHM,
) -> str | None:
    """验证密码重置 token，返回 email 或 None。"""
    try:
        decoded = jwt.decode(token, secret_key, algorithms=[algorithm])
        return str(decoded["sub"])
    except InvalidTokenError:
        return None
