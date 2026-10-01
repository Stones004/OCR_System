"""
Provisioned stub -- always passes. Real per-page structural checks
(e.g. skew via app.validator.utils.estimate_skew against
app.core.config.thresholds.MAX_SAFE_SKEW) can be dropped in here later
without changing app/validator/validator.py's orchestration.
"""

import numpy as np

from app.validator.schemas import (
    StructuralCheckResult
)


def run_structural_checks(
    gray: np.ndarray
) -> StructuralCheckResult:

    return StructuralCheckResult(
        passed=True,
        issue=None,
        value=None,
        metrics={},
    )
