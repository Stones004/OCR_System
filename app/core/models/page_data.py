"""Ported unchanged from D:\\OMR_System\\app\\core\\models\\page_data.py."""

from typing import Optional
from typing import List
from typing import Dict
from typing import Any

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field

from app.validator.schemas import (
    ValidationResult
)

from app.core.models.detection import (
    PredictionResult
)

from app.core.models.ocr import (
    OCRResult
)

from app.core.models.omr_results import (
    OMRResult
)


# =========================================================
# PAGE DATA
# =========================================================

class PageData(BaseModel):

    # =====================================================
    # PAGE INFO
    # =====================================================

    page_number: int

    file_name: Optional[str] = None

    # =====================================================
    # VALIDATION
    # =====================================================

    validation_result: Optional[
        ValidationResult
    ] = None

    # =====================================================
    # PREPROCESSING
    # =====================================================

    preprocessing_time: Optional[
        float
    ] = None

    # =====================================================
    # PREDICTION
    # =====================================================

    prediction_result: Optional[
        PredictionResult
    ] = None

    # =====================================================
    # OCR
    # =====================================================

    ocr_results: List[OCRResult] = Field(
        default_factory=list
    )

    # =====================================================
    # EXTRACTION
    # =====================================================

    omr_result: Optional[
        OMRResult
    ] = None

    # =====================================================
    # PIPELINE STATE
    # =====================================================

    status: str = "PENDING"

    errors: List[str] = Field(
        default_factory=list
    )

    warnings: List[str] = Field(
        default_factory=list
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict
    )

    # =====================================================
    # PIPELINE LIFECYCLE
    # =====================================================

    current_stage: str = "PENDING"

    stage_history: List[str] = Field(
        default_factory=list
    )

    review_required: bool = False

    review_reason: Optional[str] = None

    # =====================================================
    # TIMINGS
    # =====================================================

    total_processing_time: Optional[
        float
    ] = None


class PageProcessingResult(BaseModel):

    page_number: int

    prediction_result: PredictionResult

    omr_result: OMRResult

    validation_result: Optional[ValidationResult] = None
