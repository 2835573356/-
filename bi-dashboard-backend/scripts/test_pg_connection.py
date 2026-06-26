"""测试 Supabase PostgreSQL 连接"""
import psycopg2

PASSWORD = '15033236963zzj'
PROJECT = 'dkjgcavnxxnxalzuoock'

configs = [
    ('Session pooler 5432', 'aws-0.us-east-1.pooler.supabase.com', 5432, f'postgres.{PROJECT}'),
    ('Transaction pooler 6543', 'aws-0.us-east-1.pooler.supabase.com', 6543, f'postgres.{PROJECT}'),
    ('Direct 5432', f'db.{PROJECT}.supabase.co', 5432, 'postgres'),
    ('Direct 6543', f'db.{PROJECT}.supabase.co', 6543, 'postgres'),
    ('Session pooler us-west-1', 'aws-0.us-west-1.pooler.supabase.com', 5432, f'postgres.{PROJECT}'),
    ('Transaction pooler us-west-1', 'aws-0.us-west-1.pooler.supabase.com', 6543, f'postgres.{PROJECT}'),
]

for name, host, port, user in configs:
    try:
        conn = psycopg2.connect(
            host=host, port=port, dbname='postgres',
            user=user, password=PASSWORD,
            sslmode='require', connect_timeout=8
        )
        print(f'OK: {name} - {host}:{port}')
        cur = conn.cursor()
        cur.execute('SELECT count(*) FROM posts')
        print(f'  posts count: {cur.fetchone()[0]}')
        conn.close()
        break
    except Exception as e:
        print(f'FAIL: {name} - {str(e)[:100]}')
