"""
Adapted from D:\\OMR_System\\app\\api\\routes\\config.py: the original
returned/updated "ocr" (LM Studio bubble-UID OCR, dead code -- see
app.services in this project's docstrings) and "model" (YOLOX weights
path/confidence threshold, no longer applicable) sections. Dropped both;
everything else is unchanged.
"""

from fastapi import APIRouter
from pydantic import BaseModel
import yaml

from app.core.config.config_loader import (
    CONFIG,
    CONFIG_PATH
)

router = APIRouter()


@router.get("/config")
def get_config():

    return {

        "runtime": CONFIG["runtime"],

        "output": CONFIG["output"],

        "visualization":
            CONFIG["visualization"],

        "observability":
            CONFIG["observability"],

        "thresholds":
            CONFIG["thresholds"]
    }


class ConfigUpdate(BaseModel):

    runtime: dict | None = None

    output: dict | None = None

    visualization: dict | None = None

    observability: dict | None = None

    thresholds: dict | None = None


@router.patch("/config")
def update_config(

    payload: ConfigUpdate
):

    updates = payload.dict(
        exclude_none=True
    )

    for section, values in updates.items():

        if section not in CONFIG:

            continue

        CONFIG[section].update(
            values
        )

    with open(

        CONFIG_PATH,

        "w",

        encoding="utf-8"

    ) as f:

        yaml.safe_dump(
            CONFIG,
            f,
            sort_keys=False
        )

    return {

        "success": True
    }
