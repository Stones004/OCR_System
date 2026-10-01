"""Ported unchanged from D:\\OMR_System\\app\\execution\\execution_manager.py."""

from app.execution.local_dispatcher import (
    LocalDispatcher
)

from app.core.config.config_loader import (
    CONFIG
)

from app.workers.celery_dispatcher import (
    CeleryDispatcher
)


class ExecutionManager:

    def __init__(self):

        backend = (
            CONFIG["execution"][
                "backend"
            ]
        )

        if backend == "local":

            self.dispatcher = (
                LocalDispatcher()
            )

        elif backend == "celery":

            self.dispatcher = (
                CeleryDispatcher()
            )

        else:

            raise ValueError(

                f"UNKNOWN EXECUTION "
                f"BACKEND: {backend}"
            )

    def dispatch(
        self,
        task_name,
        payload
    ):

        return self.dispatcher.dispatch(
            task_name,
            payload
        )


execution_manager = (
    ExecutionManager()
)
