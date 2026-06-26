"""
Redis 缓存工具 — 对应需求文档 3.2
"""
import json
from functools import wraps
from typing import Optional, Callable
from app.config import settings

# redis 为可选依赖
try:
    import redis as _redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False


class CacheManager:
    """缓存管理器 — 支持 Redis 和内存缓存"""

    def __init__(self):
        self._redis = None
        self._memory_cache = {}
        if settings.USE_REDIS and HAS_REDIS:
            try:
                self._redis = _redis.from_url(settings.REDIS_URL, decode_responses=True)
                self._redis.ping()
            except Exception:
                self._redis = None

    def get(self, key: str) -> Optional[str]:
        """获取缓存"""
        if self._redis:
            return self._redis.get(key)
        return self._memory_cache.get(key)

    def set(self, key: str, value: str, ttl: int = 300) -> None:
        """设置缓存，ttl 单位为秒"""
        if self._redis:
            self._redis.setex(key, ttl, value)
        else:
            self._memory_cache[key] = value

    def delete(self, key: str) -> None:
        """删除缓存"""
        if self._redis:
            self._redis.delete(key)
        else:
            self._memory_cache.pop(key, None)

    def delete_pattern(self, pattern: str) -> None:
        """按模式删除缓存"""
        if self._redis:
            keys = self._redis.keys(pattern)
            if keys:
                self._redis.delete(*keys)
        else:
            keys_to_delete = [k for k in self._memory_cache if pattern.replace("*", "") in k]
            for k in keys_to_delete:
                self._memory_cache.pop(k, None)

    def get_json(self, key: str) -> Optional[dict]:
        """获取 JSON 缓存"""
        val = self.get(key)
        if val:
            try:
                return json.loads(val)
            except json.JSONDecodeError:
                return None
        return None

    def set_json(self, key: str, value: dict, ttl: int = 300) -> None:
        """设置 JSON 缓存"""
        self.set(key, json.dumps(value, ensure_ascii=False, default=str), ttl)


# 全局缓存实例
cache = CacheManager()


def cached(ttl: int = 300, key_prefix: str = ""):
    """缓存装饰器"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 构建缓存 key
            key_parts = [key_prefix or func.__name__]
            key_parts.extend([str(a) for a in args])
            key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
            cache_key = ":".join(key_parts)

            # 尝试从缓存获取
            cached_val = cache.get_json(cache_key)
            if cached_val is not None:
                return cached_val

            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache.set_json(cache_key, result if isinstance(result, dict) else {"value": result}, ttl)
            return result
        return wrapper
    return decorator


def invalidate_cache(pattern: str):
    """清除指定模式的缓存"""
    cache.delete_pattern(pattern)
