"""Ported unchanged from D:\\OMR_System\\app\\api\\websocket\\websocket_transport.py."""

import asyncio

from app.core.events.transports.base_transport import (
    BaseTransport
)

from app.api.websocket.manager import (
    websocket_manager
)


# =========================================================
# WEBSOCKET TRANSPORT
# =========================================================

class WebSocketTransport(

    BaseTransport
):

    def send(

        self,

        event_name,

        payload
    ):

        print(

            "[WS TRANSPORT]",

            event_name
        )

        if websocket_manager.loop is None:
            return

        asyncio.run_coroutine_threadsafe(

            websocket_manager.broadcast(
                payload
            ),

            websocket_manager.loop
        )
