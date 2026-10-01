"""
Ported from D:\\OMR_System\\app\\pipeline\\processing_pipeline.py. The
per-page loop (GPU-queue windowing, validation, event emission, job
manifest updates) is unchanged -- it's generic Celery async dispatch, not
YOLOX/GPU-specific, and still gives real value here: it overlaps this
process's page loading/validation with the OCR worker process's PARSeq
inference.

One addition: annotation_assembler.assemble() runs ONCE, after every page
has been collected and sorted into page_number order (see
_assemble_annotations below), because a question's answer can run onto
the next page -- that needs sequential state the per-page engine calls
don't have (they're dispatched as independent, possibly out-of-order
Celery tasks; see finalize_page's ready_tasks/pending handling below).
Each page's raw omr_result.questions (bbox/text/confidence per detected
label) is replaced with the final assembled Annotation list
(question_id/is_continuation/question_bbox/answer_bbox/lookup_tag) before
export, and page_processed is re-emitted so the live UI catches up.

The export_payload page shape is also adjusted from the original's
`{**page.model_dump(), image_path, ...}` (which dumped the whole
PageProcessingResult, OMR-flavoured) to `{"page_number", "annotations"}`,
matching this project's target schema exactly.
"""

from app.monitoring.metrics import GPU_TIME
from app.core.models.inference_request import PageInferenceRequest
from pathlib import Path
from time import perf_counter
from collections import deque

from app.core.utils.image_transport import ImageTransport

# pyrefly: ignore [missing-import]
import fitz

from app.pipeline.job_manager import (
    job_manager
)

from app.services.validation_service import (
    ValidationService
)

from app.services.export_service import (
    export_omr_results
)

from app.core.utils.pdf_loader import (
    PDFLoader
)

from app.core.models.omr_results import ( OMRResult )


from app.core.logging.logger import (
    logger
)

from app.services.visualization_service import (
    VisualizationService
)

from app.core.models.page_data import (
    PageProcessingResult
)

from app.core.config.config_loader import (
    CONFIG
)

from app.core.events.event_bus import (
    event_bus
)

from app.core.events.serializers import (
    serialize_page_result
)
from app.services.cleanup_service import (
    CleanupService
)

from app.monitoring.metrics import (
    PDF_PROCESSED,
    PDF_FAILED,
    ACTIVE_JOBS,
    VALIDATION_TIME,
    VISUALIZATION_TIME,
    PDF_DURATION,
    GPU_QUEUE_WAIT
)


from app.core.models.detection import ( PredictionResult )

from app.observability.tracer import (
    tracer
)

from app.engine.annotation_assembler import (
    PageLabels,
    assemble,
)

from app.engine.question_mapping import (
    QuestionMapper,
)

from app.core.config.ocr_engine_config import (
    ocr_engine_config
)

# =====================================================
# PROCESS PDF TASK
# =====================================================

def process_pdf_task(
    pdf_path
):

    pipeline = ProcessingPipeline()

    result = pipeline.process_job(
        pdf_path
    )

    return result

# =========================================================
# PROCESSING PIPELINE
# =========================================================

class ProcessingPipeline:

    def __init__(self):

        self.job_manager = (
            job_manager
        )

        self.visualization_service = (
            VisualizationService()
        )

        self.validation_service = (
            ValidationService()
        )

        self.cleanup_service = (
            CleanupService()
        )

        self.question_mapper = (
            QuestionMapper(ocr_engine_config.question_mapping)
        )

        from app.services.gpu_service import gpu_service

        self.gpu_service = gpu_service


    def finalize_page(
        self,
        *,
        page,
        request,
        validation_result,
        result,
        job_results,
        job_id,
        booklet_id,
    ):

        page_number = request.page_number

        prediction_result = (
            PredictionResult( **result["prediction_result"] )
        )

        omr_result = ( OMRResult( **result["omr_result"] ) )


        event_bus.emit(
            "inference_completed",
            {

                "event_type": (
                    "inference_completed"
                ),

                "job_id": job_id,

                "booklet_id": booklet_id,

                "page_number": (
                    page_number
                ),

                "payload": (
                    result["prediction_result"]
                )
            }
        )

        page_result = PageProcessingResult(

            page_number=page_number,

            prediction_result=( prediction_result ),

            omr_result=(
                omr_result
            ),

            validation_result=(
                validation_result
            )
        )

        # =====================================================
        # EMIT PAGE EVENT (raw, pre-assembly -- see module docstring)
        # =====================================================

        self._emit_page_processed(
            job_id=job_id,
            booklet_id=booklet_id,
            page=page_result,
            image=page,
        )

        job_results.append(page_result)

        # =========================================
        # UPDATE PROGRESS
        # =========================================

        self.job_manager.update_page_progress(

            job_id,

            page_number
        )

        ImageTransport.cleanup(
            request.image_path
        )

    # =====================================================
    # EMIT PAGE EVENT + VISUALIZATION
    # =====================================================

    def _emit_page_processed(self, *, job_id, booklet_id, page, image):

        page_number = page.page_number

        serialized_result = (

            serialize_page_result(
                page
            )
        )

        event_payload = {

            "event_type": "page_processed",

            "job_id": job_id,

            "booklet_id": booklet_id,

            "page_number": page_number,

            "status": (
                "REVIEW"
                if page.validation_result.fatal_failure
                or page.omr_result.flagged_for_review
                else "PASS"
            ),

            "review_required": (
                page.validation_result.fatal_failure
                or
                page.omr_result.flagged_for_review
            ),

            "reasons": (
                [page.omr_result.message]
                if page.omr_result.message
                else []
            ),

            "payload": serialized_result,

            "image_path": (
                f"{booklet_id}/page_{page_number:03d}.png"
            ),

            "image_width": int(image.shape[1]),

            "image_height": int(image.shape[0])
        }

        # Persisted so a browser refresh can rebuild this page (image
        # included) from GET /jobs even while the job is still running --
        # otherwise this payload only ever existed in the WebSocket push
        # that's about to go out below, and reloading the page loses it.
        self.job_manager.record_page(
            job_id,
            page_number,
            event_payload
        )

        if CONFIG["visualization"]["enabled"]:
            try:
                viz_start = perf_counter()
                with tracer.start_as_current_span(
                    "visualization"
                ) as viz_span:
                    viz_span.set_attribute(
                        "page.number",
                        page_number
                    )
                    self.visualization_service.save_page_visualizations(
                        job_id=job_id,
                        booklet_id=booklet_id,
                        page_number=page_number,
                        image=image,
                        prediction_result=page.prediction_result,
                        omr_result=page.omr_result,
                    )
                viz_time = (
                    perf_counter()
                    - viz_start
                )
                VISUALIZATION_TIME.observe(viz_time)
                logger.info(
                    f"[TIMING] "
                    f"job={job_id} "
                    f"page={page_number} "
                    f"stage=visualization "
                    f"time={viz_time:.3f}s"
                )
            except Exception as e:
                logger.exception(
                    f"VISUALIZATION FAILED "
                    f"ON PAGE {page_number}: {e}"
                )

        event_bus.emit(
            "page_processed",
            event_payload
        )

    # =====================================================
    # ASSEMBLE ANNOTATIONS (job-level, after every page lands)
    # =====================================================

    def _assemble_annotations(self, job_results, question_paper_id):

        page_labels = []

        for page in job_results:

            metadata = page.omr_result.metadata

            page_labels.append(PageLabels(
                page_number=page.page_number,
                page_height=float(page.prediction_result.image_height),
                body_x1=float(metadata.get("body_x1", 0.0)),
                body_x2=float(metadata.get("body_x2", page.prediction_result.image_width)),
                labels=list(page.omr_result.questions),
                detection_failed=not metadata.get("separator_found", True),
            ))

        annotations_by_page = assemble(page_labels)

        for page in job_results:

            resolved = []

            for ann in annotations_by_page.get(page.page_number, []):

                lookup_tag = self.question_mapper.resolve(
                    ann.question_id, question_paper_id
                )

                resolved.append(
                    ann.model_copy(update={"lookup_tag": lookup_tag})
                )

            missing_lookup = [
                ann.question_id
                for ann in resolved
                if not ann.is_continuation and ann.lookup_tag is None
            ]

            page.omr_result.questions = [
                ann.model_dump(exclude_none=True) for ann in resolved
            ]

            if missing_lookup:

                page.omr_result.flagged_for_review = True

                page.omr_result.status = "REVIEW"

                page.omr_result.message = (
                    "No lookup_tag for question(s): "
                    + ", ".join(missing_lookup)
                )

            elif page.omr_result.status == "SUCCESS":

                page.omr_result.status = "PASS"

    # =====================================================
    # PROCESS JOB
    # =====================================================

    def process_job(
        self,
        pdf_path
    ):


        pdf_path = Path(pdf_path)

        rescan_file = (

            Path(
                CONFIG["paths"][
                    "needs_rescan_dir"
                ]
            )

            /

            pdf_path.name.replace(
                ".processing.pdf",
                ".pdf"
            )
        )

        if rescan_file.exists():

            logger.info(

                f"REMOVING RESCAN FILE: "

                f"{rescan_file}"
            )

            rescan_file.unlink()


        with tracer.start_as_current_span(
            "process_pdf"
        ) as root_span:

            root_span.set_attribute(
                "file.path",
                str(pdf_path),
            )

            logger.info(
                f"STARTING JOB: {pdf_path}"
            )
            ACTIVE_JOBS.inc()

            pdf_start_time = perf_counter()

            # =================================================
            # LOAD PAGES
            # =================================================

            pdf_load_start = perf_counter()

            pdf = fitz.open(pdf_path)

            pdf_load_time = (
                perf_counter()
                - pdf_load_start
            )

            pages_total = len(pdf)

            pdf.close()

            # =================================================
            # CREATE JOB
            # =================================================

            booklet_id = (
                Path(pdf_path)
                .stem
                .replace(".processing", "")
            )

            manifest = (
                self.job_manager.get_or_create_job(

                    pdf_path=pdf_path,

                    pages_total=pages_total
                )
            )

            job_id = manifest["job_id"]

            manifest["booklet_id"] = booklet_id

            self.job_manager.save_manifest(
                job_id,
                manifest
            )

            # Reserved for later: a human-assigned question_paper_id lets
            # app.engine.question_mapping resolve the per-paper override
            # file for labels that don't match the NNa pattern. Not wired
            # into job submission yet -- falls back to NNa-only matching.
            question_paper_id = manifest.get("question_paper_id")

            last_page = manifest.get(
                "pages_processed",
                0
            )

            logger.warning(
                f"LAST PROCESSED PAGE = {last_page}"
            )

            logger.info(

                f"RECOVERY MODE | "

                f"job={job_id} "

                f"resume_from={last_page + 1}"
            )


            root_span.set_attribute(
                "job.id",
                job_id
            )

            root_span.set_attribute(
                "pdf.filename",
                pdf_path.name
            )

            root_span.set_attribute(
                "pdf.pages",
                pages_total
            )

            root_span.set_attribute(
                "runtime.device",
                CONFIG["runtime"][
                    "preferred_device"
                ]
            )

            logger.info(
                f"[PDF_LOAD] "
                f"job={job_id} "
                f"time={pdf_load_time:.3f}s"
            )


            event_bus.emit(
                "job_started",
                {

                    "event_type": (
                        "job_started"
                    ),
                    "job_id": job_id,
                    "booklet_id": booklet_id,
                    "file_path": str(
                        pdf_path
                    )
                }
            )

            logger.info(
                f"JOB CREATED: {job_id}"
            )

            try:

                # =============================================
                # PREPROCESSING
                # =============================================

                self.job_manager.update_status(

                    job_id,

                    "PREPROCESSING"
                )

                # =============================================
                # INFERENCE
                # =============================================

                self.job_manager.update_status(

                    job_id,

                    "INFERENCE"
                )

                job_results = []

                self.job_manager.update_status(

                    job_id,

                    "VALIDATING"
                )

                pdf_loader = PDFLoader()

                pages = pdf_loader.load_pages(pdf_path)

                # =========================================
                # OCR-worker queue scheduler
                #
                # Submits pages ahead of collecting their results, so
                # this process's page-load/validation work overlaps
                # with the OCR worker process's PARSeq inference on
                # earlier pages. finalize_page() is intentionally
                # called in whatever order tasks complete in the first
                # loop below -- that's fine for per-page validation/
                # visualization/progress, but it's exactly why
                # _assemble_annotations() runs separately afterwards,
                # once, on job_results sorted by page_number.
                # =========================================

                WINDOW_SIZE = 3

                pending = deque()

                def _collect_oldest():

                    gpu_future, pending_page, pending_request, pending_validation = (
                        pending.popleft()
                    )

                    queue_wait_start = perf_counter()

                    with tracer.start_as_current_span(
                        "gpu_queue_wait"
                    ) as gpu_span:

                        gpu_span.set_attribute(
                            "page.number",
                            pending_request.page_number
                        )

                        result = self.gpu_service.collect(
                            gpu_future
                        )

                    gpu_time = (
                        perf_counter()
                        - queue_wait_start
                    )

                    GPU_TIME.observe(gpu_time)

                    logger.info(
                        f"[TIMING] "
                        f"job={job_id} "
                        f"page={pending_request.page_number} "
                        f"stage=gpu_total "
                        f"time={gpu_time:.3f}s"
                    )

                    self.finalize_page(
                        page=pending_page,
                        request=pending_request,
                        validation_result=pending_validation,
                        result=result,
                        job_results=job_results,
                        job_id=job_id,
                        booklet_id=booklet_id,
                    )

                for idx, (page_number, page) in enumerate(pages):

                    # =========================================
                    # RECOVERY SKIP
                    # =========================================

                    if page_number <= last_page:

                        logger.warning(

                            f"SKIPPING PAGE "

                            f"{page_number}"

                        )

                        continue

                    # =========================================
                    # VALIDATION
                    # =========================================

                    validation_start = perf_counter()

                    with tracer.start_as_current_span(
                        "validation"
                    ) as validation_span:

                        validation_span.set_attribute(
                            "page.number",
                            page_number
                        )

                        validation_result = (

                            self.validation_service
                            .validate_page(
                                image=page,
                                page_number=page_number
                            )
                        )

                        validation_span.set_attribute(
                            "validation.fatal_failure",
                            validation_result.fatal_failure
                        )

                    validation_time = (
                        perf_counter()
                        - validation_start
                    )

                    VALIDATION_TIME.observe(
                        validation_time
                    )

                    logger.info(
                        f"[TIMING] "
                        f"job={job_id} "
                        f"page={page_number} "
                        f"stage=validation "
                        f"time={validation_time:.3f}s"
                    )

                    # =========================================
                    # FAILED VALIDATION
                    # =========================================

                    if validation_result.fatal_failure:

                        logger.warning(

                            f"[{job_id}] "

                            f"PAGE {page_number} "

                            f"REQUIRES REVIEW"
                        )

                        self.job_manager.mark_review_required(
                            job_id
                        )

                    event_bus.emit(

                        "validation_completed",

                        {

                            "event_type": (
                                "validation_completed"
                            ),

                            "job_id": job_id,

                            "booklet_id": booklet_id,

                            "page_number": (
                                page_number
                            ),

                            "payload": (
                                validation_result
                                .model_dump()
                            )
                        }
                    )

                    logger.info(

                        f"[{job_id}] "

                        f"PROCESSING PAGE "

                        f"{page_number}/"
                        f"{pages_total}"
                    )

                    save_start =  perf_counter()

                    image_path = ImageTransport.save(page)

                    request = PageInferenceRequest(
                        job_id=job_id,
                        booklet_id=booklet_id,
                        page_number=page_number,
                        image_path=image_path,
                    )

                    save_time = (
                        perf_counter()
                        - save_start
                    )

                    logger.info(
                        f"[PAGE_SAVE] "
                        f"page={page_number} "
                        f"time={save_time:.3f}s"
                    )

                    gpu_future = self.gpu_service.submit(request)
                    pending.append(
                        (
                            gpu_future,
                            page,
                            request,
                            validation_result
                        )
                    )

                    # Cap how many pages are in flight (submitted but not
                    # yet collected) at WINDOW_SIZE, so a large PDF doesn't
                    # dump every page's full-res ImageTransport.save() onto
                    # disk at once -- this is what actually overlaps this
                    # process's validation/save work on later pages with
                    # the OCR worker's inference on earlier ones.
                    while len(pending) >= WINDOW_SIZE:
                        _collect_oldest()

                while pending:
                    _collect_oldest()

                # =============================================
                # ASSEMBLE ANNOTATIONS (job-level, order-dependent)
                # =============================================

                job_results.sort(key=lambda p: p.page_number)

                self._assemble_annotations(job_results, question_paper_id)

                review_required = any(

                    page.validation_result.fatal_failure

                    or

                    page.omr_result.flagged_for_review

                    for page in job_results
                )

                rescan_required = any(

                    page.validation_result.fatal_failure

                    for page in job_results
                )

                if rescan_required:

                    final_status = "RESCAN"

                elif review_required:

                    final_status = "REVIEW"

                else:

                    final_status = "PASS"

                export_path = None

                if CONFIG["output"]["save_exports"]:
                    with tracer.start_as_current_span(
                        "export_results"
                    ):
                        export_payload = {

                            "job_id": job_id,

                            "export_version": ocr_engine_config.assembler.export_version,

                            "booklet_id": booklet_id,

                            "status": final_status,

                            "image_root": booklet_id,

                            "review_required": review_required,

                            "pages": [

                                {

                                    "page_number": page.page_number,

                                    "annotations": page.omr_result.questions,

                                }

                                for page in job_results

                            ]
                        }

                    logger.error(
                        f"EXPORT PAYLOAD = "
                        f"{export_payload.keys()}"
                    )

                    export_path = (
                        export_omr_results(

                            pdf_name=pdf_path.stem,

                            omr_results=export_payload
                        )
                    )

                # Re-emit page_processed now that omr_result.questions
                # holds the final assembled annotations, not the raw
                # per-label detections finalize_page saw.
                for page in job_results:

                    self._emit_page_processed_final(
                        job_id=job_id,
                        booklet_id=booklet_id,
                        page=page,
                    )

                event_bus.emit(
                    "job_completed",
                    {
                        "event_type": "job_completed",
                        "job_id": job_id,
                        "booklet_id": booklet_id,
                        "status": final_status,
                        "review_required": review_required,
                        "reasons": []
                    }
                )

                self.job_manager.update_status(
                    job_id,
                    final_status
                )

                self.job_manager.set_export_path(

                    job_id,

                    export_path
                )

                root_span.set_attribute(
                    "job.status",
                    "success"
                )

                pdf_total_time = (
                    perf_counter()
                    - pdf_start_time
                )

                logger.info(

                    f"[PDF_METRICS] "

                    f"job={job_id} "
                    f"pages={pages_total} "
                    f"total={pdf_total_time:.2f}s"
                )

                logger.info(

                    f"JOB COMPLETED: "
                    f"{job_id}"
                )

                PDF_DURATION.observe(
                    pdf_total_time
                )

                PDF_PROCESSED.inc()

                ACTIVE_JOBS.dec()



                if final_status == "PASS":

                    destination_dir = Path(
                        CONFIG["paths"]["processed_dir"]
                    )

                elif final_status == "REVIEW":

                    destination_dir = Path(
                        CONFIG["paths"]["review_dir"]
                    )

                else:

                    destination_dir = Path(
                        CONFIG["paths"]["needs_rescan_dir"]
                    )

                final_filename = pdf_path.name.replace(
                    ".processing.pdf",
                    ".pdf"
                )

                destination_dir.mkdir(
                    parents=True,
                    exist_ok=True
                )

                destination = (
                    destination_dir /
                    final_filename
                )

                if pdf_path.exists():
                    pdf_path.rename(destination)
                else:
                    logger.warning(
                        f"SOURCE FILE MISSING: {pdf_path}"
                    )

                cleanup_start = perf_counter()

                with tracer.start_as_current_span(
                    "cleanup"
                ) as cleanup_span:
                    self.cleanup_service.cleanup_job_pages(
                        job_id
                    )

                cleanup_time = (
                    perf_counter()
                    - cleanup_start
                )

                logger.info(
                    f"[CLEANUP_TIME] "
                    f"job={job_id} "
                    f"time={cleanup_time:.3f}s"
                )

                logger.info(
                    f"MOVED TO PROCESSED: "
                    f"{destination}"
                )



                return job_results

        # =================================================
        # FAILURE
        # =================================================

            except Exception as e:

                logger.exception(

                    f"JOB FAILED: "
                    f"{job_id}"
                )
                PDF_FAILED.inc()

                ACTIVE_JOBS.dec()

                event_bus.emit(

                    "pipeline_error",

                    {

                        "event_type": (
                            "pipeline_error"
                        ),

                        "job_id": job_id,

                        "booklet_id": booklet_id,

                        "error": str(e)
                    }
                )

                self.job_manager.mark_failed(

                    job_id,

                    str(e)
                )

                root_span.set_attribute(
                    "job.status",
                    "failed"
                )

                root_span.record_exception(
                    e
                )

                raise

    # =====================================================
    # RE-EMIT PAGE EVENT AFTER ASSEMBLY (no image, no re-visualization)
    # =====================================================

    def _emit_page_processed_final(self, *, job_id, booklet_id, page):

        serialized_result = (
            serialize_page_result(page)
        )

        event_payload = {

            "event_type": "page_processed",

            "job_id": job_id,

            "booklet_id": booklet_id,

            "page_number": page.page_number,

            "status": page.omr_result.status,

            "review_required": page.omr_result.flagged_for_review,

            "reasons": (
                [page.omr_result.message]
                if page.omr_result.message
                else []
            ),

            "payload": serialized_result,

            "image_path": (
                f"{booklet_id}/page_{page.page_number:03d}.png"
            ),

            "image_width": page.prediction_result.image_width,

            "image_height": page.prediction_result.image_height,
        }

        # Overwrites the pre-assembly record_page call in
        # _emit_page_processed with the final assembled annotations, so a
        # refresh after job completion restores the same data this event
        # is about to push live.
        self.job_manager.record_page(
            job_id,
            page.page_number,
            event_payload
        )

        event_bus.emit(
            "page_processed",
            event_payload
        )
