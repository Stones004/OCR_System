"""
Annotation Detector

Detects handwritten annotation regions by removing printed table
lines, extracting connected components, merging nearby fragments and
filtering candidates based on size and ink density. Returns cropped
ROIs for OCR.

Every threshold comes from config.yaml (annotation_detector); see the
comments there for what each one does.
"""
import cv2
import numpy as np

from app.core.config.ocr_engine_config import AnnotationDetectorConfig, VisualizationConfig


class AnnotationDetector:

    def __init__(
        self,
        config: AnnotationDetectorConfig,
        visualization: VisualizationConfig,
        verbose: bool,
    ):

        self.min_width = config.min_width
        self.min_height = config.min_height
        self.padding = config.padding
        self.merge_dist = config.merge_dist

        self.min_confident_area = config.min_confident_area
        self.min_confident_dim = config.min_confident_dim
        self.min_ink_pixels = config.min_ink_pixels
        self.min_fill_ratio = config.min_fill_ratio
        self.row_y_tolerance = config.row_y_tolerance

        # Fixed printed horizontal line (e.g. a table header rule) near
        # the top of the crop. Anything entirely above it is header/table
        # bleed-through, not a handwritten annotation, so it is rejected.
        self.reject_above_top_line = config.reject_above_top_line
        self.top_line_search_frac = config.top_line_search_frac
        self.top_line_min_len_ratio = config.top_line_min_len_ratio
        self.top_line_margin = config.top_line_margin

        # Sparse, elongated strokes (hand-drawn arrows/pointers/connector
        # lines) have a low ink-density-per-bbox-area even though their
        # bbox isn't necessarily extreme aspect ratio. Left in the merge
        # step, their huge sparse bbox drags any real digit merged with
        # them below min_fill_ratio, rejecting both together. Dropping
        # them before merging keeps real digits isolated and intact.
        self.exclude_sparse_strokes = config.exclude_sparse_strokes
        self.sparse_stroke_density_max = config.sparse_stroke_density_max
        self.sparse_stroke_min_dim = config.sparse_stroke_min_dim

        # Long, narrow vertical strips (page-edge shadows, ruled-line
        # remnants) are noise regardless of how dense they are -- a solid
        # thin line passes the sparse-stroke density check just fine, so
        # it needs its own plain width/height rule.
        self.exclude_long_vertical_strips = config.exclude_long_vertical_strips
        self.long_strip_max_width = config.long_strip_max_width
        self.long_strip_min_height = config.long_strip_min_height

        # Splitting of unusually tall merged ROIs.
        self.refine_height = config.refine_height
        self.valley_threshold = config.valley_threshold
        self.min_valley_width = config.min_valley_width
        self.min_segment_height = config.min_segment_height
        self.refine_blur_ksize = config.refine_blur_ksize

        # Printed-line removal.
        self.line_kernel_min = config.line_kernel_min
        self.line_kernel_divisor = config.line_kernel_divisor
        self.line_dilate_kernel = config.line_dilate_kernel

        self.roi_color = tuple(visualization.roi_color)
        self.roi_thickness = visualization.roi_thickness

        self.verbose = verbose

    # --------------------------------------------------

    def _refine_rois(self, merged, binary):
        """
        Split vertically merged ROIs using horizontal projection.

        Runs ONLY on unusually tall ROIs.
        """

        refined = []

        for (x1, y1, x2, y2) in merged:

            roi_h = y2 - y1

            # Small ROIs are assumed correct
            if roi_h < self.refine_height:
                refined.append((x1, y1, x2, y2))
                continue

            roi = binary[y1:y2, x1:x2]

            # Horizontal projection
            projection = np.count_nonzero(roi, axis=1).astype(np.float32)

            # Smooth projection
            projection = cv2.GaussianBlur(
                projection.reshape(-1, 1),
                (1, self.refine_blur_ksize),
                0
            ).flatten()

            threshold = projection.max() * self.valley_threshold

            valleys = []

            start = None

            for i, value in enumerate(projection):

                if value < threshold:

                    if start is None:
                        start = i

                else:

                    if start is not None:

                        if (i - start) >= self.min_valley_width:
                            valleys.append((start + i) // 2)

                        start = None

            # No valid valleys
            if len(valleys) == 0:
                refined.append((x1, y1, x2, y2))
                continue

            prev = 0
            pieces = []

            for split in valleys:

                if split - prev >= self.min_segment_height:
                    pieces.append(
                        (
                            x1,
                            y1 + prev,
                            x2,
                            y1 + split
                        )
                    )

                prev = split

            if roi_h - prev >= self.min_segment_height:
                pieces.append(
                    (
                        x1,
                        y1 + prev,
                        x2,
                        y2
                    )
                )

            # Safety check
            if len(pieces) <= 1:
                refined.append((x1, y1, x2, y2))
            else:
                refined.extend(pieces)

        return refined

    # --------------------------------------------------

    def _line_kernels(self, h, w):
        """
        Horizontal and vertical structuring elements used to pick out
        printed table lines.
        """

        horiz_kernel = cv2.getStructuringElement(
            cv2.MORPH_RECT,
            (max(self.line_kernel_min, w // self.line_kernel_divisor), 1)
        )

        vert_kernel = cv2.getStructuringElement(
            cv2.MORPH_RECT,
            (1, max(self.line_kernel_min, h // self.line_kernel_divisor))
        )

        return horiz_kernel, vert_kernel

    # --------------------------------------------------

    def _find_top_line_y(self, binary):
        """
        Locate the fixed printed horizontal rule near the top of the
        crop (e.g. a table header separator) and return the y-coordinate
        of its bottom edge, or None if no such line is found.

        Must run on the ORIGINAL binary, before remove_lines() strips
        horizontal lines out of it.
        """

        h, w = binary.shape

        horiz_kernel, _ = self._line_kernels(h, w)

        horiz_lines = cv2.morphologyEx(
            binary,
            cv2.MORPH_OPEN,
            horiz_kernel
        )

        search_rows = max(1, int(h * self.top_line_search_frac))
        row_ink = np.count_nonzero(horiz_lines[:search_rows], axis=1)

        min_len = self.top_line_min_len_ratio * w
        candidate_rows = np.where(row_ink >= min_len)[0]

        if len(candidate_rows) == 0:
            return None

        # Bottom-most row of the topmost matching band = its bottom edge
        return int(candidate_rows.max())

    # --------------------------------------------------

    def remove_lines(self, binary):

        h, w = binary.shape

        horiz_kernel, vert_kernel = self._line_kernels(h, w)

        horiz_lines = cv2.morphologyEx(
            binary,
            cv2.MORPH_OPEN,
            horiz_kernel
        )

        vert_lines = cv2.morphologyEx(
            binary,
            cv2.MORPH_OPEN,
            vert_kernel
        )

        lines = cv2.bitwise_or(
            horiz_lines,
            vert_lines
        )

        lines = cv2.dilate(
            lines,
            np.ones((self.line_dilate_kernel, self.line_dilate_kernel), np.uint8),
            iterations=1
        )

        return cv2.bitwise_and(
            binary,
            cv2.bitwise_not(lines)
        )

    # --------------------------------------------------

    def _boxes_close(self, a, b):

        ax1, ay1, ax2, ay2 = a
        bx1, by1, bx2, by2 = b

        ax1 -= self.merge_dist
        ay1 -= self.merge_dist
        ax2 += self.merge_dist
        ay2 += self.merge_dist

        return not (
            bx2 < ax1 or
            bx1 > ax2 or
            by2 < ay1 or
            by1 > ay2
        )

    # --------------------------------------------------

    def _merge_boxes(self, boxes):

        changed = True

        while changed:

            changed = False
            merged = []
            used = [False] * len(boxes)

            for i in range(len(boxes)):

                if used[i]:
                    continue

                current = list(boxes[i])
                used[i] = True

                for j in range(i + 1, len(boxes)):

                    if used[j]:
                        continue

                    if self._boxes_close(
                        tuple(current),
                        boxes[j]
                    ):

                        current[0] = min(current[0], boxes[j][0])
                        current[1] = min(current[1], boxes[j][1])
                        current[2] = max(current[2], boxes[j][2])
                        current[3] = max(current[3], boxes[j][3])

                        used[j] = True
                        changed = True

                merged.append(tuple(current))

            boxes = merged

        return boxes

    # --------------------------------------------------

    def _group_boxes_by_y(self, boxes):
        """
        Group boxes that belong to the same horizontal writing row.

        Each box is represented as:
            (x1, y1, x2, y2)

        Boxes are grouped using their vertical center.
        """

        rows = []

        # Process from top to bottom
        boxes = sorted(
            boxes,
            key=lambda b: (b[1] + b[3]) / 2
        )

        for box in boxes:

            x1, y1, x2, y2 = box

            cy = (y1 + y2) / 2

            assigned = False

            for row in rows:

                # Current average Y position of this row
                row_cy = row["center_y"]

                if abs(cy - row_cy) <= self.row_y_tolerance:

                    row["boxes"].append(box)

                    # Recalculate row center
                    centers = [
                        (b[1] + b[3]) / 2
                        for b in row["boxes"]
                    ]

                    row["center_y"] = float(
                        np.mean(centers)
                    )

                    assigned = True
                    break

            if not assigned:

                rows.append({
                    "center_y": cy,
                    "boxes": [box]
                })

        # ---------------------------------------------
        # Convert each row into one bounding box
        # ---------------------------------------------

        row_boxes = []

        for row in rows:

            boxes_in_row = row["boxes"]

            x1 = min(
                b[0]
                for b in boxes_in_row
            )

            y1 = min(
                b[1]
                for b in boxes_in_row
            )

            x2 = max(
                b[2]
                for b in boxes_in_row
            )

            y2 = max(
                b[3]
                for b in boxes_in_row
            )

            row_boxes.append(
                (x1, y1, x2, y2)
            )

        return row_boxes


    def detect(
        self,
        gray,
        binary
    ):

        # Locate the fixed top header line before it gets stripped out
        top_line_y = None
        if self.reject_above_top_line:
            top_line_y = self._find_top_line_y(binary)

        # Remove printed table lines only
        binary = self.remove_lines(binary)

        # Connected components
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
            binary,
            connectivity=8
        )

        boxes = []

        for i in range(1, num_labels):

            x = stats[i, cv2.CC_STAT_LEFT]
            y = stats[i, cv2.CC_STAT_TOP]
            w = stats[i, cv2.CC_STAT_WIDTH]
            h = stats[i, cv2.CC_STAT_HEIGHT]
            area = stats[i, cv2.CC_STAT_AREA]

            if w < self.min_width:
                continue

            if h < self.min_height:
                continue

            if top_line_y is not None and (y + h) <= top_line_y + self.top_line_margin:
                continue

            if self.exclude_sparse_strokes and max(w, h) > self.sparse_stroke_min_dim:
                density = area / float(w * h)
                if density < self.sparse_stroke_density_max:
                    continue

            if self.exclude_long_vertical_strips and w < self.long_strip_max_width and h > self.long_strip_min_height:
                continue

            boxes.append(
                (
                    x,
                    y,
                    x + w,
                    y + h
                )
            )

        # Merge nearby fragments
        merged = self._merge_boxes(boxes)

        merged = self._refine_rois(
            merged,
            binary
        )

        confident = []

        for x1, y1, x2, y2 in merged:
            w = x2 - x1
            h = y2 - y1

            bbox_area = w * h

            ink_pixels = cv2.countNonZero(
                binary[y1:y2, x1:x2]
            )

            fill_ratio = ink_pixels / float(bbox_area)

            if self.verbose:
                print(
                    f"\nCandidate:"
                    f" bbox={w}x{h}"
                    f" | bbox_area={bbox_area}"
                    f" | ink_pixels={ink_pixels}"
                    f" | fill_ratio={fill_ratio:.3f}"
                )

            reject = None

            if bbox_area < self.min_confident_area:
                reject = f"bbox_area {bbox_area} < {self.min_confident_area}"

            elif w < self.min_confident_dim:
                reject = f"width {w} < {self.min_confident_dim}"

            elif h < self.min_confident_dim:
                reject = f"height {h} < {self.min_confident_dim}"

            elif ink_pixels < self.min_ink_pixels:
                reject = f"ink_pixels {ink_pixels} < {self.min_ink_pixels}"

            elif fill_ratio < self.min_fill_ratio:
                reject = f"fill_ratio {fill_ratio:.3f} < {self.min_fill_ratio}"

            if reject is not None:
                if self.verbose:
                    print(f"  REJECT -> {reject}")
                continue

            if self.verbose:
                print("  ACCEPT")

            confident.append(
                (
                    x1,
                    y1,
                    x2,
                    y2
                )
            )

        # ==================================================
        # GROUP CONFIDENT ROIs BY HORIZONTAL ROW
        # ==================================================

        grouped = self._group_boxes_by_y(confident)

        # ==================================================
        # FINAL ROI CREATION
        # ==================================================

        detected = cv2.cvtColor(
            gray,
            cv2.COLOR_GRAY2BGR
        )

        rois = []

        for x1, y1, x2, y2 in grouped:

            x1 = max(0, x1 - self.padding)
            y1 = max(0, y1 - self.padding)
            x2 = min(gray.shape[1], x2 + self.padding)
            y2 = min(gray.shape[0], y2 + self.padding)

            roi = gray[
                y1:y2,
                x1:x2
            ]

            rois.append(
                {
                    "bbox": (
                        x1,
                        y1,
                        x2,
                        y2
                    ),
                    "roi": roi
                }
            )

            cv2.rectangle(
                detected,
                (x1, y1),
                (x2, y2),
                self.roi_color,
                self.roi_thickness
            )

        return rois, {
            "binary": binary,
            "detected": detected
        }
