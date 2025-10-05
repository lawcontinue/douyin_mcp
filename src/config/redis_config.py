"""
Redis配置
"""

import json
import pickle
from typing import Any, Optional, Union
from datetime import timedelta

import redis.asyncio as redis
from loguru import logger

from .settings import settings


class RedisConfig:
    """Redis配置类"""
    
    def __init__(self):
        self.client: Optional[redis.Redis] = None
        self._initialized = False
    
    def initialize(self) -> None:
        """初始化Redis连接"""
        if self._initialized:
            logger.warning("Redis已经初始化")
            return
        
        try:
            # 解析Redis URL
            self.client = redis.from_url(
                settings.REDIS_URL,
                password=settings.REDIS_PASSWORD,
                db=settings.REDIS_DB,
                decode_responses=False,  # 使用bytes模式以支持pickle
                health_check_interval=30
            )
            
            self._initialized = True
            logger.info("Redis连接初始化成功")
            
        except Exception as e:
            logger.error(f"Redis初始化失败: {e}")
            raise
    
    async def ping(self) -> bool:
        """检查Redis连接"""
        if not self._initialized:
            self.initialize()
        
        try:
            await self.client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis连接检查失败: {e}")
            return False
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[Union[int, timedelta]] = None,
        serializer: str = "json"
    ) -> bool:
        """设置缓存值"""
        if not self._initialized:
            self.initialize()
        
        try:
            # 序列化值
            if serializer == "json":
                serialized_value = json.dumps(value, ensure_ascii=False, default=str)
            elif serializer == "pickle":
                serialized_value = pickle.dumps(value)
            else:
                serialized_value = str(value)
            
            # 设置TTL
            if ttl is None:
                ttl = settings.CACHE_TTL
            
            await self.client.set(key, serialized_value, ex=ttl)
            return True
            
        except Exception as e:
            logger.error(f"Redis设置失败 key={key}: {e}")
            return False
    
    async def get(
        self,
        key: str,
        default: Any = None,
        serializer: str = "json"
    ) -> Any:
        """获取缓存值"""
        if not self._initialized:
            self.initialize()
        
        try:
            value = await self.client.get(key)
            if value is None:
                return default
            
            # 反序列化值
            if serializer == "json":
                return json.loads(value.decode('utf-8'))
            elif serializer == "pickle":
                return pickle.loads(value)
            else:
                return value.decode('utf-8')
                
        except Exception as e:
            logger.error(f"Redis获取失败 key={key}: {e}")
            return default
    
    async def delete(self, *keys: str) -> int:
        """删除缓存键"""
        if not self._initialized:
            self.initialize()
        
        try:
            return await self.client.delete(*keys)
        except Exception as e:
            logger.error(f"Redis删除失败 keys={keys}: {e}")
            return 0
    
    async def exists(self, *keys: str) -> int:
        """检查键是否存在"""
        if not self._initialized:
            self.initialize()
        
        try:
            return await self.client.exists(*keys)
        except Exception as e:
            logger.error(f"Redis存在检查失败 keys={keys}: {e}")
            return 0
    
    async def expire(self, key: str, ttl: Union[int, timedelta]) -> bool:
        """设置键的过期时间"""
        if not self._initialized:
            self.initialize()
        
        try:
            return await self.client.expire(key, ttl)
        except Exception as e:
            logger.error(f"Redis设置过期时间失败 key={key}: {e}")
            return False
    
    async def ttl(self, key: str) -> int:
        """获取键的剩余生存时间"""
        if not self._initialized:
            self.initialize()
        
        try:
            return await self.client.ttl(key)
        except Exception as e:
            logger.error(f"Redis获取TTL失败 key={key}: {e}")
            return -1
    
    async def incr(self, key: str, amount: int = 1) -> int:
        """递增计数器"""
        if not self._initialized:
            self.initialize()
        
        try:
            return await self.client.incr(key, amount)
        except Exception as e:
            logger.error(f"Redis递增失败 key={key}: {e}")
            return 0
    
    async def decr(self, key: str, amount: int = 1) -> int:
        """递减计数器"""
        if not self._initialized:
            self.initialize()
        
        try:
            return await self.client.decr(key, amount)
        except Exception as e:
            logger.error(f"Redis递减失败 key={key}: {e}")
            return 0
    
    async def hset(self, name: str, mapping: dict) -> int:
        """设置哈希表"""
        if not self._initialized:
            self.initialize()
        
        try:
            # 序列化哈希表值
            serialized_mapping = {}
            for k, v in mapping.items():
                if isinstance(v, (dict, list)):
                    serialized_mapping[k] = json.dumps(v, ensure_ascii=False, default=str)
                else:
                    serialized_mapping[k] = str(v)
            
            return await self.client.hset(name, mapping=serialized_mapping)
        except Exception as e:
            logger.error(f"Redis哈希设置失败 name={name}: {e}")
            return 0
    
    async def hget(self, name: str, key: str, default: Any = None) -> Any:
        """获取哈希表值"""
        if not self._initialized:
            self.initialize()
        
        try:
            value = await self.client.hget(name, key)
            if value is None:
                return default
            
            value_str = value.decode('utf-8')
            try:
                # 尝试JSON反序列化
                return json.loads(value_str)
            except json.JSONDecodeError:
                # 如果不是JSON，返回字符串
                return value_str
                
        except Exception as e:
            logger.error(f"Redis哈希获取失败 name={name} key={key}: {e}")
            return default
    
    async def hgetall(self, name: str) -> dict:
        """获取整个哈希表"""
        if not self._initialized:
            self.initialize()
        
        try:
            data = await self.client.hgetall(name)
            result = {}
            
            for k, v in data.items():
                key = k.decode('utf-8')
                value_str = v.decode('utf-8')
                
                try:
                    # 尝试JSON反序列化
                    result[key] = json.loads(value_str)
                except json.JSONDecodeError:
                    # 如果不是JSON，返回字符串
                    result[key] = value_str
            
            return result
            
        except Exception as e:
            logger.error(f"Redis哈希获取全部失败 name={name}: {e}")
            return {}
    
    async def hdel(self, name: str, *keys: str) -> int:
        """删除哈希表字段"""
        if not self._initialized:
            self.initialize()
        
        try:
            return await self.client.hdel(name, *keys)
        except Exception as e:
            logger.error(f"Redis哈希删除失败 name={name} keys={keys}: {e}")
            return 0
    
    async def close(self) -> None:
        """关闭Redis连接"""
        if self.client:
            await self.client.close()
            logger.info("Redis连接已关闭")


# 全局Redis配置实例
redis_config = RedisConfig()


# 便捷函数
async def get_redis() -> RedisConfig:
    """获取Redis实例"""
    if not redis_config._initialized:
        redis_config.initialize()
    return redis_config
