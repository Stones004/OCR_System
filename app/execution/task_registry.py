"""Ported unchanged from D:\\OMR_System\\app\\execution\\task_registry.py."""

from app.pipeline.processing_pipeline import (
    process_pdf_task
)


TASK_REGISTRY = {

    "process_pdf": (
        process_pdf_task
    )
}
