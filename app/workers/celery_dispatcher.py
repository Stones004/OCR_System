"""Ported unchanged from D:\\OMR_System\\app\\workers\\celery_dispatcher.py."""

from app.execution.dispatcher import (
    TaskDispatcher
)

from app.workers.celery_app import (
    celery_app
)


class CeleryDispatcher(
    TaskDispatcher
):

    def dispatch(

        self,

        task_name: str,

        payload: dict
    ):

        celery_app.send_task(

            task_name,

            args=[payload]
        )
