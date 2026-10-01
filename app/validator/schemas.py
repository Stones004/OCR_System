"""Ported unchanged from D:\\OMR_System\\app\\validator\\schemas.py."""

from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field


# =========================
# VALIDATION ISSUE
# =========================

class ValidationIssue(BaseModel):

    code: str

    message: str

    severity: str = "warning"


# =========================
# VALIDATION RESULT
# =========================

class ValidationResult(BaseModel):

    # Page metadata
    page_number: int

    timestamp: str

    processing_time: float

    # Overall validation state
    status: str

    # Final validation score
    score: float

    # Fatal validation failure
    fatal_failure: bool

    # Validation issues
    issues: List[ValidationIssue] = Field(
        default_factory=list
    )

    # Raw validation metrics
    metrics: Dict[str, Any] = Field(
        default_factory=dict
    )

    # Optional overlay/debug image
    overlay_path: Optional[str] = None

    # Operator override state
    overridden: bool = False

# =========================
# GEOMETRY VALIDATION RESULT
# =========================

class GeometryValidationResult(BaseModel):

    passed: bool

    reasons: List[str]

    coverage: float

    perspective_score: float

    border_touch: bool

    contour: Optional[List[List[float]]] = None


# =========================
# STRUCTURAL CHECK RESULT
# =========================

class StructuralCheckResult(BaseModel):

    passed: bool

    issue: Optional[str] = None

    value: Optional[float] = None

    metrics: Dict[str, Any]= Field(
        default_factory=dict
    )

# =========================
# QUALITY METRICS
# =========================

class QualityMetrics(BaseModel):

    blur: float

    brightness: float

    contrast: float

    content_density: float

    edge_density: float
