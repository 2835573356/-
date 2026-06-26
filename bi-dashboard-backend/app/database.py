"""
数据库连接和会话管理
支持 SQLite (本地开发) 和 PostgreSQL (服务器部署)
使用方式: 修改 .env 中 DATABASE_URL 即可切换
"""
import logging
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

logger = logging.getLogger("bi-dashboard.database")

# 根据 DATABASE_URL 自动识别数据库类型
IS_SQLITE = settings.DATABASE_URL.startswith("sqlite")

if IS_SQLITE:
    logger.info("数据库模式: SQLite (本地开发)")
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=settings.DEBUG,
    )
else:
    logger.info("数据库模式: PostgreSQL (远程服务器)")
    # PostgreSQL 连接池配置
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=20,
        max_overflow=40,
        pool_pre_ping=True,
        echo=settings.DEBUG,
    )

# 为 SQLite 启用外键约束
@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    if IS_SQLITE:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI 依赖注入: 获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_type() -> str:
    """返回当前数据库类型"""
    return "sqlite" if IS_SQLITE else "postgresql"
