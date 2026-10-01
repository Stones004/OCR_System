"""
Local PARSeq OCR

Runs the fine-tuned PARSeq handwriting model fully offline. The model
and its `strhub` dependency live in the dedicated PARSeq venv
(configured as ocr.parseq.venv_python, see its README), so it's spawned as a
subprocess and kept alive for the life of the backend -- the checkpoint
loads once and is reused across every ROI instead of per-call.
"""

import json
import subprocess
import tempfile
from pathlib import Path

import cv2

from app.core.config.ocr_engine_config import ParseqConfig

from .base import OCRBackend

WORKER_SCRIPT = Path(__file__).resolve().parent / "parseq_worker.py"


class ParseqBackend(OCRBackend):

    def __init__(self, config: ParseqConfig):

        self.shutdown_timeout = config.shutdown_timeout

        if not config.venv_python.exists():
            raise FileNotFoundError(
                f"PARSeq venv python not found: {config.venv_python}\n"
                "Set it up per ocr_dataset_builder/README.md and point "
                "ocr.parseq.venv_python in config.yaml at it."
            )

        if not config.checkpoint.exists():
            raise FileNotFoundError(
                f"PARSeq checkpoint not found: {config.checkpoint}"
            )

        # Everything the worker needs from config.yaml travels as one JSON
        # argument, since the worker runs in a different venv.
        worker_settings = json.dumps({
            "device": config.device,
            "norm_mean": config.norm_mean,
            "norm_std": config.norm_std,
        })

        self.process = subprocess.Popen(
            [
                str(config.venv_python),
                str(WORKER_SCRIPT),
                str(config.checkpoint),
                worker_settings,
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        ready = self.process.stdout.readline()

        if ready.strip() != "READY":
            raise RuntimeError(
                f"PARSeq worker failed to start:\n{self.process.stderr.read()}"
            )

    # --------------------------------------------------

    def read(self, image, preprocess=True):

        return self.read_batch([image])[0]

    def read_batch(self, images, preprocess=True):
        """One subprocess round-trip for the whole list -- a page's
        ROIs all go in together instead of one call per ROI. Every image
        resizes to the model's fixed img_size inside the worker, so this
        is also a real stacked forward pass, not just N calls folded into
        one round-trip."""

        if not images:
            return []

        image_paths = []
        temp_paths = []

        try:
            for image in images:

                if isinstance(image, (str, Path)):
                    image_paths.append(str(image))
                    continue

                success, buffer = cv2.imencode(".png", image)

                if not success:
                    raise RuntimeError("Failed to encode image.")

                tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                tmp.write(buffer.tobytes())
                tmp.close()

                image_paths.append(tmp.name)
                temp_paths.append(tmp.name)

            if self.process.poll() is not None:
                raise RuntimeError(
                    f"PARSeq worker exited unexpectedly:\n{self.process.stderr.read()}"
                )

            self.process.stdin.write(json.dumps(image_paths) + "\n")
            self.process.stdin.flush()

            line = self.process.stdout.readline()

            if not line:
                raise RuntimeError(
                    f"PARSeq worker closed unexpectedly:\n{self.process.stderr.read()}"
                )

            results = json.loads(line)

            output = []

            for result in results:

                if "error" in result:
                    raise RuntimeError(result["error"])

                output.append({
                    "text": result["prediction"],
                    "confidence": result["confidence"],
                    "words": [],
                })

            return output

        finally:
            for temp_path in temp_paths:
                Path(temp_path).unlink(missing_ok=True)

    # --------------------------------------------------

    def close(self):

        process = getattr(self, "process", None)

        if process and process.poll() is None:
            self.process.stdin.close()
            self.process.wait(timeout=self.shutdown_timeout)

    def __del__(self):
        self.close()
