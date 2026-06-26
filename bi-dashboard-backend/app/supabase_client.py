"""
Supabase 客户端模块
通过 REST API 连接远程 Supabase PostgreSQL 数据库
当 DB_BACKEND=supabase 时替代 SQLAlchemy 直连
"""
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import date, datetime

from supabase import create_client, Client

from app.config import settings

logger = logging.getLogger("bi-dashboard.supabase")

# 全局 Supabase 客户端实例
_supabase: Optional[Client] = None


def get_supabase() -> Client:
    """获取 Supabase 客户端（单例）"""
    global _supabase
    if _supabase is None:
        if not settings.SUPABASE_URL or not settings.SUPABASE_SECRET_KEY:
            raise RuntimeError(
                "Supabase 未配置。请检查 .env 中的 SUPABASE_URL 和 SUPABASE_SECRET_KEY"
            )
        _supabase = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SECRET_KEY,
        )
        logger.info("Supabase 客户端初始化成功: %s", settings.SUPABASE_URL)
    return _supabase


def reset_supabase():
    """重置 Supabase 客户端（测试用）"""
    global _supabase
    _supabase = None


# ============================================================
# Post 数据操作 (对应 posts 表)
# ============================================================

@dataclass
class PostRecord:
    """帖子记录"""
    id: Optional[int] = None
    title: str = ""
    content: Optional[str] = None
    category: str = "未分类"
    priority: str = "P2"
    sentiment: str = "neutral"
    view_count: int = 0
    reply_count: int = 0
    author_name: Optional[str] = None
    source: Optional[str] = None
    tags: Optional[List[str]] = None
    is_anomaly: bool = False
    risk_level: Optional[str] = None
    root_cause_cluster: Optional[str] = None
    keywords: Optional[List[str]] = None
    data_date: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转为 Supabase REST API 可接受的字典"""
        d = {
            "title": self.title,
            "content": self.content or "",
            "category": self.category,
            "priority": self.priority,
            "sentiment": self.sentiment,
            "view_count": self.view_count,
            "reply_count": self.reply_count,
            "author_name": self.author_name or "",
            "source": self.source or "",
            "tags": self.tags or [],
            "is_anomaly": self.is_anomaly,
            "risk_level": self.risk_level or "",
            "root_cause_cluster": self.root_cause_cluster or "",
            "keywords": self.keywords or [],
            "data_date": self.data_date or date.today().isoformat(),
        }
        if self.created_at:
            d["created_at"] = self.created_at
        return d


def insert_post(record: PostRecord) -> Optional[Dict[str, Any]]:
    """插入单条帖子"""
    try:
        client = get_supabase()
        result = client.table("posts").insert(record.to_dict()).execute()
        if result.data:
            logger.debug("帖子插入成功: %s", record.title[:40])
            return result.data[0]
        return None
    except Exception as e:
        logger.error("插入帖子失败: %s", e)
        return None


def insert_posts_batch(records: List[PostRecord], batch_size: int = 50) -> int:
    """批量插入帖子，返回成功条数"""
    total = 0
    client = get_supabase()
    for i in range(0, len(records), batch_size):
        batch = records[i : i + batch_size]
        try:
            batch_dicts = [r.to_dict() for r in batch]
            result = client.table("posts").insert(batch_dicts).execute()
            if result.data:
                total += len(result.data)
            logger.info(
                "批量插入: %d/%d 条成功", i + len(batch), len(records)
            )
        except Exception as e:
            logger.error("批量插入失败 (批次 %d-%d): %s", i, i + batch_size, e)
    return total


def get_posts(
    category: Optional[str] = None,
    priority: Optional[str] = None,
    sentiment: Optional[str] = None,
    data_date: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """查询帖子列表"""
    try:
        client = get_supabase()
        query = client.table("posts").select("*")

        if category:
            query = query.eq("category", category)
        if priority:
            query = query.eq("priority", priority)
        if sentiment:
            query = query.eq("sentiment", sentiment)
        if data_date:
            query = query.eq("data_date", data_date)

        result = (
            query.order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        return result.data or []
    except Exception as e:
        logger.error("查询帖子失败: %s", e)
        return []


def get_post_count(
    category: Optional[str] = None,
    data_date: Optional[str] = None,
) -> int:
    """获取帖子总数"""
    try:
        client = get_supabase()
        query = client.table("posts").select("*", count="exact")

        if category:
            query = query.eq("category", category)
        if data_date:
            query = query.eq("data_date", data_date)

        result = query.limit(1).execute()
        return result.count if hasattr(result, "count") and result.count else 0
    except Exception as e:
        logger.error("统计帖子数失败: %s", e)
        return 0


def get_posts_by_date_range(
    start_date: str,
    end_date: str,
) -> List[Dict[str, Any]]:
    """按日期范围查询帖子"""
    try:
        client = get_supabase()
        result = (
            client.table("posts")
            .select("*")
            .gte("data_date", start_date)
            .lte("data_date", end_date)
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []
    except Exception as e:
        logger.error("按日期范围查询帖子失败: %s", e)
        return []


# ============================================================
# 数据库初始化
# ============================================================

def check_table_exists(table_name: str) -> bool:
    """检查表是否存在"""
    try:
        client = get_supabase()
        result = client.table(table_name).select("*", count="exact").limit(1).execute()
        return True
    except Exception:
        return False


def get_supabase_status() -> Dict[str, Any]:
    """获取 Supabase 连接状态"""
    try:
        client = get_supabase()
        # 尝试检查 posts 表
        posts_ok = check_table_exists("posts")
        return {
            "connected": True,
            "url": settings.SUPABASE_URL,
            "posts_table_exists": posts_ok,
            "backend": "supabase",
        }
    except Exception as e:
        return {
            "connected": False,
            "url": settings.SUPABASE_URL,
            "error": str(e),
            "backend": "supabase",
        }
