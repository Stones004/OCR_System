"""Ported unchanged from D:\\OMR_System\\main.py."""

from pathlib import Path
import asyncio

from app.api.runtime.runtime_watcher import (
    runtime_watcher
)

from app.core.logging.logger import (
    logger
)

from app.core.config.config_loader import (
    CONFIG
)

from app.core.events.transports.transport_manager import (
    transport_manager
)

from app.core.events.transports.local_transport import (
    LocalTransport
)

from app.monitoring.prometheus_server import (
    start_metrics_server
)

# =========================================================
# EVENT TRANSPORT
# =========================================================

local_transport = (
    LocalTransport()
)

transport_manager.register(
    local_transport
)

# =========================================================
# INPUT DIRECTORY
# =========================================================

INPUT_DIR = Path(

    CONFIG["paths"]["incoming_dir"]
)

# =========================================================
# MAIN
# =========================================================

def main():
    from app.observability.tracing import init_tracing
    init_tracing()

    runtime_cfg = CONFIG["runtime"]
    if runtime_cfg["api_mode"]:
        logger.info("API MODE ENABLED")
        return

    logger.info("OCR SYSTEM STARTED")
    logger.info(
        f"RUNTIME DEVICE: "
        f"{CONFIG['runtime']['preferred_device']}"
    )
    start_metrics_server()
    if runtime_cfg["watch_mode"]:
        logger.info("WATCH MODE ENABLED")
        asyncio.run(runtime_watcher())
    else:
        logger.info("WATCH MODE DISABLED")

# =========================================================
# ENTRYPOINT
# =========================================================

if __name__ == "__main__":

    main()
