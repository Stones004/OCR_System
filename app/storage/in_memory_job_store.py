"""Ported unchanged from D:\\OMR_System\\app\\storage\\in_memory_job_store.py."""

from app.storage.job_store import (
    JobStore
)


class InMemoryJobStore(JobStore):

    def __init__(self):

        self.jobs = {}

    def create_job(
        self,
        job_id,
        job_data
    ):

        self.jobs[job_id] = job_data

    def get_job(
        self,
        job_id
    ):

        return self.jobs.get(job_id)

    def update_job(
        self,
        job_id,
        job_data
    ):

        self.jobs[job_id] = job_data

    def delete_job(
        self,
        job_id
    ):

        if job_id in self.jobs:

            del self.jobs[job_id]

    def list_jobs(self):

        return self.jobs
