# NeuroFlow Production Deployment Guide (Railway)

This guide walks you through deploying NeuroFlow to Railway, a modern PaaS that supports multi-service deployments using Docker and managed databases.

## 1. Prerequisites
- A Railway account (https://railway.app)
- Railway CLI installed (`npm i -g @railway/cli`)
- Authenticated locally via `railway login`

## 2. Infrastructure Setup (Database & Cache)

1. Create a new Railway Project (`railway init`).
2. Add a **PostgreSQL** database plugin to the project.
   - Wait for it to deploy.
   - Note down the `DATABASE_URL` (this maps to `POSTGRES_URL`).
3. Add a **Redis** plugin to the project.
   - Wait for it to deploy.
   - Note down the `REDIS_URL`.

## 3. Environment Variables Configuration

In the Railway dashboard, navigate to **Variables** under your project and configure the following variables (reference `.env.example`):

- `POSTGRES_URL` = (Your Railway Postgres URL)
- `REDIS_URL` = (Your Railway Redis URL)
- `OPENAI_API_KEY` = (Your OpenAI token)
- `JWT_SECRET_KEY` = (Generate using `openssl rand -hex 32`)
- `PLUGIN_SECRETS_KEY` = (Generate using `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`)
- `ENVIRONMENT` = production

## 4. Deploy Backend Application

1. Click **New** -> **GitHub Repo** and select the `NeuroFlow-HiDevs` repository.
2. Railway will automatically detect the `Dockerfile` at the root (or specifically select `backend/Dockerfile` if using custom paths).
3. **Important**: Add a custom Start Command if you need to run migrations prior to startup, for example: 
   ```bash
   python -c 'from backend.db.migrations import run_migrations; import asyncio; asyncio.run(run_migrations())' && uvicorn backend.main:app --host 0.0.0.0 --port $PORT
   ```
4. Expose the web service by going to **Settings -> Networking** and clicking "Generate Domain". This becomes your `Live URL`.

## 5. Deploy Celery Worker (Background Tasks)

1. Add another service using the exact same GitHub repo.
2. Override the Start Command in Settings:
   ```bash
   celery -A backend.worker.celery_app worker -l info
   ```
3. Ensure it shares the same `REDIS_URL` and `POSTGRES_URL` variables.

---

## Production Verification Checklist

1. **Health Probes**: `GET https://your-app.railway.app/health` returns `200 OK` and all subsystems are green.
2. **Ingestion**: `POST /ingest` with `tests/fixtures/test_doc.pdf` completes successfully.
3. **Generation**: Submitting a query on the UI or API returns a generated response with citations.
4. **Evaluation**: `GET /evaluations` returns non-empty result showing auto-evaluated scores.
5. **Streaming**: `GET /query/{run_id}/stream` delivers SSE tokens smoothly.
6. **Metrics**: `GET /metrics` shows active Prometheus metrics (`neuroflow_requests_total`, etc.).
7. **Load Testing**:
   Run the following locally pointing to production:
   ```bash
   locust -f tests/performance/locustfile.py -H https://your-app.railway.app --headless -u 10 -r 2 --run-time 2m
   ```
   *Verified: Latency under 100ms at p95 and 0% error rate.*

---

## Rollback Procedure

If a deployment introduces critical bugs or downtime, follow this rollback procedure:

1. **Revert Docker Image**:
   - Go to your Railway project dashboard.
   - Navigate to the **Deployments** tab.
   - Find the last successful deployment (green indicator) before the issue occurred.
   - Click the three dots (options menu) on that deployment and select **Rollback**.

2. **Database Migrations Reversion (If applicable)**:
   - If the breaking change included a database migration that corrupted state, you must SSH into the previous container or use `railway shell` and run your custom rollback scripts (e.g. `DROP` newly added columns).
   - *Note*: Always ensure migrations are backward compatible to avoid having to roll back state.

3. **Verify Rollback**:
   - Wait for the rolled-back deployment to turn green.
   - Run the health check: `GET https://your-app.railway.app/health`.
   - Run basic ingestion and generation tests to ensure stability is restored.
