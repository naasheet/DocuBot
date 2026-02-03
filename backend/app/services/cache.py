import json
from typing import Any, Optional

import redis

from app.config import settings


class CacheService:
    def __init__(self, url: Optional[str] = None, default_ttl: Optional[int] = None) -> None:
        self.url = url or settings.REDIS_URL
        self.default_ttl = default_ttl or settings.CACHE_TTL_SECONDS
        self._client = redis.Redis.from_url(self.url, decode_responses=True)

    def get_json(self, key: str) -> Optional[Any]:
        value = self._client.get(key)
        if value is None:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return None

    def set_json(self, key: str, payload: Any, ttl: Optional[int] = None) -> None:
        data = json.dumps(payload)
        self._client.setex(key, ttl or self.default_ttl, data)

    def delete(self, key: str) -> None:
        self._client.delete(key)

    def ping(self) -> bool:
        try:
            return self._client.ping()
        except redis.RedisError:
            return False
