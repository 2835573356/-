"""
FastAPI 应用入口
影刀社区 · 企业级运营数据看板 — 后端服务
"""
import sys
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler

# 修复 Windows GBK 编码问题
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app.config import settings
from app.database import engine, Base
from app.core.middleware import setup_middleware
from app.api import auth, dashboard, posts, export, admin, websocket, upload

# 配置日志
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("bi-dashboard")

# 定时任务调度器
scheduler = BackgroundScheduler(timezone="Asia/Shanghai")


def scheduled_generate_daily_summary():
    """定时任务：每日生成汇总数据"""
    from app.database import SessionLocal
    from app.services.analysis_service import AnalysisService
    from app.utils.date_utils import yesterday

    logger.info("定时任务: 开始生成每日汇总数据...")
    db = SessionLocal()
    try:
        summary = AnalysisService.generate_daily_summary(db, yesterday())
        if summary:
            logger.info(f"定时任务: 汇总数据生成成功 - {yesterday()} (帖子 {summary.total_posts} 条)")
        else:
            logger.warning(f"定时任务: {yesterday()} 没有数据")
    except Exception as e:
        logger.error(f"定时任务失败: {e}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    from app.database import get_db_type, IS_SQLITE

    logger.info("=" * 60)
    logger.info("影刀社区 · BI 看板后端服务启动中...")
    logger.info(f"数据库: {get_db_type().upper()} ({settings.DATABASE_URL})")

    # Supabase REST API 连接检查 (导入脚本用)
    if settings.SUPABASE_URL:
        try:
            from app.supabase_client import get_supabase, check_table_exists
            get_supabase()
            logger.info(f"Supabase REST API: 已连接 ({settings.SUPABASE_URL})")
            if check_table_exists("posts"):
                logger.info("Supabase posts 表已就绪")
        except Exception as e:
            logger.debug(f"Supabase REST API 未连接: {e}")

    # 创建所有表
    Base.metadata.create_all(bind=engine)
    logger.info("本地数据库表初始化完成")

    # 启动定时任务
    if settings.ENABLE_SCHEDULER:
        scheduler.add_job(
            scheduled_generate_daily_summary,
            trigger="cron",
            hour=settings.DAILY_SUMMARY_HOUR,
            minute=settings.DAILY_SUMMARY_MINUTE,
            id="daily_summary",
            name="每日汇总数据生成",
        )
        scheduler.start()
        logger.info(
            f"定时任务已启动: "
            f"每日 {settings.DAILY_SUMMARY_HOUR:02d}:{settings.DAILY_SUMMARY_MINUTE:02d}"
            f" 生成汇总数据"
        )

    logger.info(f"服务地址: http://{settings.HOST}:{settings.PORT}")
    logger.info(f"API 文档: http://{settings.HOST}:{settings.PORT}/docs")
    logger.info("=" * 60)

    yield

    # 关闭时
    logger.info("正在关闭服务...")
    if scheduler.running:
        scheduler.shutdown(wait=False)
    logger.info("服务已关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title="影刀社区 · BI 看板 API",
    description="企业级运营数据看板后端服务 — 监控/趋势/异常/归因/风险",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# 注册中间件
setup_middleware(app)

# 注册路由
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(posts.router)
app.include_router(export.router)
app.include_router(admin.router)
app.include_router(websocket.router)
app.include_router(upload.router)


@app.get("/", summary="服务健康检查")
def root():
    """根路径 — 服务健康检查"""
    return {
        "service": "影刀社区 · BI 看板 API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", summary="健康检查")
def health_check():
    """健康检查端点"""
    from app.database import get_db_type

    supabase_status = None
    if settings.SUPABASE_URL:
        try:
            from app.supabase_client import get_supabase_status
            supabase_status = get_supabase_status()
        except Exception:
            supabase_status = {"connected": False}

    db_host = settings.DATABASE_URL
    if "@" in db_host:
        db_host = db_host.split("@")[-1].split("/")[0]

    return {
        "status": "ok",
        "db_type": get_db_type(),
        "database": db_host,
        "supabase": supabase_status,
        "websocket_connections": websocket.manager.connection_count,
    }


@app.get("/api/v1/status", summary="系统状态")
def system_status():
    """系统状态端点"""
    from app.database import get_db_type

    supabase_status = None
    if settings.SUPABASE_URL:
        try:
            from app.supabase_client import get_supabase_status
            supabase_status = get_supabase_status()
        except Exception as e:
            supabase_status = {"connected": False, "error": str(e)}

    # 尝试查帖子数
    post_count = -1
    try:
        from app.database import SessionLocal
        from app.models.post import Post
        db = SessionLocal()
        post_count = db.query(Post).count()
        db.close()
    except Exception:
        pass

    return {
        "service": "影刀社区 · BI 看板 API",
        "version": "1.0.0",
        "status": "running",
        "db_type": get_db_type(),
        "post_count": post_count,
        "supabase": supabase_status,
    }


# 程序入口
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
