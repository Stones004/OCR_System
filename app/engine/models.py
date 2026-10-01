"""
The flat per-label annotation this engine produces. One entry per
detected question label -- no parent/subpart hierarchy. Serialized (via
.model_dump(exclude_none=True)) into app.core.models.omr_results.
OMRResult.questions, so `question_bbox` is omitted (not null) on
continuation rows, matching the target export shape:

    {
      "instance_id": 7,
      "question_id": "1",
      "text": "1",
      "normalized_text": "1",
      "is_continuation": false,
      "question_bbox": [108.0, 615.0, 171.0, 678.0],
      "answer_bbox": [173.0, 605.0, 2292.0, 3223.0],
      "confidence": 0.8732
    }

question_id is the literal OCR text of the label -- two unrelated
detections both read as "7" get the same question_id, on purpose (no
hierarchy, no parsing). That makes question_id useless as an identity key:
grouping or highlighting "every detection with question_id == '1'" would
conflate every distinct "1" in the booklet into one. instance_id exists
for exactly that -- a unique, job-scoped id per detected answer instance,
assigned once by annotation_assembler.assemble() and shared by a label and
its own continuation rows (never by two different labels, even same text).
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict

BBox = tuple[float, float, float, float]


class Annotation(BaseModel):
    model_config = ConfigDict(frozen=True)

    instance_id: int
    question_id: str
    text: str
    normalized_text: str
    is_continuation: bool
    question_bbox: Optional[BBox] = None
    answer_bbox: BBox
    confidence: Optional[float] = None
    lookup_tag: Optional[str] = None
