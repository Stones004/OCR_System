"""Ported unchanged from D:\\OMR_System\\app\\pipeline\\recovery_manager.py."""

from pathlib import Path

from app.pipeline.job_manager import (
    job_manager
)

from app.workers.celery_app import (
    celery_app
)

from app.core.logging.logger import (
    logger
)

RECOVERABLE = {

    "PREPROCESSING",

    "VALIDATING",

    "INFERENCE",

    "EXPORTING"
}


def recover_jobs():

    logger.warning(
        "RECOVERY MANAGER STARTED"
    )

    jobs = job_manager.list_jobs()

    logger.warning(
        f"FOUND {len(jobs)} MANIFESTS"
    )

    for job_id, manifest in jobs.items():

        logger.warning(
            f"FOUND JOB {job_id}"
        )

        status = manifest.get(
            "status"
        )

        logger.warning(
            f"STATUS = {status}"
        )

        if status not in RECOVERABLE:
            continue

        pdf_path = manifest.get(
            "pdf_path"
        )

        if not pdf_path:
            continue

        if not Path(pdf_path).exists():

            logger.warning(
                f"RECOVERY SKIPPED: "
                f"{pdf_path} NOT FOUND"
            )

            continue

        logger.warning(

            f"RECOVERING JOB "

            f"{job_id}"
        )

        celery_app.send_task(

            "process_pdf",

            args=[
                {
                    "pdf_path": pdf_path
                }
            ]
        )
