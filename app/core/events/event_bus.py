"""Ported unchanged from D:\\OMR_System\\app\\core\\events\\event_bus.py."""

from typing import Any

from app.core.events.transports.transport_manager import (
    transport_manager
)


# =========================================================
# EVENT BUS
# =========================================================

class EventBus:

    # =====================================================
    # EMIT
    # =====================================================

    def emit(

        self,

        event_name: str,

        payload: Any
    ):

        transport_manager.dispatch(

            event_name,

            payload
        )


# =========================================================
# GLOBAL EVENT BUS
# =========================================================

event_bus = EventBus()
