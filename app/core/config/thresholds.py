"""
Named constants over CONFIG["thresholds"] / CONFIG["layout"]. Ported
unchanged from D:\\OMR_System -- provisioned for app/validator, not yet
enforced (see that package's docstring).
"""

from app.core.config.config_loader import (
    CONFIG
)


# =========================
# GEOMETRY
# =========================

MIN_PAGE_COVERAGE = (
    CONFIG["thresholds"]["geometry"][
        "min_page_coverage"
    ]
)

MIN_PERSPECTIVE_SCORE = (
    CONFIG["thresholds"]["geometry"][
        "min_perspective_score"
    ]
)

BORDER_MARGIN = (
    CONFIG["thresholds"]["geometry"][
        "border_margin"
    ]
)


# =========================
# BLUR
# =========================

BLUR_HARD_THRESHOLD = (
    CONFIG["thresholds"]["blur"][
        "hard_threshold"
    ]
)

BLUR_SOFT_THRESHOLD = (
    CONFIG["thresholds"]["blur"][
        "soft_threshold"
    ]
)


# =========================
# SKEW
# =========================

MAX_SAFE_SKEW = (
    CONFIG["thresholds"]["skew"][
        "max_safe_angle"
    ]
)

MIN_HOUGH_LINES = (
    CONFIG["thresholds"]["skew"][
        "min_hough_lines"
    ]
)


# =========================
# BRIGHTNESS
# =========================

MIN_BRIGHTNESS = (
    CONFIG["thresholds"]["brightness"][
        "min_brightness"
    ]
)

MAX_BRIGHTNESS = (
    CONFIG["thresholds"]["brightness"][
        "max_brightness"
    ]
)


# =========================
# CONTRAST
# =========================

MIN_CONTRAST = (
    CONFIG["thresholds"]["contrast"][
        "min_contrast"
    ]
)


# =========================
# CONTENT DENSITY
# =========================

MIN_CONTENT_DENSITY = (
    CONFIG["thresholds"][
        "content_density"
    ]["min_density"]
)


# =========================
# EDGE DENSITY
# =========================

MIN_EDGE_DENSITY = (
    CONFIG["thresholds"][
        "edge_density"
    ]["min_density"]
)


# =========================
# SCORING
# =========================

MIN_ACCEPTABLE_SCORE = (
    CONFIG["thresholds"]["scoring"][
        "min_acceptable_score"
    ]
)


# =========================
# LAYOUT
# =========================

ASPECT_RATIO_MIN = (
    CONFIG["layout"][
        "aspect_ratio"
    ]["min"]
)

ASPECT_RATIO_MAX = (
    CONFIG["layout"][
        "aspect_ratio"
    ]["max"]
)

QR_REQUIRED = (
    CONFIG["layout"][
        "qr_required"
    ]
)
