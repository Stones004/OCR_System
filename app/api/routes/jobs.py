"""Ported unchanged from D:\\OMR_System\\app\\api\\routes\\jobs.py."""

from fastapi import APIRouter
from fastapi import HTTPException

from pathlib import Path
import shutil

from app.core.config.config_loader import CONFIG

from app.pipeline.job_manager import (
    job_manager
)

from pydantic import BaseModel

import json

from fastapi.responses import JSONResponse
# =========================================================
# ROUTER
# =========================================================

router = APIRouter()

class StatusUpdate(BaseModel):
    status: str


# =========================================================
# GET ALL JOBS
# =========================================================

@router.get("/jobs")

def get_jobs():

    return {

        "jobs": (
            job_manager.list_jobs()
        )
    }


# =========================================================
# GET ACTIVE JOBS
# =========================================================

@router.get("/jobs/active")

def get_active_jobs():

    active_jobs = {}

    for job_id, job_data in (

        job_manager.list_jobs().items()
    ):

        status = job_data.get(
            "status"
        )

        if status not in [

            "COMPLETED",

            "FAILED"
        ]:

            active_jobs[
                job_id
            ] = job_data

    return {

        "active_jobs": (
            active_jobs
        )
    }


# =========================================================
# GET SINGLE JOB
# =========================================================

@router.get("/jobs/{job_id}")

def get_job(

    job_id: str
):

    job = job_manager.get_job(
        job_id
    )

    if job is None:

        raise HTTPException(

            status_code=404,

            detail=(
                "JOB NOT FOUND"
            )
        )

    return job

@router.patch(
    "/jobs/{job_id}/status"
)
def update_job_status(

    job_id: str,

    payload: StatusUpdate

):

    job = job_manager.get_job(
        job_id
    )

    if job is None:

        raise HTTPException(
            status_code=404,
            detail="JOB NOT FOUND"
        )

    job_manager.update_status(
        job_id,
        payload.status
    )

    return {
        "success": True,
        "job_id": job_id,
        "status": payload.status
    }

@router.post(
    "/jobs/{job_id}/rescan"
)
def send_to_rescan(
    job_id: str
):

    manifest = job_manager.get_job(
        job_id
    )

    if manifest is None:

        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    original_name = (
        Path(
            manifest["pdf_path"]
        ).name.replace(
            ".processing.pdf",
            ".pdf"
        )
    )

    # A booklet being sent to rescan is most often sitting in review_dir
    # (final_status == "REVIEW"); processed_dir is the fallback for a
    # PASS booklet an operator decides to rescan anyway.
    source_pdf = (
        Path(
            CONFIG["paths"]["review_dir"]
        )
        /
        original_name
    )

    if not source_pdf.exists():

        source_pdf = (
            Path(
                CONFIG["paths"]["processed_dir"]
            )
            /
            original_name
        )

    if not source_pdf.exists():

        raise HTTPException(
            status_code=404,
            detail=f"PDF not found in review_dir or processed_dir: {original_name}"
        )

    rescan_pdf = (
        Path(
            CONFIG["paths"]["needs_rescan_dir"]
        )
        /
        original_name
    )

    rescan_pdf.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    shutil.move(
        str(source_pdf),
        str(rescan_pdf)
    )

    manifest["status"] = (
        "RESCAN"
    )

    manifest["review_required"] = (
        True
    )

    job_manager.save_manifest(
        job_id,
        manifest
    )

    return {

        "success": True,

        "job_id": job_id,

        "status": "RESCAN",

        "path": str(rescan_pdf)
    }


# =========================================================
# GET JOB EXPORT
# =========================================================

@router.get("/jobs/{job_id}/export")
def get_job_export(
    job_id: str
):

    manifest = job_manager.get_job(job_id)

    if manifest is None:

        raise HTTPException(
            status_code=404,
            detail="JOB NOT FOUND"
        )

    export_path = manifest.get(
        "export_path"
    )

    if not export_path:

        raise HTTPException(
            status_code=404,
            detail="EXPORT NOT AVAILABLE"
        )

    export_file = Path(export_path)

    if not export_file.exists():

        raise HTTPException(
            status_code=404,
            detail="EXPORT FILE NOT FOUND"
        )

    with open(
        export_file,
        "r",
        encoding="utf-8"
    ) as f:

        export_data = json.load(f)

    return JSONResponse(
        content=export_data
    )
