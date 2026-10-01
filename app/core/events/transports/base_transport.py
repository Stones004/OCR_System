"""Ported unchanged from D:\\OMR_System."""

from abc import ABC
from abc import abstractmethod

from typing import Any


# =========================================================
# BASE EVENT TRANSPORT
# =========================================================

class BaseTransport(ABC):

    @abstractmethod
    def send(

        self,

        event_name: str,

        payload: Any
    ):

        pass
