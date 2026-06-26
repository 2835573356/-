"""
帖子表模型 — 对应需求文档 3.1.1
"""
from sqlalchemy import (
    Column, BigInteger, String, Text, Integer,
    Boolean, DateTime, Date, JSON, Float
)
from sqlalchemy.sql import func
from app.database import Base


class Post(Base):
    __tablename__ = "posts"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False, comment="帖子标题")
    content = Column(Text, comment="帖子正文")
    category = Column(String(100), nullable=False, index=True, comment="问题分类")
    priority = Column(String(10), nullable=False, default="P2", index=True, comment="优先级: P0/P1/P2")
    sentiment = Column(String(20), nullable=False, index=True, comment="情绪: negative/neutral/positive")
    view_count = Column(Integer, default=0, comment="浏览量")
    reply_count = Column(Integer, default=0, comment="回复数")
    author_name = Column(String(100), comment="发帖人")
    source = Column(String(100), comment="来源渠道")
    tags = Column(JSON, default=list, comment="标签")
    is_anomaly = Column(Boolean, default=False, comment="是否异常")
    risk_level = Column(String(20), comment="风险等级: high/medium/low")
    root_cause_cluster = Column(String(200), comment="根因聚类标签")
    keywords = Column(JSON, default=list, comment="关键词")
    data_date = Column(Date, nullable=False, index=True, comment="数据日期")
    created_at = Column(DateTime, server_default=func.now(), comment="发帖时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<Post(id={self.id}, title='{self.title[:30]}...', category='{self.category}')>"

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "category": self.category,
            "priority": self.priority,
            "sentiment": self.sentiment,
            "view_count": self.view_count,
            "reply_count": self.reply_count,
            "author_name": self.author_name,
            "source": self.source,
            "tags": self.tags or [],
            "is_anomaly": self.is_anomaly,
            "risk_level": self.risk_level,
            "root_cause_cluster": self.root_cause_cluster,
            "keywords": self.keywords or [],
            "data_date": self.data_date.isoformat() if self.data_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
