"""
风险告警表模型 — 对应需求文档 3.1.5
"""
from sqlalchemy import (
    Column, BigInteger, String, Integer,
    DateTime, Date, Text, Boolean
)
from sqlalchemy.sql import func
from app.database import Base


class RiskAlert(Base):
    __tablename__ = "risk_alerts"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    data_date = Column(Date, nullable=False, index=True, comment="数据日期")
    title = Column(String(300), nullable=False, comment="告警标题")
    priority = Column(String(10), nullable=False, index=True, comment="优先级: P0/P1/P2")
    description = Column(Text, comment="告警描述")
    view_count = Column(Integer, default=0, comment="相关浏览量")
    is_systemic = Column(Boolean, default=False, comment="是否系统性风险")
    status = Column(String(20), default="active", index=True, comment="状态: active/resolved/ignored")
    resolved_at = Column(DateTime, comment="解决时间")
    created_at = Column(DateTime, server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "data_date": self.data_date.isoformat() if self.data_date else None,
            "title": self.title,
            "priority": self.priority,
            "description": self.description,
            "view_count": self.view_count,
            "is_systemic": self.is_systemic,
            "status": self.status,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
