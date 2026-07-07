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

app = FastAPI(title="NeuroFlow API", lifespan=lifespan)

# Instrument FastAPI App with OpenTelemetry
FastAPIInstrumentor.instrument_app(app)

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
    postgres_ok = await check_postgres()
    redis_ok = await check_redis()
    mlflow_ok = await check_mlflow()
    
    status = "ok" if (postgres_ok and redis_ok and mlflow_ok) else "error"
    return {
        "status": status,
        "checks": {
            "postgres": postgres_ok,
            "redis": redis_ok,
            "mlflow": mlflow_ok
        }
    }

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
