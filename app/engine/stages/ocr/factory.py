"""
OCR Backend Factory

Only the PARSeq backend is wired up for v1 (see D:\\OCR_codes\\src\\ocr\\lmstudio.py
for a reference implementation if an LM Studio fallback is added later).
"""

from app.core.config.ocr_engine_config import OcrConfig


def _parseq(config: OcrConfig):
    from .parseq import ParseqBackend
    return ParseqBackend(config.parseq)


BACKENDS = {

    "parseq": _parseq,
}


def create_backend(name: str, config: OcrConfig):

    name = name.lower()

    try:
        builder = BACKENDS[name]

    except KeyError:

        raise ValueError(

            f"Unknown OCR backend '{name}'. "

            f"Available: {list(BACKENDS.keys())}"

        )

    return builder(config)
