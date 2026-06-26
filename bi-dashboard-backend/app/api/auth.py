"""
认证接口 — 对应需求文档 4.1
POST /api/v1/auth/login
POST /api/v1/auth/logout
GET  /api/v1/auth/me
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserLogin, TokenOut, UserOut
from app.schemas.common import success_response, error_response
from app.api.deps import require_auth
from app.models.user import User
from app.services.user_service import UserService

router = APIRouter(prefix="/api/v1/auth", tags=["认证"])


@router.post("/login", summary="用户登录")
def login(body: UserLogin, db: Session = Depends(get_db)):
    """
    用户登录接口
    - **username**: 用户名
    - **password**: 密码
    - 返回 JWT access_token 和用户信息
    """
    result = UserService.authenticate(db, body.username, body.password)
    if result is None:
        return error_response(40100, "用户名或密码错误")
    return success_response(result, "登录成功")


@router.post("/logout", summary="用户登出")
def logout(user: User = Depends(require_auth)):
    """
    用户登出接口
    前端清除 token 即可，后端记录登出日志
    """
    return success_response(message="登出成功")


@router.get("/me", summary="获取当前用户信息")
def get_me(user: User = Depends(require_auth)):
    """
    获取当前登录用户的详细信息
    """
    return success_response(user.to_dict())
