"""
帖子服务 — CRUD 操作，支持筛选、排序、分页
"""
from typing import List, Optional, Tuple
from datetime import date
from sqlalchemy import func, desc, asc
from sqlalchemy.orm import Session
from app.models.post import Post
from app.utils.cache import cache


class PostService:
    """帖子管理服务"""

    @staticmethod
    def get_list(
        db: Session,
        keyword: Optional[str] = None,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        sentiment: Optional[str] = None,
        risk_level: Optional[str] = None,
        data_date_start: Optional[date] = None,
        data_date_end: Optional[date] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[dict], int]:
        """
        获取帖子列表（分页、筛选、排序）
        """
        query = db.query(Post)

        # 关键词搜索（标题 + 内容）
        if keyword:
            keyword_filter = f"%{keyword}%"
            query = query.filter(
                (Post.title.ilike(keyword_filter))
                | (Post.content.ilike(keyword_filter))
            )

        # 分类筛选
        if category:
            query = query.filter(Post.category == category)

        # 优先级筛选
        if priority:
            query = query.filter(Post.priority == priority)

        # 情绪筛选
        if sentiment:
            query = query.filter(Post.sentiment == sentiment)

        # 风险等级筛选
        if risk_level:
            query = query.filter(Post.risk_level == risk_level)

        # 日期范围筛选
        if data_date_start:
            query = query.filter(Post.data_date >= data_date_start)
        if data_date_end:
            query = query.filter(Post.data_date <= data_date_end)

        # 总数
        total = query.count()

        # 排序（以 id 作为同值时的稳定次级排序，避免批量导入时间相同导致顺序错乱）
        sort_column = getattr(Post, sort_by, Post.created_at)
        if sort_order == "asc":
            query = query.order_by(asc(sort_column), asc(Post.id))
        else:
            query = query.order_by(desc(sort_column), desc(Post.id))

        # 分页
        posts = query.offset((page - 1) * page_size).limit(page_size).all()

        return [p.to_dict() for p in posts], total

    @staticmethod
    def get_by_id(db: Session, post_id: int) -> Optional[Post]:
        """根据 ID 获取帖子"""
        return db.query(Post).filter(Post.id == post_id).first()

    @staticmethod
    def create(db: Session, **kwargs) -> Post:
        """创建帖子"""
        post = Post(**kwargs)
        db.add(post)
        db.commit()
        db.refresh(post)
        # 清除看板相关缓存
        cache.delete_pattern("dashboard:")
        return post

    @staticmethod
    def update(db: Session, post_id: int, **kwargs) -> Optional[Post]:
        """更新帖子"""
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            return None
        for key, value in kwargs.items():
            if value is not None and hasattr(post, key):
                setattr(post, key, value)
        db.commit()
        db.refresh(post)
        # 清除看板相关缓存
        cache.delete_pattern("dashboard:")
        return post

    @staticmethod
    def delete(db: Session, post_id: int) -> bool:
        """删除帖子"""
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            return False
        db.delete(post)
        db.commit()
        # 清除看板相关缓存
        cache.delete_pattern("dashboard:")
        return True

    @staticmethod
    def get_categories_list(db: Session) -> List[str]:
        """获取所有分类名称"""
        results = db.query(Post.category).distinct().all()
        return [r[0] for r in results]

    @staticmethod
    def get_statistics(db: Session, target_date: date) -> dict:
        """获取帖子统计信息"""
        total = db.query(func.count(Post.id)).filter(
            Post.data_date == target_date
        ).scalar() or 0

        by_category = dict(
            db.query(Post.category, func.count(Post.id)).filter(
                Post.data_date == target_date
            ).group_by(Post.category).all()
        )

        by_sentiment = dict(
            db.query(Post.sentiment, func.count(Post.id)).filter(
                Post.data_date == target_date
            ).group_by(Post.sentiment).all()
        )

        by_priority = dict(
            db.query(Post.priority, func.count(Post.id)).filter(
                Post.data_date == target_date
            ).group_by(Post.priority).all()
        )

        return {
            "total": total,
            "by_category": by_category,
            "by_sentiment": by_sentiment,
            "by_priority": by_priority,
        }
