"""
Ported unchanged from D:\\OMR_System\\app\\core\\models\\omr_results.py.
`questions: List[Dict[str, Any]]` is a natural fit for this engine's flat
Annotation list (question_id/text/normalized_text/is_continuation/
question_bbox/answer_bbox/confidence/lookup_tag per app.engine.models) --
no schema change needed, just different content.
"""

from typing import Optional
from typing import Dict
from typing import Any
from typing import List

from pydantic import BaseModel, Field


# =========================================================
# OMR RESULT
# =========================================================

class OMRResult(BaseModel):

    status: str = "SUCCESS"

    extraction_success: bool = True

    flagged_for_review: bool = False

    message: Optional[str] = None

    questions: List[Dict[str, Any]] = Field(
        default_factory=list
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict
    )

    page_size: Dict[str, int] = Field(
        default_factory=dict
    )
