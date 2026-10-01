"""
PDF -> per-page images, for app/pipeline/processing_pipeline.py.

Adapted from D:\\OMR_System\\app\\core\\utils\\pdf_loader.py with two
deliberate changes:

1. Renders in COLOR (BGR), not grayscale. The original rendered
   grayscale directly (colorspace=fitz.csGRAY) because YOLOX bubble
   detection never needed colour. This engine's ink-removal stage is an
   HSV mask over red/green reviewer pen, which needs the real colour
   image -- grayscale would throw that information away before it ever
   reaches the pipeline. Downstream code that wants grayscale already
   handles a 3-channel input (e.g. app/validator's quality checks).
2. Honors pdf.skip_pages (the 2-page cover sheet with no margin/answer
   split) here, once, so the cover pages are never handed to the engine
   at all -- it stays stateless about them. page_number is the page's
   actual 1-indexed position in the source PDF (page_index + 1), NOT
   renumbered to start at 1 for the first content page: a reviewer
   opening page_number N in a PDF viewer must land on the same page the
   export/UI is showing them, skip_pages offset and all.
"""

from pathlib import Path

import fitz
import numpy as np
import cv2

from app.core.logging.logger import (
    logger
)

from app.core.config.config_loader import (
    CONFIG
)

PDF_POINTS_PER_INCH = 72

# =========================================================
# PDF LOADER
# =========================================================

class PDFLoader:

    def __init__(

        self,

        dpi=None
    ):

        pdf_cfg = CONFIG["pdf"]

        self.dpi = (
            dpi
            or
            pdf_cfg["dpi"]
        )

        self.skip_pages = pdf_cfg["skip_pages"]

    # =====================================================
    # LOAD PDF PAGES
    # =====================================================

    def load_pages(

        self,

        pdf_path
    ):

        pdf_path = Path(pdf_path)

        if not pdf_path.exists():

            raise FileNotFoundError(

                f"PDF NOT FOUND: "
                f"{pdf_path}"
            )

        logger.info(
            f"LOADING PDF: {pdf_path.name}"
        )

        pages = []

        doc = fitz.open(pdf_path)

        try:

            zoom = self.dpi / PDF_POINTS_PER_INCH

            matrix = fitz.Matrix(
                zoom,
                zoom
            )

            total_pages = len(doc)

            logger.info(
                f"TOTAL PAGES: {total_pages}"
            )

            for page_index in range(self.skip_pages, total_pages):

                try:

                    page = doc[page_index]

                    pix = page.get_pixmap(

                        matrix=matrix,

                        alpha=False
                    )

                    image = np.frombuffer(

                        pix.samples,

                        dtype=np.uint8

                    ).reshape(
                        pix.height,
                        pix.width,
                        pix.n
                    )

                    image = cv2.cvtColor(
                        image,
                        cv2.COLOR_RGB2BGR
                    )

                    pages.append(
                        (
                            page_index + 1,
                            image
                        )
                    )

                except Exception as e:

                    logger.exception(

                        f"FAILED TO LOAD PAGE "
                        f"{page_index + 1}: {e}"
                    )

                    continue

        finally:

            doc.close()

        return pages
