"""Ported unchanged from D:\\OMR_System\\app\\core\\models\\overlay.py."""

from typing import Literal
from typing import Optional
from typing import Dict
from typing import Any
from typing import List

from pydantic import BaseModel
from pydantic import Field


# =========================================================
# OVERLAY STYLE
# =========================================================

class OverlayStyle(BaseModel):

    color: str = "#00FF00"

    thickness: int = 2

    opacity: float = 1.0

    fill: bool = False


# =========================================================
# OVERLAY
# =========================================================

class OverlayObject(BaseModel):

    overlay_id: str

    overlay_type: Literal[
        "bbox",
        "bubble",
        "ocr_region",
        "validation_warning",
        "section"
    ]

    render_mode: Literal[
        "rectangle",
        "circle",
        "polygon",
        "label"
    ]

    label: Optional[str] = None

    bbox: Optional[
        List[int]
    ] = None

    points: Optional[
        List[Dict[str, int]]
    ] = None

    metadata: Dict[
        str,
        Any
    ] = Field(default_factory=dict)

    style: OverlayStyle = (
        OverlayStyle()
    )
