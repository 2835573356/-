"""
一次性修复脚本：用新的 classify_priority 逻辑重算所有帖子的优先级，
并重新生成受影响日期的每日汇总（前端 P0/P1/P2 计数来源）。

运行: python -m scripts.fix_priority
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app.database import SessionLocal
from app.models.post import Post
from app.services.analysis_service import AnalysisService
from scripts.import_excel import classify_priority

db = SessionLocal()
try:
    posts = db.query(Post).all()
    changed = 0
    affected_dates = set()
    for p in posts:
        new_pri = classify_priority(p.view_count or 0, p.category or "")
        if new_pri != p.priority:
            print(f"  [{p.priority} -> {new_pri}] view={p.view_count} {p.category} | {p.title[:36]}")
            p.priority = new_pri
            changed += 1
        affected_dates.add(p.data_date)
    db.commit()
    print(f"\n优先级已更新: {changed} 条")

    # 重新生成受影响日期的汇总
    for d in sorted(affected_dates):
        summary = AnalysisService.generate_daily_summary(db, d)
        if summary:
            print(f"  汇总刷新 {d}: P0={summary.p0_count} P1={summary.p1_count} P2={summary.p2_count}")
    print("完成")
finally:
    db.close()
