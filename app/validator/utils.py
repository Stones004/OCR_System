"""
Ported unchanged from D:\\OMR_System\\app\\validator\\utils.py. Generic
image-quality helpers (blur/brightness/contrast/density/skew/aspect
ratio) -- none of this is bubble-specific, so it's kept intact for
whenever the real checks in app/validator/quality_checks.py and
structural_checks.py get filled in (see app/validator/validator.py).
"""

import cv2
import numpy as np


# =========================
# INPUT VALIDATION
# =========================

def validate_grayscale_image(gray):

    if gray is None:

        raise ValueError(
            "Input image is None."
        )

    if len(gray.shape) != 2:

        raise ValueError(
            "Expected grayscale image."
        )

    return gray


# =========================
# BLUR
# =========================

def variance_of_laplacian(
    gray: np.ndarray
) -> float:

    validate_grayscale_image(gray)

    lap = cv2.Laplacian(
        gray,
        cv2.CV_64F
    )

    return float(lap.var())


# =========================
# BRIGHTNESS
# =========================

def compute_brightness(
    gray: np.ndarray
) -> float:

    validate_grayscale_image(gray)

    return float(np.mean(gray))


# =========================
# CONTRAST
# =========================

def compute_contrast(
    gray: np.ndarray
) -> float:

    validate_grayscale_image(gray)

    return float(np.std(gray))


# =========================
# CONTENT DENSITY
# =========================

def compute_content_density(
    gray: np.ndarray
) -> float:

    validate_grayscale_image(gray)

    dark_pixels = np.sum(
        gray < 200
    )

    total_pixels = gray.size

    return float(
        dark_pixels / total_pixels
    )


# =========================
# EDGE DENSITY
# =========================

def compute_edge_density(
    gray: np.ndarray
) -> float:

    validate_grayscale_image(gray)

    edges = cv2.Canny(
        gray,
        100,
        200
    )

    edge_pixels = np.sum(
        edges > 0
    )

    total_pixels = edges.size

    return float(
        edge_pixels / total_pixels
    )


# =========================
# SKEW ESTIMATION
# =========================

def estimate_skew(
    gray: np.ndarray
):

    validate_grayscale_image(gray)

    edges = cv2.Canny(
        gray,
        50,
        150
    )

    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 180,
        threshold=100,
        minLineLength=300,
        maxLineGap=30
    )

    if lines is None:
        return None

    angles = []

    for line in lines:

        # Handle both OpenCV output formats:
        # [[x1,y1,x2,y2]]  and  [x1,y1,x2,y2]

        if len(line) == 1:
            x1, y1, x2, y2 = line[0]
        else:
            x1, y1, x2, y2 = line

        angle = np.degrees(
            np.arctan2(
                y2 - y1,
                x2 - x1
            )
        )

        if -45 < angle < 45:
            angles.append(angle)

    if len(angles) == 0:
        return None

    return float(
        np.median(angles)
    )


# =========================
# ASPECT RATIO
# =========================

def compute_aspect_ratio(
    gray: np.ndarray
) -> float:

    validate_grayscale_image(gray)

    h, w = gray.shape

    return float(h / w)
