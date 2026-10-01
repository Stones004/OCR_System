"""Ported unchanged from D:\\OMR_System\\app\\observability\\tracing.py."""

from opentelemetry import trace
import base64
import os

from app.core.config.config_loader import CONFIG
from app.core.logging.logger import logger

# Safe no-op tracer used before init_tracing() is called,
# and whenever observability is disabled.
tracer = trace.get_tracer(__name__)

def init_tracing():
    """
    Call once from main.py (and from gpu_tasks.py worker startup).
    Safe to call multiple times — subsequent calls are no-ops.
    """
    global tracer

    cfg = CONFIG["observability"]

    cfg["endpoint"] = os.getenv("OPENOBSERVE_ENDPOINT", cfg["endpoint"])
    cfg["username"] = os.getenv("OPENOBSERVE_USERNAME", cfg["username"])
    cfg["password"] = os.getenv("OPENOBSERVE_PASSWORD", cfg["password"])
    cfg["service_name"] = os.getenv("OPENOBSERVE_SERVICE_NAME", cfg["service_name"])

    if not cfg["enabled"]:
        logger.info("OPENOBSERVE DISABLED — using no-op tracer")
        return  # tracer stays as the no-op above

    logger.info(
        f"OPENOBSERVE ENABLED | "
        f"endpoint={cfg['endpoint']} | "
        f"service={cfg['service_name']}"
    )

    try:
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

        credentials = f"{cfg['username']}:{cfg['password']}"
        auth_header = base64.b64encode(credentials.encode()).decode()

        resource = Resource.create({
            "service.name": cfg["service_name"],
            "deployment.environment": cfg["environment"],
            "service.version": "1.0.0",
        })

        provider = TracerProvider(resource=resource)
        provider.add_span_processor(
            BatchSpanProcessor(
                OTLPSpanExporter(
                    endpoint=cfg["endpoint"],
                    headers={"Authorization": f"Basic {auth_header}"},
                )
            )
        )
        trace.set_tracer_provider(provider)
        tracer = trace.get_tracer(cfg["service_name"])
        logger.info("OPENOBSERVE tracer initialised successfully")

    except Exception as e:
        logger.warning(
            f"OPENOBSERVE init failed — falling back to no-op tracer: {e}"
        )
        # tracer already points to the no-op; nothing else to do
