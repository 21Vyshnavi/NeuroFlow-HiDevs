import json
import logging
import uuid
import redis.asyncio as redis
from backend.db.pool import db_pool
from backend.config import settings
from pipelines.finetuning.tracker import tracker as mlflow_tracker

logger = logging.getLogger(__name__)

async def submit_finetuning_job(job_id: str, base_model: str, jsonl_path: str, pair_count: int, avg_quality: float):
    # Log run to mlflow
    run_id = mlflow_tracker.start_run(job_id, base_model, pair_count, avg_quality)

    pool = db_pool.get_pool()
    if not pool:
        logger.error("DB Pool offline")
        return

    # Update database status to processing
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO finetune_jobs (id, provider_job_id, base_model, status, training_pair_count, mlflow_run_id)
            VALUES ($1, $2, $3, 'running', $4, $5)
            """,
            uuid.UUID(job_id),
            f"ft-provider-job-{job_id}",
            base_model,
            pair_count,
            run_id
        )

        # Flag training pairs as completed
        await conn.execute(
            "UPDATE training_pairs SET included_in_job = $1 WHERE included_in_job IS NULL",
            uuid.UUID(job_id)
        )

    # Mock background trainer finish trigger
    # In actual pipelines, this would communicate with OpenAI API or local trainer and trigger callback
    await asyncio.sleep(5)
    
    # Complete job successfully
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE finetune_jobs SET status = 'succeeded', completed_at = NOW() WHERE id = $1",
            uuid.UUID(job_id)
        )
    
    # End mlflow run
    mlflow_tracker.end_run(run_id, 0.082, 0.095, pair_count * 150)

    # Update ModelRouter in redis
    try:
        r = redis.Redis(host=settings.redis_host, port=settings.redis_port, password=settings.redis_password)
        # Append mock registered models
        new_model_spec = {
            "model_name": f"neuroflow-finetune-{job_id}",
            "provider": "openai",
            "is_vision": False,
            "context_limit": 16384,
            "estimated_input_cost": 0.10,
            "estimated_output_cost": 0.40,
            "is_fine_tuned": True,
            "task_type": "rag_generation"
        }
        # Fetch current specs
        data = await r.get("router:models")
        configs = json.loads(data) if data else []
        configs.append(new_model_spec)
        await r.set("router:models", json.dumps(configs))
        await r.aclose()
    except Exception as e:
        logger.warning(f"Could not register fine-tuned model in Redis: {e}")
