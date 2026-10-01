"""
Replaces D:\\OMR_System\\app\\engine\\debug_visualizer.py (bubble/OMR/band
overlays) with question-label / answer-region overlays for the OCR
engine. Same two entry points app.services.visualization_service calls
(visualize_detections, visualize_extraction(..., save_path=...)), so that
service needed no changes beyond its colour lookup.
"""

from __future__ import annotations

import cv2

from app.core.config.config_loader import CONFIG


class DebugVisualizer:

    def __init__(self):

        viz_cfg = CONFIG["visualization"]

        self.thickness = viz_cfg["detection_box_thickness"]

        self.font_scale = viz_cfg["font_scale"]

        colors = viz_cfg["class_colors"]

        self.label_color = tuple(colors["question_label"])

        self.answer_color = tuple(colors["answer_region"])

    # =========================================================
    # RAW DETECTIONS (one box per detected ROI, pre-assembly)
    # =========================================================

    def visualize_detections(self, image, detections, save_path):

        vis = image.copy()

        for det in detections:

            x1, y1, x2, y2 = (int(c) for c in det.bbox)

            cv2.rectangle(
                vis, (x1, y1), (x2, y2), self.label_color, self.thickness
            )

            cv2.putText(
                vis,
                f"{det.score:.2f}",
                (x1, max(0, y1 - 5)),
                cv2.FONT_HERSHEY_SIMPLEX,
                self.font_scale,
                self.label_color,
                1,
            )

        cv2.imwrite(save_path, vis)

    # =========================================================
    # ASSEMBLED / RAW QUESTIONS
    #
    # Called once per page as soon as that page finishes (before the
    # job-level annotation_assembler.assemble() pass has run), so
    # omr_result.questions may still be the raw per-label dicts
    # ({"bbox","text","confidence"}) rather than the final assembled
    # shape ({"question_bbox","answer_bbox","lookup_tag",...}). Both are
    # handled here.
    # =========================================================

    def visualize_extraction(self, image, omr_result, save_path):

        vis = image.copy()

        for q in omr_result.questions:

            question_bbox = q.get("question_bbox", q.get("bbox"))

            if question_bbox:

                x1, y1, x2, y2 = (int(c) for c in question_bbox)

                cv2.rectangle(
                    vis, (x1, y1), (x2, y2), self.label_color, self.thickness
                )

                label = str(
                    q.get("lookup_tag")
                    or q.get("question_id")
                    or q.get("text", "")
                )

                cv2.putText(
                    vis,
                    label,
                    (x1, max(0, y1 - 5)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    self.font_scale,
                    self.label_color,
                    1,
                )

            answer_bbox = q.get("answer_bbox")

            if answer_bbox:

                x1, y1, x2, y2 = (int(c) for c in answer_bbox)

                cv2.rectangle(
                    vis,
                    (x1, y1),
                    (x2, y2),
                    self.answer_color,
                    max(1, self.thickness - 1),
                )

        cv2.imwrite(save_path, vis)
