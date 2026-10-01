"""Ported unchanged from D:\\OMR_System\\app\\api\\routes\\websocket.py."""

import asyncio

from fastapi import APIRouter
from fastapi import WebSocket
from fastapi import WebSocketDisconnect

from app.api.websocket.manager import (
    websocket_manager
)


# =========================================================
# ROUTER
# =========================================================

router = APIRouter()


# =========================================================
# WEBSOCKET ENDPOINT
# =========================================================

@router.websocket("/ws")
async def websocket_endpoint(

    websocket: WebSocket
):

    await websocket_manager.connect(
        websocket
    )

    print(
        "WEBSOCKET CONNECTED"
    )

    try:

        while True:

            await asyncio.sleep(1)

    except WebSocketDisconnect:

        websocket_manager.disconnect(
            websocket
        )

        print(
            "WEBSOCKET DISCONNECTED"
        )
