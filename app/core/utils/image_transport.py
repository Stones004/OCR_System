"""
Hands a page image from the main pipeline process to the OCR worker
process via a shared file (Celery tasks are JSON, so a raw ndarray can't
ride in the task payload).

Adapted from D:\\OMR_System\\app\\core\\utils\\image_transport.py: the
original hardcoded CACHE_DIR to "/workspace/runtime/page_cache" (a
Docker-only absolute path). Reads paths.page_cache_dir from config
instead, so this also works running natively.

Also diverges from the original here: save() now PNG-encodes the page
instead of writing a raw .npy. A page at this stage is a full-res color
scan (roughly 2200x3900x3 uint8, ~25MB uncompressed) -- with WINDOW_SIZE
pages in flight per document (see processing_pipeline.py) and several
documents running concurrently (cpu-worker's --concurrency=3), that was
real, measured disk I/O on the hot path between the CPU and OCR worker
processes. PNG is lossless (unlike JPEG, won't introduce compression
artifacts around ink/text that the detection and OCR stages read), and
compresses scanned-document pages -- mostly uniform background -- hard;
the ROI crops already cross this exact same process boundary via PNG
(see ocr/parseq.py, ocr/noise_classifier_worker.py's temp files), so this
also makes every image hand-off in the pipeline consistent.
"""

from pathlib import Path
import uuid

import cv2

from app.core.config.config_loader import (
    CONFIG
)


class ImageTransport:

    CACHE_DIR = Path(CONFIG["paths"]["page_cache_dir"])

    @classmethod
    def save(cls, image):
        cls.CACHE_DIR.mkdir(parents=True, exist_ok=True)

        path = cls.CACHE_DIR / f"{uuid.uuid4().hex}.png"

        success, buffer = cv2.imencode(".png", image)

        if not success:
            raise RuntimeError("Failed to encode page image.")

        path.write_bytes(buffer.tobytes())

        return str(path)

    @classmethod
    def load(cls, path):
        image = cv2.imread(str(path), cv2.IMREAD_COLOR)

        if image is None:
            raise RuntimeError(f"Failed to load page image: {path}")

        return image

    @classmethod
    def cleanup(cls, path):
        Path(path).unlink(missing_ok=True)
