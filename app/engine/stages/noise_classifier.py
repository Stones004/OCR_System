"""
Noise Classifier (pre-OCR triage)

Tags every detected annotation ROI as "noise" (blank/illegible/never worth
transcribing) or "clean" (real handwriting worth sending to PARSeq), using
the ResNet-18 crop classifier trained in the trocr-handwriting-v2 project.
ROIs that land in the "noise" bucket are dropped from the list passed on
to ROITextExtractor, so PARSeq never sees them -- gated by
ocr_engine.pipeline.use_noise_classifier in config.yaml.

Runs as a subprocess under the PARSeq venv (ocr.noise_classifier.venv_python,
normally the same interpreter as ocr.parseq.venv_python), exactly like
app.engine.stages.ocr.parseq.ParseqBackend: this project's own venv has no
torch/torchvision, so the classifier can't run in-process here the way it
does in D:\\OCR_codes.
"""

import json
import subprocess
import tempfile
from pathlib import Path

import cv2

from app.core.config.ocr_engine_config import NoiseClassifierConfig
from app.core.logging.logger import logger

WORKER_SCRIPT = Path(__file__).resolve().parent / "ocr" / "noise_classifier_worker.py"


class NoiseClassifier:

    def __init__(self, config: NoiseClassifierConfig):

        if not config.venv_python.exists():
            raise FileNotFoundError(
                f"Noise classifier venv python not found: {config.venv_python}\n"
                "It reuses the PARSeq venv for torch/torchvision -- see "
                "ocr_engine.noise_classifier.venv_python in config.yaml."
            )

        if not config.checkpoint.exists():
            raise FileNotFoundError(
                f"Noise classifier checkpoint not found: {config.checkpoint}\n"
                "Copy it from the trocr-handwriting-v2 project's "
                "models/noise_classifier/best.pt, or retrain it there."
            )

        self.confidence_threshold = config.confidence_threshold
        self.drop_uncertain = config.drop_uncertain
        self.shutdown_timeout = config.shutdown_timeout

        worker_settings = json.dumps({"device": config.device})

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
                f"Noise classifier worker failed to start:\n{self.process.stderr.read()}"
            )

    # --------------------------------------------------

    def _classify_batch(self, roi_images) -> list:
        """roi_images: grayscale ndarrays, as produced by AnnotationDetector.
        Returns noise_score = P(noise) in [0, 1] per image, same order, in
        ONE subprocess round-trip for the whole page instead of one call
        per ROI."""

        if not roi_images:
            return []

        temp_paths = []

        try:
            for roi_image in roi_images:

                success, buffer = cv2.imencode(".png", roi_image)

                if not success:
                    raise RuntimeError("Failed to encode ROI for noise classification.")

                tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                tmp.write(buffer.tobytes())
                tmp.close()

                temp_paths.append(tmp.name)

            if self.process.poll() is not None:
                raise RuntimeError(
                    f"Noise classifier worker exited unexpectedly:\n{self.process.stderr.read()}"
                )

            self.process.stdin.write(json.dumps(temp_paths) + "\n")
            self.process.stdin.flush()

            line = self.process.stdout.readline()

            if not line:
                raise RuntimeError(
                    f"Noise classifier worker closed unexpectedly:\n{self.process.stderr.read()}"
                )

            results = json.loads(line)

            scores = []

            for result in results:

                if "error" in result:
                    raise RuntimeError(result["error"])

                scores.append(float(result["noise_score"]))

            return scores

        finally:
            for temp_path in temp_paths:
                Path(temp_path).unlink(missing_ok=True)

    def _bucket(self, noise_score: float) -> str:
        """noise_score -> "noise" (>= confidence_threshold), "clean"
        (<= 1 - confidence_threshold), or "uncertain" (the symmetric band
        around 0.5 in between)."""

        if noise_score >= self.confidence_threshold:
            return "noise"
        if noise_score <= 1 - self.confidence_threshold:
            return "clean"
        return "uncertain"

    # --------------------------------------------------

    def filter_rois(self, rois, page_number=None):
        """Tags every ROI dict in place with noise_score/noise_bucket, then
        drops the ones bucketed as "noise" (and, if drop_uncertain is set,
        "uncertain" too) before they ever reach PARSeq. Returns the
        surviving ROIs, in their original order."""

        kept = []
        counts = {"clean": 0, "noise": 0, "uncertain": 0}

        scores = self._classify_batch([roi["roi"] for roi in rois])

        for roi, noise_score in zip(rois, scores):

            bucket = self._bucket(noise_score)

            roi["noise_score"] = noise_score
            roi["noise_bucket"] = bucket
            counts[bucket] += 1

            if bucket == "noise":
                continue
            if bucket == "uncertain" and self.drop_uncertain:
                continue

            kept.append(roi)

        logger.info(
            f"[NOISE_CLASSIFIER] "
            f"page={page_number} "
            f"rois={len(rois)} "
            f"kept={len(kept)} "
            f"clean={counts['clean']} "
            f"noise={counts['noise']} "
            f"uncertain={counts['uncertain']}"
        )

        return kept

    # --------------------------------------------------

    def close(self):

        process = getattr(self, "process", None)

        if process and process.poll() is None:
            self.process.stdin.close()
            self.process.wait(timeout=self.shutdown_timeout)

    def __del__(self):
        self.close()
