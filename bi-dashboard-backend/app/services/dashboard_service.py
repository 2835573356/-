"""
看板数据服务 — 为所有看板 API 提供数据查询和聚合
对应需求文档 4.2 所有接口
"""
from typing import List, Dict, Optional
from datetime import date, timedelta
from sqlalchemy import func, desc
from sqlalchemy.orm import Session
from app.models.post import Post
from app.models.daily_summary import DailySummary
from app.models.root_cause import RootCauseAnalysis
from app.models.insight import BusinessInsight
from app.models.risk_alert import RiskAlert
from app.services.analysis_service import AnalysisService
from app.utils.date_utils import date_range_str, yesterday


class DashboardService:
    """看板数据查询服务"""

    @staticmethod
    def _resolve_post_date(db: Session, target_date: date) -> Optional[date]:
        """
        将请求日期解析为"实际有帖子数据的日期"。

        帖子可能并非每天都有（例如演示数据集中在某一天）。看板默认查询当天，
        若当天没有任何帖子，则回退到 <= target_date 的最近一天；若仍没有，
        再取全表最新的一天。返回 None 表示库中完全没有帖子。
        """
        # 1) 请求日期当天就有数据
        exists = db.query(Post.id).filter(Post.data_date == target_date).first()
        if exists:
            return target_date

        # 2) 回退到不晚于请求日期的最近一天
        prev = db.query(func.max(Post.data_date)).filter(
            Post.data_date <= target_date
        ).scalar()
        if prev:
            return prev

        # 3) 整体最新的一天（请求日期早于所有数据时）
        latest = db.query(func.max(Post.data_date)).scalar()
        return latest

    # ---- 4.2.1 看板总览 ----

    @staticmethod
    def get_summary(db: Session, target_date: date) -> dict:
        """获取看板总览数据"""
        # 尝试从每日汇总表获取
        summary = db.query(DailySummary).filter(
            DailySummary.data_date == target_date
        ).first()

        # 如果汇总表没有数据，实时计算
        if not summary:
            AnalysisService.generate_daily_summary(db, target_date)
            summary = db.query(DailySummary).filter(
                DailySummary.data_date == target_date
            ).first()

        if not summary:
            return {
                "date": target_date.isoformat(),
                "health_score": 100,
                "health_status": "healthy",
                "health_description": "暂无数据",
                "total_posts": 0,
                "daily_avg_posts": 0,
                "bug_ratio": 0,
                "negative_ratio": 0,
                "today_vs_yesterday": {
                    "change_type": "stable",
                    "change_percent": 0,
                    "description": "",
                    "bar_percent": 0,
                },
                "p0_risk": {
                    "level": "normal",
                    "emergency_count": 0,
                    "systemic_bug_count": 0,
                    "p0_count": 0,
                    "p1_count": 0,
                    "p2_count": 0,
                },
                "data_period": {"start": "", "end": ""},
                "sample_count": 0,
            }

        total = summary.total_posts
        bug_ratio = round(summary.bug_posts / total * 100, 1) if total > 0 else 0
        negative_ratio = round(summary.negative_count / total * 100, 1) if total > 0 else 0

        # 计算日均
        posts_in_range = db.query(func.count(Post.id)).filter(
            Post.data_date >= target_date - timedelta(days=6),
            Post.data_date <= target_date,
        ).scalar() or total
        daily_avg = round(posts_in_range / 7, 1) if posts_in_range > 0 else 0

        # 日环比
        prev_summary = db.query(DailySummary).filter(
            DailySummary.data_date == target_date - timedelta(days=1)
        ).first()
        if prev_summary and prev_summary.total_posts > 0:
            change_pct = round(
                (total - prev_summary.total_posts) / prev_summary.total_posts * 100, 1
            )
            if change_pct > 15:
                change_type = "surge"
            elif change_pct > 5:
                change_type = "increase"
            elif change_pct >= -5:
                change_type = "stable"
            else:
                change_type = "decrease"
        else:
            change_pct = 0
            change_type = "stable"

        today_vs_yesterday = {
            "change_type": change_type,
            "change_percent": abs(change_pct),
            "description": f"Bug类问题变化 {abs(change_pct)}%",
            "bar_percent": min(abs(change_pct), 100),
        }

        # P0 风险
        p0_count = summary.p0_count
        emergency = db.query(Post).filter(
            Post.data_date == target_date, Post.category == "紧急求助"
        ).count()
        systemic_bug = db.query(Post).filter(
            Post.data_date == target_date,
            Post.category == "Bug / 系统异常",
            Post.priority == "P0",
        ).count()

        if p0_count >= 5 or emergency >= 3:
            risk_level = "urgent"
        elif p0_count >= 2 or summary.p1_count > 150:
            risk_level = "need_attention"
        else:
            risk_level = "normal"

        p0_risk = {
            "level": risk_level,
            "emergency_count": emergency,
            "systemic_bug_count": systemic_bug,
            "p0_count": p0_count,
            "p1_count": summary.p1_count,
            "p2_count": summary.p2_count,
        }

        # 数据周期
        min_date = db.query(func.min(Post.data_date)).scalar()
        max_date = db.query(func.max(Post.data_date)).scalar()
        data_period = {
            "start": min_date.isoformat() if min_date else "",
            "end": max_date.isoformat() if max_date else "",
        }

        # 样本量
        sample_count = db.query(func.count(Post.id)).scalar()

        # 健康度
        health_score = summary.health_score
        health_status = AnalysisService.get_health_status(health_score)

        # 健康描述
        health_description = DashboardService._generate_health_description(
            bug_ratio, negative_ratio, p0_count, health_status
        )

        return {
            "date": target_date.isoformat(),
            "health_score": health_score,
            "health_status": health_status,
            "health_description": health_description,
            "total_posts": total,
            "daily_avg_posts": daily_avg,
            "bug_ratio": bug_ratio,
            "negative_ratio": negative_ratio,
            "today_vs_yesterday": today_vs_yesterday,
            "p0_risk": p0_risk,
            "data_period": data_period,
            "sample_count": sample_count,
        }

    @staticmethod
    def _generate_health_description(
        bug_ratio: float, negative_ratio: float, p0_count: int, status: str
    ) -> str:
        """生成健康度文字描述"""
        if status == "high_risk":
            parts = []
            if bug_ratio > 30:
                parts.append(f"Bug占比高达{bug_ratio}%")
            if negative_ratio > 45:
                parts.append(f"消极情绪占比{negative_ratio}%")
            if p0_count > 0:
                parts.append(f"出现{p0_count}条P0紧急问题")
            desc = "、".join(parts) if parts else "多项指标异常"
            return f"评分逻辑：{desc}。系统处于承压区间，建议进入预警状态。"
        elif status == "warning":
            return f"部分指标接近预警线（Bug占比{bug_ratio}%、消极情绪{negative_ratio}%），建议关注趋势变化。"
        else:
            return "各项指标正常，社区运营处于健康状态。"

    # ---- 4.2.2 趋势数据 ----

    @staticmethod
    def get_trend(db: Session, start_date: date, end_date: date) -> dict:
        """获取趋势数据（折线图）"""
        dates = []
        current = start_date
        while current <= end_date:
            dates.append(current)
            current += timedelta(days=1)

        date_labels = date_range_str(start_date, end_date, "%m/%d")
        # 如果包含今天，标记最后一天
        today = date.today()
        if end_date >= today:
            date_labels[-1] = date_labels[-1] + "*"

        categories = [
            {"name": "Bug / 系统异常", "color": "#ef4444"},
            {"name": "功能咨询", "color": "#8b5cf6"},
            {"name": "RPA执行问题", "color": "#3b82f6"},
            {"name": "Excel数据问题", "color": "#f59e0b"},
            {"name": "第三方系统问题", "color": "#10b981"},
        ]

        series = []
        anomaly_tags = []

        for cat_info in categories:
            data = []
            for d in dates:
                count = db.query(func.count(Post.id)).filter(
                    Post.data_date == d,
                    Post.category == cat_info["name"],
                ).scalar() or 0
                data.append(count)

            series_item = {
                "name": cat_info["name"],
                "data": data,
                "color": cat_info["color"],
                "anomaly": None,
            }

            # 检测该分类的异常
            if len(data) >= 2 and data[-2] > 0:
                change = (data[-2] - data[-3]) / data[-3] * 100 if len(data) >= 3 and data[-3] > 0 else 0
                if abs(change) > 15:
                    anomaly_info = {
                        "type": "surge" if change > 0 else "drop",
                        "percent": round(abs(change), 1),
                        "peak_date": date_labels[-2],
                        "peak_value": data[-2],
                    }
                    series_item["anomaly"] = anomaly_info
                    anomaly_tags.append({
                        "label": f"{cat_info['name']} {'突增' if change > 0 else '骤降'} {abs(change):.1f}%",
                        "type": "danger" if change > 0 else "warn",
                    })

            series.append(series_item)

        # 生成描述
        total_today = sum(s["data"][-1] for s in series)
        description = DashboardService._generate_trend_description(
            series, date_labels, total_today
        )

        return {
            "dates": date_labels,
            "series": series,
            "anomaly_tags": anomaly_tags[:3],  # Top 3
            "description": description,
        }

    @staticmethod
    def _generate_trend_description(series, date_labels, total_today) -> str:
        """生成趋势描述文字"""
        bug_series = next((s for s in series if "Bug" in s["name"]), None)
        if bug_series and len(bug_series["data"]) >= 2:
            bug_today = bug_series["data"][-1]
            bug_peak = max(bug_series["data"][:-1]) if len(bug_series["data"]) > 1 else 0
            return (
                f"整体帖量处于观察区间，Bug类问题创周期峰值"
                f"{bug_peak}条，存在功能集中爆发迹象；"
                f"最新数据为采集中，不参与异常判定。"
            )
        return "趋势数据收集中。"

    # ---- 4.2.3 情绪数据 ----

    @staticmethod
    def get_sentiment(db: Session, target_date: date) -> dict:
        """获取情绪分布数据"""
        # 回退到实际有帖子数据的日期
        resolved = DashboardService._resolve_post_date(db, target_date)
        if resolved:
            target_date = resolved

        sentiments = [
            ("negative", "消极", "#ef4444"),
            ("neutral", "中性", "#8b5cf6"),
            ("positive", "积极", "#10b981"),
        ]

        items = []
        total = db.query(func.count(Post.id)).filter(
            Post.data_date == target_date
        ).scalar() or 0

        dominant = "neutral"
        max_count = 0

        for sent_val, sent_name, sent_color in sentiments:
            count = db.query(func.count(Post.id)).filter(
                Post.data_date == target_date,
                Post.sentiment == sent_val,
            ).scalar() or 0
            percent = round(count / total * 100, 1) if total > 0 else 0
            items.append({
                "name": sent_name,
                "value": count,
                "percent": percent,
                "color": sent_color,
            })
            if count > max_count:
                max_count = count
                dominant = sent_val

        # 生成描述
        negative_count = next((i["value"] for i in items if i["name"] == "消极"), 0)
        description = (
            f"消极情绪连续多日处于高位，主要驱动来自Bug/系统异常"
            if negative_count > 40
            else "情绪分布正常。"
        )

        return {
            "items": items,
            "dominant": dominant,
            "description": description,
        }

    # ---- 4.2.4 问题分类 ----

    @staticmethod
    def get_categories(db: Session, target_date: date) -> dict:
        """获取问题分类数据"""
        # 回退到实际有帖子数据的日期
        resolved = DashboardService._resolve_post_date(db, target_date)
        if resolved:
            target_date = resolved

        category_colors = {
            "Bug / 系统异常": "#ef4444",
            "功能咨询": "#8b5cf6",
            "RPA执行问题": "#3b82f6",
            "Excel数据问题": "#f59e0b",
            "第三方系统问题": "#10b981",
            "紧急求助": "#f97316",
        }

        results = db.query(
            Post.category,
            func.count(Post.id).label("count"),
        ).filter(
            Post.data_date == target_date
        ).group_by(Post.category).order_by(desc("count")).all()

        total = sum(r.count for r in results)
        categories = []
        for cat_name, count in results:
            categories.append({
                "name": cat_name,
                "count": count,
                "percent": round(count / total * 100, 1) if total > 0 else 0,
                "color": category_colors.get(cat_name, "#3b82f6"),
            })

        return {"categories": categories, "total": total}

    @staticmethod
    def get_priority_distribution(
        db: Session,
        target_date: date,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> dict:
        """Get P0/P1/P2 counts directly from posts for one day or a date range."""
        if start_date and end_date:
            filters = [Post.data_date >= start_date, Post.data_date <= end_date]
        else:
            resolved = DashboardService._resolve_post_date(db, target_date)
            filters = [Post.data_date == (resolved or target_date)]

        rows = db.query(
            Post.priority,
            func.count(Post.id).label("count"),
        ).filter(*filters).group_by(Post.priority).all()

        counts = {"P0": 0, "P1": 0, "P2": 0}
        for priority, count in rows:
            if priority in counts:
                counts[priority] = count

        emergency_count = db.query(func.count(Post.id)).filter(
            *filters,
            Post.category == "紧急求助",
        ).scalar() or 0
        systemic_bug_count = db.query(func.count(Post.id)).filter(
            *filters,
            Post.category == "Bug / 系统异常",
            Post.priority == "P0",
        ).scalar() or 0

        return {
            "p0_risk": {
                "level": "urgent" if counts["P0"] >= 5 else ("need_attention" if counts["P0"] >= 2 or counts["P1"] >= 20 else "normal"),
                "emergency_count": emergency_count,
                "systemic_bug_count": systemic_bug_count,
                "p0_count": counts["P0"],
                "p1_count": counts["P1"],
                "p2_count": counts["P2"],
            },
            "total_posts": counts["P0"] + counts["P1"] + counts["P2"],
        }

    # ---- 4.2.5 热门帖子 ----

    @staticmethod
    def get_hot_posts(
        db: Session,
        target_date: date,
        limit: int = 8,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> dict:
        """获取热门帖子 TOP N"""
        if start_date and end_date:
            filters = [Post.data_date >= start_date, Post.data_date <= end_date]
        else:
            # 回退到实际有帖子数据的日期
            resolved = DashboardService._resolve_post_date(db, target_date)
            if resolved:
                target_date = resolved
            filters = [Post.data_date == target_date]

        posts = db.query(Post).filter(
            *filters,
            Post.view_count > 0,
        ).order_by(desc(Post.view_count), desc(Post.id)).limit(limit).all()

        return {
            "posts": [
                {
                    "id": p.id,
                    "title": p.title,
                    "category": p.category,
                    "sentiment": p.sentiment,
                    "view_count": p.view_count,
                    "priority": p.priority,
                }
                for p in posts
            ]
        }

    # ---- 4.2.6 根因分析 ----

    @staticmethod
    def get_root_cause(db: Session, target_date: date) -> dict:
        """获取根因分析数据"""
        clusters = db.query(RootCauseAnalysis).filter(
            RootCauseAnalysis.data_date == target_date
        ).order_by(RootCauseAnalysis.cluster_index).all()

        if not clusters:
            return {"clusters": [], "total_clusters": 0}

        return {
            "clusters": [
                {
                    "index": c.cluster_index,
                    "name": c.cluster_name,
                    "count": c.post_count,
                    "percent": c.percentage,
                    "priority": "danger" if c.post_count > 30 else ("warn" if c.post_count > 15 else "info"),
                    "keywords": c.keywords or [],
                    "possible_cause": c.possible_cause,
                    "suggestion": c.suggestion,
                }
                for c in clusters
            ],
            "total_clusters": len(clusters),
        }

    # ---- 4.2.7 业务洞察 ----

    @staticmethod
    def get_insights(db: Session, target_date: date) -> dict:
        """获取业务洞察数据"""
        insights = db.query(BusinessInsight).filter(
            BusinessInsight.data_date == target_date
        ).order_by(BusinessInsight.insight_index).all()

        severity_colors = {
            "critical": "#ef4444",
            "high": "#f59e0b",
            "medium": "#8b5cf6",
            "low": "#3b82f6",
        }

        return {
            "insights": [
                {
                    "index": i.insight_index,
                    "title": i.title,
                    "impact": i.impact,
                    "suggestion": i.suggestion,
                    "severity": i.severity,
                    "color": severity_colors.get(i.severity, "#3b82f6"),
                }
                for i in insights
            ]
        }

    # ---- 4.2.8 风险告警 ----

    @staticmethod
    def get_risk_alerts(db: Session, target_date: date) -> dict:
        """获取风险告警数据"""
        resolved = DashboardService._resolve_post_date(db, target_date)
        if resolved:
            target_date = resolved

        alerts = db.query(RiskAlert).filter(
            RiskAlert.data_date == target_date,
            RiskAlert.status == "active",
        ).order_by(RiskAlert.priority).all()

        alert_items = [
            {
                "id": a.id,
                "title": a.title,
                "priority": a.priority,
                "description": a.description,
                "is_systemic": a.is_systemic,
                "status": a.status,
            }
            for a in alerts
        ]

        if not alert_items:
            alert_items = DashboardService._generate_dynamic_risk_alerts(db, target_date)

        p0_alerts = [a for a in alert_items if a["priority"] == "P0"]
        p1_alerts = [a for a in alert_items if a["priority"] == "P1"]
        is_systemic = len(p0_alerts) >= 2 or any(a["is_systemic"] for a in alert_items)
        urgent = len(p0_alerts) > 0

        suggestion = ""
        if is_systemic:
            suggestion = "建议立刻拉起跨研发-产品-客服三方应急例会，并在48小时内向客户发出官方告知。"
        elif urgent:
            suggestion = "关注P0告警进展，确保24小时内给出初步处理方案。"
        elif p1_alerts:
            suggestion = "当前存在 P1 风险信号，建议安排负责人跟进，并在下个工作日完成初步定位。"
        else:
            suggestion = "当前风险可控，保持日常监控。"

        return {
            "is_systemic_risk": is_systemic,
            "urgent_action_required": urgent,
            "suggestion": suggestion,
            "alerts": alert_items,
        }

    @staticmethod
    def _generate_dynamic_risk_alerts(db: Session, target_date: date) -> list:
        """Generate display alerts from posts when no active manual alerts exist."""
        alerts = []
        next_id = -1

        p1_count = db.query(func.count(Post.id)).filter(
            Post.data_date == target_date,
            Post.priority == "P1",
        ).scalar() or 0
        p0_count = db.query(func.count(Post.id)).filter(
            Post.data_date == target_date,
            Post.priority == "P0",
        ).scalar() or 0

        if p0_count >= 1:
            alerts.append({
                "id": next_id,
                "title": f"P0 问题出现 {p0_count} 条",
                "priority": "P0",
                "description": "已达到最高优先级风险阈值，需要立即确认影响面和修复负责人。",
                "is_systemic": p0_count >= 2,
                "status": "active",
            })
            next_id -= 1

        if p1_count >= 5:
            alerts.append({
                "id": next_id,
                "title": f"P1 故障类问题累计 {p1_count} 条",
                "priority": "P1",
                "description": "功能异常类反馈已超过 5 条低阈值预警线，建议集中排查高频模块。",
                "is_systemic": p1_count >= 10,
                "status": "active",
            })
            next_id -= 1

        category_thresholds = {
            "Bug / 系统异常": (3, "Bug / 系统异常反馈升高"),
            "RPA执行问题": (5, "RPA 执行问题集中出现"),
            "Excel数据问题": (3, "Excel 数据问题达到预警线"),
            "第三方系统问题": (3, "第三方系统问题达到预警线"),
        }
        rows = db.query(
            Post.category,
            func.count(Post.id).label("count"),
        ).filter(
            Post.data_date == target_date,
            Post.category.in_(category_thresholds.keys()),
        ).group_by(Post.category).order_by(desc("count")).all()

        for category, count in rows:
            threshold, title = category_thresholds[category]
            if count < threshold:
                continue
            alerts.append({
                "id": next_id,
                "title": title,
                "priority": "P1",
                "description": f"{target_date.isoformat()} {category} 共 {count} 条，已超过 {threshold} 条预警阈值。",
                "is_systemic": count >= threshold * 2,
                "status": "active",
            })
            next_id -= 1
            if len(alerts) >= 4:
                break

        return alerts[:4]
