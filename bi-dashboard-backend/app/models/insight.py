"""
业务洞察表模型 — 对应需求文档 3.1.4
"""
from sqlalchemy import (
    Column, BigInteger, String, Integer,
    DateTime, Date, Text
)
from sqlalchemy.sql import func
from app.database import Base


class BusinessInsight(Base):
    __tablename__ = "business_insights"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    data_date = Column(Date, nullable=False, index=True, comment="数据日期")
    insight_index = Column(Integer, nullable=False, comment="洞察序号 1-5")
    title = Column(String(300), nullable=False, comment="洞察标题")
    impact = Column(Text, comment="影响描述")
    suggestion = Column(Text, comment="建议措施")
    severity = Column(String(20), default="medium", comment="严重程度: critical/high/medium/low")
    category = Column(String(50), comment="分类")
    created_at = Column(DateTime, server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "data_date": self.data_date.isoformat() if self.data_date else None,
            "insight_index": self.insight_index,
            "title": self.title,
            "impact": self.impact,
            "suggestion": self.suggestion,
            "severity": self.severity,
            "category": self.category,
        }
