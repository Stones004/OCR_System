"""Ported unchanged from D:\\OMR_System\\app\\monitoring\\metrics.py."""

from prometheus_client import (
    Counter,
    Gauge,
    Histogram
)

PDF_PROCESSED = Counter(
    "pdf_processed_total",
    "Total PDFs processed"
)

PDF_FAILED = Counter(
    "pdf_failed_total",
    "Total PDFs failed"
)

ACTIVE_JOBS = Gauge(
    "active_jobs",
    "Currently active PDF jobs"
)

VALIDATION_TIME = Histogram(
    "validation_seconds",
    "Validation duration"
)

GPU_TIME = Histogram(
    "gpu_total_seconds",
    "GPU processing duration"
)

VISUALIZATION_TIME = Histogram(
    "visualization_seconds",
    "Visualization duration"
)

PDF_DURATION = Histogram(
    "pdf_duration_seconds",
    "Total PDF duration"
)

GPU_QUEUE_WAIT = Histogram(
    "gpu_queue_wait_seconds",
    "Time waiting for GPU task completion"
)
