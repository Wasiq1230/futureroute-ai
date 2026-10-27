import json
from typing import Any
import redis.asyncio as redis
from redis.exceptions import RedisError
from backend.app.core.config import get_settings


class Cache:
    def __init__(self) -> None:
        self._client: redis.Redis | None = None

    async def client(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.from_url(get_settings().redis_url, decode_responses=True)
        return self._client

    async def get_json(self, key: str) -> Any | None:
        try:
            value = await (await self.client()).get(key)
            return json.loads(value) if value else None
        except RedisError:
            return None

    async def set_json(self, key: str, value: Any, ttl: int = 300) -> None:
        try:
            await (await self.client()).setex(key, ttl, json.dumps(value))
        except RedisError:
            return


cache = Cache()
