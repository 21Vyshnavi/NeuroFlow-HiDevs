import os
import logging
from backend.db.pool import db_pool

logger = logging.getLogger(__name__)

async def run_migrations():
    pool = db_pool.get_pool()
    if not pool:
        raise RuntimeError("Database pool not initialized.")

    async with pool.acquire() as conn:
        # Check if the tables exist
        tables_exist = await conn.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'documents')"
        )
        if not tables_exist:
            logger.info("Database schema not found. Executing 001_schema.sql...")
            # Try to read local file or absolute file path
            schema_path = "/Users/vaish/Downloads/projects/Complete Recommendation System/NeuroFlow-HiDevs/infra/init/001_schema.sql"
            if os.path.exists(schema_path):
                with open(schema_path, "r") as f:
                    schema_sql = f.read()
                await conn.execute(schema_sql)
                logger.info("Database schema successfully applied.")
            else:
                logger.error(f"Schema file not found at {schema_path}")
        else:
            logger.info("Database schema already exists. Skipping migrations.")
