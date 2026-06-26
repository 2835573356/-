"""
告警服务 — 创建、更新、查询告警
"""
from typing import List, Optional
from datetime import date, datetime
from sqlalchemy.orm import Session
from app.models.risk_alert import RiskAlert


class AlertService:
    """风险告警管理服务"""

    @staticmethod
    def get_active_alerts(db: Session, target_date: Optional[date] = None) -> List[RiskAlert]:
        """获取活跃告警"""
        query = db.query(RiskAlert).filter(RiskAlert.status == "active")
        if target_date:
            query = query.filter(RiskAlert.data_date == target_date)
        return query.order_by(RiskAlert.priority, RiskAlert.created_at.desc()).all()

    @staticmethod
    def get_all_alerts(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        priority: Optional[str] = None,
    ) -> tuple:
        """获取告警列表（分页）"""
        query = db.query(RiskAlert)
        if status:
            query = query.filter(RiskAlert.status == status)
        if priority:
            query = query.filter(RiskAlert.priority == priority)

        total = query.count()
        alerts = query.order_by(
            RiskAlert.data_date.desc(),
            RiskAlert.priority,
        ).offset((page - 1) * page_size).limit(page_size).all()

        return [a.to_dict() for a in alerts], total

    @staticmethod
    def create(
        db: Session,
        data_date: date,
        title: str,
        priority: str,
        description: str = "",
        view_count: int = 0,
        is_systemic: bool = False,
    ) -> RiskAlert:
        """创建告警"""
        alert = RiskAlert(
            data_date=data_date,
            title=title,
            priority=priority,
            description=description,
            view_count=view_count,
            is_systemic=is_systemic,
            status="active",
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert

    @staticmethod
    def resolve(db: Session, alert_id: int) -> Optional[RiskAlert]:
        """标记告警为已解决"""
        alert = db.query(RiskAlert).filter(RiskAlert.id == alert_id).first()
        if not alert:
            return None
        alert.status = "resolved"
        alert.resolved_at = datetime.utcnow()
        db.commit()
        db.refresh(alert)
        return alert

    @staticmethod
    def ignore(db: Session, alert_id: int) -> Optional[RiskAlert]:
        """忽略告警"""
        alert = db.query(RiskAlert).filter(RiskAlert.id == alert_id).first()
        if not alert:
            return None
        alert.status = "ignored"
        db.commit()
        db.refresh(alert)
        return alert

    @staticmethod
    def delete(db: Session, alert_id: int) -> bool:
        """删除告警"""
        alert = db.query(RiskAlert).filter(RiskAlert.id == alert_id).first()
        if not alert:
            return False
        db.delete(alert)
        db.commit()
        return True
