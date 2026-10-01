"""
Ported unchanged from D:\\OMR_System\\app\\services\\gpu_service.py.

The name is inherited, not literal: this dispatches the "infer_page"
Celery task onto its own queue, consumed by exactly one worker process
(see docker-compose.yml / start scripts, --pool=solo, one process) --
that single-consumer queue is what gives this engine its one PARSeq
subprocess (its stdin/stdout pipe isn't shareable across processes), the
same way it used to guarantee exclusive GPU access for YOLOX. Renaming it
everywhere (config keys, metric names, docker service names, the health
check's gpu_worker_name lookup) was judged not worth the blast radius for
a purely cosmetic change.
"""

from app.core.models.inference_request import PageInferenceRequest
from app.workers.celery_app import celery_app
from opentelemetry import propagate


class GPUService:
    def submit(self, request: PageInferenceRequest):
        # Inject the current trace context so the OCR worker
        # can continue the trace as a child span.
        carrier = {}
        propagate.inject(carrier)

        return celery_app.send_task(
            "infer_page",
            kwargs={
                "request": request.model_dump(),
                "trace_carrier": carrier,
            },
            queue="gpu_inference",
        )

    def collect(self, task):
        return task.get(
            disable_sync_subtasks=False  # also fixes the deadlock risk
        )


gpu_service = GPUService()
