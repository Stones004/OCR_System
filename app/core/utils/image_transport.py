"""
Hands a page image from the main pipeline process to the OCR worker
process via a shared file (Celery tasks are JSON, so a raw ndarray can't
ride in the task payload).

Adapted from D:\\OMR_System\\app\\core\\utils\\image_transport.py: the
original hardcoded CACHE_DIR to "/workspace/runtime/page_cache" (a
Docker-only absolute path). Reads paths.page_cache_dir from config
instead, so this also works running natively.
"""

from pathlib import Path
import numpy as np
import uuid

from app.core.config.config_loader import (
    CONFIG
)


class ImageTransport:

    CACHE_DIR = Path(CONFIG["paths"]["page_cache_dir"])

    @classmethod
    def save(cls, image):
        cls.CACHE_DIR.mkdir(parents=True, exist_ok=True)

        path = cls.CACHE_DIR / f"{uuid.uuid4().hex}.npy"

        np.save(path, image)

        return str(path)

    @classmethod
    def load(cls, path):
        return np.load(path, allow_pickle=False)

    @classmethod
    def cleanup(cls, path):
        Path(path).unlink(missing_ok=True)
