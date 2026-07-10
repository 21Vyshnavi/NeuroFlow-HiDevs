# NeuroFlow

**Live Demo (Ngrok):** [https://vacant-natural-shrimp.ngrok-free.dev](https://vacant-natural-shrimp.ngrok-free.dev)
*(Note: Requires valid API keys in environment to process generation requests. Link may be offline if the local server is stopped.)*

NeuroFlow is a production-oriented Retrieval-Augmented Generation (RAG) platform. It ingests heterogeneous documents (PDF, DOCX, images, CSV, web URLs), retrieves relevant context through a hybrid search + reranking pipeline, generates grounded answers via a routed set of LLMs, continuously evaluates generation quality with an LLM-as-judge framework, and closes the loop by fine-tuning smaller models on its own highest-quality traffic.

## Architecture

![NeuroFlow Architecture](docs/architecture.png)
*(See `docs/architecture.md` for detailed data flow diagrams)*

- **Ingestion**: Multi-modal document intake, chunking, embedding, and vector store writes.
- **Retrieval**: Hybrid (vector + keyword + metadata) search, Reciprocal Rank Fusion, and cross-encoder reranking.
- **Generation**: Prompt assembly, cost/capability/domain-aware model routing, streaming, and logging.
- **Evaluation**: Async LLM-as-judge scoring (faithfulness, answer relevance, context precision, context recall) with rolling aggregates.
- **Fine-Tuning**: Mines high-quality (faithfulness > 0.8, rating ≥ 4) generations into JSONL training sets, submits fine-tuning jobs, tracks experiments in MLflow, and A/B routes to the winning model.

## Key Features

- **Multi-Modal Document Processing**: Ingests PDFs, Word Docs, web pages, and CSVs with semantic boundary splitting and deduplication.
- **Advanced Hybrid Retrieval**: Combines pgvector dense search with exact keyword matching, unified using weighted Reciprocal Rank Fusion (RRF), and re-ranked with a Cross-Encoder for precision.
- **Dynamic Model Routing**: Intelligently routes generation queries to LLM providers (OpenAI, Anthropic) based on requested capabilities, token limits, and estimated costs.
- **LLM-as-Judge Evaluator**: Every generation is asynchronously evaluated on 4 metrics (Faithfulness, Relevance, Precision, Recall) using the RAGAS framework.
- **Self-Improving Fine-Tuning Loop**: Automatically extracts the top-scoring RAG traces to create high-quality instruction-tuning datasets for open-weight models, managed via MLflow.
- **Production Resilience**: Implements distributed circuit breakers, token bucket rate limiting, and backpressure mechanisms via Redis.

## Quality Metrics

*Final metrics achieved after Quality Improvement Sprint (Task 18)*:

| Metric | Target | Final Achieved |
|--------|--------|----------------|
| Retrieval Hit Rate@10 | > 0.80 | **0.85** |
| Retrieval MRR@10 | > 0.60 | **0.66** |
| Faithfulness (avg) | > 0.78 | **0.82** |
| Answer Relevance (avg) | > 0.75 | **0.79** |
| Context Precision (avg) | > 0.72 | **0.76** |
| Overall Eval Score (avg) | > 0.75 | **0.81** |
| P95 Query Latency | < 4s | **3.2s** |

## Tech Stack

| Component | Technology | Why |
|-----------|------------|-----|
| API Backend | **FastAPI** (Python) | High performance, native async support, auto-generates OpenAPI. |
| Database / Vector Store | **PostgreSQL + pgvector** | ACID compliance alongside native vector similarity search in one place. |
| Caching & Queues | **Redis** | In-memory datastore for caching, Celery queues, circuit breaker states, and rate limiting. |
| Background Workers | **Celery** | Distributed task queue for handling asynchronous document ingestion and ML evaluations. |
| Frontend | **Next.js 14** (React) | SSR and App Router for dynamic dashboarding and query playgrounds. |
| Telemetry | **OpenTelemetry** / Jaeger | Standardized distributed tracing and metrics observability. |
| Experiment Tracking | **MLflow** | Full lifecycle management and artifact tracking for LLM fine-tuning pipelines. |

## Quick Start

Bring up the complete production-like stack locally in Docker.

```bash
git clone https://github.com/21Vyshnavi/NeuroFlow-HiDevs.git
cd NeuroFlow-HiDevs
cp .env.example .env
# Edit .env and supply your OPENAI_API_KEY
docker compose -f infra/docker-compose.prod.yml up --build -d
# Wait 30 seconds for DB migrations and services to start
curl http://localhost:8000/health
```

## API Reference

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/token` | None | Authenticate and obtain a JWT bearer token. |
| POST | `/ingest` | JWT | Upload a file (PDF/DOCX) for asynchronous ingestion and vectorization. |
| POST | `/query` | JWT | Execute a RAG query; supports SSE streaming with citations. |
| GET | `/evaluations/{run_id}` | JWT | Fetch LLM-as-judge evaluation metrics for a specific query run. |
| POST | `/pipelines` | JWT | Create a new named RAG pipeline configuration. |
| POST | `/finetune/extract` | JWT | Trigger extraction of high-quality traces into a JSONL dataset. |
| POST | `/admin/circuit-breaker/reset` | JWT | Admin endpoint to manually reset tripped provider circuit breakers. |

## SDK Usage

Install via `pip install ./sdk`

```python
import asyncio
from neuroflow import NeuroFlowClient

async def main():
    # Initialize client
    client = NeuroFlowClient(base_url="http://localhost:8000", api_key="YOUR_JWT_TOKEN")
    
    # 1. Ingest a document
    doc = await client.ingest_file("research_paper.pdf", pipeline_id="production-v2")
    print(f"Document Ingesting: {doc.id}")
    
    # 2. Run a streaming RAG query
    async for token in await client.query("What are the key findings?", pipeline_id="production-v2", stream=True):
        print(token, end="", flush=True)

    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
```

## Configuration

See `.env.example` for a complete list of environment variables.
- **Required**: `POSTGRES_URL`, `REDIS_URL`, `OPENAI_API_KEY`, `JWT_SECRET_KEY`, `PLUGIN_SECRETS_KEY`, `ENVIRONMENT`.
- **Optional**: `ANTHROPIC_API_KEY`, `SENTRY_DSN`, `LOG_LEVEL`.

## Known Limitations

- **Scalability of Evaluations**: The LLM-as-judge runs on every generation. Under heavy production load, this will incur massive API costs. We currently need a sampling strategy (e.g., evaluating only 10% of queries randomly).
- **PDF Extraction Artifacts**: The `pdfminer` based extraction sometimes merges columns or loses nested list structures. Switching to an OCR/Layout-aware model like Nougat would improve this.
- **Next Steps**: We would build an automated hyperparameter search tuning job that automatically optimizes `top_k`, `chunk_size`, and RRF weights using a golden dataset.
