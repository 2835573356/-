"""
种子数据脚本 — 生成与 step5.html 一致的模拟数据
运行方式: python -m scripts.seed_data
"""
import sys
import os
import random
from datetime import date, datetime, timedelta

# 修复 Windows GBK 编码问题
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 将项目根目录加入 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, Base, SessionLocal
from app.models.post import Post
from app.models.daily_summary import DailySummary
from app.models.root_cause import RootCauseAnalysis
from app.models.insight import BusinessInsight
from app.models.risk_alert import RiskAlert
from app.models.user import User
from app.core.security import hash_password


def seed_users(db):
    """创建默认用户"""
    users_data = [
        {"username": "admin", "password": "admin123", "role": "admin", "display_name": "系统管理员", "email": "admin@yingdao.com"},
    ]
    for idx, u in enumerate(users_data, 1):
        if not db.query(User).filter(User.username == u["username"]).first():
            user = User(
                id=idx,
                username=u["username"],
                password_hash=hash_password(u["password"]),
                role=u["role"],
                display_name=u["display_name"],
                email=u["email"],
                is_active=True,
            )
            db.add(user)
    db.commit()
    print("[OK] 用户数据创建完成: admin (密码: admin123)")


def seed_posts(db):
    """生成 314 条帖子数据，匹配 demo 页面"""
    if db.query(Post).count() > 0:
        print("  - 帖子数据已存在，跳过")
        return

    dates = [date(2026, 6, d) for d in range(20, 26)]  # 6/20 - 6/25

    # 趋势数据: 每天每个分类的数量
    trend_data = {
        "Bug / 系统异常":  [4, 8, 28, 28, 33, 8],
        "功能咨询":         [2, 12, 26, 29, 22, 12],
        "RPA执行问题":      [1, 6, 5, 12, 11, 9],
        "Excel数据问题":    [3, 2, 5, 6, 8, 4],
        "第三方系统问题":    [0, 1, 7, 9, 7, 4],
        "紧急求助":          [0, 0, 0, 0, 1, 0],
    }

    # 情绪分配权重（消极主导）
    sentiment_weights = {
        "Bug / 系统异常":  {"negative": 0.78, "neutral": 0.20, "positive": 0.02},
        "功能咨询":         {"negative": 0.40, "neutral": 0.57, "positive": 0.03},
        "RPA执行问题":      {"negative": 0.55, "neutral": 0.42, "positive": 0.03},
        "Excel数据问题":    {"negative": 0.45, "neutral": 0.50, "positive": 0.05},
        "第三方系统问题":    {"negative": 0.40, "neutral": 0.55, "positive": 0.05},
        "紧急求助":          {"negative": 0.90, "neutral": 0.10, "positive": 0.00},
    }

    # 优先级分配权重
    priority_weights = {
        "Bug / 系统异常":  {"P0": 0.05, "P1": 0.65, "P2": 0.30},
        "功能咨询":         {"P0": 0.00, "P1": 0.40, "P2": 0.60},
        "RPA执行问题":      {"P0": 0.02, "P1": 0.63, "P2": 0.35},
        "Excel数据问题":    {"P0": 0.00, "P1": 0.55, "P2": 0.45},
        "第三方系统问题":    {"P0": 0.00, "P1": 0.50, "P2": 0.50},
        "紧急求助":          {"P0": 1.00, "P1": 0.00, "P2": 0.00},
    }

    # 标题模板
    titles = {
        "Bug / 系统异常": [
            "多台电脑反复出现元素错位",
            "批量数据抓取BUG：抓单列变成抓一行",
            "登录后页面白屏无法操作",
            "定时触发失败，提示未知错误",
            "iframe内元素无法识别",
            "Chrome新版兼容性问题：xpath失效",
            "多账号切换后元素定位偏移",
            "懒加载页面元素无法捕获",
            "数据抓取结果为空",
            "批量操作时程序崩溃",
            "网页自动化执行到一半卡住",
            "控件点击无响应",
        ],
        "功能咨询": [
            "是否喜欢RPA数据自动化工作",
            "这周离职又要找工作",
            "我真是chovy了影刀",
            "你们面试需要机考吗",
            "影刀社区官方似乎没有维护",
            "很多公司跟影刀合作",
            "学习影刀为什么要学python",
            "如何用xpath定位动态元素",
            "请教定时触发配置方法",
            "有没有RPA学习路线推荐",
        ],
        "RPA执行问题": [
            "RPA执行到一半报错停止",
            "自动化流程执行效率太低",
            "批量处理时内存占用过高",
            "多线程执行出现数据混乱",
            "执行日志不完整无法排查",
            "流程发布后无法正常运行",
        ],
        "Excel数据问题": [
            "Excel小绿标问题无法解决",
            "数据透视表自动刷新失败",
            "Excel公式在新版Office失效",
            "对象已关闭错误频繁出现",
            "Excel读取大量数据时卡死",
            "合并单元格数据读取异常",
        ],
        "第三方系统问题": [
            "飞书消息推送失败403",
            "钉钉多维表数据同步异常",
            "WPS兼容性问题",
            "紫鸟浏览器登录会话过期",
            "挖象平台API返回数据异常",
            "千牛平台接口变更通知",
        ],
        "紧急求助": [
            "生产环境全面崩溃，所有流程无法执行",
        ],
    }

    post_id = 0
    all_posts = []

    for day_idx, d in enumerate(dates):
        for category, counts in trend_data.items():
            count = counts[day_idx]
            cat_titles = titles.get(category, ["默认标题"])
            sent_weights = sentiment_weights.get(category, {})
            pri_weights = priority_weights.get(category, {})

            for i in range(count):
                post_id += 1

                # 分配情绪
                r = random.random()
                if r < sent_weights.get("negative", 0.5):
                    sentiment = "negative"
                elif r < sent_weights.get("negative", 0.5) + sent_weights.get("neutral", 0.3):
                    sentiment = "neutral"
                else:
                    sentiment = "positive"

                # 分配优先级
                r2 = random.random()
                if r2 < pri_weights.get("P0", 0.01):
                    priority = "P0"
                elif r2 < pri_weights.get("P0", 0.01) + pri_weights.get("P1", 0.5):
                    priority = "P1"
                else:
                    priority = "P2"

                # 选择标题
                title = cat_titles[i % len(cat_titles)]
                if count > len(cat_titles):
                    title = f"{title} (变体{i // len(cat_titles) + 1})"

                # 浏览量: P0帖子高浏览量
                if priority == "P0":
                    view_count = random.randint(200, 350)
                elif priority == "P1":
                    view_count = random.randint(50, 280)
                else:
                    view_count = random.randint(10, 200)

                # 关键词
                keywords_map = {
                    "Bug / 系统异常": ["元素错位", "xpath", "iframe", "Chrome", "兼容性", "白屏", "崩溃"],
                    "功能咨询": ["xpath", "教程", "学习路线", "面试", "社区"],
                    "RPA执行问题": ["执行失败", "报错", "效率", "内存", "日志"],
                    "Excel数据问题": ["小绿标", "透视表", "公式", "对象已关闭", "Office365"],
                    "第三方系统问题": ["飞书", "钉钉", "WPS", "紫鸟", "千牛", "API"],
                    "紧急求助": ["崩溃", "全面故障", "紧急"],
                }
                post_keywords = random.sample(
                    keywords_map.get(category, ["其他"]),
                    min(3, len(keywords_map.get(category, ["其他"])))
                )

                # 风险等级
                if priority == "P0":
                    risk_level = "high"
                elif priority == "P1" and sentiment == "negative":
                    risk_level = "medium"
                else:
                    risk_level = "low" if random.random() > 0.3 else None

                # 根因聚类标签
                if category == "Bug / 系统异常":
                    root_clusters = ["元素定位 / 元素错位", "触发与登录稳定性", None]
                    root_weights = [0.55, 0.20, 0.25]
                elif category == "Excel数据问题":
                    root_clusters = ["Excel 指令稳定性", None]
                    root_weights = [0.7, 0.3]
                elif category == "第三方系统问题":
                    root_clusters = ["第三方平台对接", None]
                    root_weights = [0.7, 0.3]
                else:
                    root_clusters = [None]
                    root_weights = [1.0]

                r3 = random.random()
                cumulative = 0
                root_cause = None
                for cluster, weight in zip(root_clusters, root_weights):
                    cumulative += weight
                    if r3 < cumulative:
                        root_cause = cluster
                        break

                post = Post(
                    id=post_id,
                    title=title,
                    content=f"这是关于 {title} 的详细描述。涉及 {category} 相关问题。",
                    category=category,
                    priority=priority,
                    sentiment=sentiment,
                    view_count=view_count,
                    reply_count=random.randint(0, 15),
                    author_name=random.choice(["用户A", "用户B", "用户C", "匿名用户", "新手上路"]),
                    source="社区论坛",
                    tags=post_keywords,
                    is_anomaly=(category == "Bug / 系统异常" and day_idx >= 3),
                    risk_level=risk_level,
                    root_cause_cluster=root_cause,
                    keywords=post_keywords,
                    data_date=d,
                    created_at=datetime(2026, 6, d.day, random.randint(8, 22), random.randint(0, 59)),
                )
                all_posts.append(post)

    # 批量写入
    db.bulk_save_objects(all_posts)
    db.commit()
    print(f"[OK] 帖子数据创建完成: {len(all_posts)} 条")


def seed_daily_summaries(db):
    """生成每日汇总数据"""
    if db.query(DailySummary).count() > 0:
        print("  - 每日汇总数据已存在，跳过")
        return

    summaries_data = [
        {"date": "2026-06-20", "total": 10, "bug": 4, "consult": 2, "rpa": 1, "excel": 3, "third": 0, "emergency": 0,
         "neg": 5, "neu": 4, "pos": 1, "p0": 0, "p1": 5, "p2": 5, "score": 92},
        {"date": "2026-06-21", "total": 29, "bug": 8, "consult": 12, "rpa": 6, "excel": 2, "third": 1, "emergency": 0,
         "neg": 12, "neu": 14, "pos": 3, "p0": 0, "p1": 18, "p2": 11, "score": 78},
        {"date": "2026-06-22", "total": 71, "bug": 28, "consult": 26, "rpa": 5, "excel": 5, "third": 7, "emergency": 0,
         "neg": 38, "neu": 30, "pos": 3, "p0": 1, "p1": 42, "p2": 28, "score": 58},
        {"date": "2026-06-23", "total": 84, "bug": 28, "consult": 29, "rpa": 12, "excel": 6, "third": 9, "emergency": 0,
         "neg": 43, "neu": 39, "pos": 2, "p0": 1, "p1": 50, "p2": 33, "score": 52},
        {"date": "2026-06-24", "total": 82, "bug": 33, "consult": 22, "rpa": 11, "excel": 8, "third": 7, "emergency": 1,
         "neg": 46, "neu": 35, "pos": 1, "p0": 3, "p1": 48, "p2": 31, "score": 42},
        {"date": "2026-06-25", "total": 38, "bug": 8, "consult": 12, "rpa": 9, "excel": 4, "third": 4, "emergency": 0,
         "neg": 16, "neu": 28, "pos": 0, "p0": 1, "p1": 18, "p2": 19, "score": 60},
    ]

    for idx, s in enumerate(summaries_data, 1):
        summary = DailySummary(
            id=idx,
            data_date=date.fromisoformat(s["date"]),
            total_posts=s["total"],
            bug_posts=s["bug"],
            consultation_posts=s["consult"],
            rpa_posts=s["rpa"],
            excel_posts=s["excel"],
            third_party_posts=s["third"],
            emergency_posts=s["emergency"],
            negative_count=s["neg"],
            neutral_count=s["neu"],
            positive_count=s["pos"],
            p0_count=s["p0"],
            p1_count=s["p1"],
            p2_count=s["p2"],
            health_score=s["score"],
            anomaly_flag=(s["score"] < 60),
        )
        db.add(summary)

    db.commit()
    print(f"[OK] 每日汇总创建完成: {len(summaries_data)} 天")


def seed_root_causes(db):
    """生成根因分析数据"""
    if db.query(RootCauseAnalysis).count() > 0:
        print("  - 根因分析数据已存在，跳过")
        return

    clusters = [
        {
            "index": 1, "name": "元素定位 / 元素错位",
            "count": 42, "percent": 13.4,
            "keywords": ["元素错位", "多账号偏移", "xpath", "iframe", "懒加载"],
            "cause": "近期发版引入DOM兼容性回归，跨账号/浏览器渲染差异未覆盖；与谷歌内核新版本相关。",
            "suggestion": "作为P0缺陷立项，回归覆盖：多账号、Chrome新版、iframe、懒加载四类场景。",
            "priority": "P0",
        },
        {
            "index": 2, "name": "Excel 指令稳定性",
            "count": 28, "percent": 8.9,
            "keywords": ["小绿标", "数据透视表", "公式失效", "对象已关闭"],
            "cause": "Excel指令集与Office 365新版兼容性问题，对象生命周期管理在并发场景下异常。",
            "suggestion": "组织Excel兼容性专项测试，覆盖Office 365各版本。",
            "priority": "P1",
        },
        {
            "index": 3, "name": "第三方平台对接",
            "count": 28, "percent": 8.9,
            "keywords": ["飞书", "钉钉多维表", "wps", "紫鸟", "挖象", "千牛"],
            "cause": "外部平台API变更（403/数据异常）+ 浏览器登录会话被频繁踢出，非平台自身缺陷，但需补充故障告警。",
            "suggestion": "在指令运行结果中明确区分'外部平台异常'与'影刀异常'，建立每日健康巡检。",
            "priority": "P1",
        },
        {
            "index": 4, "name": "触发与登录稳定性",
            "count": 17, "percent": 5.4,
            "keywords": ["定时触发失败", "登录不上", "网页白屏", "日期参数"],
            "cause": "调度服务在峰值时段出现失败，疑似与近一周后端版本相关，需SRE排查。",
            "suggestion": "排查调度服务峰值时段异常，增加失败重试和故障转移机制。",
            "priority": "P0",
        },
    ]

    today = date(2026, 6, 25)
    for idx, c in enumerate(clusters, 1):
        cluster = RootCauseAnalysis(
            id=idx,
            data_date=today,
            cluster_name=c["name"],
            cluster_index=c["index"],
            post_count=c["count"],
            percentage=c["percent"],
            keywords=c["keywords"],
            possible_cause=c["cause"],
            suggestion=c["suggestion"],
            priority_level=c["priority"],
        )
        db.add(cluster)

    db.commit()
    print(f"[OK] 根因分析创建完成: {len(clusters)} 个聚类")


def seed_insights(db):
    """生成业务洞察数据"""
    if db.query(BusinessInsight).count() > 0:
        print("  - 业务洞察数据已存在，跳过")
        return

    insights = [
        {
            "index": 1,
            "title": "Bug类问题进入爆发期，需立刻冻结非必要发版",
            "impact": "消极情绪51%，已显著超过预警线（35%）。",
            "suggestion": "组织RPA引擎+浏览器适配专项hotfix，48小时内合入。",
            "severity": "critical",
        },
        {
            "index": 2,
            "title": "\"元素错位 / 多账号偏移\" 已具备系统性特征",
            "impact": "覆盖42个独立反馈，跨多个用户与电脑。",
            "suggestion": "作为P0缺陷立项，回归覆盖：多账号、Chrome新版、iframe、懒加载四类场景。",
            "severity": "high",
        },
        {
            "index": 3,
            "title": "第三方平台问题非自身缺陷，但用户体感等同Bug",
            "impact": "用户无法区分外部异常和产品异常。",
            "suggestion": "在指令运行结果中明确区分\"外部平台异常\"与\"影刀异常\"，并对飞书/钉钉/wps/千牛建立每日健康巡检。",
            "severity": "medium",
        },
        {
            "index": 4,
            "title": "功能咨询占32.8%，社区自助内容力不足",
            "impact": "Top浏览帖多为情感/求职话题，技术咨询长尾分散。",
            "suggestion": "将高频P2（如xpath写法、Excel透视表、定时触发）固化为\"问答+示例工程\"知识库入口。",
            "severity": "medium",
        },
        {
            "index": 5,
            "title": "\"社区官方维护缺位\" 的负面舆论已显现",
            "impact": "相关帖浏览量进入Top 10。",
            "suggestion": "建立官方响应SLA（24h内首次回复），并在P0/P1帖子下置顶官方进展。",
            "severity": "high",
        },
    ]

    today = date(2026, 6, 25)
    for idx, ins in enumerate(insights, 1):
        insight = BusinessInsight(
            id=idx,
            data_date=today,
            insight_index=ins["index"],
            title=ins["title"],
            impact=ins["impact"],
            suggestion=ins["suggestion"],
            severity=ins["severity"],
            category="运营决策",
        )
        db.add(insight)

    db.commit()
    print(f"[OK] 业务洞察创建完成: {len(insights)} 条")


def seed_risk_alerts(db):
    """生成风险告警数据"""
    if db.query(RiskAlert).count() > 0:
        print("  - 风险告警数据已存在，跳过")
        return

    alerts = [
        {
            "title": "多电脑反复出现元素错位",
            "priority": "P0",
            "description": "浏览量337（周期最高），跨账号复现，已具备系统性风险。",
            "view_count": 337,
            "is_systemic": True,
        },
        {
            "title": "批量数据抓取BUG：抓单列变成抓一行",
            "priority": "P0",
            "description": "影响数据正确性，对生产链路冲击大，需立刻hotfix。",
            "view_count": 280,
            "is_systemic": True,
        },
        {
            "title": "定时触发失败 / 登录不上",
            "priority": "P1",
            "description": "多个独立反馈，疑似调度后端在峰值时段抖动。",
            "view_count": 150,
            "is_systemic": False,
        },
        {
            "title": "Excel指令兼容性（小绿标/透视表/对象关闭）",
            "priority": "P1",
            "description": "28条聚集，建议本迭代锁定Excel兼容性专项。",
            "view_count": 120,
            "is_systemic": False,
        },
    ]

    today = date(2026, 6, 25)
    for idx, a in enumerate(alerts, 1):
        alert = RiskAlert(
            id=idx,
            data_date=today,
            title=a["title"],
            priority=a["priority"],
            description=a["description"],
            view_count=a["view_count"],
            is_systemic=a["is_systemic"],
            status="active",
        )
        db.add(alert)

    db.commit()
    print(f"[OK] 风险告警创建完成: {len(alerts)} 条")


def main():
    """主函数：运行所有种子数据生成"""
    print("=" * 60)
    print("影刀社区 · BI 看板 — 种子数据生成器")
    print("=" * 60)

    # 创建表
    print("\n初始化数据库表...")
    Base.metadata.create_all(bind=engine)
    print("[OK] 数据库表初始化完成")

    db = SessionLocal()
    try:
        print("\n--- 创建用户 ---")
        seed_users(db)

        print("\n--- 创建帖子数据 (314条) ---")
        seed_posts(db)

        print("\n--- 创建每日汇总 ---")
        seed_daily_summaries(db)

        print("\n--- 创建根因分析 ---")
        seed_root_causes(db)

        print("\n--- 执行业务洞察 ---")
        seed_insights(db)

        print("\n--- 创建风险告警 ---")
        seed_risk_alerts(db)

        print("\n" + "=" * 60)
        print("种子数据生成完成！")
        print("=" * 60)
        print("\n默认账号:")
        print("  admin     / admin123      (管理员)")
        print("  operator  / operator123   (运营)")
        print("  developer / developer123  (产研)")
        print("  viewer    / viewer123     (只读)")
        print("\n启动服务: python -m app.main")
        print("API 文档: http://localhost:8000/docs")

    except Exception as e:
        print(f"\n[ERROR] 错误: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
