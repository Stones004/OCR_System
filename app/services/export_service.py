"""
Ported unchanged from D:\\OMR_System\\app\\services\\export_service.py.
Entirely generic JSON export/serialization helpers -- no OMR-specific
logic at all, so nothing needed to change.
"""

import json

from pathlib import Path
from typing import List, Tuple
from app.validator.schemas import ( ValidationResult )

# pyrefly: ignore [missing-import]
import numpy as np
from app.core.logging.logger import (
    logger
)

from app.core.config.config_loader import (
    CONFIG
)

from app.validator.validation_report import (
    build_validation_report
)


def convert(obj):

    # =============================================
    # PYDANTIC
    # =============================================

    if hasattr(obj, "model_dump"):

        return convert(
            obj.model_dump()
        )

    # =============================================
    # NUMPY ARRAY
    # =============================================

    if isinstance(obj, np.ndarray):

        return f"<ndarray shape={obj.shape}>"

    # =============================================
    # NUMPY SCALARS
    # =============================================

    if isinstance(obj, np.integer):

        return int(obj)

    if isinstance(obj, np.floating):

        return float(obj)

    if isinstance(obj, np.bool_):

        return bool(obj)

    # =============================================
    # DICT
    # =============================================

    if isinstance(obj, dict):

        return {

            k: convert(v)

            for k, v in obj.items()
        }

    # =============================================
    # LIST
    # =============================================

    if isinstance(obj, list):

        return [

            convert(x)

            for x in obj
        ]

    return obj



def build_overlay_export(
    page_result
):
    return


def save_json(
    data,
    output_path: Path
) -> Path:

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as f:

        data = convert(data)
        json.dump(
            data,
            f,
            indent=CONFIG["output"]["json_indent"],
            ensure_ascii=False
        )


    return output_path


def export_omr_results(

    pdf_name: str,

    omr_results: dict
) -> Path | None:

    if not CONFIG["output"]["save_exports"]:

        return None

    export_dir = Path(
        CONFIG["paths"]["exports_dir"]
    )

    export_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    output_path = (

        export_dir /

        f"{Path(pdf_name).stem}_ocr_min.json"
    )

    serialized_results = convert(
        omr_results
    )

    try:

        return save_json(

            serialized_results,

            output_path
        )

    except Exception as e:

        logger.exception(

            f"EXPORT FAILED: {e}"
        )

        return None


# =========================
# EXPORT REPORT
# =========================

def export_validation_report(

    pdf_name: str,

    page_results: List[ Tuple[int, ValidationResult] ]

) -> Path | None:

    if not CONFIG["output"]["save_exports"]:

        return None

    report_dir = Path(
        CONFIG["paths"]["reports_dir"]
    )

    report_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    report = build_validation_report(

        pdf_name,
        page_results
    )

    output_path = (

        report_dir /

        f"{Path(pdf_name).stem}.json"
    )

    save_json(
        report,
        output_path
    )

    logger.info(
        f"EXPORT SAVED: {output_path}"
    )

    return output_path
