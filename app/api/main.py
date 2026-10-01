"""Ported unchanged from D:\\OMR_System\\app\\api\\main.py (title changed)."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config.config_loader import BASE_DIR

from app.api.routes.health import (
    router as health_router
)

from app.api.routes.runtime import (
    router as runtime_router
)

from app.api.routes.jobs import (
    router as jobs_router
)

from app.api.websocket.websocket_transport import (
    WebSocketTransport
)

from app.core.events.transports.transport_manager import (
    transport_manager
)

from app.api.routes.websocket import (
    router as websocket_router
)

from app.api.routes.process import (
    router as process_router
)

from app.api.routes.images import (
    router as images_router
)

import asyncio

from app.api.runtime.runtime_watcher import (
    runtime_watcher
)
from app.core.logging.logger import (
    logger
)

from app.core.events.transports.redis_transport import (
    RedisTransport
)

from app.core.config.config_loader import (
    BASE_DIR,
    CONFIG
)

from app.api.routes.config import (
    router as config_router
)

from app.pipeline.recovery_manager import (
    recover_jobs
)

# =========================================================
# FASTAPI APP
# =========================================================

app = FastAPI(

    title="OCR Answer-Script Scanner API",

    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# ROUTES
# =========================================================

app.include_router(
    health_router
)

app.include_router(
    runtime_router
)

app.include_router(
    jobs_router
)

app.include_router(
    config_router
)

websocket_transport = (
    WebSocketTransport()
)

transport_manager.register(
    websocket_transport
)

broker_url = (
    CONFIG["execution"][
        "broker_url"
    ]
)

def handle_redis_event(
    event_name,
    payload
):

    logger.info(
        f"[REDIS->WS] {event_name}"
    )

    websocket_transport.send(
        event_name,
        payload
    )

redis_subscriber = RedisTransport(

    broker_url=broker_url,

    is_subscriber=True,

    local_dispatch_callback=
        handle_redis_event
)

app.include_router(
    websocket_router
)

app.include_router(
    process_router
)

app.include_router(
    images_router
)

@app.on_event("startup")
async def startup_event():
    from app.observability.tracing import init_tracing
    init_tracing()

    # D:\OMR_System only started this from the standalone main.py watcher
    # entrypoint, never from here -- so the documented/Docker path
    # (uvicorn app.api.main:app) never actually exposed Prometheus
    # metrics. Started here too so :8001/metrics works whichever way the
    # API process is launched.
    try:
        from app.monitoring.prometheus_server import start_metrics_server
        start_metrics_server()
    except OSError:
        # Already running (e.g. a previous reload) -- not fatal.
        pass

    recover_jobs()
    asyncio.create_task(runtime_watcher())


# =========================================================
# STATIC FILES (FRONTEND)
# =========================================================

FRONTEND_DIST = BASE_DIR / "frontend" / "dist"

if FRONTEND_DIST.exists():
    app.mount(
        "/",
        StaticFiles(directory=str(FRONTEND_DIST), html=True),
        name="frontend"
    )
