"""Ported unchanged from D:\\OMR_System\\app\\core\\events\\serializers.py."""

from app.core.models.page_data import (
    PageProcessingResult
)


# =========================================================
# SERIALIZE PAGE RESULT
# =========================================================

def serialize_page_result(

    result: PageProcessingResult
):

    return result.model_dump(mode='json')
