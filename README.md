# NeuroFlow

**Live Demo (Railway):** [https://neuroflow-production.up.railway.app](https://neuroflow-production.up.railway.app)
*(Note: Requires valid API keys in environment to process generation requests)*
NeuroFlow is a production-oriented Retrieval-Augmented Generation (RAG) platform. It ingests
heterogeneous documents (PDF, DOCX, images, CSV, web URLs), retrieves relevant context through a
hybrid search + reranking pipeline, generates grounded answers via a routed set of LLMs,
continuously evaluates generation quality with an LLM-as-judge framework, and closes the loop by
fine-tuning smaller models on its own highest-quality traffic.

This repository is the **architecture-first** milestone: before any production code is written,
the full system design, API contracts, data models, and key architectural decisions are documented
and locked in. All 19 subsequent implementation tasks build on top of what's defined here.

## Repository layout

```
NeuroFlow-HiDevs/
├── backend/          # API service, subsystem implementations (future tasks)
├── frontend/         # User-facing app (future tasks)
├── pipelines/         # Ingestion / retrieval / generation pipeline configs & runners
├── evaluation/        # Evaluation harness, LLM-as-judge scorers, aggregation jobs
├── infra/             # IaC, deployment configs, Docker/Compose, CI
├── docs/
│   ├── architecture.md      # 5 subsystems + data flow diagrams
│   ├── api-contracts.md     # Full REST API specification
│   ├── data-models.md       # Postgres / pgvector schema
│   └── adr/                 # Architecture Decision Records
│       ├── 001-vector-store.md
│       ├── 002-chunking-strategy.md
│       ├── 003-evaluation-framework.md
│       └── 004-model-routing.md
├── .gitignore
└── README.md
```

## System overview

NeuroFlow is composed of five subsystems, each documented in detail in
[`docs/architecture.md`](docs/architecture.md):

1. **Ingestion** — multi-modal document intake, chunking, embedding, vector store writes.
2. **Retrieval** — hybrid (vector + keyword + metadata) search, Reciprocal Rank Fusion, cross-encoder reranking.
3. **Generation** — prompt assembly, cost/capability/domain-aware model routing, streaming, logging.
4. **Evaluation** — async LLM-as-judge scoring (faithfulness, answer relevance, context precision, context recall) with rolling aggregates.
5. **Fine-Tuning** — mines high-quality (faithfulness > 0.8, rating ≥ 4) generations into JSONL training sets, submits fine-tuning jobs, tracks experiments in MLflow, and A/B routes to the winning model.

## Key documents

| Document | Purpose |
|---|---|
| [`docs/architecture.md`](docs/architecture.md) | Subsystem design + data flow diagrams |
| [`docs/api-contracts.md`](docs/api-contracts.md) | REST API surface, request/response schemas, auth, rate limits |
| [`docs/data-models.md`](docs/data-models.md) | Postgres/pgvector schema shared across subsystems |
| [`docs/adr/001-vector-store.md`](docs/adr/001-vector-store.md) | Why pgvector |
| [`docs/adr/002-chunking-strategy.md`](docs/adr/002-chunking-strategy.md) | Chunking strategy comparison and choice |
| [`docs/adr/003-evaluation-framework.md`](docs/adr/003-evaluation-framework.md) | Why LLM-as-judge over pure human annotation |
| [`docs/adr/004-model-routing.md`](docs/adr/004-model-routing.md) | Model routing matrix (spec for Task 38) |

## Status

Architecture and contracts only — no production code yet. This is intentional: decisions made
here (vector store choice, chunking strategy, evaluation framework, routing matrix) constrain all
subsequent implementation work.

## Branching

- `main` — architecture baseline (this milestone).
- `task-31` — this task's submission branch.
- `task-01` — mirrors `task-31` for submission-format compatibility.
