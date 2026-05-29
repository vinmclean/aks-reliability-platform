import asyncio
import logging
import os
import random
import time

from fastapi import FastAPI, HTTPException, Response
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "inventory-api")

ENABLE_OTEL = os.getenv("ENABLE_OTEL", "false").lower() == "true"
if ENABLE_OTEL:
    tracer_provider = TracerProvider(
        resource=Resource.create(
            {
                "service.name": SERVICE_NAME,
                "service.version": "0.1.0",
                "deployment.environment": os.getenv("DEPLOYMENT_ENVIRONMENT", "dev"),
            }
        )
    )
    tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(tracer_provider)
tracer = trace.get_tracer(__name__)

old_record_factory = logging.getLogRecordFactory()


def record_factory(*args, **kwargs):
    record = old_record_factory(*args, **kwargs)
    span_context = trace.get_current_span().get_span_context()
    record.trace_id = format(span_context.trace_id, "032x") if span_context.trace_id else "-"
    record.span_id = format(span_context.span_id, "016x") if span_context.span_id else "-"
    return record


logging.setLogRecordFactory(record_factory)
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s service=%(name)s trace_id=%(trace_id)s span_id=%(span_id)s %(message)s",
)
logger = logging.getLogger(SERVICE_NAME)

REQUESTS = Counter(
    "inventory_requests_total",
    "Total inventory requests.",
    ["route", "method", "status"],
)
LOOKUP_LATENCY = Histogram(
    "inventory_lookup_duration_seconds",
    "Inventory lookup latency.",
    ["product_status"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2),
)

app = FastAPI(title="Inventory API", version="0.1.0")
FastAPIInstrumentor.instrument_app(app)


@app.middleware("http")
async def record_request_metrics(request, call_next):
    response = await call_next(request)
    REQUESTS.labels(
        route=request.url.path,
        method=request.method,
        status=str(response.status_code),
    ).inc()
    return response


@app.get("/healthz")
async def healthz():
    return {"status": "ok", "service": SERVICE_NAME}


@app.get("/readyz")
async def readyz():
    return {"status": "ready"}


@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/api/inventory/{product_id}")
async def inventory(product_id: str):
    started = time.perf_counter()

    if product_id == "404":
        LOOKUP_LATENCY.labels(product_status="missing").observe(time.perf_counter() - started)
        raise HTTPException(status_code=404, detail="product not found")

    if product_id == "slow":
        await asyncio.sleep(1.2)

    if product_id == "error" or random.random() < float(os.getenv("INVENTORY_ERROR_RATE", "0.02")):
        LOOKUP_LATENCY.labels(product_status="error").observe(time.perf_counter() - started)
        logger.error("inventory lookup failed for product_id=%s", product_id)
        raise HTTPException(status_code=500, detail="inventory database unavailable")

    available = 0 if product_id == "empty" else random.randint(1, 25)
    LOOKUP_LATENCY.labels(product_status="ok").observe(time.perf_counter() - started)
    return {"product_id": product_id, "available": available}
