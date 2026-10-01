import cv2
import numpy as np

from app.core.config.ocr_engine_config import VerticalConfig


"""
Vertical Line Extractor

Extracts prominent vertical structures from a scanned page using
thresholding and morphological operations. The extracted image is
used to locate the table separator.
"""

class VerticalExtractor:

    def __init__(self, config: VerticalConfig, verbose: bool):
        self.threshold = config.threshold
        self.min_kernel_height = config.min_kernel_height
        self.kernel_height_divisor = config.kernel_height_divisor
        self.repair_kernel_size = tuple(config.repair_kernel)
        self.verbose = verbose

    def extract(self, image):

        debug = {}

        # --------------------------------------------------
        # 1. Convert to grayscale
        # --------------------------------------------------

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        debug["gray"] = gray

        # --------------------------------------------------
        # 2. Binary Inverse
        #
        # Background -> Black
        # Ink/Lines -> White
        # --------------------------------------------------

        _, binary = cv2.threshold(
            gray,
            self.threshold,
            255,
            cv2.THRESH_BINARY_INV
        )

        debug["binary"] = binary

        # --------------------------------------------------
        # 3. Extract Vertical Structures
        # --------------------------------------------------

        height, width = image.shape[:2]

        kernel_height = max(
            self.min_kernel_height,
            height // self.kernel_height_divisor
        )

        # Repair broken lines
        repair_kernel = cv2.getStructuringElement(
            cv2.MORPH_RECT,
            self.repair_kernel_size
        )

        binary = cv2.morphologyEx(
            binary,
            cv2.MORPH_CLOSE,
            repair_kernel
        )

        # Now isolate vertical objects
        vertical_kernel = cv2.getStructuringElement(
            cv2.MORPH_RECT,
            (1, kernel_height)
        )

        vertical = cv2.morphologyEx(
            binary,
            cv2.MORPH_OPEN,
            vertical_kernel
        )

        debug["vertical"] = vertical

        if self.verbose:
            print("Inside VerticalExtractor")
            print(vertical.shape)
            print(vertical.dtype)
            print(np.unique(vertical))

        return vertical, debug
