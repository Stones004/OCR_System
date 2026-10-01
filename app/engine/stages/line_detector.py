import cv2
import numpy as np

from app.core.config.ocr_engine_config import SeparatorConfig, VisualizationConfig


"""
Separator Detector

Identifies the vertical separator line from the extracted vertical
structures using connected component analysis and geometric filtering.
The detected separator is later used to isolate the annotation margin.
"""

class LineDetector:

    def __init__(
        self,
        config: SeparatorConfig,
        visualization: VisualizationConfig,
        verbose: bool,
    ):
        """
        config.left_ratio : float
            Ignore detections too close to the left page border.

        config.right_ratio : float
            Ignore detections beyond this percentage of the page width.

        config.min_height_ratio : float
            Minimum component height as a fraction of the page height.

        config.min_aspect_ratio : float
            Minimum height / width of a component.

        config.expected_x : int | None
            Expected x-coordinate of the separator.

        config.tolerance : int | None
            Allowed deviation from expected_x.
        """

        self.left_ratio = config.left_ratio
        self.right_ratio = config.right_ratio
        self.min_height_ratio = config.min_height_ratio
        self.min_aspect_ratio = config.min_aspect_ratio

        self.expected_x = config.expected_x
        self.tolerance = config.tolerance

        self.candidate_color = tuple(visualization.separator_candidate_color)
        self.candidate_thickness = visualization.separator_candidate_thickness
        self.selected_color = tuple(visualization.separator_selected_color)
        self.selected_thickness = visualization.separator_selected_thickness

        self.verbose = verbose

    def detect(self, vertical):

        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
            vertical,
            connectivity=8
        )

        h, w = vertical.shape

        LEFT_LIMIT = int(w * self.left_ratio)
        RIGHT_LIMIT = int(w * self.right_ratio)

        output = cv2.cvtColor(vertical, cv2.COLOR_GRAY2BGR)

        candidates = []

        for i in range(1, num_labels):

            x = stats[i, cv2.CC_STAT_LEFT]
            y = stats[i, cv2.CC_STAT_TOP]
            width = stats[i, cv2.CC_STAT_WIDTH]
            height = stats[i, cv2.CC_STAT_HEIGHT]
            area = stats[i, cv2.CC_STAT_AREA]

            # -----------------------------
            # Basic geometric filtering
            # -----------------------------

            reason = None

            if height < h * self.min_height_ratio:
                reason = f"Too short ({height}px)"

            elif ( height / width) < self.min_aspect_ratio:
                reason = f"Poor aspect ratio ({(height / width):.1f})"

            elif x < LEFT_LIMIT:
                reason = f"Too close to left border (x={x})"

            elif x > RIGHT_LIMIT:
                reason = f"Outside left half (x={x})"

            if reason is not None:
                if self.verbose:
                    print(
                        f"Rejected Component {i} | "
                        f"x={x}, y={y}, w={width}, h={height} | "
                        f"Reason: {reason}"
                    )

                continue

            component_mask = np.zeros_like(vertical)
            component_mask[labels == i] = 255

            points = np.column_stack(np.where(component_mask > 0))

            candidate = {

                "x": x,
                "y": y,
                "w": width,
                "h": height,
                "area": area,

                "mask": component_mask,
                "points": points
            }

            candidates.append(candidate)

            # Draw every valid candidate
            cv2.rectangle(
                output,
                (x, y),
                (x + width, y + height),
                self.candidate_color,
                self.candidate_thickness
            )

            if self.verbose:
                print("\nValid Candidates")

                for c in candidates:
                    print(
                        f"x={c['x']}, "
                        f"h={c['h']}, "
                        f"w={c['w']}, "
                        f"area={c['area']}"
                    )

        # ------------------------------------------------
        # No candidates
        # ------------------------------------------------

        if len(candidates) == 0:
            return output, None

        # ------------------------------------------------
        # If we know approximately where the separator is,
        # choose the closest candidate.
        # ------------------------------------------------

        if self.expected_x is not None:

            if self.tolerance is not None:

                filtered = []

                for c in candidates:

                    if abs(c["x"] - self.expected_x) <= self.tolerance:
                        filtered.append(c)

                if len(filtered) > 0:
                    candidates = filtered

            best = min(
                candidates,
                key=lambda c: abs(c["x"] - self.expected_x)
            )

        else:

            # No expected position configured:
            # choose the left-most candidate.

            best = min(
                candidates,
                key=lambda c: c["x"]
            )

        # Draw best candidate
        cv2.rectangle(
            output,
            (best["x"], best["y"]),
            (best["x"] + best["w"], best["y"] + best["h"]),
            self.selected_color,
            self.selected_thickness
        )

        if self.verbose:
            print("\nSelected Candidate")
            print(best)

        return output, best
