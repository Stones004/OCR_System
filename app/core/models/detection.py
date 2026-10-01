"""
Ported unchanged from D:\\OMR_System\\app\\core\\models\\detection.py.
Generic bbox/score/class detection container -- populated by app/engine/
ocr_engine.py with one DetectionResult per detected question-label ROI
(class_name="question_label") instead of YOLOX bubble-grid classes.
"""

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict
from typing import List
from typing import Tuple

# =========================
# SINGLE DETECTION
# =========================

class DetectionResult(BaseModel):

    bbox: Tuple[float, float, float, float]

    score: float

    class_id: int

    class_name: str

    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )


# =========================
# PREDICTION RESULT
# =========================

class PredictionResult(BaseModel):

    detections: List[DetectionResult]

    image_width: int

    image_height: int

    inference_time: float

    model_name: str

    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )
