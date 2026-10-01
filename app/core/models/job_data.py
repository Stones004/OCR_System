"""Ported unchanged from D:\\OMR_System\\app\\core\\models\\job_data.py."""

from typing import Optional
from typing import List
from typing import Dict
from typing import Any

from pydantic import BaseModel

from app.core.models.page_data import (
    PageData
)


# =========================================================
# JOB DATA
# =========================================================

class JobData(BaseModel):

    # =====================================================
    # JOB INFO
    # =====================================================

    job_id: str

    file_name: str

    input_path: Optional[str] = None

    output_dir: Optional[str] = None

    # =====================================================
    # PAGE DATA
    # =====================================================

    pages: List[PageData] = []

    # =====================================================
    # PIPELINE STATUS
    # =====================================================

    status: str = "PENDING"

    total_pages: int = 0

    processed_pages: int = 0

    failed_pages: int = 0

    # =====================================================
    # PIPELINE METRICS
    # =====================================================

    total_processing_time: Optional[
        float
    ] = None

    validation_time: Optional[
        float
    ] = None

    inference_time: Optional[
        float
    ] = None

    extraction_time: Optional[
        float
    ] = None

    # =====================================================
    # EXPORTS
    # =====================================================

    exported_json: Optional[str] = None

    exported_csv: Optional[str] = None

    exported_excel: Optional[str] = None

    # =====================================================
    # FAILURES
    # =====================================================

    errors: List[str] = []

    warnings: List[str] = []

    # =====================================================
    # METADATA
    # =====================================================

    metadata: Dict[str, Any] = {}
