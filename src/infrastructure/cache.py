"""
文件名: cache.py
描述: Redis缓存连接和管理模块

本模块提供Redis缓存的连接管理和操作功能：
1. Redis连接池管理
2. 缓存操作封装
3. 连接健康检查
4. 序列化和反序列化
5. 缓存策略配置

依赖模块:
   - redis: Redis客户端
   - orjson: 高性能JSON序列化
   - typing: 类型注解

使用示例:
   >>> cache = RedisCache()
   >>> await cache.set("key", {"data": "value"}, expire=3600)
   >>> result = await cache.get("key")

注意事项:
   - 使用连接池避免连接泄漏
   - 异常情况下优雅降级
   - 序列化使用orjson提升性能

作者: Think Ship Team
创建日期: 2024-12-26
最后修改: 2024-12-26
版本: 1.0.0
"""

import asyncio
from typing import Any, Dict, Optional, Union, List
import orjson
from loguru import logger

try:
    import redis.asyncio as redis
    from redis.asyncio import ConnectionPool
except ImportError:
    logger.error("Redis模块未安装，请运行：pip install redis")
    raise

from src.core.config import settings
from src.core.exceptions import DatabaseException


class RedisCache:
    """
    Redis缓存管理类
    
    提供异步Redis操作的封装，包括连接管理、数据序列化等功能
    """
    
    def __init__(self):
        """初始化Redis缓存管理器"""
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[redis.Redis] = None
        self._connected = False
    
    async def connect(self) -> None:
        """
        建立Redis连接
        
        Raises:
            DatabaseException: 连接失败时抛出异常
        """
        try:
            # 创建连接池
            self._pool = ConnectionPool.from_url(
                settings.get_redis_url(),
                max_connections=20,
                retry_on_timeout=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                health_check_interval=30,
            )
            
            # 创建Redis客户端
            self._client = redis.Redis(
                connection_pool=self._pool,
                decode_responses=False,  # 使用bytes处理，避免编码问题
            )
            
            # 测试连接
            await self._client.ping()
            
            self._connected = True
            logger.info("✅ Redis连接建立成功")
            
        except Exception as e:
            logger.error(f"❌ Redis连接失败: {e}")
            raise DatabaseException(
                message=f"Redis连接失败: {str(e)}",
                original_error=e
            )
    
    async def disconnect(self) -> None:
        """关闭Redis连接"""
        if self._client:
            await self._client.close()
            self._connected = False
            logger.info("Redis连接已关闭")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Redis健康检查
        
        Returns:
            Dict[str, Any]: 健康状态信息
        """
        try:
            if not self._connected or not self._client:
                return {
                    "status": "unhealthy",
                    "message": "Redis未连接"
                }
            
            # 测试ping
            start_time = asyncio.get_event_loop().time()
            await self._client.ping()
            response_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            # 获取Redis信息
            info = await self._client.info()
            
            return {
                "status": "healthy",
                "message": "Redis连接正常",
                "response_time_ms": round(response_time, 2),
                "redis_version": info.get("redis_version"),
                "connected_clients": info.get("connected_clients"),
                "used_memory_human": info.get("used_memory_human"),
            }
            
        except Exception as e:
            logger.error(f"Redis健康检查失败: {e}")
            return {
                "status": "unhealthy",
                "message": f"Redis健康检查失败: {str(e)}"
            }
    
    def _serialize(self, value: Any) -> bytes:
        """
        序列化数据
        
        Args:
            value: 要序列化的数据
            
        Returns:
            bytes: 序列化后的字节数据
        """
        if isinstance(value, (str, int, float, bool)):
            return str(value).encode('utf-8')
        else:
            return orjson.dumps(value)
    
    def _deserialize(self, value: bytes) -> Any:
        """
        反序列化数据
        
        Args:
            value: 序列化的字节数据
            
        Returns:
            Any: 反序列化后的数据
        """
        try:
            return orjson.loads(value)
        except (orjson.JSONDecodeError, ValueError):
            # 如果不是JSON，尝试作为字符串处理
            try:
                return value.decode('utf-8')
            except UnicodeDecodeError:
                return value
    
    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None,
        nx: bool = False,
        xx: bool = False
    ) -> bool:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            expire: 过期时间（秒）
            nx: 仅当键不存在时设置
            xx: 仅当键存在时设置
            
        Returns:
            bool: 设置是否成功
        """
        try:
            if not self._client:
                logger.warning("Redis未连接，跳过缓存设置")
                return False
            
            serialized_value = self._serialize(value)
            
            result = await self._client.set(
                key,
                serialized_value,
                ex=expire,
                nx=nx,
                xx=xx
            )
            
            return bool(result)
            
        except Exception as e:
            logger.error(f"Redis设置失败 key={key}: {e}")
            return False
    
    async def get(self, key: str, default: Any = None) -> Any:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            default: 默认值
            
        Returns:
            Any: 缓存值或默认值
        """
        try:
            if not self._client:
                logger.warning("Redis未连接，返回默认值")
                return default
            
            value = await self._client.get(key)
            
            if value is None:
                return default
            
            return self._deserialize(value)
            
        except Exception as e:
            logger.error(f"Redis获取失败 key={key}: {e}")
            return default
    
    async def delete(self, *keys: str) -> int:
        """
        删除缓存键
        
        Args:
            keys: 要删除的键列表
            
        Returns:
            int: 删除的键数量
        """
        try:
            if not self._client or not keys:
                return 0
            
            return await self._client.delete(*keys)
            
        except Exception as e:
            logger.error(f"Redis删除失败 keys={keys}: {e}")
            return 0
    
    async def exists(self, *keys: str) -> int:
        """
        检查键是否存在
        
        Args:
            keys: 要检查的键列表
            
        Returns:
            int: 存在的键数量
        """
        try:
            if not self._client or not keys:
                return 0
            
            return await self._client.exists(*keys)
            
        except Exception as e:
            logger.error(f"Redis检查存在失败 keys={keys}: {e}")
            return 0
    
    async def expire(self, key: str, seconds: int) -> bool:
        """
        设置键的过期时间
        
        Args:
            key: 缓存键
            seconds: 过期时间（秒）
            
        Returns:
            bool: 设置是否成功
        """
        try:
            if not self._client:
                return False
            
            return await self._client.expire(key, seconds)
            
        except Exception as e:
            logger.error(f"Redis设置过期时间失败 key={key}: {e}")
            return False
    
    async def ttl(self, key: str) -> int:
        """
        获取键的剩余过期时间
        
        Args:
            key: 缓存键
            
        Returns:
            int: 剩余过期时间（秒），-1表示永不过期，-2表示键不存在
        """
        try:
            if not self._client:
                return -2
            
            return await self._client.ttl(key)
            
        except Exception as e:
            logger.error(f"Redis获取TTL失败 key={key}: {e}")
            return -2
    
    async def incr(self, key: str, amount: int = 1) -> int:
        """
        递增计数器
        
        Args:
            key: 计数器键
            amount: 递增量
            
        Returns:
            int: 递增后的值
        """
        try:
            if not self._client:
                return 0
            
            return await self._client.incrby(key, amount)
            
        except Exception as e:
            logger.error(f"Redis递增失败 key={key}: {e}")
            return 0
    
    async def hset(self, name: str, mapping: Dict[str, Any]) -> int:
        """
        设置哈希字段
        
        Args:
            name: 哈希名称
            mapping: 字段映射
            
        Returns:
            int: 设置的字段数量
        """
        try:
            if not self._client:
                return 0
            
            # 序列化所有值
            serialized_mapping = {
                k: self._serialize(v) for k, v in mapping.items()
            }
            
            return await self._client.hset(name, mapping=serialized_mapping)
            
        except Exception as e:
            logger.error(f"Redis哈希设置失败 name={name}: {e}")
            return 0
    
    async def hget(self, name: str, key: str) -> Any:
        """
        获取哈希字段值
        
        Args:
            name: 哈希名称
            key: 字段名
            
        Returns:
            Any: 字段值
        """
        try:
            if not self._client:
                return None
            
            value = await self._client.hget(name, key)
            
            if value is None:
                return None
            
            return self._deserialize(value)
            
        except Exception as e:
            logger.error(f"Redis哈希获取失败 name={name} key={key}: {e}")
            return None
    
    async def hgetall(self, name: str) -> Dict[str, Any]:
        """
        获取所有哈希字段
        
        Args:
            name: 哈希名称
            
        Returns:
            Dict[str, Any]: 所有字段的字典
        """
        try:
            if not self._client:
                return {}
            
            result = await self._client.hgetall(name)
            
            # 反序列化所有值
            return {
                k.decode('utf-8') if isinstance(k, bytes) else k: self._deserialize(v)
                for k, v in result.items()
            }
            
        except Exception as e:
            logger.error(f"Redis哈希获取全部失败 name={name}: {e}")
            return {}


# 全局Redis实例
redis_cache = RedisCache()

# 导出
__all__ = ["RedisCache", "redis_cache"]