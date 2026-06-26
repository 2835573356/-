"""
分析服务 — 健康度评分、异常检测、语义聚类
对应需求文档附录 A、附录 B
"""
from typing import List, Dict, Optional
from datetime import date, timedelta
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.post import Post
from app.models.daily_summary import DailySummary
from app.utils.cache import cache


class AnalysisService:
    """数据分析服务"""

    # ---- 健康度评分（附录 A） ----

    @staticmethod
    def calculate_health_score(
        bug_ratio: float,
        negative_ratio: float,
        p0_count: int,
        anomaly_count: int,
    ) -> int:
        """
        计算健康度评分 0-100
        参考需求文档附录 A
        """
        score = 100.0

        # Bug 占比扣分（权重 40%）
        bug_deduction = min(bug_ratio * 100, 40)
        bug_multiplier = 1.0 if bug_ratio > 0.15 else 0.5
        score -= bug_deduction * bug_multiplier

        # 消极情绪扣分（权重 35%）
        neg_deduction = min(negative_ratio * 100, 35)
        neg_multiplier = 1.0 if negative_ratio > 0.30 else 0.5
        score -= neg_deduction * neg_multiplier

        # P0 数量扣分（权重 15%）
        score -= min(p0_count, 10) * 1.5

        # 异常数量扣分（权重 10%）
        score -= min(anomaly_count, 10) * 1.0

        return max(0, min(100, round(score)))

    @staticmethod
    def get_health_status(score: int) -> str:
        """根据评分返回状态标签"""
        if score >= 80:
            return "healthy"
        elif score >= 60:
            return "warning"
        else:
            return "high_risk"

    # ---- 异常检测（附录 B） ----

    @staticmethod
    def detect_anomalies(db: Session, current_date: date) -> List[Dict]:
        """
        异常检测规则
        返回检测到的异常列表
        """
        anomalies = []
        yesterday = current_date - timedelta(days=1)

        # 获取当日数据
        today_posts = db.query(Post).filter(Post.data_date == current_date).all()
        yesterday_posts = db.query(Post).filter(Post.data_date == yesterday).all()

        today_total = len(today_posts)
        yesterday_total = len(yesterday_posts)

        # A01: 日环比变化 > 15%
        if yesterday_total > 0:
            change = (today_total - yesterday_total) / yesterday_total * 100
            if abs(change) > 15:
                anomalies.append({
                    "rule_id": "A01",
                    "type": "surge" if change > 0 else "drop",
                    "percent": round(abs(change), 1),
                    "message": f"{'突增' if change > 0 else '骤降'} {abs(change):.1f}%",
                    "severity": "warning",
                })

        # A02: Bug 类 > 25条/日
        bug_count = sum(1 for p in today_posts if p.category in ("Bug / 系统异常",))
        if bug_count > 25:
            anomalies.append({
                "rule_id": "A02",
                "type": "bug_surge",
                "count": bug_count,
                "message": f"Bug 爆发: {bug_count} 条",
                "severity": "danger",
            })

        # A03: 消极情绪 > 40条/日
        negative_count = sum(1 for p in today_posts if p.sentiment == "negative")
        if negative_count > 40:
            anomalies.append({
                "rule_id": "A03",
                "type": "sentiment_deterioration",
                "count": negative_count,
                "message": f"情绪恶化: {negative_count} 条消极",
                "severity": "danger",
            })

        # A04: P0 数量 > 3
        p0_count = sum(1 for p in today_posts if p.priority == "P0")
        if p0_count > 3:
            anomalies.append({
                "rule_id": "A04",
                "type": "p0_accumulation",
                "count": p0_count,
                "message": f"P0 堆积: {p0_count} 条",
                "severity": "danger",
            })

        # A06: 单日帖子量 > 100
        if today_total > 100:
            anomalies.append({
                "rule_id": "A06",
                "type": "traffic_anomaly",
                "count": today_total,
                "message": f"流量异常: {today_total} 条",
                "severity": "warning",
            })

        return anomalies

    @staticmethod
    def detect_anomaly_for_category(
        db: Session, current_date: date
    ) -> Dict[str, Optional[Dict]]:
        """
        按分类检测异常（用于趋势图异常标签）
        检测每个分类的日环比变化
        """
        yesterday = current_date - timedelta(days=1)
        categories = [
            "Bug / 系统异常", "功能咨询", "RPA执行问题",
            "Excel数据问题", "第三方系统问题"
        ]

        result = {}
        for cat in categories:
            today_count = db.query(Post).filter(
                Post.data_date == current_date, Post.category == cat
            ).count()
            yesterday_count = db.query(Post).filter(
                Post.data_date == yesterday, Post.category == cat
            ).count()

            if yesterday_count > 0:
                change = (today_count - yesterday_count) / yesterday_count * 100
                if abs(change) > 15:
                    result[cat] = {
                        "type": "surge" if change > 0 else "drop",
                        "percent": round(change, 1),
                    }
                else:
                    result[cat] = None
            else:
                result[cat] = None

        return result

    # ---- 日汇总数据生成 ----

    @staticmethod
    def generate_daily_summary(db: Session, target_date: date) -> DailySummary:
        """
        生成指定日期的汇总数据
        统计 posts 表中该日期的各项指标
        """
        posts = db.query(Post).filter(Post.data_date == target_date).all()
        total = len(posts)

        if total == 0:
            return None

        # 按分类统计
        bug_posts = sum(1 for p in posts if p.category == "Bug / 系统异常")
        consultation_posts = sum(1 for p in posts if p.category == "功能咨询")
        rpa_posts = sum(1 for p in posts if "RPA" in (p.category or ""))
        excel_posts = sum(1 for p in posts if "Excel" in (p.category or ""))
        third_party_posts = sum(1 for p in posts if "第三方" in (p.category or ""))
        emergency_posts = sum(1 for p in posts if p.category == "紧急求助")

        # 按情绪统计
        negative_count = sum(1 for p in posts if p.sentiment == "negative")
        neutral_count = sum(1 for p in posts if p.sentiment == "neutral")
        positive_count = sum(1 for p in posts if p.sentiment == "positive")

        # 按优先级统计
        p0_count = sum(1 for p in posts if p.priority == "P0")
        p1_count = sum(1 for p in posts if p.priority == "P1")
        p2_count = sum(1 for p in posts if p.priority == "P2")

        # 计算占比
        bug_ratio = bug_posts / total if total > 0 else 0
        negative_ratio = negative_count / total if total > 0 else 0

        # 检测异常数量
        anomalies = AnalysisService.detect_anomalies(db, target_date)
        anomaly_count = len(anomalies)

        # 计算健康度
        health_score = AnalysisService.calculate_health_score(
            bug_ratio, negative_ratio, p0_count, anomaly_count
        )

        # 检查是否已存在该日期的汇总
        existing = db.query(DailySummary).filter(
            DailySummary.data_date == target_date
        ).first()

        if existing:
            # 更新
            existing.total_posts = total
            existing.bug_posts = bug_posts
            existing.consultation_posts = consultation_posts
            existing.rpa_posts = rpa_posts
            existing.excel_posts = excel_posts
            existing.third_party_posts = third_party_posts
            existing.emergency_posts = emergency_posts
            existing.negative_count = negative_count
            existing.neutral_count = neutral_count
            existing.positive_count = positive_count
            existing.p0_count = p0_count
            existing.p1_count = p1_count
            existing.p2_count = p2_count
            existing.health_score = health_score
            existing.anomaly_flag = anomaly_count > 0
            summary = existing
        else:
            # 新建
            summary = DailySummary(
                data_date=target_date,
                total_posts=total,
                bug_posts=bug_posts,
                consultation_posts=consultation_posts,
                rpa_posts=rpa_posts,
                excel_posts=excel_posts,
                third_party_posts=third_party_posts,
                emergency_posts=emergency_posts,
                negative_count=negative_count,
                neutral_count=neutral_count,
                positive_count=positive_count,
                p0_count=p0_count,
                p1_count=p1_count,
                p2_count=p2_count,
                health_score=health_score,
                anomaly_flag=anomaly_count > 0,
            )
            db.add(summary)

        db.commit()
        db.refresh(summary)

        # 清除相关缓存
        cache.delete_pattern("dashboard:summary")
        cache.delete_pattern("dashboard:trend")

        return summary
