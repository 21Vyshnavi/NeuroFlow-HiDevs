# ruff: noqa
# mypy: ignore-errors
# ruff: noqa
# mypy: ignore-errors
import logging

import asyncpg

from backend.config import settings

logger = logging.getLogger(__name__)

class DatabasePool:
    def __init__(self) -> None:
        self._pool = None

    async def connect(self) -> None:
        if not self._pool:
            logger.info("Initializing asyncpg connection pool...")
            self._pool = await asyncpg.create_pool(
                user=settings.postgres_user,
                password=settings.postgres_password,
                database=settings.postgres_db,
                host=settings.postgres_host,
                port=settings.postgres_port,
                min_size=2,
                max_size=10
            )

    async def disconnect(self) -> None:
        if self._pool:
            logger.info("Closing asyncpg connection pool...")
            await self._pool.close()
            self._pool = None

    def get_pool(self):
        return self._pool

db_pool = DatabasePool()
