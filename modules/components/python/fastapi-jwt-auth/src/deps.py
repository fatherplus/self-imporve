"""
FastAPI JWT Auth - Dependencies Module

FastAPI 依赖注入：数据库 session、当前用户、超级管理员权限。

使用方式：
    # 初始化
    auth_deps = create_auth_deps(
        engine=your_engine,
        secret_key="your-secret",
        token_url="/api/v1/login/access-token",
        user_model=YourUserModel,
        token_payload_model=YourTokenPayloadModel,
    )

    # 在路由中使用
    @router.get("/me")
    def read_me(current_user: auth_deps.CurrentUser):
        return current_user
"""
from collections.abc import Generator
from typing import Annotated, Any, Protocol, runtime_checkable

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlmodel import Session


@runtime_checkable
class UserProtocol(Protocol):
    """用户模型需要实现的接口。"""
    id: Any
    is_active: bool
    is_superuser: bool


class AuthDeps:
    """认证依赖容器，通过工厂函数创建。"""

    def __init__(
        self,
        SessionDep: type,
        TokenDep: type,
        CurrentUser: type,
        get_current_active_superuser: Any,
    ):
        self.SessionDep = SessionDep
        self.TokenDep = TokenDep
        self.CurrentUser = CurrentUser
        self.get_current_active_superuser = get_current_active_superuser


def create_auth_deps(
    engine: Any,
    secret_key: str,
    token_url: str,
    user_model: type,
    token_payload_model: type,
    algorithm: str = "HS256",
) -> AuthDeps:
    """
    创建认证依赖集合。

    Args:
        engine: SQLAlchemy engine
        secret_key: JWT 密钥
        token_url: OAuth2 token 端点路径
        user_model: 用户 ORM 模型（需有 id, is_active, is_superuser 字段）
        token_payload_model: Token payload Pydantic 模型（需有 sub 字段）
        algorithm: JWT 算法
    """
    reusable_oauth2 = OAuth2PasswordBearer(tokenUrl=token_url)

    def get_db() -> Generator[Session, None, None]:
        with Session(engine) as session:
            yield session

    SessionDep = Annotated[Session, Depends(get_db)]
    TokenDep = Annotated[str, Depends(reusable_oauth2)]

    def get_current_user(session: SessionDep, token: TokenDep) -> Any:
        try:
            payload = jwt.decode(token, secret_key, algorithms=[algorithm])
            token_data = token_payload_model(**payload)
        except (InvalidTokenError, ValidationError):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Could not validate credentials",
            )
        user = session.get(user_model, token_data.sub)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if not user.is_active:
            raise HTTPException(status_code=400, detail="Inactive user")
        return user

    CurrentUser = Annotated[user_model, Depends(get_current_user)]

    def get_current_active_superuser(current_user: CurrentUser) -> Any:
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=403, detail="The user doesn't have enough privileges"
            )
        return current_user

    return AuthDeps(
        SessionDep=SessionDep,
        TokenDep=TokenDep,
        CurrentUser=CurrentUser,
        get_current_active_superuser=get_current_active_superuser,
    )
