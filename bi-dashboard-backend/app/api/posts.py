"""
帖子管理接口 — 对应需求文档 4.1
GET    /api/v1/posts        帖子列表（分页、筛选）
GET    /api/v1/posts/{id}   帖子详情
POST   /api/v1/posts        新增帖子
PUT    /api/v1/posts/{id}   更新帖子
DELETE /api/v1/posts/{id}   删除帖子
"""
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.post import PostCreate, PostUpdate, PostFilter
from app.schemas.common import success_response, error_response
from app.api.deps import require_auth, require_operator_or_above, require_admin
from app.services.post_service import PostService
from app.utils.date_utils import parse_date

router = APIRouter(prefix="/api/v1/posts", tags=["帖子管理"])


@router.get("", summary="帖子列表")
def list_posts(
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    category: Optional[str] = Query(None, description="问题分类"),
    priority: Optional[str] = Query(None, description="优先级: P0/P1/P2"),
    sentiment: Optional[str] = Query(None, description="情绪: negative/neutral/positive"),
    risk_level: Optional[str] = Query(None, description="风险等级"),
    data_date_start: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    data_date_end: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    sort_by: str = Query("id", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向: asc/desc"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
):
    """
    获取帖子列表，支持关键词搜索、多维度筛选、排序和分页
    """
    start_dt = parse_date(data_date_start) if data_date_start else None
    end_dt = parse_date(data_date_end) if data_date_end else None

    posts, total = PostService.get_list(
        db=db,
        keyword=keyword,
        category=category,
        priority=priority,
        sentiment=sentiment,
        risk_level=risk_level,
        data_date_start=start_dt,
        data_date_end=end_dt,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )

    total_pages = (total + page_size - 1) // page_size

    return success_response({
        "items": posts,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    })


@router.get("/categories-list", summary="获取所有分类")
def get_categories_list(db: Session = Depends(get_db)):
    """获取所有不重复的分类名称"""
    categories = PostService.get_categories_list(db)
    return success_response(categories)


@router.get("/{post_id}", summary="帖子详情")
def get_post(post_id: int, db: Session = Depends(get_db)):
    """
    根据 ID 获取帖子详情
    """
    post = PostService.get_by_id(db, post_id)
    if not post:
        return error_response(40400, f"帖子不存在: id={post_id}")
    return success_response(post.to_dict())


@router.post("", summary="新增帖子", status_code=status.HTTP_201_CREATED)
def create_post(
    body: PostCreate,
    user: User = Depends(require_operator_or_above),
    db: Session = Depends(get_db),
):
    """
    创建新帖子（需要运营或管理员权限）
    """
    post = PostService.create(db, **body.model_dump())
    return success_response(post.to_dict(), "创建成功")


@router.put("/{post_id}", summary="更新帖子")
def update_post(
    post_id: int,
    body: PostUpdate,
    user: User = Depends(require_operator_or_above),
    db: Session = Depends(get_db),
):
    """
    更新帖子信息（需要运营或管理员权限）
    """
    post = PostService.update(db, post_id, **body.model_dump(exclude_none=True))
    if not post:
        return error_response(40400, f"帖子不存在: id={post_id}")
    return success_response(post.to_dict(), "更新成功")


@router.delete("/{post_id}", summary="删除帖子")
def delete_post(
    post_id: int,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    删除帖子（需要管理员权限）
    """
    ok = PostService.delete(db, post_id)
    if not ok:
        return error_response(40400, f"帖子不存在: id={post_id}")
    return success_response(message="删除成功")
