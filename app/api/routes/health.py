"""Ported unchanged from D:\\OMR_System\\app\\api\\routes\\health.py."""

# pyrefly: ignore [missing-import]
from fastapi import APIRouter

# pyrefly: ignore [missing-import]
import redis
import requests

from datetime import datetime

from app.core.config.config_loader import CONFIG

from urllib.parse import urlparse

router = APIRouter()


@router.get("/health")
def health_check():

    redis_ok = False
    gpu_worker_ok = False
    telemetry_ok = False

    # =====================================
    # REDIS
    # =====================================

    try:

        client = redis.from_url(
            CONFIG["execution"]["broker_url"]
        )

        client.ping()

        redis_ok = True

    except Exception:

        redis_ok = False

    # =====================================
    # OCR WORKER
    # =====================================

    try:

        # pyrefly: ignore [missing-import]
        from celery import Celery

        celery_app = Celery(
            broker=CONFIG["execution"]["broker_url"]
        )

        workers = (
            celery_app
            .control
            .inspect()
            .ping()
        )

        gpu_worker_ok = False

        if workers:

            expected_worker = (

                CONFIG["runtime"][
                    "gpu_worker_name"
                ].lower()
            )

            gpu_worker_ok = any(

                expected_worker in
                worker.lower()

                for worker in workers.keys()
            )

    except Exception:

        gpu_worker_ok = False

    # =====================================
    # TELEMETRY
    # =====================================

    try:

        parsed = urlparse(

            CONFIG["observability"][
                "endpoint"
            ]
        )

        telemetry_base = (

            f"{parsed.scheme}"
            f"://"
            f"{parsed.netloc}"

        )

        response = requests.get(

            telemetry_base,

            timeout=2
        )

        telemetry_ok = (

            response.status_code < 500
        )

    except Exception:

        telemetry_ok = False

    return {

        "api": {
            "status": "healthy"
        },

        "redis": {
            "status":
                "healthy"
                if redis_ok
                else "offline"
        },

        "gpu_worker": {
            "status":
                "healthy"
                if gpu_worker_ok
                else "offline"
        },

        "telemetry": {
            "status":
                "healthy"
                if telemetry_ok
                else "offline"
        },

        "timestamp":
            datetime.utcnow().isoformat()
    }
