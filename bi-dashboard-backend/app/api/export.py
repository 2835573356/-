"""
数据导出接口 — 对应需求文档 4.2.9
GET /api/v1/export/posts      导出帖子数据 (CSV/Excel)
GET /api/v1/export/dashboard  导出看板报告 (JSON)
"""
from datetime import date, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.api.deps import require_auth
from app.services.post_service import PostService
from app.services.export_service import ExportService
from app.services.dashboard_service import DashboardService
from app.schemas.common import success_response, error_response
from app.utils.date_utils import parse_date, today

router = APIRouter(prefix="/api/v1/export", tags=["数据导出"])


@router.get("/posts", summary="导出帖子数据")
def export_posts(
    format: str = Query("csv", description="导出格式: csv 或 excel"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    category: Optional[str] = Query(None, description="问题分类"),
    priority: Optional[str] = Query(None, description="优先级"),
    sentiment: Optional[str] = Query(None, description="情绪"),
    data_date_start: Optional[str] = Query(None, description="开始日期"),
    data_date_end: Optional[str] = Query(None, description="结束日期"),
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """
    导出帖子数据为 CSV 或 Excel 格式
    """
    start_dt = parse_date(data_date_start) if data_date_start else None
    end_dt = parse_date(data_date_end) if data_date_end else None

    # 导出全部符合条件的数据（上限 10000 条）
    posts, total = PostService.get_list(
        db=db,
        keyword=keyword,
        category=category,
        priority=priority,
        sentiment=sentiment,
        data_date_start=start_dt,
        data_date_end=end_dt,
        page=1,
        page_size=10000,
    )

    if format == "excel":
        output = ExportService.export_posts_excel(posts)
        filename = "posts_export.xlsx"
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        output = ExportService.export_posts_csv(posts)
        filename = "posts_export.csv"
        media_type = "text/csv; charset=utf-8-sig"

    return StreamingResponse(
        output,
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        },
    )


@router.get("/dashboard", summary="导出看板数据")
def export_dashboard(
    target_date: Optional[str] = Query(None, description="目标日期 YYYY-MM-DD"),
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """
    导出看板数据为 JSON 格式（前端可根据此生成 PDF）
    """
    dt = parse_date(target_date) if target_date else today()

    summary = DashboardService.get_summary(db, dt)
    trend = DashboardService.get_trend(db, dt - timedelta(days=6), dt)
    sentiment = DashboardService.get_sentiment(db, dt)
    categories = DashboardService.get_categories(db, dt)
    hot_posts = DashboardService.get_hot_posts(db, dt)
    root_cause = DashboardService.get_root_cause(db, dt)
    insights = DashboardService.get_insights(db, dt)
    risk_alerts = DashboardService.get_risk_alerts(db, dt)

    return success_response({
        "date": dt.isoformat(),
        "summary": summary,
        "trend": trend,
        "sentiment": sentiment,
        "categories": categories,
        "hot_posts": hot_posts,
        "root_cause": root_cause,
        "insights": insights,
        "risk_alerts": risk_alerts,
    })
