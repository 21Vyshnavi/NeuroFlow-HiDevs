# ruff: noqa
# mypy: ignore-errors
import os
import logging
from typing import List, Dict, Any
from backend.config import settings

logger = logging.getLogger(__name__)

# Basic MLflow tracker wrapper to record parameters, logs, and artifacts
class MLflowTracker:
    def __init__(self):
        # Configure tracking URI
        try:
            import mlflow
            mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
        except Exception:
            pass

    def start_run(self, job_id: str, base_model: str, pair_count: int, avg_quality: float) -> str:
        try:
            import mlflow
            mlflow.set_experiment("neuroflow-finetuning")
            run = mlflow.start_run(run_name=f"finetune-{job_id}")
            mlflow.log_params({
                "job_id": job_id,
                "base_model": base_model,
                "training_pair_count": pair_count,
                "avg_quality_score": avg_quality
            })
            return run.info.run_id
        except Exception as e:
            logger.warning(f"Failed to log run to MLflow: {e}")
            return f"mock_run_{job_id}"

    def end_run(self, run_id: str, training_loss: float, validation_loss: float, tokens: int):
        try:
            import mlflow
            # Ensure proper run binding
            mlflow.log_metrics({
                "training_loss": training_loss,
                "validation_loss": validation_loss,
                "training_token_count": tokens
            })
            mlflow.end_run()
        except Exception as e:
            logger.warning(f"Failed to close MLflow run {run_id}: {e}")

tracker = MLflowTracker()
