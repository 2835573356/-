"""
看板数据接口 — 对应需求文档 4.2
提供看板首页所有数据查询
"""
from datetime import date, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.dashboard_service import DashboardService
from app.schemas.common import success_response
from app.utils.date_utils import today, parse_date, get_week_range
from app.utils.cache import cache

router = APIRouter(prefix="/api/v1/dashboard", tags=["看板数据"])


@router.get("/summary", summary="4.2.1 看板总览数据")
def get_summary(
    target_date: Optional[str] = Query(None, description="目标日期 YYYY-MM-DD，默认今天"),
    db: Session = Depends(get_db),
):
    """
    获取看板总览数据：健康度评分、总帖子量、Bug占比、日环比、P0风险等
    """
    dt = parse_date(target_date) if target_date else today()

    # 尝试从缓存获取
    cache_key = f"dashboard:summary:{dt.isoformat()}"
    cached = cache.get_json(cache_key)
    if cached:
        return success_response(cached)

    data = DashboardService.get_summary(db, dt)
    cache.set_json(cache_key, data, ttl=300)
    return success_response(data)


@router.get("/trend", summary="4.2.2 趋势数据")
def get_trend(
    start: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    """
    获取趋势折线图数据：5个分类随时间变化的帖子量
    """
    if start and end:
        start_date = parse_date(start)
        end_date = parse_date(end)
    else:
        start_date, end_date = get_week_range()

    # 缓存
    cache_key = f"dashboard:trend:{start_date}:{end_date}"
    cached = cache.get_json(cache_key)
    if cached:
        return success_response(cached)

    data = DashboardService.get_trend(db, start_date, end_date)
    cache.set_json(cache_key, data, ttl=600)
    return success_response(data)


@router.get("/sentiment", summary="4.2.3 情绪分布")
def get_sentiment(
    target_date: Optional[str] = Query(None, description="目标日期 YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    """
    获取情绪环形图数据：消极/中性/积极分布
    """
    dt = parse_date(target_date) if target_date else today()

    cache_key = f"dashboard:sentiment:{dt.isoformat()}"
    cached = cache.get_json(cache_key)
    if cached:
        return success_response(cached)

    data = DashboardService.get_sentiment(db, dt)
    cache.set_json(cache_key, data, ttl=300)
    return success_response(data)


@router.get("/categories", summary="4.2.4 问题分类")
def get_categories(
    target_date: Optional[str] = Query(None, description="目标日期 YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    """
    获取问题分类横向柱状图数据
    """
    dt = parse_date(target_date) if target_date else today()

    cache_key = f"dashboard:categories:{dt.isoformat()}"
    cached = cache.get_json(cache_key)
    if cached:
        return success_response(cached)

    data = DashboardService.get_categories(db, dt)
    cache.set_json(cache_key, data, ttl=300)
    return success_response(data)


@router.get("/priority", summary="优先级分布")
def get_priority(
    target_date: Optional[str] = Query(None, description="目标日期 YYYY-MM-DD"),
    start: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    """
    获取优先级分布数据：P0/P1/P2数量和占比
    """
    dt = parse_date(target_date) if target_date else today()
    start_date = parse_date(start) if start else None
    end_date = parse_date(end) if end else None

    return success_response(DashboardService.get_priority_distribution(db, dt, start_date, end_date))


@router.get("/hot-posts", summary="4.2.5 热门帖子")
def get_hot_posts(
    target_date: Optional[str] = Query(None, description="目标日期 YYYY-MM-DD"),
    start: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    limit: int = Query(8, ge=1, le=50, description="返回数量"),
    db: Session = Depends(get_db),
):
    """
    获取热门帖子 TOP N 列表
    """
    dt = parse_date(target_date) if target_date else today()
    start_date = parse_date(start) if start else None
    end_date = parse_date(end) if end else None

    cache_key = f"dashboard:hot_posts:{dt.isoformat()}:{start or ''}:{end or ''}:{limit}"
    cached = cache.get_json(cache_key)
    if cached:
        return success_response(cached)

    data = DashboardService.get_hot_posts(db, dt, limit, start_date, end_date)
    cache.set_json(cache_key, data, ttl=120)
    return success_response(data)


@router.get("/root-cause", summary="4.2.6 根因分析")
def get_root_cause(
    target_date: Optional[str] = Query(None, description="目标日期 YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    """
    获取根因分析数据：语义聚类结果
    """
    dt = parse_date(target_date) if target_date else today()

    cache_key = f"dashboard:root_cause:{dt.isoformat()}"
    cached = cache.get_json(cache_key)
    if cached:
        return success_response(cached)

    data = DashboardService.get_root_cause(db, dt)
    cache.set_json(cache_key, data, ttl=600)
    return success_response(data)


@router.get("/insights", summary="4.2.7 业务洞察")
def get_insights(
    target_date: Optional[str] = Query(None, description="目标日期 YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    """
    获取业务洞察数据：5条可执行建议
    """
    dt = parse_date(target_date) if target_date else today()

    cache_key = f"dashboard:insights:{dt.isoformat()}"
    cached = cache.get_json(cache_key)
    if cached:
        return success_response(cached)

    data = DashboardService.get_insights(db, dt)
    cache.set_json(cache_key, data, ttl=600)
    return success_response(data)


@router.get("/risk-alerts", summary="4.2.8 风险告警")
def get_risk_alerts(
    target_date: Optional[str] = Query(None, description="目标日期 YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    """
    获取风险告警数据
    """
    dt = parse_date(target_date) if target_date else today()

    cache_key = f"dashboard:risk:{dt.isoformat()}"
    cached = cache.get_json(cache_key)
    if cached:
        return success_response(cached)

    data = DashboardService.get_risk_alerts(db, dt)
    cache.set_json(cache_key, data, ttl=300)
    return success_response(data)


@router.get("/health-score", summary="健康度评分详情")
def get_health_score(
    target_date: Optional[str] = Query(None, description="目标日期 YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    """
    获取健康度评分详细信息（含计算明细）
    """
    dt = parse_date(target_date) if target_date else today()
    summary = DashboardService.get_summary(db, dt)
    return success_response({
        "date": dt.isoformat(),
        "health_score": summary.get("health_score", 100),
        "health_status": summary.get("health_status", "healthy"),
        "health_description": summary.get("health_description", ""),
        "details": {
            "bug_ratio": summary.get("bug_ratio", 0),
            "negative_ratio": summary.get("negative_ratio", 0),
            "p0_count": summary.get("p0_risk", {}).get("p0_count", 0),
        },
    })
