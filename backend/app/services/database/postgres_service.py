from tortoise import Tortoise
from typing import Optional


class PostgresService:
    def __init__(self, postgres_url: str):
        self.postgres_url = postgres_url
        self._initialized = False
    
    async def initialize(self):
        if not self._initialized:
            await Tortoise.init(
                db_url=self.postgres_url,
                modules={'models': ['app.models']}
            )
            self._initialized = True
    
    async def generate_schema(self):
        await self.initialize()
        await Tortoise.generate_schemas()
    
    async def close(self):
        if self._initialized:
            await Tortoise.close_connections()
