"""
Excel 数据导入脚本 — 将社区数据.xlsx 导入 Supabase PostgreSQL
运行方式: python -m scripts.import_excel
"""
import sys
import os
import re
import logging
from datetime import datetime, date

# 修复 Windows GBK 编码问题
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

from app.config import settings
from app.supabase_client import get_supabase, PostRecord, insert_posts_batch, check_table_exists

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("import_excel")

# ============================================================
# 分类规则
# ============================================================

CATEGORY_RULES = [
    ("Bug / 系统异常", [
        r"报错", r"错误", r"bug", r"BUG", r"异常", r"失效", r"失败",
        r"错位", r"崩溃", r"闪退", r"卡死", r"没反映", r"没反应",
        r"捕捉不到", r"找不到元素", r"无法使用", r"不能.*定位",
        r"不能.*点击", r"获取不全", r"获取不到", r"文件不存在",
        r"登录不上", r"连接失败", r"超时", r"http.*\d{3}",
        r"元素.*错位", r"元素.*飘", r"不能精确定位",
    ]),
    ("功能咨询", [
        r"怎么", r"如何", r"怎样", r"请教", r"求助", r"请问",
        r"有没有", r"能不能", r"可以.*吗", r"什么.*方案",
        r"推荐", r"教程", r"指导", r"哪里.*看", r"哪些",
        r"证书", r"面试", r"机考", r"摸鱼", r"专区",
        r"场景.*哪些", r"查询表",
    ]),
    ("RPA执行问题", [
        r"流程", r"脚本.*失效", r"定时", r"触发",
        r"运行.*失败", r"执行.*失败", r"调度",
        r"删除.*流程", r"Playwright", r"ADB",
        r"捕获.*元素", r"监控.*元素",
    ]),
    ("Excel数据问题", [
        r"excel", r"Excel", r"EXCEL", r"表格", r"单元格",
        r"写入", r"拷贝.*excel", r"wps", r"WPS",
        r"飞书.*表格", r"多维表格", r"电子表格",
        r"公式.*计算", r"数据.*抓取", r"抓取.*数据",
        r"批量.*写入", r"覆盖.*写入", r"小绿标",
        r"透视表", r"对象关闭",
    ]),
    ("第三方系统问题", [
        r"微信", r"企业微信", r"飞书", r"钉钉", r"淘宝",
        r"alicdn", r"防盗链", r"ERP", r"iframe",
        r"网页.*元素", r"网站", r"发票",
    ]),
]

# 默认分类（无匹配时）
DEFAULT_CATEGORY = "功能咨询"


def classify_post(title: str, content: str) -> str:
    """根据标题和内容自动分类"""
    text = f"{title} {content}"
    scores = {}
    for category, patterns in CATEGORY_RULES:
        score = 0
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            score += len(matches)
        scores[category] = score

    # 返回得分最高的分类
    best = max(scores, key=scores.get)
    if scores[best] > 0:
        return best
    return DEFAULT_CATEGORY


def classify_priority(view_count: int, category: str) -> str:
    """
    根据「问题分类的严重性」判定优先级，浏览量仅在故障类内部做微调。

    设计原则（与前端「问题优先级分布」卡片的语义一致）：
      - P0 系统不可用 / 大面积 / 紧急求助
      - P1 功能异常但可绕过（故障类问题）
      - P2 咨询 / 使用问题 / 闲聊讨论

    关键修正：咨询类（功能咨询）不会因为浏览量高而升级。
    一条「面试 / 求职 / 摸鱼」等热门讨论帖本质不是待处理的故障，
    无论多热门都应停留在 P2，避免污染 P0/P1 风险指标。
    """
    # 紧急求助始终 P0
    if category == "紧急求助":
        return "P0"

    # 咨询类：永远 P2，浏览量不参与升级
    if category == "功能咨询":
        return "P2"

    # 故障类（Bug / RPA / Excel / 第三方）：基线为 P1，
    # 浏览量极高（影响面大）才升级为 P0
    fault_categories = {
        "Bug / 系统异常", "RPA执行问题", "Excel数据问题", "第三方系统问题",
    }
    if category in fault_categories:
        if view_count >= 250:
            return "P0"
        return "P1"

    # 其它未知分类：按普通使用问题处理
    return "P2"


def classify_sentiment(title: str, content: str, category: str) -> str:
    """判断情绪"""
    text = f"{title} {content}"

    # 紧急/负面关键词
    negative_patterns = [
        r"救命", r"求救", r"紧急", r"报错", r"错误", r"异常",
        r"失效", r"失败", r"崩溃", r"闪退", r"错位",
        r"找不到", r"无法", r"不能", r"不行", r"搞不定",
        r"怎么.*办", r"求.*救命", r"问题", r"干扰",
    ]
    positive_patterns = [
        r"谢谢", r"感谢", r"解决", r"好了", r"可以了",
        r"推荐", r"好用", r"完美",
    ]

    neg_score = sum(len(re.findall(p, text, re.IGNORECASE)) for p in negative_patterns)
    pos_score = sum(len(re.findall(p, text, re.IGNORECASE)) for p in positive_patterns)

    if category == "Bug / 系统异常" or category == "紧急求助":
        return "negative"
    elif neg_score > pos_score + 2:
        return "negative"
    elif pos_score > neg_score:
        return "positive"
    else:
        return "neutral"


def extract_keywords(title: str, content: str) -> list:
    """提取关键词"""
    text = f"{title} {content}"
    keywords = []

    kw_patterns = [
        (r"元素错位", "元素错位"),
        (r"数据抓取", "数据抓取"),
        (r"excel", "Excel"),
        (r"微信", "微信"),
        (r"飞书", "飞书"),
        (r"捕获.*元素", "元素捕获"),
        (r"iframe", "iframe"),
        (r"Playwright", "Playwright"),
        (r"ERP", "ERP"),
        (r"淘宝", "淘宝"),
        (r"发票", "发票"),
        (r"wps|WPS", "WPS"),
        (r"面试", "面试"),
    ]

    for pattern, kw in kw_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            keywords.append(kw)

    return keywords[:5]  # 最多 5 个


# ============================================================
# 主导入逻辑
# ============================================================

def import_to_sqlite(records):
    """回退方案：导入到本地 SQLite"""
    from app.database import SessionLocal, Base, engine
    from app.models.post import Post

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        count = 0
        for r in records:
            post = Post(
                title=r.title,
                content=r.content,
                category=r.category,
                priority=r.priority,
                sentiment=r.sentiment,
                view_count=r.view_count,
                author_name=r.author_name,
                source=r.source,
                tags=r.tags,
                keywords=r.keywords,
                data_date=r.data_date or date.today(),
            )
            db.add(post)
            count += 1
        db.commit()
        return count
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def main():
    print("=" * 60)
    print("社区数据导入工具 — Excel → Supabase / SQLite")
    print("=" * 60)

    # 检测目标后端
    backend = settings.DB_BACKEND
    print(f"\n当前后端: {backend}")

    if backend == "supabase":
        # 1. 检查 Supabase 连接
        print("\n[1/5] 检查 Supabase 连接...")
        try:
            client = get_supabase()
            print(f"  ✓ 已连接: {settings.SUPABASE_URL}")
        except Exception as e:
            print(f"  ✗ 连接失败: {e}")
            print("  将回退到本地 SQLite...")
            backend = "sqlite"

    if backend == "supabase":
        # 2. 检查 posts 表是否存在
        print("\n[2/5] 检查 Supabase posts 表...")
        if not check_table_exists("posts"):
            print("  ✗ posts 表不存在！")
            print("  请先在 Supabase SQL Editor 中执行:")
            print(f"  {os.path.join(os.path.dirname(__file__), 'migration.sql')}")
            print("  或设置 DB_BACKEND=sqlite 导入到本地数据库")
            return
        print("  ✓ posts 表已存在")
    else:
        print("\n[2/5] 使用本地 SQLite 数据库...")
        print("  ✓ 将导入到 bi_dashboard.db")

    # 3. 读取 Excel
    print("\n[3/5] 读取 Excel 文件...")
    excel_path = os.path.join(os.path.dirname(__file__), "社区数据.xlsx")
    if not os.path.exists(excel_path):
        print(f"  ✗ 文件不存在: {excel_path}")
        return

    df = pd.read_excel(excel_path)

    # 列名映射
    col_map = {
        "帖子标题": "title",
        "帖子链接": "link",
        "帖子ID": "post_id",
        "作者": "author",
        "作者个人页链接": "author_link",
        "帖子内容（文本）": "content",
        "发布时间": "publish_time",
        "浏览量": "view_count",
    }
    # 尝试标准列名
    if "帖子标题" in df.columns:
        df.rename(columns=col_map, inplace=True)

    # 过滤空行
    df = df[df["title"].notna() & (df["title"] != "")]
    print(f"  ✓ 读取到 {len(df)} 条有效数据")

    # 4. 处理数据
    print("\n[4/5] 处理分类...")
    records = []
    stats = {"categories": {}, "priorities": {}, "sentiments": {}}

    for _, row in df.iterrows():
        title = str(row["title"]).strip()
        content = str(row.get("content", "")).strip()
        if content == "nan" or pd.isna(row.get("content")):
            content = ""
        if "当前帖子内部无文字描述" in content:
            content = ""

        author = str(row.get("author", "")).strip()
        if author == "nan" or pd.isna(row.get("author")):
            author = "匿名用户"

        # 浏览量
        try:
            view_count = int(row["view_count"])
        except (ValueError, TypeError):
            view_count = 0

        # 发布时间
        pub_time = row.get("publish_time")
        if pd.notna(pub_time) and str(pub_time).strip():
            try:
                dt = pd.Timestamp(pub_time).to_pydatetime()
                data_date = dt.strftime("%Y-%m-%d")
                created_at = dt.isoformat()
            except Exception:
                data_date = date.today().isoformat()
                created_at = datetime.now().isoformat()
        else:
            data_date = date.today().isoformat()
            created_at = datetime.now().isoformat()

        # 自动分类
        category = classify_post(title, content)
        priority = classify_priority(view_count, category)
        sentiment = classify_sentiment(title, content, category)
        keywords = extract_keywords(title, content)

        # 统计
        stats["categories"][category] = stats["categories"].get(category, 0) + 1
        stats["priorities"][priority] = stats["priorities"].get(priority, 0) + 1
        stats["sentiments"][sentiment] = stats["sentiments"].get(sentiment, 0) + 1

        record = PostRecord(
            title=title,
            content=content,
            category=category,
            priority=priority,
            sentiment=sentiment,
            view_count=view_count,
            author_name=author,
            source="社区导入",
            keywords=keywords,
            data_date=data_date,
            created_at=created_at,
        )
        records.append(record)

        print(
            f"  [{category}] [{priority}] [{sentiment}] "
            f"view={view_count} | {title[:50]}"
        )

    # 打印统计
    print("\n  分类统计:")
    for k, v in sorted(stats["categories"].items(), key=lambda x: -x[1]):
        print(f"    {k}: {v} 条")
    print("  优先级统计:")
    for k, v in sorted(stats["priorities"].items()):
        print(f"    {k}: {v} 条")
    print("  情绪统计:")
    for k, v in sorted(stats["sentiments"].items()):
        print(f"    {k}: {v} 条")

    # 5. 导入
    if backend == "supabase":
        print(f"\n[5/5] 导入 {len(records)} 条数据到 Supabase...")
        success = insert_posts_batch(records, batch_size=20)
        print(f"  ✓ 成功导入: {success} 条")
        if success < len(records):
            print(f"  ✗ 失败: {len(records) - success} 条")
    else:
        print(f"\n[5/5] 导入 {len(records)} 条数据到本地 SQLite...")
        try:
            success = import_to_sqlite(records)
            print(f"  ✓ 成功导入: {success} 条")
        except Exception as e:
            print(f"  ✗ 导入失败: {e}")
            import traceback
            traceback.print_exc()
            return

    print("\n" + "=" * 60)
    print("导入完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
