"""
Adapted from D:\\OMR_System\\app\\workers\\gpu_tasks.py. This is the
single-consumer worker process that hosts the OCR engine (and,
transitively, the one PARSeq subprocess -- see InferenceService /
AnswerScriptEngine) -- see app/services/gpu_service.py's docstring for
why the "gpu_*" naming was kept even though nothing here needs a GPU.

One deliberate change from the original: app.workers.celery_app imports
this module (and celery_tasks.py) unconditionally at the bottom, so
EVERY worker process that boots off that app -- including cpu-worker,
which only ever consumes the "celery" queue and never runs infer_page --
used to eagerly build InferenceService() (and so spawn its own PARSeq
subprocess) purely by importing this file. The original got away with
that because its equivalent (an in-process YOLOX model load) is just
wasteful; here it doubled PARSeq's torch/subprocess memory footprint
across both worker processes and produced a real MemoryError on a
modest dev machine. InferenceService is built lazily here, on the first
infer_page task, so only a worker that actually consumes the
gpu_inference queue ever constructs it.
"""

import json
from time import perf_counter

import cv2
import numpy as np
from opentelemetry import propagate, trace

from app.core.logging.logger import logger
from app.core.models.inference_request import PageInferenceRequest
from app.core.utils.image_transport import ImageTransport
from app.observability.tracer import tracer
from app.services.inference_service import InferenceService
from app.workers.celery_app import celery_app

_inference_service = None


def _get_inference_service() -> InferenceService:

    global _inference_service

    if _inference_service is None:
        _inference_service = InferenceService()

    return _inference_service


@celery_app.task(name="infer_page", queue="gpu_inference")
def infer_page_task(request, trace_carrier=None):
    # Re-attach to the parent trace so this span appears
    # as a child of process_pdf in OpenObserve.
    ctx = propagate.extract(trace_carrier or {})

    request = PageInferenceRequest(**request)
    task_start = perf_counter()
    logger.info(
        f"[GPU_QUEUE] page={request.page_number} task_received"
    )

    image = ImageTransport.load(request.image_path)

    inference_start = perf_counter()
    with tracer.start_as_current_span(
        "gpu_inference",
        context=ctx,
    ) as gpu_infer_span:
        gpu_infer_span.set_attribute("page.number", request.page_number)
        result = _get_inference_service().run_inference(
            image=image,
            page_number=request.page_number,
        )

    inference_time = perf_counter() - inference_start
    logger.info(
        f"[GPU_INFERENCE] page={request.page_number} time={inference_time:.3f}s"
    )

    gpu_task_time = perf_counter() - task_start
    logger.info(
        f"[GPU_TASK_TOTAL] page={request.page_number} time={gpu_task_time:.3f}s"
    )

    return {
        "prediction_result": json.loads(result["prediction_result"].model_dump_json()),
        "omr_result": json.loads(result["omr_result"].model_dump_json()),
    }
