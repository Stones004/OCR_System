"""Ported unchanged from D:\\OMR_System\\app\\services\\validation_service.py."""

from datetime import datetime

from app.validator.validator import (
    validate_scan
)

from app.core.logging.logger import (
    logger
)
import cv2


# =========================================================
# VALIDATION SERVICE
# =========================================================

class ValidationService:

    def __init__(self):

        pass

    # =====================================================
    # VALIDATE PAGE
    # =====================================================

    def validate_page(

        self,

        image,

        page_number
    ):

        logger.info(

            f"VALIDATING PAGE "
            f"{page_number}"
        )

        # =====================================================
        # CONVERT TO GRAYSCALE
        # =====================================================

        if len(image.shape) == 3:

            gray = cv2.cvtColor(

                image,

                cv2.COLOR_BGR2GRAY
            )

        else:

            gray = image.copy()

        # =====================================================
        # VALIDATION TIMING
        # =====================================================

        import time

        validation_start = time.time()

        # =====================================================
        # VALIDATE
        # =====================================================

        result = validate_scan(

            gray,

            page_number,

            timestamp=(
                datetime.now()
                .isoformat()
            ),

            processing_time=0.0
        )

        validation_time = (
            time.time()
            - validation_start
        )

        logger.info(

            f"[VALIDATION] "
            f"page={page_number} | "
            f"time={validation_time:.3f}s"
        )

        return result
