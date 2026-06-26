"""
Excel → SQLite 直接导入 (绕过 BigInteger 自增问题)
"""
import sys, os
from datetime import date as date_type

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from app.database import SessionLocal, Base, engine
from app.models.post import Post
from scripts.import_excel import (
    classify_post, classify_priority, classify_sentiment, extract_keywords
)

# 清理旧数据
print('清理旧帖子数据...')
db_temp = SessionLocal()
try:
    from sqlalchemy import delete
    db_temp.execute(delete(Post))
    db_temp.commit()
    print('已清理旧帖子数据')
except Exception as e:
    db_temp.rollback()
    print(f'清理跳过: {e}')
finally:
    db_temp.close()

Base.metadata.create_all(bind=engine)
print('数据库表初始化完成')

# 读取 Excel
excel_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '社区数据.xlsx')
df = pd.read_excel(excel_path)
df = df.dropna(subset=[df.columns[0]])

cm = {
    '帖子标题': 'title', '帖子链接': 'link', '帖子ID': 'post_id',
    '作者': 'author', '作者个人页链接': 'author_link',
    '帖子内容（文本）': 'content', '发布时间': 'publish_time', '浏览量': 'view_count'
}
df.rename(columns=cm, inplace=True)
df = df[df['title'].notna() & (df['title'] != '')]
print(f'读取到 {len(df)} 条有效数据')

# 导入
db = SessionLocal()
count = 0
stats = {}

for i, (_, row) in enumerate(df.iterrows(), 1):
    title = str(row['title']).strip()
    content = str(row.get('content', '')).strip()
    if content == 'nan' or pd.isna(row.get('content')):
        content = ''
    if '当前帖子内部无文字描述' in content:
        content = ''

    author = str(row.get('author', '')).strip()
    if author == 'nan' or pd.isna(row.get('author')):
        author = '匿名用户'

    try:
        vc = int(row['view_count'])
    except:
        vc = 0

    pub = row.get('publish_time')
    if pd.notna(pub) and str(pub).strip():
        try:
            dd = pd.Timestamp(pub).to_pydatetime().date()
        except:
            dd = date_type.today()
    else:
        dd = date_type.today()

    cat = classify_post(title, content)
    pri = classify_priority(vc, cat)
    sent = classify_sentiment(title, content, cat)
    kw = extract_keywords(title, content) or []

    stats[cat] = stats.get(cat, 0) + 1

    post = Post(
        id=i,
        title=title, content=content,
        category=cat, priority=pri, sentiment=sent,
        view_count=vc, author_name=author,
        source='社区导入', tags=[], keywords=kw,
        data_date=dd,
    )
    db.add(post)
    count += 1

db.commit()
db.close()

print(f'\n✓ 成功导入 {count} 条帖子到 SQLite')
print(f'\n分类统计:')
for k, v in sorted(stats.items(), key=lambda x: -x[1]):
    print(f'  {k}: {v} 条')
