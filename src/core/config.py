"""
文件名: config.py
描述: 头条矩阵系统配置管理模块

本模块负责管理应用的所有配置信息，包括：
1. 环境变量读取和验证
2. 数据库连接配置
3. Redis缓存配置
4. AI服务配置
5. 安全相关配置
6. 日志配置

依赖模块:
   - pydantic: 数据验证和设置管理
   - pydantic-settings: 环境变量管理

使用示例:
   >>> from src.core.config import settings
   >>> print(settings.DATABASE_URL)
   >>> print(settings.OPENAI_API_KEY)

注意事项:
   - 敏感信息必须通过环境变量传入
   - 生产环境配置需要特别注意安全性
   - 配置变更需要重启应用生效

作者: Think Ship Team
创建日期: 2024-12-26
最后修改: 2024-12-26
版本: 1.0.0
"""

import secrets
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from pydantic import (
    AnyHttpUrl,
    HttpUrl,
    PostgresDsn,
    RedisDsn,
    validator,
    Field,
)
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    应用配置类
    
    使用Pydantic BaseSettings自动从环境变量读取配置
    """
    
    # ===== 基础配置 =====
    PROJECT_NAME: str = "头条矩阵系统"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "智能内容生产与发布平台"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True, env="DEBUG")
    
    # API配置
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8天
    
    # ===== 服务器配置 =====
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    
    # CORS配置
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:8000",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8000",
        ],
        env="BACKEND_CORS_ORIGINS"
    )
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """处理CORS origins配置"""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # ===== 数据库配置 =====
    # PostgreSQL配置
    POSTGRES_SERVER: str = Field(default="localhost", env="POSTGRES_SERVER")
    POSTGRES_USER: str = Field(default="postgres", env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(default="", env="POSTGRES_PASSWORD")
    POSTGRES_DB: str = Field(default="think_ship", env="POSTGRES_DB")
    POSTGRES_PORT: int = Field(default=5432, env="POSTGRES_PORT")
    
    # PostgreSQL管理员配置（用于创建表）
    POSTGRES_ADMIN_USER: str = Field(default="postgres", env="POSTGRES_ADMIN_USER")
    POSTGRES_ADMIN_PASSWORD: str = Field(default="", env="POSTGRES_ADMIN_PASSWORD")
    
    DATABASE_URL: Optional[PostgresDsn] = None
    
    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        """组装数据库连接URL"""
        if isinstance(v, str):
            return v
        user = values.get("POSTGRES_USER")
        password = values.get("POSTGRES_PASSWORD")
        host = values.get("POSTGRES_SERVER")
        port = values.get("POSTGRES_PORT")
        db = values.get("POSTGRES_DB")
        
        if password:
            return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"
        else:
            return f"postgresql+asyncpg://{user}@{host}:{port}/{db}"
    
    # 数据库连接池配置
    DATABASE_POOL_SIZE: int = Field(default=5, env="DATABASE_POOL_SIZE")
    DATABASE_MAX_OVERFLOW: int = Field(default=10, env="DATABASE_MAX_OVERFLOW")
    DATABASE_POOL_TIMEOUT: int = Field(default=30, env="DATABASE_POOL_TIMEOUT")
    
    # ===== Redis配置 =====
    REDIS_HOST: str = Field(default="localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, env="REDIS_PORT")
    REDIS_PASSWORD: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    REDIS_DB: int = Field(default=0, env="REDIS_DB")
    
    REDIS_URL: Optional[RedisDsn] = None
    
    @validator("REDIS_URL", pre=True)
    def assemble_redis_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        """组装Redis连接URL"""
        if isinstance(v, str):
            return v
        
        scheme = "redis"
        host = values.get("REDIS_HOST")
        port = values.get("REDIS_PORT")
        password = values.get("REDIS_PASSWORD")
        db = values.get("REDIS_DB")
        
        if password:
            return f"{scheme}://:{password}@{host}:{port}/{db}"
        return f"{scheme}://{host}:{port}/{db}"
    
    # ===== AI服务配置 =====
    # OpenAI配置
    OPENAI_API_KEY: str = Field(default="", env="OPENAI_API_KEY")
    OPENAI_API_BASE: str = Field(default="https://api.openai.com/v1", env="OPENAI_API_BASE")
    OPENAI_MODEL: str = Field(default="gpt-3.5-turbo", env="OPENAI_MODEL")
    OPENAI_MAX_TOKENS: int = Field(default=2048, env="OPENAI_MAX_TOKENS")
    OPENAI_TEMPERATURE: float = Field(default=0.7, env="OPENAI_TEMPERATURE")
    
    # Anthropic配置
    ANTHROPIC_API_KEY: str = Field(default="", env="ANTHROPIC_API_KEY")
    ANTHROPIC_MODEL: str = Field(default="claude-3-sonnet-20240229", env="ANTHROPIC_MODEL")
    
    # AI服务超时配置
    AI_REQUEST_TIMEOUT: int = Field(default=60, env="AI_REQUEST_TIMEOUT")
    AI_MAX_RETRIES: int = Field(default=3, env="AI_MAX_RETRIES")
    
    # ===== Celery配置 =====
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/1", env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/2", env="CELERY_RESULT_BACKEND")
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: List[str] = ["json"]
    CELERY_TIMEZONE: str = "Asia/Shanghai"
    CELERY_ENABLE_UTC: bool = True
    
    # ===== 爬虫配置 =====
    # 请求配置
    REQUEST_TIMEOUT: int = Field(default=30, env="REQUEST_TIMEOUT")
    REQUEST_DELAY: float = Field(default=1.0, env="REQUEST_DELAY")  # 请求间隔(秒)
    MAX_CONCURRENT_REQUESTS: int = Field(default=10, env="MAX_CONCURRENT_REQUESTS")
    
    # User-Agent配置
    USER_AGENTS: List[str] = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    ]
    
    # 代理配置
    PROXY_ENABLED: bool = Field(default=False, env="PROXY_ENABLED")
    PROXY_URLS: List[str] = Field(default=[], env="PROXY_URLS")
    
    # ===== 文件存储配置 =====
    # 本地存储配置
    UPLOAD_DIR: Path = Field(default=Path("uploads"), env="UPLOAD_DIR")
    MAX_FILE_SIZE: int = Field(default=10 * 1024 * 1024, env="MAX_FILE_SIZE")  # 10MB
    
    # 对象存储配置（阿里云OSS/MinIO）
    OBJECT_STORAGE_TYPE: str = Field(default="local", env="OBJECT_STORAGE_TYPE")  # local/oss/minio
    OSS_ACCESS_KEY_ID: str = Field(default="", env="OSS_ACCESS_KEY_ID")
    OSS_ACCESS_KEY_SECRET: str = Field(default="", env="OSS_ACCESS_KEY_SECRET")
    OSS_BUCKET_NAME: str = Field(default="", env="OSS_BUCKET_NAME")
    OSS_ENDPOINT: str = Field(default="", env="OSS_ENDPOINT")
    
    # ===== 安全配置 =====
    # JWT配置
    JWT_ALGORITHM: str = "HS256"
    JWT_SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    
    # 密码配置
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_HASH_ROUNDS: int = 12
    
    # 限流配置
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    
    # ===== 监控配置 =====
    # Sentry配置
    SENTRY_DSN: Optional[HttpUrl] = Field(default=None, env="SENTRY_DSN")
    
    # 日志配置
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FILE_MAX_SIZE: str = Field(default="100 MB", env="LOG_FILE_MAX_SIZE")
    LOG_FILE_RETENTION: str = Field(default="30 days", env="LOG_FILE_RETENTION")
    
    # ===== 业务配置 =====
    # 内容生成配置
    CONTENT_MIN_LENGTH: int = Field(default=100, env="CONTENT_MIN_LENGTH")
    CONTENT_MAX_LENGTH: int = Field(default=5000, env="CONTENT_MAX_LENGTH")
    
    # 发布配置
    MAX_ACCOUNTS_PER_PLATFORM: int = Field(default=50, env="MAX_ACCOUNTS_PER_PLATFORM")
    PUBLISH_RETRY_TIMES: int = Field(default=3, env="PUBLISH_RETRY_TIMES")
    PUBLISH_RETRY_DELAY: int = Field(default=60, env="PUBLISH_RETRY_DELAY")  # 秒
    
    # 热点采集配置
    HOT_TOPIC_FETCH_INTERVAL: int = Field(default=300, env="HOT_TOPIC_FETCH_INTERVAL")  # 5分钟
    HOT_TOPIC_MIN_SCORE: float = Field(default=0.6, env="HOT_TOPIC_MIN_SCORE")
    
    class Config:
        """Pydantic配置"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        
    def get_database_url(self) -> str:
        """获取数据库连接URL"""
        return str(self.DATABASE_URL)
    
    def get_redis_url(self) -> str:
        """获取Redis连接URL"""
        return str(self.REDIS_URL)
    
    def is_production(self) -> bool:
        """判断是否为生产环境"""
        return self.ENVIRONMENT.lower() == "production"
    
    def is_development(self) -> bool:
        """判断是否为开发环境"""
        return self.ENVIRONMENT.lower() == "development"


# 创建全局配置实例
settings = Settings()

# 导出常用配置
__all__ = ["settings", "Settings"]