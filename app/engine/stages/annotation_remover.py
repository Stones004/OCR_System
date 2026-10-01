import cv2
import numpy as np

from app.core.config.ocr_engine_config import InkRemovalConfig


class AnnotationRemover:

    def __init__(self, config: InkRemovalConfig):

        # Red / green HSV ranges. Anti-aliased "fringe" pixels around the
        # coloured ink are too faint (low saturation) to match the strict
        # ranges directly, but loosening them globally risks matching real
        # black/gray ink, since near-gray pixels have unstable hue. So the
        # fringe pass only trusts "any non-white pixel" within a generous
        # dilation of confirmed mask components. See config.yaml
        # (ink_removal) for the values and their rationale.

        self.red_lower1 = np.array(config.red_lower1, dtype=np.uint8)
        self.red_upper1 = np.array(config.red_upper1, dtype=np.uint8)

        self.red_lower2 = np.array(config.red_lower2, dtype=np.uint8)
        self.red_upper2 = np.array(config.red_upper2, dtype=np.uint8)

        self.green_lower = np.array(config.green_lower, dtype=np.uint8)
        self.green_upper = np.array(config.green_upper, dtype=np.uint8)

        self.kernel = np.ones(
            (config.kernel_size, config.kernel_size),
            np.uint8
        )

        self.close_iterations = config.close_iterations
        self.dilate_iterations = config.dilate_iterations

        self.remove_fringe = config.remove_fringe
        self.fringe_zone_kernel = np.ones(
            (config.fringe_zone_kernel_size, config.fringe_zone_kernel_size),
            np.uint8
        )
        self.fringe_zone_iterations = config.fringe_zone_iterations
        self.fringe_lightness_max = config.fringe_lightness_max
        self.fringe_min_component_area = config.fringe_min_component_area

        self.fill_color = tuple(config.fill_color)

    def create_mask(self, image):

        hsv = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2HSV
        )

        red1 = cv2.inRange(
            hsv,
            self.red_lower1,
            self.red_upper1
        )

        red2 = cv2.inRange(
            hsv,
            self.red_lower2,
            self.red_upper2
        )

        red = cv2.bitwise_or(
            red1,
            red2
        )

        green = cv2.inRange(
            hsv,
            self.green_lower,
            self.green_upper
        )

        mask = cv2.bitwise_or(
            red,
            green
        )

        mask = cv2.morphologyEx(
            mask,
            cv2.MORPH_CLOSE,
            self.kernel,
            iterations=self.close_iterations
        )

        mask = cv2.dilate(
            mask,
            self.kernel,
            iterations=self.dilate_iterations
        )

        if self.remove_fringe:

            num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
                mask,
                connectivity=8
            )

            confident_mask = np.zeros_like(mask)

            for i in range(1, num_labels):
                if stats[i, cv2.CC_STAT_AREA] >= self.fringe_min_component_area:
                    confident_mask[labels == i] = 255

            fringe_zone = cv2.dilate(
                confident_mask,
                self.fringe_zone_kernel,
                iterations=self.fringe_zone_iterations
            )

            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            _, non_white = cv2.threshold(
                gray,
                self.fringe_lightness_max,
                255,
                cv2.THRESH_BINARY_INV
            )

            fringe = cv2.bitwise_and(non_white, fringe_zone)

            mask = cv2.bitwise_or(mask, fringe)

        return mask

    def process(self, image):

        mask = self.create_mask(image)

        cleaned = image.copy()

        cleaned[mask > 0] = self.fill_color

        return cleaned

    def process_debug(self, image):

        mask = self.create_mask(image)

        cleaned = image.copy()
        cleaned[mask > 0] = self.fill_color

        return cleaned, mask