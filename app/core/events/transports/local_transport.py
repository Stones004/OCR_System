"""Ported unchanged from D:\\OMR_System."""

from typing import Callable
from typing import Dict
from typing import List
from typing import Any

from .base_transport import (
    BaseTransport
)


# =========================================================
# LOCAL TRANSPORT
# =========================================================

class LocalTransport(

    BaseTransport
):

    def __init__(self):

        self.listeners: Dict[
            str,
            List[Callable]
        ] = {}

    # =====================================================
    # SUBSCRIBE
    # =====================================================

    def subscribe(

        self,

        event_name: str,

        callback: Callable
    ):

        if event_name not in self.listeners:

            self.listeners[event_name] = []

        self.listeners[
            event_name
        ].append(callback)

    # =====================================================
    # SEND
    # =====================================================

    def send(

        self,

        event_name: str,

        payload: Any
    ):

        callbacks = self.listeners.get(

            event_name,

            []
        )

        for callback in callbacks:

            callback(payload)
