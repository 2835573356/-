"""
根因分析表模型 — 对应需求文档 3.1.3
"""
from sqlalchemy import (
    Column, BigInteger, String, Integer,
    DateTime, Date, JSON, Text, Float
)
from sqlalchemy.sql import func
from app.database import Base


class RootCauseAnalysis(Base):
    __tablename__ = "root_cause_analysis"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    data_date = Column(Date, nullable=False, index=True, comment="分析日期")
    cluster_name = Column(String(200), nullable=False, comment="聚类名称")
    cluster_index = Column(Integer, nullable=False, comment="聚类序号")
    post_count = Column(Integer, default=0, comment="涉及帖子数")
    percentage = Column(Float, default=0, comment="占比")
    keywords = Column(JSON, default=list, comment="关键词")
    possible_cause = Column(Text, comment="可能原因")
    suggestion = Column(Text, comment="建议措施")
    priority_level = Column(String(10), default="P1", comment="优先级")
    created_at = Column(DateTime, server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "data_date": self.data_date.isoformat() if self.data_date else None,
            "cluster_name": self.cluster_name,
            "cluster_index": self.cluster_index,
            "post_count": self.post_count,
            "percentage": self.percentage,
            "keywords": self.keywords or [],
            "possible_cause": self.possible_cause,
            "suggestion": self.suggestion,
            "priority_level": self.priority_level,
        }
