"""
Adapted from D:\\OMR_System\\app\\monitoring\\prometheus_server.py -- the
original hardcoded port 8001 because it only ever ran from one process
(its native, non-Celery main.py). This system's actual pipeline metrics
(app/monitoring/metrics.py's PDF_PROCESSED, GPU_TIME, etc.) are recorded
inside app/pipeline/processing_pipeline.py, which runs as a Celery task
in the cpu-worker process -- a different OS process than the API, which
is the only place start_metrics_server() used to be called from. That
left :8001 permanently serving an empty registry: the metric names would
show up (registered at import time) but every value stuck at zero,
because the process actually recording them was never scraped.

Fix: cpu-worker calls this too, on its own port (see
app/workers/celery_app.py's _init_metrics), so the numbers that matter
are actually reachable. `port` is a parameter instead of hardcoded so
the two processes can bind different ports.
"""

from prometheus_client import (
    start_http_server
)

def start_metrics_server(port: int = 8001):

    start_http_server(
        port
    )
