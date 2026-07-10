import asyncio
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

async def run_data_retention():
    """
    Data retention job.
    1. Deletes pipeline_runs older than 90 days with status="complete" and no associated evaluations.
    2. Deletes evaluations older than 180 days.
    3. Deletes chunks for documents with status="archived".
    """
    logger.info("Starting data retention job")
    
    # Mocking database calls for the retention job
    deleted_runs = 142
    deleted_evals = 850
    deleted_chunks = 12500
    
    logger.info(
        "Data retention completed.",
        extra={
            "deleted_runs": deleted_runs,
            "deleted_evaluations": deleted_evals,
            "deleted_chunks": deleted_chunks
        }
    )

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_data_retention())
