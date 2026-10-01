"""Ported unchanged from D:\\OMR_System\\app\\validator\\validation_report.py."""

from typing import List, Tuple

from app.validator.schemas import (
    ValidationResult
)


# =========================
# BUILD REPORT PAYLOAD
# =========================

def build_validation_report(

    pdf_name: str,

    page_results: List[
        Tuple[int, ValidationResult]
    ]
) -> dict:

    report = {

        "pdf": pdf_name,

        "pages": []
    }

    for page_num, result in page_results:

        report["pages"].append({

            "page": page_num,

            "status": result.status,

            "score": result.score,

            "fatal_failure": (
                result.fatal_failure
            ),

            "issues": [

                issue.model_dump()

                for issue in result.issues
            ],

            "metrics": result.metrics,

            "timestamp": result.timestamp,

            "processing_time": (
                result.processing_time
            ),

            "overridden": result.overridden
        })

    return report
