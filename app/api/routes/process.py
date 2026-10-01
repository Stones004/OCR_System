"""Ported unchanged from D:\\OMR_System\\app\\api\\routes\\process.py."""

from fastapi import APIRouter

from pathlib import Path

from app.pipeline.processing_pipeline import (
    ProcessingPipeline
)

from app.core.logging.logger import (
    logger
)

from app.core.config.config_loader import (
    CONFIG
)


# =========================================================
# ROUTER
# =========================================================

router = APIRouter()


# =========================================================
# PROCESS INCOMING PDFs
# =========================================================

import asyncio

@router.post("/runtime/process")

async def process_runtime():

    incoming_dir = Path(
        CONFIG["paths"]["incoming_dir"]
    )

    pdf_files = list(

        incoming_dir.glob("*.pdf")
    )

    pipeline = (
        ProcessingPipeline()
    )

    processed = []

    for pdf_path in pdf_files:

        try:

            logger.info(
                f"API PROCESSING: {pdf_path.name}"
            )

            await asyncio.to_thread(

                pipeline.process_job,

                pdf_path
            )

            processed.append(
                pdf_path.name
            )

        except Exception as e:

            logger.exception(
                f"API PROCESSING FAILED: {e}"
            )

    return {

        "processed_files": (
            processed
        )
    }
