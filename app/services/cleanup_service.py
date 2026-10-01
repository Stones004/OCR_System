"""Ported unchanged from D:\\OMR_System\\app\\services\\cleanup_service.py."""

from pathlib import Path

from app.core.config.config_loader import (
    CONFIG
)

from app.core.logging.logger import (
    logger
)


class CleanupService:

    def cleanup_job_pages(
        self,
        job_id: str
    ):

        temp_dir = Path(

            CONFIG["paths"][
                "temp_pages_dir"
            ]
        )

        if not temp_dir.exists():
            return

        deleted = 0

        for file in temp_dir.glob(
            f"{job_id}_*.png"
        ):

            try:

                file.unlink()

                deleted += 1

            except Exception as e:

                logger.warning(
                    f"FAILED TO DELETE "
                    f"{file}: {e}"
                )

        logger.info(
            f"CLEANED {deleted} "
            f"TEMP PAGES FOR {job_id}"
        )
