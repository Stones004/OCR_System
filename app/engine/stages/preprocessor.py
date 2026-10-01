"""
Preprocessor

Converts the cropped annotation region into grayscale and a cleaned
binary image by removing small connected components. The processed
binary image improves annotation detection.
"""

import cv2
import numpy as np

from app.core.config.ocr_engine_config import PreprocessConfig


class Preprocessor:

    def __init__(self, config: PreprocessConfig):

        self.min_area = config.min_area

        # On a page with no real ink, grayscale values form one tight
        # cluster of paper/scan noise. Otsu still forces some split
        # even on that unimodal data, and it can degenerately land
        # within a few gray levels of the background mean -- flooding
        # the binary with background noise instead of real content
        # (seen on a visually blank margin where the threshold landed
        # 1.4 levels below the mean and marked 37% of the page as
        # "ink"). Real ink is always separated from the paper
        # background by a wide margin, so require the chosen threshold
        # to sit well below the mean before trusting it.
        self.min_contrast_gap = config.min_contrast_gap

    # --------------------------------------------------

    def process(self, image):

        if len(image.shape) == 3:
            gray = cv2.cvtColor(
                image,
                cv2.COLOR_BGR2GRAY
            )
        else:
            gray = image.copy()

        otsu_t, binary = cv2.threshold(
            gray,
            0,
            255,
            cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
        )

        if gray.mean() - otsu_t < self.min_contrast_gap:
            binary = np.zeros_like(gray)

        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
            binary,
            connectivity=8
        )

        clean = np.zeros_like(binary)

        for i in range(1, num_labels):

            area = stats[i, cv2.CC_STAT_AREA]

            if area >= self.min_area:
                clean[labels == i] = 255

        return gray, clean