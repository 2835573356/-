"""
帖子相关 Pydantic Schema
"""
from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel, Field


class PostCreate(BaseModel):
    """创建帖子"""
    title: str = Field(..., min_length=1, max_length=500)
    content: Optional[str] = None
    category: str = Field(..., min_length=1, max_length=100)
    priority: str = Field(default="P2", pattern="^(P0|P1|P2)$")
    sentiment: str = Field(..., pattern="^(negative|neutral|positive)$")
    view_count: int = 0
    reply_count: int = 0
    author_name: Optional[str] = None
    source: Optional[str] = None
    tags: Optional[List[str]] = []
    is_anomaly: bool = False
    risk_level: Optional[str] = None
    root_cause_cluster: Optional[str] = None
    keywords: Optional[List[str]] = []
    data_date: date


class PostUpdate(BaseModel):
    """更新帖子"""
    title: Optional[str] = Field(None, max_length=500)
    content: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = Field(None, pattern="^(P0|P1|P2)$")
    sentiment: Optional[str] = Field(None, pattern="^(negative|neutral|positive)$")
    view_count: Optional[int] = None
    reply_count: Optional[int] = None
    author_name: Optional[str] = None
    source: Optional[str] = None
    tags: Optional[List[str]] = None
    is_anomaly: Optional[bool] = None
    risk_level: Optional[str] = None
    root_cause_cluster: Optional[str] = None
    keywords: Optional[List[str]] = None
    data_date: Optional[date] = None


class PostOut(BaseModel):
    """帖子输出"""
    id: int
    title: str
    content: Optional[str] = None
    category: str
    priority: str
    sentiment: str
    view_count: int = 0
    reply_count: int = 0
    author_name: Optional[str] = None
    source: Optional[str] = None
    tags: List[str] = []
    is_anomaly: bool = False
    risk_level: Optional[str] = None
    root_cause_cluster: Optional[str] = None
    keywords: List[str] = []
    data_date: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class PostFilter(BaseModel):
    """帖子筛选参数"""
    keyword: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    sentiment: Optional[str] = None
    risk_level: Optional[str] = None
    data_date_start: Optional[date] = None
    data_date_end: Optional[date] = None
    sort_by: str = "created_at"
    sort_order: str = "desc"
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
