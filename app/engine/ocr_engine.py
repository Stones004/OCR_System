"""
Replaces D:\\OMR_System\\app\\engine\\omr_engine.py (YOLOX bubble detector)
with the ported D:\\OCR_codes pipeline: deskew -> find margin separator ->
crop -> remove red/green evaluator ink -> preprocess -> detect
handwritten label ROIs -> OCR each ROI with PARSeq.

Keeps the exact same call contract app.services.inference_service.
InferenceService expects (process_image(image, page_number) -> {
"prediction_result": PredictionResult, "omr_result": OMRResult }), so
nothing above inference_service needed to change.

Per-page output is intentionally RAW: one label detection per entry in
omr_result.questions (bbox/text/confidence), not yet assembled into the
final question_id/is_continuation/answer_bbox shape. Assembly needs
cross-page state (a label's answer can run onto the next page) but
pages are dispatched as independent, potentially out-of-order Celery
tasks (see processing_pipeline.py's GPU-queue windowing) -- so
app.engine.annotation_assembler.assemble() runs once at the job level,
after every page has been collected and sorted by page_number, in
app/pipeline/processing_pipeline.py.
"""

from __future__ import annotations

import time

from app.core.config.ocr_engine_config import ocr_engine_config
from app.core.models.detection import DetectionResult, PredictionResult
from app.core.models.omr_results import OMRResult
from app.core.logging.logger import logger

from app.engine.stages.deskewer import Deskewer
from app.engine.stages.vertical_extractor import VerticalExtractor
from app.engine.stages.line_detector import LineDetector
from app.engine.stages.cropper import Cropper
from app.engine.stages.annotation_remover import AnnotationRemover
from app.engine.stages.preprocessor import Preprocessor
from app.engine.stages.annotation_detector import AnnotationDetector
from app.engine.stages.noise_classifier import NoiseClassifier
from app.engine.stages.roi_text_extractor import ROITextExtractor


class AnswerScriptEngine:

    def __init__(self):

        cfg = ocr_engine_config

        self.deskewer = Deskewer(cfg.deskew)

        self.vertical_extractor = VerticalExtractor(
            cfg.vertical, verbose=cfg.pipeline.verbose
        )

        self.line_detector = LineDetector(
            cfg.separator, cfg.visualization, verbose=cfg.pipeline.verbose
        )

        self.cropper = Cropper(cfg.crop)

        self.preprocessor = Preprocessor(cfg.preprocess)

        self.annotation_detector = AnnotationDetector(
            cfg.annotation_detector, cfg.visualization, verbose=cfg.pipeline.verbose
        )

        self.annotation_remover = (
            AnnotationRemover(cfg.ink_removal)
            if cfg.pipeline.use_annotation_removal
            else None
        )

        # Spawns a second torch subprocess (shares the PARSeq venv) purely
        # to triage ROIs before OCR -- see app/engine/stages/noise_classifier.py.
        self.noise_classifier = (
            NoiseClassifier(cfg.noise_classifier)
            if cfg.pipeline.use_noise_classifier
            else None
        )

        # Spawns the PARSeq subprocess. Created once per AnswerScriptEngine
        # instance, which app.services.inference_service creates once at
        # worker-process startup -- see app/workers/gpu_tasks.py.
        self.text_extractor = ROITextExtractor(cfg.ocr)

        self.right_padding = cfg.crop.right_padding

    # =========================================================
    # ENGINE CORE
    # =========================================================

    def process_image(self, image, page_number=1):

        total_start = time.time()

        corrected, _angle = self.deskewer.process(image)

        vertical, _debug = self.vertical_extractor.extract(corrected)

        _overlay, separator = self.line_detector.detect(vertical)

        page_height, page_width = corrected.shape[:2]

        if separator is None:

            logger.warning(
                f"[PAGE {page_number}] SEPARATOR NOT FOUND"
            )

            prediction_result = PredictionResult(
                detections=[],
                image_width=page_width,
                image_height=page_height,
                inference_time=round(time.time() - total_start, 4),
                model_name="ocr-answer-script-engine",
            )

            omr_result = OMRResult(
                status="REVIEW",
                extraction_success=False,
                flagged_for_review=True,
                message="Margin separator not found.",
                questions=[],
                metadata={
                    "body_x1": 0.0,
                    "body_x2": float(page_width),
                    "separator_found": False,
                },
                page_size={"width": page_width, "height": page_height},
            )

            return {
                "prediction_result": prediction_result,
                "omr_result": omr_result,
            }

        crop = self.cropper.crop(corrected, separator)

        if self.annotation_remover is not None:
            clean_crop, _mask = self.annotation_remover.process_debug(crop)
        else:
            clean_crop = crop

        gray, binary = self.preprocessor.process(clean_crop)

        rois, _det_debug = self.annotation_detector.detect(gray, binary)

        if self.noise_classifier is not None and rois:
            rois = self.noise_classifier.filter_rois(rois, page_number=page_number)

        labels = self.text_extractor.extract(gray, rois) if rois else []

        detections = [
            DetectionResult(
                bbox=tuple(float(c) for c in label["bbox"]),
                score=float(label["confidence"] or 0.0),
                class_id=0,
                class_name="question_label",
            )
            for label in labels
        ]

        questions = [
            {
                "bbox": [float(c) for c in label["bbox"]],
                "text": label["text"],
                "confidence": label["confidence"],
            }
            for label in labels
        ]

        body_x1 = float(separator["x"] + self.right_padding)
        body_x2 = float(page_width)

        omr_result = OMRResult(
            status="SUCCESS",
            extraction_success=True,
            flagged_for_review=False,
            message=None,
            questions=questions,
            metadata={
                "body_x1": body_x1,
                "body_x2": body_x2,
                "separator_found": True,
                "separator_x": int(separator["x"]),
            },
            page_size={"width": page_width, "height": page_height},
        )

        prediction_result = PredictionResult(
            detections=detections,
            image_width=page_width,
            image_height=page_height,
            inference_time=round(time.time() - total_start, 4),
            model_name="parseq",
        )

        return {
            "prediction_result": prediction_result,
            "omr_result": omr_result,
        }
