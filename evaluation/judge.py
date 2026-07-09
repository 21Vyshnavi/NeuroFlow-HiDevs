import json
import uuid
import asyncio
import logging
from opentelemetry import trace
from backend.db.pool import db_pool
from evaluation.metrics.faithfulness import evaluate_faithfulness
from evaluation.metrics.answer_relevance import evaluate_answer_relevance
from evaluation.metrics.context_precision import evaluate_context_precision
from evaluation.metrics.context_recall import evaluate_context_recall

logger = logging.getLogger(__name__)
tracer = trace.get_tracer("neuroflow.evaluation")

class EvaluationJudge:
    async def evaluate_run(self, run_id: str, query: str, answer: str, context: str, chunk_contents: list[str]) -> dict:
        pool = db_pool.get_pool()
        if not pool:
            raise RuntimeError("Database pool not initialized.")

        with tracer.start_as_current_span("evaluation.judge") as span:
            # 1. Parallel metric checks
            task_faith = evaluate_faithfulness(query, answer, context)
            task_relevance = evaluate_answer_relevance(query, answer)
            task_precision = evaluate_context_precision(query, chunk_contents, answer)
            task_recall = evaluate_context_recall(query, chunk_contents, answer)

            faith, relevance, precision, recall = await asyncio.gather(
                task_faith, task_relevance, task_precision, task_recall
            )

            # Overall weighted score
            overall_score = 0.35 * faith + 0.30 * relevance + 0.20 * precision + 0.15 * recall

            # Trace attributes logging
            span.set_attribute("metric.faithfulness", faith)
            span.set_attribute("metric.answer_relevance", relevance)
            span.set_attribute("metric.context_precision", precision)
            span.set_attribute("metric.context_recall", recall)
            span.set_attribute("metric.overall_score", overall_score)

            async with pool.acquire() as conn:
                # 2. Write details into evaluations table
                eval_id = uuid.uuid4()
                await conn.execute(
                    """
                    INSERT INTO evaluations (id, run_id, faithfulness, answer_relevance, context_precision, context_recall, overall_score, judge_model)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    """,
                    eval_id,
                    uuid.UUID(run_id),
                    faith,
                    relevance,
                    precision,
                    recall,
                    overall_score,
                    "gpt-4o-mini"
                )

                # 3. Check if we should insert as fine-tuning training pair candidate
                if overall_score > 0.8:
                    # Retrieve prompt history
                    await conn.execute(
                        """
                        INSERT INTO training_pairs (run_id, system_prompt, user_message, assistant_message, quality_score)
                        VALUES ($1, 'You are a precise research assistant.', $2, $3, $4)
                        """,
                        uuid.UUID(run_id),
                        query,
                        answer,
                        overall_score
                    )

                # Fetch pipeline_id to update metrics
                row = await conn.fetchrow("SELECT pipeline_id FROM pipeline_runs WHERE id = $1", uuid.UUID(run_id))
                pipeline_id = str(row["pipeline_id"]) if row and row["pipeline_id"] else "default"

            try:
                from backend.monitoring.metrics import eval_faithfulness, eval_overall
                eval_faithfulness.labels(pipeline_id=pipeline_id).set(faith)
                eval_overall.labels(pipeline_id=pipeline_id).set(overall_score)
            except ImportError:
                pass

            return {
                "eval_id": str(eval_id),
                "faithfulness": faith,
                "answer_relevance": relevance,
                "context_precision": precision,
                "context_recall": recall,
                "overall_score": overall_score
            }
