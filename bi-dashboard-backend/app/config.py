"""
应用配置管理
从 .env 文件和环境变量中加载配置
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # 数据库后端选择: "sqlite" | "supabase"
    DB_BACKEND: str = "sqlite"

    # SQLite / PostgreSQL 直连
    DATABASE_URL: str = "sqlite:///./bi_dashboard.db"

    # Supabase (REST API 模式，当 DB_BACKEND=supabase 时使用)
    SUPABASE_URL: str = ""
    SUPABASE_PUBLISHABLE_KEY: str = ""
    SUPABASE_SECRET_KEY: str = ""
    SUPABASE_JWKS_URL: str = ""
    SUPABASE_DB_PASSWORD: str = ""

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    USE_REDIS: bool = False

    # JWT
    SECRET_KEY: str = "yingdao-community-bi-dashboard-secret-key-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # 服务
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # 定时任务
    ENABLE_SCHEDULER: bool = True
    DAILY_SUMMARY_HOUR: int = 2
    DAILY_SUMMARY_MINUTE: int = 0

    # 影刀 RPA 开放平台（Excel 上传 + 流程异步执行）
    YINGDAO_TOKEN: str = "AP_WHyUK1D5ZsHpxBXH"
    YINGDAO_UPLOAD_URL: str = "https://power-api.yingdao.com/oapi/power/v1/file/upload"
    YINGDAO_FLOW_URL: str = "https://power-api.yingdao.com/oapi/power/v1/rest/flow/4b8eb5ba-1ebb-4173-8023-f80511d2dd18/execute"
    YINGDAO_FLOW_ASYNC_URL: str = "https://power-api.yingdao.com/oapi/power/v1/rest/flow/4b8eb5ba-1ebb-4173-8023-f80511d2dd18/execute/async"
    YINGDAO_RESULT_URL: str = "https://power-api.yingdao.com/oapi/power/v1/rest/flow/execute/result"
    YINGDAO_TIMEOUT: int = 60

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
