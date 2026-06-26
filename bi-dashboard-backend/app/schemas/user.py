"""
用户相关 Pydantic Schema
"""
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserLogin(BaseModel):
    """登录请求"""
    username: str = Field(..., min_length=2, max_length=100, description="用户名")
    password: str = Field(..., min_length=4, max_length=100, description="密码")


class UserCreate(BaseModel):
    """创建用户"""
    username: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=4, max_length=100)
    role: str = Field(default="viewer", pattern="^(admin|operator|developer|viewer)$")
    display_name: Optional[str] = None
    email: Optional[str] = None


class UserUpdate(BaseModel):
    """更新用户"""
    role: Optional[str] = Field(None, pattern="^(admin|operator|developer|viewer)$")
    display_name: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None


class UserOut(BaseModel):
    """用户输出"""
    id: int
    username: str
    role: str
    display_name: Optional[str] = None
    email: Optional[str] = None
    is_active: bool = True
    last_login_at: Optional[str] = None
    created_at: Optional[str] = None


class TokenOut(BaseModel):
    """Token 输出"""
    access_token: str
    token_type: str = "bearer"
    user: UserOut
