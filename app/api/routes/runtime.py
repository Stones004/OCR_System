"""Ported unchanged from D:\\OMR_System\\app\\api\\routes\\runtime.py."""

from fastapi import APIRouter

from app.core.config.config_loader import (
    CONFIG
)


# =========================================================
# ROUTER
# =========================================================

router = APIRouter()


# =========================================================
# RUNTIME STATUS
# =========================================================

@router.get("/runtime/status")

def runtime_status():

    return {

        "device": (
            CONFIG["runtime"][
                "preferred_device"
            ]
        ),

        "environment": (
            CONFIG["system"][
                "environment"
            ]
        ),

        "version": (
            CONFIG["system"][
                "version"
            ]
        )
    }
