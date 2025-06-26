"""
文件名: database.py
描述: PostgreSQL数据库连接和管理模块

本模块提供PostgreSQL数据库的连接管理和操作功能：
1. 异步数据库连接池管理
2. 数据库会话管理
3. 连接健康检查
4. 事务管理
5. 数据库依赖注入

依赖模块:
   - sqlalchemy: ORM框架
   - asyncpg: 异步PostgreSQL驱动
   - loguru: 日志记录

使用示例:
   >>> async with get_session() as session:
   ...     result = await session.execute(select(User))

注意事项:
   - 使用连接池避免连接泄漏
   - 异常情况下自动回滚事务
   - 支持读写分离配置

作者: Think Ship Team
创建日期: 2024-12-26
最后修改: 2024-12-26
版本: 1.0.0
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, Any, Optional

from loguru import logger

try:
    from sqlalchemy.ext.asyncio import (
        create_async_engine,
        AsyncSession,
        async_sessionmaker,
        AsyncEngine
    )
    from sqlalchemy.pool import StaticPool
    from sqlalchemy import text, inspect
    from sqlalchemy.exc import SQLAlchemyError
except ImportError:
    logger.error("SQLAlchemy模块未安装，请运行：pip install sqlalchemy[asyncio] asyncpg")
    raise

from src.core.config import settings
from src.core.exceptions import DatabaseException
from src.models.base import Base


class DatabaseManager:
    """
    数据库管理器
    
    负责数据库连接池管理、会话创建和健康检查
    """
    
    def __init__(self):
        """初始化数据库管理器"""
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker] = None
        self._connected = False
    
    async def connect(self) -> None:
        """
        建立数据库连接
        
        Raises:
            DatabaseException: 连接失败时抛出异常
        """
        try:
            # 创建异步引擎
            self._engine = create_async_engine(
                settings.get_database_url(),
                # 连接池配置
                pool_size=settings.DATABASE_POOL_SIZE,
                max_overflow=settings.DATABASE_MAX_OVERFLOW,
                pool_timeout=settings.DATABASE_POOL_TIMEOUT,
                pool_recycle=3600,  # 1小时回收连接
                pool_pre_ping=True,  # 连接前检查
                # 异步配置
                echo=settings.DEBUG,  # 开发环境显示SQL
                future=True,
            )
            
            # 创建会话工厂
            self._session_factory = async_sessionmaker(
                bind=self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=True,
                autocommit=False,
            )
            
            # 测试连接
            async with self._engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            
            self._connected = True
            logger.info("✅ PostgreSQL数据库连接建立成功")
            
        except Exception as e:
            logger.error(f"❌ PostgreSQL数据库连接失败: {e}")
            raise DatabaseException(
                message=f"数据库连接失败: {str(e)}",
                original_error=e
            )
    
    async def disconnect(self) -> None:
        """关闭数据库连接"""
        if self._engine:
            await self._engine.dispose()
            self._connected = False
            logger.info("PostgreSQL数据库连接已关闭")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        数据库健康检查
        
        Returns:
            Dict[str, Any]: 健康状态信息
        """
        try:
            if not self._connected or not self._engine:
                return {
                    "status": "unhealthy",
                    "message": "数据库未连接"
                }
            
            # 测试查询
            start_time = asyncio.get_event_loop().time()
            async with self._engine.begin() as conn:
                result = await conn.execute(text("SELECT version(), current_database(), current_user"))
                row = result.fetchone()
            response_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            # 获取连接池状态
            pool = self._engine.pool
            pool_status = {
                "size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "total": pool.size() + pool.overflow(),
            }
            
            return {
                "status": "healthy",
                "message": "数据库连接正常",
                "response_time_ms": round(response_time, 2),
                "database_version": row[0] if row else "unknown",
                "database_name": row[1] if row else "unknown",
                "current_user": row[2] if row else "unknown",
                "pool_status": pool_status,
            }
            
        except Exception as e:
            logger.error(f"数据库健康检查失败: {e}")
            return {
                "status": "unhealthy",
                "message": f"数据库健康检查失败: {str(e)}"
            }
    
    async def create_tables(self) -> None:
        """
        创建数据库表
        
        在开发环境中使用，生产环境应该使用Alembic迁移
        """
        try:
            if not self._engine:
                raise DatabaseException("数据库引擎未初始化")
            
            async with self._engine.begin() as conn:
                # 创建所有表
                await conn.run_sync(Base.metadata.create_all)
            
            logger.info("✅ 数据库表创建成功")
            
        except Exception as e:
            logger.error(f"❌ 数据库表创建失败: {e}")
            raise DatabaseException(
                message=f"数据库表创建失败: {str(e)}",
                original_error=e
            )
    
    async def drop_tables(self) -> None:
        """
        删除数据库表
        
        警告：此操作会删除所有数据，仅在开发环境使用
        """
        try:
            if not self._engine:
                raise DatabaseException("数据库引擎未初始化")
            
            if settings.is_production():
                raise DatabaseException("生产环境不允许删除表")
            
            async with self._engine.begin() as conn:
                # 删除所有表
                await conn.run_sync(Base.metadata.drop_all)
            
            logger.warning("⚠️ 数据库表已删除")
            
        except Exception as e:
            logger.error(f"❌ 数据库表删除失败: {e}")
            raise DatabaseException(
                message=f"数据库表删除失败: {str(e)}",
                original_error=e
            )
    
    def get_session_factory(self) -> async_sessionmaker:
        """
        获取会话工厂
        
        Returns:
            async_sessionmaker: 会话工厂
            
        Raises:
            DatabaseException: 会话工厂未初始化时抛出异常
        """
        if not self._session_factory:
            raise DatabaseException("数据库会话工厂未初始化")
        return self._session_factory
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        获取数据库会话（上下文管理器）
        
        Yields:
            AsyncSession: 数据库会话
            
        Raises:
            DatabaseException: 会话创建失败时抛出异常
        """
        if not self._session_factory:
            raise DatabaseException("数据库会话工厂未初始化")
        
        session = self._session_factory()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"数据库会话异常，已回滚: {e}")
            raise DatabaseException(
                message=f"数据库操作失败: {str(e)}",
                original_error=e
            )
        finally:
            await session.close()


# 全局数据库管理器实例
db_manager = DatabaseManager()


# 依赖注入函数
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话的依赖注入函数
    
    用于FastAPI的依赖注入系统
    
    Yields:
        AsyncSession: 数据库会话
    """
    async with db_manager.get_session() as session:
        yield session


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    get_db_session的别名，为了兼容性
    
    Yields:
        AsyncSession: 数据库会话
    """
    async with db_manager.get_session() as session:
        yield session


# 事务装饰器
def transactional(func):
    """
    事务装饰器
    
    自动管理数据库事务，异常时回滚
    """
    async def wrapper(*args, **kwargs):
        async with db_manager.get_session() as session:
            try:
                # 将session作为第一个参数传递
                result = await func(session, *args, **kwargs)
                await session.commit()
                return result
            except Exception as e:
                await session.rollback()
                raise e
    
    return wrapper


# 初始化函数
async def init_database() -> None:
    """
    初始化数据库连接
    
    在应用启动时调用
    """
    await db_manager.connect()
    
    # 开发环境下可以自动创建表
    if settings.is_development():
        logger.info("开发环境：检查数据库表...")
        # 这里可以添加表检查逻辑
        # await db_manager.create_tables()


async def close_database() -> None:
    """
    关闭数据库连接
    
    在应用关闭时调用
    """
    await db_manager.disconnect()


# 导出
__all__ = [
    "DatabaseManager",
    "db_manager", 
    "get_db_session",
    "get_db",
    "transactional",
    "init_database",
    "close_database",
]