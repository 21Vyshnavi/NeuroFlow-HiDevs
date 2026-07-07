from contextlib import asynccontextmanager
from fastapi import FastAPI, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Counter, Histogram
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from backend.db.pool import db_pool
from backend.db.migrations import run_migrations
from backend.db.health import check_postgres, check_redis, check_mlflow
from backend.config import settings

# Setup OpenTelemetry Tracing
provider = TracerProvider()
processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=settings.otlp_endpoint, insecure=True))
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

# Prometheus metrics setup
REQUEST_COUNTER = Counter("neuroflow_requests_total", "Total requests received", ["method", "endpoint"])
REQUEST_LATENCY = Histogram("neuroflow_request_latency_seconds", "Request latency", ["method", "endpoint"])

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    await db_pool.connect()
    await run_migrations()
    yield
    # Shutdown actions
    await db_pool.disconnect()

from backend.api.ingest import router as ingest_router
from backend.api.query import router as query_router
from backend.api.rating import router as rating_router
from backend.api.compare import router as compare_router
from backend.api.pipelines import router as pipelines_router
from backend.api.finetune import router as finetune_router

app = FastAPI(title="NeuroFlow API", lifespan=lifespan)

# Instrument FastAPI App with OpenTelemetry
FastAPIInstrumentor.instrument_app(app)

app.include_router(ingest_router)
app.include_router(query_router)
app.include_router(rating_router)
app.include_router(compare_router)
app.include_router(pipelines_router)
app.include_router(finetune_router)






@app.middleware("http")
async def add_metrics_middleware(request, call_next):
    method = request.method
    endpoint = request.url.path
    REQUEST_COUNTER.labels(method=method, endpoint=endpoint).inc()
    
    # Simple timer using standard library
    import time
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)
    return response

@app.get("/health")
async def health():
    import time as _time
    import redis.asyncio as redis

    # Core service checks with latency
    t0 = _time.time()
    postgres_ok = await check_postgres()
    pg_lat = int((_time.time() - t0) * 1000)

    t0 = _time.time()
    redis_ok = await check_redis()
    rd_lat = int((_time.time() - t0) * 1000)

    t0 = _time.time()
    mlflow_ok = await check_mlflow()
    ml_lat = int((_time.time() - t0) * 1000)

    # Circuit breaker states
    circuit_breakers = {}
    queue_depth = 0
    try:
        r = redis.Redis(host=settings.redis_host, port=settings.redis_port, password=settings.redis_password)
        for cb_name in ["openai", "anthropic"]:
            state = (await r.get(f"circuit:{cb_name}:state") or b"CLOSED").decode()
            fail_count = int(await r.get(f"circuit:{cb_name}:failure_count") or 0)
            opened_at = await r.get(f"circuit:{cb_name}:opened_at")
            circuit_breakers[cb_name] = {
                "state": state.lower(),
                "failure_count": fail_count,
            }
            if opened_at:
                circuit_breakers[cb_name]["opened_at"] = float(opened_at)
        queue_depth = await r.llen("queue:ingest")
        await r.aclose()
    except Exception:
        pass

    # Determine overall status
    any_open = any(cb.get("state") == "open" for cb in circuit_breakers.values())
    if not postgres_ok or not redis_ok:
        status = "critical"
    elif any_open:
        status = "degraded"
    else:
        status = "ok"

    return {
        "status": status,
        "checks": {
            "postgres": {"status": "ok" if postgres_ok else "error", "latency_ms": pg_lat},
            "redis": {"status": "ok" if redis_ok else "error", "latency_ms": rd_lat},
            "mlflow": {"status": "ok" if mlflow_ok else "error", "latency_ms": ml_lat},
            "circuit_breakers": circuit_breakers,
            "queue_depth": queue_depth
        }
    }

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
