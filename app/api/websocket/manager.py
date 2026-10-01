"""Ported unchanged from D:\\OMR_System\\app\\api\\websocket\\manager.py."""

from fastapi import WebSocket

from typing import List
import asyncio

# =========================================================
# WEBSOCKET MANAGER
# =========================================================

class WebSocketManager:

    def __init__(self):

        self.connections: List[
            WebSocket
        ] = []

        self.loop = None

    # =====================================================
    # CONNECT
    # =====================================================

    async def connect(

        self,

        websocket: WebSocket
    ):

        await websocket.accept()
        self.loop = asyncio.get_running_loop()

        self.connections.append(
            websocket
        )

    # =====================================================
    # DISCONNECT
    # =====================================================

    def disconnect(

        self,

        websocket: WebSocket
    ):

        if websocket in self.connections:

            self.connections.remove(
                websocket
            )

    # =====================================================
    # BROADCAST
    # =====================================================

    async def broadcast(

        self,

        payload
    ):
        print(

            "[BROADCAST]",

            payload
        )

        disconnected = []

        for connection in self.connections:

            try:

                print(

                    "[WEBSOCKET BROADCAST]",

                    payload.get(
                        "event_type"
                    )
                )

                await connection.send_json(
                    payload
                )

            except Exception as e:

                print("WEBSOCKET SEND ERROR:", e)
                disconnected.append(
                    connection
                )

        for connection in disconnected:

            self.disconnect(
                connection
            )


# =========================================================
# GLOBAL WEBSOCKET MANAGER
# =========================================================

websocket_manager = (
    WebSocketManager()
)
