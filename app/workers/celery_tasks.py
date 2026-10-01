"""Ported unchanged from D:\\OMR_System\\app\\workers\\celery_tasks.py."""

from app.workers.celery_app import (
    celery_app
)

from app.pipeline.processing_pipeline import (
    process_pdf_task
)


@celery_app.task(
    name="process_pdf"
)
def celery_process_pdf_task(
    payload
):

    from app.pipeline.processing_pipeline import process_pdf_task

    process_pdf_task(
        payload["pdf_path"]
    )

    return {
        "status": "completed"
    }
