# NeuroFlow Architecture Runbook

This runbook outlines procedures for mitigating the five most common production incidents in NeuroFlow.

## Incident 1 — High Query Latency (P95 > 10s)

**Symptoms**: Slow responses on the frontend, users complaining about timeouts.
**Checks**:
1. Check Jaeger traces to identify the slow span (is it Retrieval or Generation?).
2. Check Redis memory usage and cache hit rate in the dashboard.
3. Check Postgres query performance via `pg_stat_statements`.
**Remediation**:
- If Redis is evicting heavily, flush the cache or increase memory limits.
- If Postgres is slow, ensure `hnsw` indexes are fully built and not corrupted. Reindex if necessary.
- If generation is slow, scale API replicas or switch to a faster fallback model (e.g., `gpt-4o-mini`).

## Incident 2 — Evaluation Scores Degrading

**Symptoms**: Automated LLM-as-Judge scores (Faithfulness, Answer Relevance) dropping below 0.70 thresholds.
**Checks**:
1. Check which pipeline and which metric is failing.
2. Check recent ingested documents — low-quality input guarantees low-quality output.
3. Check MLflow for recent fine-tuning job deployments.
**Remediation**:
- Revert the active model to the previous known good fine-tuned model.
- Inspect and scrub the training data quality. Delete poor documents from the vector store and reingest clean copies.

## Incident 3 — LLM Provider Circuit Breaker Open

**Symptoms**: Queries failing fast with `503 Service Unavailable`, `circuit_breaker_open` error codes.
**Checks**:
1. Check `GET /health` for circuit breaker status.
2. Check the external provider's status page (e.g., OpenAI, Anthropic).
**Remediation**:
- The system will automatically fall back to alternative providers if configured.
- Wait for the recovery timeout (default 60s).
- If the provider is back but the breaker is stuck, manually reset via `POST /admin/circuit-breaker/reset`.

## Incident 4 — Ingestion Queue Depth > 100

**Symptoms**: Uploaded documents are stuck in "processing" state for long periods.
**Checks**:
1. Check `GET /health` for Celery queue depth.
2. Check worker process logs for OOM (Out Of Memory) errors or infinite loops in PDF extraction.
**Remediation**:
- Restart worker containers.
- Scale out worker replicas.
- Check Redis for stuck/poison pill jobs and clear them if necessary.

## Incident 5 — Database Disk Usage > 80%

**Symptoms**: Alerts firing for volume capacity on the managed PostgreSQL instance.
**Checks**:
1. Check which table is growing fastest (`pg_stat_user_tables`).
2. Verify if the Data Retention cron job ran successfully.
**Remediation**:
- Run the data retention job manually to clear old evaluations and runs.
- Increase the database volume size in the cloud provider console.
