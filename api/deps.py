"""
API 依赖注入（认证和权限检查）
"""
import config

from typing import Optional, List

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from models import SessionLocal
from models.user import User
from models.permission import Permission
from services.auth import auth_service

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    获取当前认证用户（必须登录）
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = auth_service.verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username = payload.get("sub")
    user = auth_service.get_user_by_username(db, username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用",
        )

    return user


async def get_optional_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    获取当前用户（可选登录，未登录返回None）
    """
    if not token:
        return None

    payload = auth_service.verify_token(token)
    if not payload:
        return None

    username = payload.get("sub")
    user = auth_service.get_user_by_username(db, username)
    if not user or not user.is_active:
        return None

    return user


def require_role(allowed_roles: List[str]):
    """
    角色检查依赖

    用法：
        @router.post("/xxx")
        async def endpoint(current_user: User = Depends(require_role(["admin", "teacher"]))):
            ...
    """
    async def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        user_role = current_user.role.value if hasattr(current_user.role, 'value') else current_user.role
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足，需要角色：{' 或 '.join(allowed_roles)}",
            )
        return current_user

    return role_checker


def require_permission(resource: str, action: str):
    """
    权限检查依赖（资源+操作）

    用法：
        @router.post("/xxx")
        async def endpoint(current_user: User = Depends(require_permission("course", "create"))):
            ...
    """
    async def permission_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        # 检查用户是否拥有所需权限
        has_permission = False
        for role in current_user.roles:
            for perm in role.permissions:
                if perm.resource == resource and perm.action == action:
                    has_permission = True
                    break
                # 管理员拥有所有权限
                if perm.resource == "*" and perm.action == "*":
                    has_permission = True
                    break
            if has_permission:
                break

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足，需要：{resource}:{action}",
            )
        return current_user

    return permission_checker
