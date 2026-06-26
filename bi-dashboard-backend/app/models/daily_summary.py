"""
每日汇总表模型 — 对应需求文档 3.1.2
"""
from sqlalchemy import (
    Column, BigInteger, Integer, Boolean,
    DateTime, Date, Float
)
from sqlalchemy.sql import func
from app.database import Base


class DailySummary(Base):
    __tablename__ = "daily_summary"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    data_date = Column(Date, nullable=False, unique=True, index=True, comment="数据日期")
    total_posts = Column(Integer, default=0, comment="总帖子量")
    bug_posts = Column(Integer, default=0, comment="Bug类帖子量")
    consultation_posts = Column(Integer, default=0, comment="咨询类帖子量")
    rpa_posts = Column(Integer, default=0, comment="RPA执行类帖子量")
    excel_posts = Column(Integer, default=0, comment="Excel类帖子量")
    third_party_posts = Column(Integer, default=0, comment="第三方系统类帖子量")
    emergency_posts = Column(Integer, default=0, comment="紧急求助帖子量")
    negative_count = Column(Integer, default=0, comment="消极情绪数")
    neutral_count = Column(Integer, default=0, comment="中性情绪数")
    positive_count = Column(Integer, default=0, comment="积极情绪数")
    p0_count = Column(Integer, default=0, comment="P0数量")
    p1_count = Column(Integer, default=0, comment="P1数量")
    p2_count = Column(Integer, default=0, comment="P2数量")
    health_score = Column(Integer, default=100, comment="健康度评分 0-100")
    anomaly_flag = Column(Boolean, default=False, comment="异常标记")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "data_date": self.data_date.isoformat() if self.data_date else None,
            "total_posts": self.total_posts,
            "bug_posts": self.bug_posts,
            "consultation_posts": self.consultation_posts,
            "rpa_posts": self.rpa_posts,
            "excel_posts": self.excel_posts,
            "third_party_posts": self.third_party_posts,
            "emergency_posts": self.emergency_posts,
            "negative_count": self.negative_count,
            "neutral_count": self.neutral_count,
            "positive_count": self.positive_count,
            "p0_count": self.p0_count,
            "p1_count": self.p1_count,
            "p2_count": self.p2_count,
            "health_score": self.health_score,
            "anomaly_flag": self.anomaly_flag,
        }
