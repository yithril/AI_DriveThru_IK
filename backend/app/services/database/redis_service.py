import redis.asyncio as redis
from typing import Optional, Any
import json


class RedisService:
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self._client: Optional[redis.Redis] = None
    
    async def get_client(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.from_url(self.redis_url, decode_responses=True)
        return self._client
    
    async def get(self, key: str) -> Optional[str]:
        client = await self.get_client()
        return await client.get(key)
    
    async def set(self, key: str, value: str, expire: Optional[int] = None) -> bool:
        client = await self.get_client()
        return await client.set(key, value, ex=expire)
    
    async def get_json(self, key: str) -> Optional[dict]:
        value = await self.get(key)
        if value:
            return json.loads(value)
        return None
    
    async def set_json(self, key: str, value: dict, expire: Optional[int] = None) -> bool:
        return await self.set(key, json.dumps(value), expire)
    
    async def delete(self, key: str) -> bool:
        client = await self.get_client()
        return await client.delete(key) > 0
    
    async def close(self):
        if self._client:
            await self._client.close()
