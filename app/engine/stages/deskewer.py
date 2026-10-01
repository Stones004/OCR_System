import cv2
import numpy as np

from app.core.config.ocr_engine_config import DeskewConfig


"""
Deskewer

Automatically estimates the skew angle of scanned pages using
projection profile analysis and rotates the image to improve
alignment for downstream processing.
"""

class Deskewer:

    def __init__(self, config: DeskewConfig):

        self.angle_min = config.angle_min
        self.angle_max = config.angle_max
        self.coarse_step = config.coarse_step
        self.fine_step = config.fine_step
        self.fine_window = config.fine_window
        self.border_value = config.border_value
        self.edge_fallback_angle = config.edge_fallback_angle
        self.search_width = config.search_width

    # --------------------------------------------------
    # Horizontal Projection Score
    # --------------------------------------------------

    @staticmethod
    def projection_score(binary):

        projection = np.sum(binary == 255, axis=1)

        return np.var(projection)

    # --------------------------------------------------
    # Rotate image
    # --------------------------------------------------

    def rotate(self, image, angle):

        h, w = image.shape[:2]

        center = (w // 2, h // 2)

        M = cv2.getRotationMatrix2D(
            center,
            angle,
            1.0
        )

        rotated = cv2.warpAffine(
            image,
            M,
            (w, h),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=self.border_value
        )

        return rotated

    # --------------------------------------------------
    # Find Best Angle
    # --------------------------------------------------

    def find_best_angle(self, binary):

        best_angle = 0
        best_score = -1

        # ------------------------
        # Coarse Search
        # ------------------------

        for angle in np.arange(
            self.angle_min,
            self.angle_max + self.coarse_step,
            self.coarse_step
        ):

            rotated = self.rotate(binary, angle)

            score = self.projection_score(rotated)

            if score > best_score:

                best_score = score
                best_angle = angle

        # If the coarse search's best angle sits at the very edge of the
        # search range, the projection-variance metric is diverging
        # toward the boundary rather than converging on a real skew (seen
        # on near-blank pages and pages with a dominant watermark
        # competing with the true ruled lines). Trust the fallback angle
        # instead of chasing that runaway result with a fine search.
        if best_angle in (self.angle_min, self.angle_max):
            return self.edge_fallback_angle

        # ------------------------
        # Fine Search
        # ------------------------

        fine_start = best_angle - self.fine_window
        fine_end = best_angle + self.fine_window

        best_score = -1

        for angle in np.arange(
            fine_start,
            fine_end + self.fine_step,
            self.fine_step
        ):

            rotated = self.rotate(binary, angle)

            score = self.projection_score(rotated)

            if score > best_score:

                best_score = score
                best_angle = angle

        return best_angle

    # --------------------------------------------------
    # Deskew
    # --------------------------------------------------

    def process(self, image):

        gray = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2GRAY
        )

        _, binary = cv2.threshold(
            gray,
            0,
            255,
            cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
        )

        # Skew angle is scale-invariant, so the ~40-candidate search runs
        # on a downscaled copy -- only the final rotate() below needs full
        # resolution. INTER_NEAREST keeps the resized image strictly
        # binary (0/255), matching what projection_score expects.
        search_binary = binary

        if binary.shape[1] > self.search_width:

            scale = self.search_width / binary.shape[1]

            search_binary = cv2.resize(
                binary,
                None,
                fx=scale,
                fy=scale,
                interpolation=cv2.INTER_NEAREST
            )

        angle = self.find_best_angle(search_binary)

        corrected = self.rotate(image, angle)

        return corrected, angle
