"""
中间件 — CORS、请求日志
"""
import time
import logging
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

logger = logging.getLogger("bi-dashboard")


def setup_cors(app):
    """配置 CORS 中间件"""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def setup_middleware(app):
    """注册所有中间件"""
    setup_cors(app)

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """请求日志中间件"""
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(
            f"{request.method} {request.url.path} "
            f"status={response.status_code} "
            f"duration={process_time:.3f}s"
        )
        response.headers["X-Process-Time"] = str(process_time)
        return response
