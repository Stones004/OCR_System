"""Ported unchanged from D:\\OMR_System\\app\\workers\\celery_app.py."""

# pyrefly: ignore [missing-import]
from celery import Celery
import os


from app.core.config.config_loader import (
    CONFIG
)

from app.core.events.transports.redis_transport import RedisTransport
from app.core.events.transports.transport_manager import transport_manager

broker_url = os.getenv(
    "BROKER_URL",
    CONFIG["execution"]["broker_url"]
)

redis_transport = RedisTransport(broker_url=broker_url, is_subscriber=False)
transport_manager.register(redis_transport)

celery_app = Celery(

    "ocr_worker",

    broker=broker_url,

    backend=broker_url
)

celery_app.conf.update(

    task_serializer="json",

    accept_content=["json"],

    result_serializer="json",

    timezone="Asia/Kolkata",

    enable_utc=True,

    task_acks_late=True,

    task_reject_on_worker_lost=True,

    worker_prefetch_multiplier=1,

    task_track_started=True,

    task_soft_time_limit=1800,

    task_time_limit=2100
)

from celery.signals import worker_process_init


def _init_observability(**kwargs):
    from app.observability.tracing import init_tracing
    init_tracing()


# Call eagerly at import time. This is the path that actually fires
# for `--pool=threads` and `--pool=solo`, where worker_process_init
# either doesn't fire or isn't guaranteed to fire before tasks run.
_init_observability()

# Also hook the signal for prefork-family pools, where each forked
# child process needs its own init. init_tracing() is idempotent,
# so double-calling on solo/threads workers is harmless.
worker_process_init.connect(_init_observability)


# app/monitoring/metrics.py's counters/histograms are only ever touched
# from inside app/pipeline/processing_pipeline.py, i.e. only in the
# cpu-worker process -- never the API process (which already runs its
# own metrics server, see app/api/main.py) and never ocr-worker/Flower
# (which import this module too but don't record anything). METRICS_PORT
# is therefore only set for the cpu-worker process (see RUNBOOK.md /
# docker-compose.yml); everyone else importing this module leaves it
# unset and skips this entirely.
_metrics_started = False


def _init_metrics(**kwargs):
    global _metrics_started
    if _metrics_started:
        return
    metrics_port = os.getenv("METRICS_PORT")
    if not metrics_port:
        return
    from app.monitoring.prometheus_server import start_metrics_server
    start_metrics_server(int(metrics_port))
    _metrics_started = True


_init_metrics()
worker_process_init.connect(_init_metrics)


import app.workers.celery_tasks
import app.workers.gpu_tasks
