"""Ported unchanged from D:\\OMR_System\\app\\api\\routes\\images.py."""

from fastapi import APIRouter
from fastapi.responses import FileResponse

from pathlib import Path

from app.core.config.config_loader import (
    CONFIG
)


# =========================================================
# ROUTER
# =========================================================

router = APIRouter()


# =========================================================
# GET PAGE IMAGE
# =========================================================

@router.get("/images/{image_path:path}")
def get_image(
    image_path: str
):

    file_path = (
        Path(
            CONFIG["paths"]["debug_output_dir"]
        )
        / image_path
    )

    if not file_path.exists():

        return {
            "error": "IMAGE NOT FOUND"
        }

    return FileResponse(file_path)
