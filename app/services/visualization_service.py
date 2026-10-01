"""
Ported unchanged from D:\\OMR_System\\app\\services\\visualization_service.py
(the OMR-specific parts live in app.engine.debug_visualizer, which this
already delegated to; nothing here needed to change).
"""

from app.core.models.overlay import (OverlayObject, OverlayStyle)
from pathlib import Path

from app.engine.debug_visualizer import (
    DebugVisualizer
)

from app.core.config.config_loader import (
    CONFIG
)

from app.core.logging.logger import (
    logger
)

class VisualizationService:

    def __init__(self):

        self.visualizer = (
            DebugVisualizer()
        )

        self.viz_cfg = (
            CONFIG["visualization"]
        )

    def build_detection_overlays(

        self,

        prediction_result
    ):


        overlays = []

        for idx, det in enumerate(
            prediction_result.detections
        ):

            x1, y1, x2, y2 = map(
                int,
                det.bbox
            )

            overlays.append(

                OverlayObject(

                    overlay_id=(
                        f"detection_{idx}"
                    ),

                    overlay_type="bbox",

                    render_mode="rectangle",

                    label=(
                        f"{det.class_name} "
                        f"{det.score:.2f}"
                    ),

                    bbox=[
                        x1,
                        y1,
                        x2,
                        y2
                    ],

                    metadata={

                        "class_id": det.class_id,

                        "class_name": det.class_name,

                        "score": det.score
                    },

                    style=OverlayStyle(

                        color="#00FF00",

                        thickness=2
                    )
                )
            )

        return overlays

    # =====================================================
    # SAVE PAGE VISUALIZATIONS
    # =====================================================

    def save_page_visualizations(

        self,

        job_id,

        page_number,

        image,

        prediction_result,

        omr_result,

        booklet_id

    ) -> dict:


        ui_path = None
        debug_path = None

        try:

            # =============================================
            # UI VISUALIZATION
            # =============================================

            if self.viz_cfg["save_ui_images"]:

                ui_dir = Path(
                    CONFIG["paths"]["ui_output_dir"]
                )

                ui_dir.mkdir(
                    parents=True,
                    exist_ok=True
                )

                ui_path = (
                    ui_dir /
                    f"{job_id}_page_"
                    f"{page_number:03d}_ui.png"
                )

                self.visualizer.visualize_detections(

                    image,

                    prediction_result.detections,

                    save_path=str(ui_path)
                )

            # =============================================
            # DEBUG VISUALIZATION
            # =============================================

            if self.viz_cfg["save_debug_images"]:

                debug_dir = (
                    Path(
                        CONFIG["paths"]["debug_output_dir"]
                    )
                    /
                    booklet_id
                )

                debug_dir.mkdir(
                    parents=True,
                    exist_ok=True
                )

                debug_path = (
                    debug_dir /
                    f"page_{page_number:03d}.png"
                )

                self.visualizer.visualize_extraction(

                    image,

                    omr_result,

                    save_path=str(debug_path)
                )

            return {

                "ui_path": str(ui_path),

                "debug_path": str(debug_path),

            }

        except Exception as e:

            logger.exception(

                f"VISUALIZATION FAILED "
                f"ON PAGE {page_number}: {e}"
            )

            return {

                "ui_path": None,

                "debug_path": None,
            }
