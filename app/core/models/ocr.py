"""
Ported unchanged from D:\\OMR_System\\app\\core\\models\\ocr.py. Kept for
schema parity with app.core.models.page_data.PageData.ocr_results, but
unused: the LM Studio bubble-UID OCR service this modeled is dead code in
the source repo (nothing imported app.services.ocr_service outside
itself), and this engine's own OCR results live in PredictionResult /
OMRResult instead.
"""

from typing import Optional

from pydantic import BaseModel


class OCRResult(BaseModel):

    uid: str

    raw_text: str

    confidence: float

    provider: str

    success: bool

    error: Optional[str] = None
