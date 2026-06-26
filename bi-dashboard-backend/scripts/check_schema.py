import sys; sys.path.insert(0,'.')
from app.database import Base, engine
import os

# Delete old DB
db_path = os.path.join(os.path.dirname(__file__) or '.', 'bi_dashboard.db')
if os.path.exists(db_path):
    os.remove(db_path)

Base.metadata.create_all(bind=engine)

import sqlite3
conn = sqlite3.connect(db_path)
cursor = conn.execute("SELECT sql FROM sqlite_master WHERE name='posts'")
row = cursor.fetchone()
if row:
    print('posts table schema:')
    print(row[0])
conn.close()
