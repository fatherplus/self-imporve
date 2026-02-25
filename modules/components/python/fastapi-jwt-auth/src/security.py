"""
FastAPI JWT Auth - Security Module

密码哈希（Argon2 + Bcrypt 双哈希器）和 JWT token 生成。
"""
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from pwdlib.hashers.bcrypt import BcryptHasher

# 双哈希器：Argon2 为主，Bcrypt 为兼容迁移
password_hash = PasswordHash(
    (
        Argon2Hasher(),
        BcryptHasher(),
    )
)

ALGORITHM = "HS256"


def create_access_token(
    subject: str | Any,
    expires_delta: timedelta,
    secret_key: str,
    algorithm: str = ALGORITHM,
) -> str:
    """生成 JWT access token。"""
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"exp": expire, "sub": str(subject)}
    return jwt.encode(to_encode, secret_key, algorithm=algorithm)


def verify_password(
    plain_password: str, hashed_password: str
) -> tuple[bool, str | None]:
    """
    验证密码并检查是否需要 rehash。
    返回 (是否匹配, 更新后的hash或None)。
    """
    return password_hash.verify_and_update(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """生成密码哈希（默认 Argon2）。"""
    return password_hash.hash(password)
