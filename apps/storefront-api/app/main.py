import asyncio
import logging
import os
import random
import time
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, Response
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "storefront-api")
INVENTORY_URL = os.getenv("INVENTORY_URL", "http://inventory-api:8080")

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

REQUESTS = Counter(
    "storefront_requests_total",
    "Total storefront requests.",
    ["route", "method", "status"],
)
CHECKOUTS = Counter(
    "storefront_checkouts_total",
    "Total checkout attempts.",
    ["result"],
)
LATENCY = Histogram(
    "storefront_request_duration_seconds",
    "Storefront request latency.",
    ["route"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5),
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http = httpx.AsyncClient(timeout=2.0)
    yield
    await app.state.http.aclose()


app = FastAPI(title="Storefront API", version="0.1.0", lifespan=lifespan)
FastAPIInstrumentor.instrument_app(app)
HTTPXClientInstrumentor().instrument()

# Keep intentional lab scenarios visible as their own Prometheus route labels.
# Ordinary dynamic IDs are normalized to the FastAPI route template.
SPECIAL_METRIC_ROUTES = {
    "/api/products/slow",
    "/api/products/error",
    "/api/checkout/empty",
    "/api/error",
}


def get_metric_route(request):
    path = request.url.path

    if path in SPECIAL_METRIC_ROUTES:
        return path

    matched_route = request.scope.get("route")
    if matched_route is not None:
        return getattr(matched_route, "path", "unknown")

    return "unknown"


@app.middleware("http")
async def record_request_metrics(request, call_next):
    started = time.perf_counter()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        duration = time.perf_counter() - started
        route = get_metric_route(request)

        REQUESTS.labels(
            route=route,
            method=request.method,
            status=str(status_code),
        ).inc()
        LATENCY.labels(route=route).observe(duration)


@app.get("/healthz")
async def healthz():
    return {"status": "ok", "service": SERVICE_NAME}


@app.get("/readyz")
async def readyz():
    return {"status": "ready"}


@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/api/products/{product_id}")
async def get_product(product_id: str, fail: bool = False):
    if fail:
        logger.error("simulated storefront product failure product_id=%s", product_id)
        raise HTTPException(
            status_code=500,
            detail="simulated storefront product failure",
        )

    with tracer.start_as_current_span("lookup_product") as span:
        span.set_attribute("product.id", product_id)

        try:
            inventory = await app.state.http.get(
                f"{INVENTORY_URL}/api/inventory/{product_id}"
            )
        except httpx.RequestError as exc:
            logger.error(
                "inventory dependency request failed product_id=%s error=%s",
                product_id,
                exc,
            )
            raise HTTPException(
                status_code=502,
                detail="inventory dependency unavailable",
            ) from exc

    if inventory.status_code == 404:
        raise HTTPException(status_code=404, detail="product not found")

    if inventory.status_code >= 500:
        logger.error(
            "inventory dependency failed product_id=%s status=%s",
            product_id,
            inventory.status_code,
        )
        raise HTTPException(
            status_code=502,
            detail="inventory dependency failed",
        )

    inventory.raise_for_status()

    return {
        "id": product_id,
        "name": f"demo-product-{product_id}",
        "inventory": inventory.json(),
    }


@app.post("/api/checkout/{product_id}")
async def checkout(product_id: str, fail: bool = False):
    if fail:
        CHECKOUTS.labels(result="failed").inc()
        logger.error("simulated checkout failure product_id=%s", product_id)
        raise HTTPException(
            status_code=500,
            detail="simulated checkout failure",
        )

    product = await get_product(product_id)

    if product["inventory"]["available"] <= 0:
        CHECKOUTS.labels(result="out_of_stock").inc()
        raise HTTPException(status_code=409, detail="out of stock")

    if random.random() < float(os.getenv("CHECKOUT_ERROR_RATE", "0.05")):
        CHECKOUTS.labels(result="failed").inc()
        logger.error("checkout failed for product_id=%s", product_id)
        raise HTTPException(status_code=500, detail="payment processor unavailable")

    CHECKOUTS.labels(result="success").inc()
    logger.info("checkout completed for product_id=%s", product_id)
    return {"status": "accepted", "product_id": product_id}


@app.get("/api/slow")
async def slow(fail: bool = False):
    delay = random.uniform(0.5, 2.5)
    await asyncio.sleep(delay)

    if fail:
        logger.error("simulated slow-route failure delay_seconds=%.3f", delay)
        raise HTTPException(
            status_code=500,
            detail="simulated slow endpoint failure",
        )

    return {"delay_seconds": round(delay, 3)}


@app.get("/api/error")
async def error():
    logger.error("intentional error endpoint called")
    raise HTTPException(status_code=500, detail="intentional demo error")
