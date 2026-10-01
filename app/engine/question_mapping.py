"""
Question-id -> lookup_tag mapping.

Most real labels already read as the legacy `NNa` pattern -- a two-digit
question number plus one lowercase sub-part letter, e.g. "07b". Those are
matched with a regex. When a question_id doesn't match (unusual OCR
output, a genuinely different labelling scheme, ...), lookup_tag is left
null and the page is flagged for review rather than guessed at -- unless a
human has already filled in an exception for this question paper in the
override file.

Override file format ({question_paper_id: {question_id: lookup_tag}}):

    Doc0611_paper:
      "1": 01a
      "2b": 02b

Bare-numeral labels ("1", "2", "10" -- no sub-part letter) are a second,
separately-toggled case: question papers with no lettered sub-parts at
all produce these instead of NNa-shaped labels. When
question_mapping.allow_bare_numerals is true, they resolve directly to a
zero-padded lookup_tag ("01", "02", "10") without needing an override
entry. When false, they fall through to the override file / review flag
exactly like any other non-NNa label.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from app.core.config.ocr_engine_config import QuestionMappingConfig

_NNA_PATTERN = re.compile(r"^(\d{2})([a-z])$")
_NUMERIC_PATTERN = re.compile(r"^\d{1,3}$")


def _to_nna(question_id: str) -> str | None:
    candidate = question_id.strip().lower().replace(" ", "")
    if _NNA_PATTERN.match(candidate):
        return candidate
    return None


def _to_numeric(question_id: str) -> str | None:
    candidate = question_id.strip()
    if _NUMERIC_PATTERN.match(candidate):
        return f"{int(candidate):02d}"
    return None


class QuestionMapper:

    def __init__(self, config: QuestionMappingConfig):
        self.override_file: Path = config.override_file
        self.allow_bare_numerals: bool = config.allow_bare_numerals
        self._overrides: dict[str, dict[str, str]] = self._load_overrides()

    def _load_overrides(self) -> dict[str, dict[str, str]]:

        if not self.override_file.exists():
            return {}

        with open(self.override_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        if not isinstance(data, dict):
            raise ValueError(
                f"{self.override_file}: expected a mapping of "
                "{question_paper_id: {question_id: lookup_tag}}"
            )

        return {
            str(paper_id): {str(qid): str(tag) for qid, tag in mapping.items()}
            for paper_id, mapping in data.items()
        }

    def resolve(self, question_id: str, question_paper_id: str | None) -> str | None:
        """
        Try the NNa pattern first, then (if enabled) bare numerals, then
        the per-question-paper override file. Returns None (leave for
        human review) if nothing matches.
        """

        tag = _to_nna(question_id)
        if tag is not None:
            return tag

        if self.allow_bare_numerals:
            tag = _to_numeric(question_id)
            if tag is not None:
                return tag

        if question_paper_id is None:
            return None

        return self._overrides.get(question_paper_id, {}).get(question_id)
