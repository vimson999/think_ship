"""
文件名: main.py
描述: 头条矩阵系统FastAPI应用主入口

本模块是头条矩阵系统的核心启动文件，负责：
1. FastAPI应用初始化和配置
2. 中间件注册（CORS、日志、错误处理等）
3. API路由注册
4. 数据库连接初始化
5. 应用启动和关闭事件处理

依赖模块:
   - fastapi: Web框架核心
   - uvicorn: ASGI服务器
   - loguru: 日志记录

使用示例:
   >>> # 开发环境启动
   >>> uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
   
   >>> # 生产环境启动
   >>> gunicorn src.main:app -w 4 -k uvicorn.workers.UvicornWorker

注意事项:
   - 确保环境变量正确配置
   - 数据库连接需要在启动前验证
   - 生产环境需要配置适当的日志级别

作者: Think Ship Team
创建日期: 2024-12-26
最后修改: 2024-12-26
版本: 1.0.0
"""

import sys
from pathlib import Path
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

# 添加src目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from src.core.config import settings
from src.core.exceptions import BusinessException
from src.api.v1 import api_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    FastAPI应用生命周期管理
    
    处理应用启动和关闭时的初始化和清理工作
    """
    # 应用启动事件
    logger.info("🚀 头条矩阵系统启动中...")
    
    # TODO: 初始化数据库连接池
    # TODO: 初始化Redis连接
    # TODO: 验证AI服务连接
    # TODO: 启动定时任务
    
    logger.info("✅ 系统初始化完成")
    
    yield
    
    # 应用关闭事件  
    logger.info("🛑 头条矩阵系统关闭中...")
    
    # TODO: 关闭数据库连接池
    # TODO: 关闭Redis连接
    # TODO: 停止定时任务
    
    logger.info("✅ 系统清理完成")


def create_application() -> FastAPI:
    """
    创建和配置FastAPI应用实例
    
    Returns:
        FastAPI: 配置完成的应用实例
    """
    # 创建FastAPI应用
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="智能内容生产与发布平台",
        version="1.0.0",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
        lifespan=lifespan,
    )
    
    # 配置CORS中间件
    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    # 注册全局异常处理器
    @app.exception_handler(BusinessException)
    async def business_exception_handler(request: Request, exc: BusinessException):
        """业务异常处理器"""
        logger.error(f"业务异常: {exc.message} - URL: {request.url}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": True,
                "message": exc.message,
                "code": exc.code,
                "timestamp": exc.timestamp.isoformat(),
            }
        )
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """全局异常处理器"""
        logger.error(f"系统异常: {str(exc)} - URL: {request.url}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "message": "系统内部错误，请稍后重试",
                "code": "INTERNAL_ERROR",
            }
        )
    
    # 注册API路由
    app.include_router(api_router, prefix=settings.API_V1_STR)
    
    # 健康检查端点
    @app.get("/health")
    async def health_check():
        """系统健康检查"""
        return {
            "status": "healthy",
            "service": settings.PROJECT_NAME,
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT,
        }
    
    @app.get("/")
    async def root():
        """根路径欢迎信息"""
        return {
            "message": f"欢迎使用{settings.PROJECT_NAME}",
            "docs": "/docs",
            "health": "/health",
        }
    
    return app


# 创建应用实例
app = create_application()

# 配置日志
def setup_logging():
    """配置系统日志"""
    # 移除默认处理器
    logger.remove()
    
    # 控制台日志
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
               "<level>{message}</level>",
        level="INFO" if not settings.DEBUG else "DEBUG",
        colorize=True,
    )
    
    # 文件日志
    logger.add(
        "logs/app/app_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="30 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level="INFO",
        encoding="utf-8",
    )
    
    # 错误日志
    logger.add(
        "logs/error/error_{time:YYYY-MM-DD}.log",
        rotation="1 day", 
        retention="30 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level="ERROR",
        encoding="utf-8",
    )


# 初始化日志
setup_logging()

if __name__ == "__main__":
    import uvicorn
    
    logger.info("🔧 开发模式启动")
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["src"],
        log_level="info",
    )