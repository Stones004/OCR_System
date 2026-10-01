"""
Annotation Assembler

Turns raw per-page label detections (bbox, text, confidence from the OCR
backend, already in page-pixel coordinates) into the flat Annotation list
the export schema wants. There is no parent/child question hierarchy --
every detected label is its own independent entry.

Coordinate note: the engine only crops the page's WIDTH down to the margin
before running annotation detection (Cropper keeps columns [0 : separator.x
+ right_padding]); it never crops or offsets the height. So an ROI bbox
coming out of AnnotationDetector is already expressed in full-page pixel
coordinates and needs no translation here.

Continuation logic (deliberately simple, no counters/parent-tracking, no
validity checking): every detected label is its own new answer, full
stop. A section is identified by nothing more than "the next detection" --
not by whether its text happens to parse as a question number. Whether
that label's text later resolves to a lookup_tag (app/engine/
question_mapping.py) is a separate, downstream concern that doesn't
change how boundaries are drawn here.

  - Each detected label on a page becomes its own entry
    (is_continuation=False, question_bbox=its own bbox).
  - A page's LAST label is "open": its answer might run onto the next page.
  - If a page has literally NO detected labels while a question is still
    open, the whole page is one continuation row for that question
    (question_bbox omitted, answer_bbox spans the full page).
  - answer_bbox for a real label runs from the label's top down to the top
    of the next label on the page (or the page bottom if it's the last
    label on the page).

Identity: question_id is just the label's literal OCR text, so two
unrelated labels that both read "1" are NOT the same answer. Each new
(non-continuation) label gets a fresh instance_id (a simple job-scoped
counter); its own continuation rows reuse that same instance_id. Callers
(the frontend, in particular) must group/select by instance_id, never by
question_id -- see app/engine/models.py's Annotation docstring.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.engine.models import Annotation


@dataclass
class PageLabels:
    """One page's raw label detections, ready for assembly."""

    page_number: int
    page_height: float
    body_x1: float             # left edge of the answer body (x2 of the margin crop)
    body_x2: float             # right edge of the answer body (page width)
    labels: list[dict] = field(default_factory=list)
    # each label: {"bbox": (x1,y1,x2,y2), "text": str, "confidence": float|None}
    detection_failed: bool = False   # separator not found / detector crashed


@dataclass
class _OpenQuestion:
    instance_id: int
    question_id: str
    text: str
    normalized_text: str
    confidence: float | None


def _normalize_text(raw: str) -> str:
    return raw.strip()


def assemble(pages: list[PageLabels]) -> dict[int, list[Annotation]]:
    """
    Returns {page_number: [Annotation, ...]} in reading order.
    """

    by_page: dict[int, list[Annotation]] = {}
    open_question: _OpenQuestion | None = None
    next_instance_id = 1

    for page in sorted(pages, key=lambda p: p.page_number):

        annotations: list[Annotation] = []
        labels = page.labels

        if not labels:

            if open_question is not None:
                annotations.append(Annotation(
                    instance_id=open_question.instance_id,
                    question_id=open_question.question_id,
                    text=open_question.text,
                    normalized_text=open_question.normalized_text,
                    is_continuation=True,
                    question_bbox=None,
                    answer_bbox=(page.body_x1, 0.0, page.body_x2, page.page_height),
                    confidence=open_question.confidence,
                ))
            # else: nothing detected and nothing open -- an empty page.
            # Left with zero annotations; review flagging handles it via
            # detection_failed / missing lookup_tag upstream.

        else:

            for i, label in enumerate(labels):

                x1, y1, x2, y2 = label["bbox"]
                next_y = labels[i + 1]["bbox"][1] if i + 1 < len(labels) else page.page_height

                text = label["text"]
                normalized_text = _normalize_text(text)
                instance_id = next_instance_id
                next_instance_id += 1

                annotations.append(Annotation(
                    instance_id=instance_id,
                    question_id=normalized_text,
                    text=text,
                    normalized_text=normalized_text,
                    is_continuation=False,
                    question_bbox=(float(x1), float(y1), float(x2), float(y2)),
                    answer_bbox=(page.body_x1, float(y1), page.body_x2, float(next_y)),
                    confidence=label["confidence"],
                ))

                open_question = _OpenQuestion(
                    instance_id=instance_id,
                    question_id=normalized_text,
                    text=text,
                    normalized_text=normalized_text,
                    confidence=label["confidence"],
                )

        by_page[page.page_number] = annotations

    return by_page
