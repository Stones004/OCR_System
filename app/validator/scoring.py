"""
Provisioned stub -- always scores 100 / never a fatal failure. Once
app.validator.structural_checks and quality_checks compute real values,
this is where they'd be combined into a score and a pass/fail verdict
(mirroring how app.core.config.thresholds.MIN_ACCEPTABLE_SCORE is already
loaded and waiting).
"""

from app.validator.schemas import (
    StructuralCheckResult,
    QualityMetrics,
    ValidationResult,
)


def compute_validation_result(

    *,

    structural: StructuralCheckResult,

    quality: QualityMetrics,

    page_number: int,

    timestamp: str,

    processing_time: float,

) -> ValidationResult:

    return ValidationResult(
        page_number=page_number,
        timestamp=timestamp,
        processing_time=processing_time,
        status="OK",
        score=100.0,
        fatal_failure=False,
        issues=[],
        metrics={
            "structural": structural.model_dump(),
            "quality": quality.model_dump(),
        },
    )
