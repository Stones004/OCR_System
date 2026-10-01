"""Ported unchanged from D:\\OMR_System\\app\\core\\models\\inference_request.py."""

from pydantic import BaseModel


class PageInferenceRequest(BaseModel):

    job_id: str

    booklet_id: str

    page_number: int

    image_path: str
