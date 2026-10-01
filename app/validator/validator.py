"""
Pre-inference page validation.

D:\\OMR_System ran this as a full image-quality gate (blur/skew/
brightness/contrast/density/geometry) BEFORE attempting bubble detection,
since a badly-scanned bubble sheet is unrecoverable. Per your direction,
this is kept as a provisioned scaffold rather than ported in full: the
orchestration and the ValidationResult contract are identical to the
original (validate_scan(gray, page_number, timestamp, processing_time) ->
ValidationResult, called from app.services.validation_service exactly as
before), but every sub-check underneath is a pass-through stub for now
(see page_geometry.py, structural_checks.py, quality_checks.py,
scoring.py in this package). Filling in real checks later only means
editing those four files -- nothing that calls validate_scan needs to
change.
"""

# pyrefly: ignore [missing-import]
from app.validator.utils import (
    validate_grayscale_image
)

from app.validator.schemas import (
    ValidationResult,
    ValidationIssue
)

# pyrefly: ignore [missing-import]
import numpy as np
import cv2

from app.validator.page_geometry import (
    validate_page_geometry
)

from app.validator.structural_checks import (
    run_structural_checks
)

from app.validator.quality_checks import (
    run_quality_checks
)

from app.validator.scoring import (
    compute_validation_result
)

from app.core.logging.logger import (
    logger
)

# =========================
# VALIDATION
# =========================


def validate_scan(

    gray: np.ndarray,

    page_number: int,

    timestamp: str,

    processing_time: float

) -> ValidationResult:


    gray = validate_grayscale_image(gray)
    geometry = validate_page_geometry(gray)

    structural = run_structural_checks(gray)

    validation_gray = cv2.resize(
        gray,
        None,
        fx=0.5,
        fy=0.5
    )

    quality = run_quality_checks(validation_gray)

    result = compute_validation_result(

        structural=structural,

        quality=quality,

        page_number=page_number,

        timestamp=timestamp,

        processing_time=processing_time
    )

    result.metrics["geometry"] = (
        geometry.model_dump()
    )

    return result
