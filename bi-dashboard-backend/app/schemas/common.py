"""
通用 Pydantic Schema — 对应需求文档 4.3 通用响应格式
"""
from typing import Optional, Any
from pydantic import BaseModel


class APIResponse(BaseModel):
    """通用 API 响应格式"""
    code: int = 0
    data: Optional[Any] = None
    message: str = "ok"

    class Config:
        json_schema_extra = {
            "example": {
                "code": 0,
                "data": {},
                "message": "ok"
            }
        }


class PaginatedData(BaseModel):
    """分页数据"""
    items: list = []
    total: int = 0
    page: int = 1
    page_size: int = 20
    total_pages: int = 0


class PaginatedResponse(BaseModel):
    """分页响应"""
    code: int = 0
    data: PaginatedData = PaginatedData()
    message: str = "ok"


def success_response(data: Any = None, message: str = "ok") -> dict:
    """构建成功响应"""
    return {"code": 0, "data": data, "message": message}


def error_response(code: int, message: str) -> dict:
    """构建错误响应"""
    return {"code": code, "data": None, "message": message}
