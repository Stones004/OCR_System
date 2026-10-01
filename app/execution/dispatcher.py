"""Ported unchanged from D:\\OMR_System\\app\\execution\\dispatcher.py."""

from abc import ABC
from abc import abstractmethod


class TaskDispatcher(ABC):

    @abstractmethod
    def dispatch(
        self,
        task_name,
        payload
    ):
        pass
