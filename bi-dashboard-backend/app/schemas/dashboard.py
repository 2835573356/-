"""
看板数据 Pydantic Schema — 对应需求文档 4.2 所有接口响应
"""
from typing import Optional, List
from pydantic import BaseModel


# ---- 4.2.1 看板总览 ----

class TodayVsYesterday(BaseModel):
    change_type: str = "stable"       # surge/increase/stable/decrease
    change_percent: float = 0.0
    description: str = ""
    bar_percent: float = 0.0


class P0Risk(BaseModel):
    level: str = "normal"             # urgent/need_attention/normal
    emergency_count: int = 0
    systemic_bug_count: int = 0
    p0_count: int = 0
    p1_count: int = 0
    p2_count: int = 0


class HealthScoreSummary(BaseModel):
    """4.2.1 看板总览"""
    date: str = ""
    health_score: int = 100
    health_status: str = "healthy"    # healthy/warning/high_risk
    health_description: str = ""
    total_posts: int = 0
    daily_avg_posts: float = 0.0
    bug_ratio: float = 0.0
    negative_ratio: float = 0.0
    today_vs_yesterday: TodayVsYesterday = TodayVsYesterday()
    p0_risk: P0Risk = P0Risk()
    data_period: dict = {}
    sample_count: int = 0


# ---- 4.2.2 趋势数据 ----

class TrendSeries(BaseModel):
    name: str = ""
    data: List[float] = []
    color: str = "#3b82f6"
    anomaly: Optional[dict] = None


class TrendData(BaseModel):
    """4.2.2 趋势数据"""
    dates: List[str] = []
    series: List[TrendSeries] = []
    anomaly_tags: List[dict] = []
    description: str = ""


# ---- 4.2.3 情绪数据 ----

class SentimentItem(BaseModel):
    name: str = ""
    value: int = 0
    percent: float = 0.0
    color: str = "#3b82f6"


class SentimentData(BaseModel):
    """4.2.3 情绪数据"""
    items: List[SentimentItem] = []
    dominant: str = "neutral"         # negative/neutral/positive
    description: str = ""


# ---- 4.2.4 问题分类 ----

class CategoryItem(BaseModel):
    name: str = ""
    count: int = 0
    percent: float = 0.0
    color: str = "#3b82f6"


class CategoryData(BaseModel):
    """4.2.4 问题分类"""
    categories: List[CategoryItem] = []
    total: int = 0


# ---- 4.2.5 热门帖子 ----

class HotPost(BaseModel):
    id: int
    title: str
    category: str = ""
    sentiment: str = ""
    view_count: int = 0
    priority: str = "P2"


class HotPostsData(BaseModel):
    """4.2.5 热门帖子"""
    posts: List[HotPost] = []


# ---- 4.2.6 根因分析 ----

class RootCauseCluster(BaseModel):
    index: int
    name: str
    count: int = 0
    percent: float = 0.0
    priority: str = "info"           # danger/warn/info
    keywords: List[str] = []
    possible_cause: str = ""
    suggestion: str = ""


class RootCauseData(BaseModel):
    """4.2.6 根因分析"""
    clusters: List[RootCauseCluster] = []
    total_clusters: int = 0


# ---- 4.2.7 业务洞察 ----

class InsightItem(BaseModel):
    index: int
    title: str
    impact: str = ""
    suggestion: str = ""
    severity: str = "medium"          # critical/high/medium/low
    color: str = "#3b82f6"


class InsightData(BaseModel):
    """4.2.7 业务洞察"""
    insights: List[InsightItem] = []


# ---- 4.2.8 风险告警 ----

class AlertItem(BaseModel):
    id: int
    title: str
    priority: str = "P1"
    description: str = ""
    is_systemic: bool = False
    status: str = "active"


class RiskAlertData(BaseModel):
    """4.2.8 风险告警"""
    is_systemic_risk: bool = False
    urgent_action_required: bool = False
    suggestion: str = ""
    alerts: List[AlertItem] = []
