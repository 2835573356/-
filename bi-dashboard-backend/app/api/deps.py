"""
API 依赖注入 — 认证、数据库会话、权限校验
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

# HTTP Bearer 认证方案
security_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    获取当前登录用户
    如果请求没有 token，返回 None（用于可选的认证场景）
    """
    if credentials is None:
        return None

    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        return None

    user_id = payload.get("user_id")
    if user_id is None:
        return None

    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    return user


def require_auth(user: Optional[User] = Depends(get_current_user)) -> User:
    """要求必须登录"""
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未认证或 token 已过期，请重新登录",
        )
    return user


def require_admin(user: User = Depends(require_auth)) -> User:
    """要求管理员角色"""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )
    return user


def require_operator_or_above(user: User = Depends(require_auth)) -> User:
    """要求运营及以上角色"""
    if user.role not in ("admin", "operator"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要运营或管理员权限",
        )
    return user
