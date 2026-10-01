"""Ported unchanged from D:\\OMR_System\\app\\core\\logging\\logger.py."""

import logging
from pathlib import Path

from app.core.config.config_loader import (
    CONFIG
)

from logging.handlers import (
    RotatingFileHandler
)
from datetime import datetime
# =========================================================
# CONFIG
# =========================================================

logging_cfg = CONFIG["logging"]

paths_cfg = CONFIG["paths"]

# =========================================================
# LOG DIRECTORY
# =========================================================

LOG_DIR = Path(
    paths_cfg["logs_dir"]
)

LOG_DIR.mkdir(
    parents=True,
    exist_ok=True
)

LOG_FILE = (

    LOG_DIR /

    f"ocr_system_"

    f"{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    f".log"
)

# =========================================================
# LOGGER
# =========================================================

logger = logging.getLogger(
    "ocr_system"
)

logger.setLevel(

    getattr(

        logging,

        logging_cfg["level"]
    )
)

# =========================================================
# PREVENT DUPLICATE HANDLERS
# =========================================================

if logger.handlers:

    logger.handlers.clear()

# =========================================================
# FORMATTER
# =========================================================

formatter = logging.Formatter(

    (
        "%(asctime)s | "
        "%(levelname)s | "
        "%(name)s | "
        "%(message)s"
    )
)

# =========================================================
# FILE HANDLER
# =========================================================

if logging_cfg["save_logs"]:

    file_handler = RotatingFileHandler(

        LOG_FILE,

        maxBytes=10 * 1024 * 1024,

        backupCount=10,

        encoding="utf-8"
    )

    file_handler.setFormatter(
        formatter
    )

    logger.addHandler(
        file_handler
    )

# =========================================================
# CONSOLE HANDLER
# =========================================================

if logging_cfg["console_logging"]:

    console_handler = logging.StreamHandler()

    console_handler.setFormatter(
        formatter
    )

    logger.addHandler(
        console_handler
    )

# =========================================================
# LOGGER PROPAGATION
# =========================================================

logger.propagate = False
