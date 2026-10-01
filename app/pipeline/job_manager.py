"""Ported unchanged from D:\\OMR_System\\app\\pipeline\\job_manager.py."""

from pathlib import Path

import json
from datetime import datetime

from app.core.config.config_loader import (
    CONFIG
)
import uuid

from threading import Lock

from app.storage.in_memory_job_store import (
    InMemoryJobStore
)

from datetime import (
    datetime,
    timedelta
)

# =========================================================
# DIRECTORIES
# =========================================================

MANIFEST_DIR = Path(
    CONFIG["paths"]["manifest_dir"]
)

MANIFEST_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# =========================================================
# JOB MANAGER
# =========================================================

JOB_STATUS = {

    "PENDING",

    "PREPROCESSING",

    "VALIDATING",

    "INFERENCE",

    "EXPORTING",

    "COMPLETED",

    "FAILED",

    "PASS",

    "REVIEW",

    "RESCAN"
}
class JobManager:

    def __init__(self):

        self.manifest_dir = (
            MANIFEST_DIR
        )

        self.lock = Lock()

        self.manifest_cache = {}

        self.cache_enabled = (
            CONFIG["runtime"]["manifest_cache"]
        )

        self.archive_dir = (
            self.manifest_dir /
            "archive"
        )

        self.archive_dir.mkdir(
            parents=True,
            exist_ok=True
        )

    # =====================================================
    # GENERATE JOB ID
    # =====================================================

    def generate_job_id(self):

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        short_id = uuid.uuid4().hex[:6]

        return (
            f"JOB_{timestamp}_{short_id}"
        )

    # =====================================================
    # MANIFEST PATH
    # =====================================================

    def get_manifest_path(
        self,
        job_id
    ):

        return (
            self.manifest_dir /
            f"{job_id}.json"
        )

    def atomic_save_manifest(
        self,
        manifest_path,
        manifest
    ):

        temp_path = (
            manifest_path.with_suffix(
                ".tmp"
            )
        )

        with open(
            temp_path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                manifest,
                f,
                indent=4,
                ensure_ascii=False
            )

        temp_path.replace(
            manifest_path
        )


    # =====================================================
    # CREATE JOB
    # =====================================================

    def create_job(
        self,
        pdf_path,
        pages_total=0
    ):

        job_id = (
            self.generate_job_id()
        )

        manifest = {

            "job_id": job_id,

            "pdf_path": str(
                pdf_path
            ),

            "status": "PENDING",

            "pages_total": pages_total,

            "pages_processed": 0,

            "review_required": False,

            "created_at": (
                datetime.now()
                .isoformat()
            ),

            "updated_at": (
                datetime.now()
                .isoformat()
            ),

            "completed_at": None,

            "export_path": None,

            "errors": [],

            # Keyed by page_number (string, since JSON object keys are
            # always strings) -> the same payload shape as a
            # "page_processed" WebSocket event (see
            # processing_pipeline.py's _emit_page_processed /
            # _emit_page_processed_final). Lets the frontend rebuild a
            # booklet's pages/images after a refresh for ANY job status,
            # not just completed ones -- a live WebSocket push is the only
            # other place this data ever existed, and that's lost on
            # reload.
            "pages": {}
        }

        if self.cache_enabled:

            self.manifest_cache[job_id] = manifest

        self.save_manifest(
            job_id,
            manifest
        )

        return manifest

    # =====================================================
    # SAVE MANIFEST
    # =====================================================

    def save_manifest(
        self,
        job_id,
        manifest
    ):

        manifest_path = (
            self.get_manifest_path(
                job_id
            )
        )

        manifest["updated_at"] = (
            datetime.now()
            .isoformat()
        )
        if self.cache_enabled:
            self.manifest_cache[job_id] = manifest

        with self.lock:

            self.atomic_save_manifest(

                manifest_path,

                manifest
            )

    # =====================================================
    # LOAD MANIFEST
    # =====================================================

    def load_manifest(
        self,
        job_id
    ):

        if (

            self.cache_enabled

            and

            job_id in self.manifest_cache
        ):

            return self.manifest_cache[job_id]

        manifest_path = (
            self.get_manifest_path(
                job_id
            )
        )

        if not manifest_path.exists():

            return None
        with self.lock:
            with open(
                manifest_path,
                "r",
                encoding="utf-8"
            ) as f:

                return json.load(f)


    # =====================================================
    # LIST JOBS
    # =====================================================

    def list_jobs(self):

        jobs = {}

        manifest_files = sorted(

            self.manifest_dir.glob("*.json")
        )

        for manifest_file in manifest_files:

            try:

                with open(

                    manifest_file,

                    "r",

                    encoding="utf-8"
                ) as f:

                    manifest = json.load(f)

                job_id = manifest.get(
                    "job_id"
                )

                if job_id:

                    jobs[job_id] = manifest

            except Exception:

                continue

        return jobs


    # =====================================================
    # GET JOB
    # =====================================================

    def get_job(

        self,

        job_id
    ):

        return self.load_manifest(
            job_id
        )

    # =====================================================
    # UPDATE STATUS
    # =====================================================

    def update_status(
        self,
        job_id,
        status
    ):

        manifest = (
            self.load_manifest(
                job_id
            )
        )
        if manifest is None:

            return None

        if status not in JOB_STATUS:

            raise ValueError(
                f"INVALID JOB STATUS: {status}"
            )

        manifest["status"] = status

        self.save_manifest(
            job_id,
            manifest
        )

    # =====================================================
    # UPDATE PAGE PROGRESS
    # =====================================================

    def update_page_progress(
        self,
        job_id,
        pages_processed
    ):

        manifest = (
            self.load_manifest(
                job_id
            )
        )
        if manifest is None:

            return None

        manifest[
            "pages_processed"
        ] = pages_processed

        self.save_manifest(
            job_id,
            manifest
        )

    # =====================================================
    # RECORD PAGE (persists page_processed payloads for refresh-recovery)
    # =====================================================

    def record_page(
        self,
        job_id,
        page_number,
        page_data
    ):

        manifest = (
            self.load_manifest(
                job_id
            )
        )

        if manifest is None:

            return None

        manifest.setdefault(
            "pages",
            {}
        )[str(page_number)] = page_data

        self.save_manifest(
            job_id,
            manifest
        )

    # =====================================================
    # SET EXPORT PATH
    # =====================================================

    def set_export_path(
        self,
        job_id,
        export_path
    ):

        manifest = (
            self.load_manifest(
                job_id
            )
        )

        if manifest is None:

            return None

        manifest[
            "export_path"
        ] = str(export_path)

        self.save_manifest(
            job_id,
            manifest
        )

    # =====================================================
    # MARK REVIEW REQUIRED
    # =====================================================

    def mark_review_required(
        self,
        job_id
    ):

        manifest = (
            self.load_manifest(
                job_id
            )
        )
        if manifest is None:

            return None

        manifest[
            "review_required"
        ] = True

        self.save_manifest(
            job_id,
            manifest
        )

    # =====================================================
    # ADD ERROR
    # =====================================================

    def add_error(
        self,
        job_id,
        error_message
    ):

        manifest = (
            self.load_manifest(
                job_id
            )
        )

        if manifest is None:
            return None

        manifest[
            "errors"
        ].append({

            "timestamp": (
                datetime.now()
                .isoformat()
            ),

            "message": str(
                error_message
            )
        })

        self.save_manifest(
            job_id,
            manifest
        )

    # =====================================================
    # MARK COMPLETED
    # =====================================================

    def mark_completed(
        self,
        job_id
    ):

        manifest = (
            self.load_manifest(
                job_id
            )
        )

        if manifest is None:
            return None

        manifest["completed_at"] = (
            datetime.now()
            .isoformat()
        )

        self.save_manifest(
            job_id,
            manifest
        )

    # =====================================================
    # MARK FAILED
    # =====================================================

    def mark_failed(
        self,
        job_id,
        error_message
    ):

        manifest = (
            self.load_manifest(
                job_id
            )
        )

        if manifest is None:
            return None

        manifest["status"] = (
            "FAILED"
        )

        manifest[
            "errors"
        ].append({

            "timestamp": (
                datetime.now()
                .isoformat()
            ),

            "message": str(
                error_message
            )
        })

        self.save_manifest(
            job_id,
            manifest
        )

    # =====================================================
    # CLEANUP OLD MANIFESTS
    # =====================================================

    def archive_old_manifests(
        self,
        days=30
    ):

        cutoff = (
            datetime.now()
            - timedelta(days=days)
        )

        for manifest_file in (
            self.manifest_dir.glob(
                "JOB_*.json"
            )
        ):

            if (
                datetime.fromtimestamp(
                    manifest_file.stat().st_mtime
                )
                < cutoff
            ):

                destination = (

                    self.archive_dir /

                    manifest_file.name
                )

                manifest_file.rename(
                    destination
                )

    # =====================================================
    # FIND JOB BY PDF
    # =====================================================

    def find_job_by_pdf(
        self,
        pdf_path
    ):

        pdf_path = str(pdf_path)

        jobs = self.list_jobs()

        for job_id, manifest in jobs.items():

            if manifest.get(
                "pdf_path"
            ) == pdf_path:

                return manifest

        return None


    # =====================================================
    # GET OR CREATE JOB
    # =====================================================

    def get_or_create_job(
        self,
        pdf_path,
        pages_total=0
    ):

        existing = self.find_job_by_pdf(
            pdf_path
        )

        if existing:

            status = existing.get(
                "status"
            )

            if status in {

                "PREPROCESSING",

                "VALIDATING",

                "INFERENCE",

                "EXPORTING"
            }:

                return existing

        return self.create_job(
            pdf_path,
            pages_total
        )

# =========================================================
# GLOBAL JOB MANAGER
# =========================================================

job_manager = JobManager()
