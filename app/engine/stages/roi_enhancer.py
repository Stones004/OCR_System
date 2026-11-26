"""
ROI Enhancer

Sharpens each detected ROI crop for OCR by Otsu-binarizing it (black ink on
a white background). Done per ROI, so the threshold adapts to the crop's own
contrast instead of the whole page's.

Ported unchanged from D:\\OCR_codes\\src\\roi_enhancer.py. Runs after the noise
classifier on purpose: that model was trained on gray crops.
"""

import cv2

from app.core.config.ocr_engine_config import RoiEnhanceConfig


class RoiEnhancer:

    def __init__(self, config: RoiEnhanceConfig):

        self.enabled = config.enabled
        self.blur_ksize = config.blur_ksize
        self.min_contrast_gap = config.min_contrast_gap

    # --------------------------------------------------

    def enhance(self, roi_image):
        """roi_image: grayscale ndarray. Returns a binary (0/255) ndarray of the same
        size, or the input unchanged if the crop has no real ink/paper split."""

        if not self.enabled or roi_image.size == 0:
            return roi_image

        smoothed = roi_image

        if self.blur_ksize:
            smoothed = cv2.GaussianBlur(
                roi_image,
                (self.blur_ksize, self.blur_ksize),
                0
            )

        otsu_t, binary = cv2.threshold(
            smoothed,
            0,
            255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )

        if smoothed.mean() - otsu_t < self.min_contrast_gap:
            return roi_image

        return binary

    def enhance_rois(self, rois):
        """Replaces each ROI dict's "roi" with its enhanced crop, in place. Returns rois."""

        for roi in rois:
            roi["roi"] = self.enhance(roi["roi"])

        return rois
