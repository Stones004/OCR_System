"""Ported unchanged from D:\\OMR_System."""

from typing import List
from typing import Any

from .base_transport import (
    BaseTransport
)


# =========================================================
# TRANSPORT MANAGER
# =========================================================

class TransportManager:

    def __init__(self):

        self.transports: List[
            BaseTransport
        ] = []

    # =====================================================
    # REGISTER TRANSPORT
    # =====================================================

    def register(

        self,

        transport: BaseTransport
    ):

        self.transports.append(
            transport
        )

    # =====================================================
    # DISPATCH
    # =====================================================

    def dispatch(

        self,

        event_name: str,

        payload: Any
    ):

        for transport in self.transports:

            transport.send(

                event_name,

                payload
            )


# =========================================================
# GLOBAL TRANSPORT MANAGER
# =========================================================

transport_manager = (
    TransportManager()
)
