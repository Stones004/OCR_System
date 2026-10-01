"""
Provisioned stub. D:\\OMR_System's page_geometry.py located the bubble
sheet's rectangular boundary within the scan (perspective/contour
detection) -- meaningless for a handwritten answer script, which has no
fixed printed form to find. Kept as a pass-through so app/validator/
validator.py's orchestration doesn't change shape when real per-page
geometry checks (if any turn out to be useful for this document type) are
added later; see the package-level note in validator.py.
"""

import numpy as np

from app.validator.schemas import (
    GeometryValidationResult
)


def validate_page_geometry(
    gray: np.ndarray
) -> GeometryValidationResult:

    return GeometryValidationResult(
        passed=True,
        reasons=[],
        coverage=1.0,
        perspective_score=1.0,
        border_touch=False,
        contour=None,
    )
