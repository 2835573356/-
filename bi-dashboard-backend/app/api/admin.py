"""
系统管理接口 — 对应需求文档 4.1
用户管理 / 系统配置 / 数据刷新
"""
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.api.deps import require_admin
from app.schemas.user import UserCreate, UserUpdate
from app.schemas.common import success_response, error_response
from app.services.user_service import UserService
from app.services.analysis_service import AnalysisService
from app.services.alert_service import AlertService
from app.utils.cache import cache, invalidate_cache
from app.utils.date_utils import today, parse_date, yesterday

router = APIRouter(prefix="/api/v1/admin", tags=["系统管理"])


# ---- 用户管理 ----

@router.get("/users", summary="用户列表")
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """获取用户列表（需要管理员权限）"""
    users, total = UserService.get_all(db, page=page, page_size=page_size)
    total_pages = (total + page_size - 1) // page_size
    return success_response({
        "items": users,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    })


@router.post("/users", summary="创建用户")
def create_user(
    body: UserCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """创建新用户"""
    existing = UserService.get_by_username(db, body.username)
    if existing:
        return error_response(40001, f"用户名已存在: {body.username}")

    user = UserService.create(
        db,
        username=body.username,
        password=body.password,
        role=body.role,
        display_name=body.display_name,
        email=body.email,
    )
    return success_response(user.to_dict(), "用户创建成功")


@router.put("/users/{user_id}", summary="更新用户")
def update_user(
    user_id: int,
    body: UserUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """更新用户信息"""
    user = UserService.update(db, user_id, **body.model_dump(exclude_none=True))
    if not user:
        return error_response(40400, f"用户不存在: id={user_id}")
    return success_response(user.to_dict(), "更新成功")


@router.delete("/users/{user_id}", summary="删除用户")
def delete_user(
    user_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """删除用户"""
    if user_id == admin.id:
        return error_response(40001, "不能删除自己")
    ok = UserService.delete(db, user_id)
    if not ok:
        return error_response(40400, f"用户不存在: id={user_id}")
    return success_response(message="删除成功")


# ---- 告警管理 ----

@router.get("/alerts", summary="告警列表")
def list_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="状态: active/resolved/ignored"),
    priority: Optional[str] = Query(None, description="优先级: P0/P1/P2"),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """获取告警列表"""
    alerts, total = AlertService.get_all_alerts(
        db, page=page, page_size=page_size, status=status, priority=priority
    )
    total_pages = (total + page_size - 1) // page_size
    return success_response({
        "items": alerts,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    })


@router.put("/alerts/{alert_id}/resolve", summary="标记告警已解决")
def resolve_alert(
    alert_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """标记告警为已解决"""
    alert = AlertService.resolve(db, alert_id)
    if not alert:
        return error_response(40400, f"告警不存在: id={alert_id}")
    cache.delete_pattern("dashboard:risk")
    return success_response(alert.to_dict(), "告警已标记为已解决")


@router.put("/alerts/{alert_id}/ignore", summary="忽略告警")
def ignore_alert(
    alert_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """忽略告警"""
    alert = AlertService.ignore(db, alert_id)
    if not alert:
        return error_response(40400, f"告警不存在: id={alert_id}")
    cache.delete_pattern("dashboard:risk")
    return success_response(alert.to_dict(), "告警已忽略")


# ---- 数据管理 ----

@router.post("/data/refresh", summary="手动触发数据刷新")
def refresh_data(
    target_date: Optional[str] = Query(None, description="目标日期 YYYY-MM-DD，默认昨天"),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    手动触发日汇总数据刷新
    重新计算指定日期的 DailySummary
    """
    dt = parse_date(target_date) if target_date else yesterday()
    summary = AnalysisService.generate_daily_summary(db, dt)

    # 清除所有看板缓存
    invalidate_cache("dashboard:")

    if summary:
        return success_response(summary.to_dict(), f"数据刷新成功: {dt.isoformat()}")
    else:
        return error_response(40400, f"日期 {dt.isoformat()} 没有帖子数据")


@router.post("/data/refresh-range", summary="批量刷新数据")
def refresh_data_range(
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """批量刷新日期范围内的汇总数据"""
    from datetime import timedelta

    start = parse_date(start_date) if start_date else yesterday() - timedelta(days=7)
    end = parse_date(end_date) if end_date else yesterday()

    results = []
    current = start
    while current <= end:
        summary = AnalysisService.generate_daily_summary(db, current)
        results.append({
            "date": current.isoformat(),
            "success": summary is not None,
            "total_posts": summary.total_posts if summary else 0,
        })
        current += timedelta(days=1)

    invalidate_cache("dashboard:")
    return success_response(results, f"批量刷新完成: {len(results)} 天")


@router.get("/config", summary="系统配置")
def get_config(admin: User = Depends(require_admin)):
    """获取系统配置（示例）"""
    return success_response({
        "enable_scheduler": True,
        "daily_summary_time": "02:00",
        "cache_ttl": {
            "summary": 300,
            "trend": 600,
            "sentiment": 300,
            "hot_posts": 120,
        },
        "version": "1.0.0",
    })
