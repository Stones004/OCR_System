"""
Ported from D:\\OMR_System\\app\\services\\inference_service.py with one
change: imports app.engine.ocr_engine.AnswerScriptEngine instead of
app.engine.omr_engine.OMREngine. Call contract (run_inference(image,
page_number) -> dict) is unchanged, so nothing above this needed to move.
"""

from app.engine.ocr_engine import (
    AnswerScriptEngine
)

from app.core.logging.logger import (
    logger
)


# =========================================================
# INFERENCE SERVICE
# =========================================================

class InferenceService:

    def __init__(self):

        self.engine: AnswerScriptEngine = (
            AnswerScriptEngine()
        )

    # =====================================================
    # RUN INFERENCE
    # =====================================================

    def run_inference(

        self,

        image,

        page_number

    ) -> dict:

        logger.debug(

            f"RUNNING INFERENCE "
            f"ON PAGE {page_number}"
        )

        try:

            result = (

                self.engine.process_image(

                    image,

                    page_number=page_number
                )
            )

            return result

        except Exception as e:

            logger.exception(

                f"INFERENCE FAILED "
                f"ON PAGE {page_number}: {e}"
            )

            raise
