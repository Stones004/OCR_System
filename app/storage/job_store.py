"""Ported unchanged from D:\\OMR_System\\app\\storage\\job_store.py."""

from abc import ABC
from abc import abstractmethod


class JobStore(ABC):

    @abstractmethod
    def create_job(
        self,
        job_id,
        job_data
    ):
        pass

    @abstractmethod
    def get_job(
        self,
        job_id
    ):
        pass

    @abstractmethod
    def update_job(
        self,
        job_id,
        job_data
    ):
        pass

    @abstractmethod
    def delete_job(
        self,
        job_id
    ):
        pass

    @abstractmethod
    def list_jobs(self):
        pass
