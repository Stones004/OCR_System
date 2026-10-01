"""Ported unchanged from D:\\OMR_System\\app\\execution\\local_dispatcher.py."""

from app.execution.dispatcher import (
    TaskDispatcher
)

from app.execution.task_registry import (
    TASK_REGISTRY
)


class LocalDispatcher(TaskDispatcher):

    def dispatch(
        self,
        task_name: str,
        payload: dict
    ):

        if task_name not in TASK_REGISTRY:

            raise ValueError(

                f"UNKNOWN TASK: "
                f"{task_name}"
            )

        task = TASK_REGISTRY[
            task_name
        ]

        result = task(**payload)

        return result
