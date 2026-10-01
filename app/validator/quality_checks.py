"""
Provisioned stub -- returns zeroed metrics rather than computing them.
The real computations already exist in app.validator.utils
(compute_brightness, compute_contrast, compute_content_density,
compute_edge_density, variance_of_laplacian) and
app.core.config.thresholds has matching thresholds already loaded from
config.yaml; wiring them up here is the only step left for later.
"""

import numpy as np

from app.validator.schemas import (
    QualityMetrics
)


def run_quality_checks(
    gray: np.ndarray
) -> QualityMetrics:

    return QualityMetrics(
        blur=0.0,
        brightness=0.0,
        contrast=0.0,
        content_density=0.0,
        edge_density=0.0,
    )
