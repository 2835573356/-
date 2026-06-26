"""
迁移脚本: 将所有表的 PK 列从 BIGINT 改为 INTEGER (SQLite 自增)
SQLite 不支持 ALTER COLUMN, 使用 rename → create → copy → drop 方式
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from app.database import engine, Base
# 导入所有 model 确保 Base.metadata 完整
import app.models  # noqa

TABLES = ["posts", "users", "daily_summary", "risk_alerts", "root_cause_analysis", "business_insights"]

con = sqlite3.connect("bi_dashboard.db")
con.execute("PRAGMA foreign_keys=OFF")

for table in TABLES:
    exists = con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    if not exists:
        print(f"  {table}: 不存在，跳过")
        continue

    old_ddl = con.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()[0]

    # 仅检查 id 列的类型 (PRAGMA 返回 INTEGER 表示已迁移)
    id_type = next(
        (row[2] for row in con.execute(f"PRAGMA table_info([{table}])").fetchall() if row[1] == "id"),
        "",
    )
    if id_type.upper() == "INTEGER":
        print(f"  {table}: 已是 INTEGER PK，跳过")
        continue

    # 重命名旧表
    con.execute(f"ALTER TABLE [{table}] RENAME TO [{table}_old]")
    # 删除旧表上的索引 (索引名会随表保留，导致 create_all 重建时冲突)
    idx_names = [
        row[0] for row in con.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name=? "
            "AND name NOT LIKE 'sqlite_%'", (f"{table}_old",)
        ).fetchall()
    ]
    for idx in idx_names:
        con.execute(f"DROP INDEX IF EXISTS [{idx}]")
    print(f"  {table}: 旧表已重命名为 {table}_old (清理 {len(idx_names)} 个索引)")
    con.commit()

# 用 ORM 创建新表 (INTEGER PK)
Base.metadata.create_all(bind=engine)
print("ORM create_all 完成")

# 复制数据
for table in TABLES:
    old_exists = con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (f"{table}_old",)
    ).fetchone()
    if not old_exists:
        continue

    cols = [row[1] for row in con.execute(f"PRAGMA table_info([{table}_old])").fetchall()]
    col_list = ", ".join(f"[{c}]" for c in cols)
    con.execute(f"INSERT INTO [{table}] ({col_list}) SELECT {col_list} FROM [{table}_old]")
    count = con.execute(f"SELECT COUNT(*) FROM [{table}]").fetchone()[0]
    con.execute(f"DROP TABLE [{table}_old]")
    con.commit()
    print(f"  {table}: 迁移完成, {count} 行")

con.execute("PRAGMA foreign_keys=ON")
con.close()
print("迁移完成")
