"""
ROI Text Extractor

Runs OCR on every detected annotation ROI and returns one record per ROI,
keeping the bbox and confidence that D:\\OCR_codes\\src\\roi_text_extractor.py
throws away. The annotation assembler needs both to build question_bbox /
answer_bbox and to know how much to trust each label, so this is a new
module rather than a straight port.
"""

from app.core.config.ocr_engine_config import OcrConfig
from app.engine.stages.ocr import create_backend


class ROITextExtractor:

    def __init__(self, config: OcrConfig):
        self.ocr = create_backend(config.backend, config)

    def extract(self, gray, rois):
        """
        gray : full preprocessed grayscale image for the page's margin crop.
        rois : [{"bbox": (x1, y1, x2, y2), "roi": ndarray}, ...] in reading
               order (top to bottom), as produced by AnnotationDetector.

        Returns [{"bbox": (x1, y1, x2, y2), "text": str, "confidence": float}, ...]
        in the same order.
        """

        if not rois:
            return []

        # One batched call for every ROI on the page, instead of one
        # subprocess round-trip per ROI -- see OCRBackend.read_batch /
        # ParseqBackend.read_batch.
        predictions = self.ocr.read_batch([roi["roi"] for roi in rois])

        results = []

        for roi, prediction in zip(rois, predictions):

            results.append({
                "bbox": roi["bbox"],
                "text": prediction.get("text", ""),
                "confidence": prediction.get("confidence"),
            })

        return results
