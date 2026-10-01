"""
Typed configuration for the OCR engine (app/engine/*), following
D:\\OCR_codes's own convention exactly: no default values anywhere in code,
a missing/misspelled/wrongly-typed key is a startup error naming the key.

This validates only the `ocr_engine:` subtree of app/core/config/config.yaml
-- the rest of that file (paths, runtime, execution, observability, ...) is
read as a raw dict by app.core.config.config_loader.CONFIG, following
D:\\OMR_System's own convention for its (much larger, generic) surrounding
architecture. Both loaders point at the same file; this one just applies
stricter validation to the section this engine owns.
"""

from __future__ import annotations

import types
import typing
from dataclasses import dataclass, fields, is_dataclass
from pathlib import Path

from app.core.config.config_loader import CONFIG, CONFIG_PATH


class ConfigError(ValueError):
    """Raised when the ocr_engine config section is missing or incomplete."""


# ======================================================================
# Pipeline behaviour
# ======================================================================

@dataclass(frozen=True)
class PipelineConfig:
    use_annotation_removal: bool      # erase red/green reviewer ink before detection
    use_noise_classifier: bool        # drop "noise" ROIs before PARSeq ever sees them
    verbose: bool                     # per-component / per-candidate console logging


# ======================================================================
# Image-processing stages (identical shape to D:\OCR_codes\src\config.py)
# ======================================================================

@dataclass(frozen=True)
class DeskewConfig:
    angle_min: float
    angle_max: float
    coarse_step: float
    fine_step: float
    fine_window: float
    border_value: int
    edge_fallback_angle: float
    # The coarse+fine angle search tries ~40 candidate angles, each a full
    # cv2.warpAffine + projection-variance score; at full page resolution
    # (e.g. 3852x2268 @ 300 DPI) that's ~2.3s of a ~2.7s total CV pipeline
    # per page. Skew angle doesn't depend on resolution, so the search
    # runs on the binary image downscaled to this width instead (measured:
    # identical angle, 6.7x faster) -- only the final rotate() at the end
    # of process() still runs at full resolution.
    search_width: int


@dataclass(frozen=True)
class VerticalConfig:
    threshold: int
    min_kernel_height: int
    kernel_height_divisor: int
    repair_kernel: tuple[int, ...]          # (width, height)


@dataclass(frozen=True)
class SeparatorConfig:
    left_ratio: float
    right_ratio: float
    min_height_ratio: float
    min_aspect_ratio: float
    expected_x: int | None
    tolerance: int | None


@dataclass(frozen=True)
class CropConfig:
    right_padding: int


@dataclass(frozen=True)
class InkRemovalConfig:
    red_lower1: tuple[int, ...]
    red_upper1: tuple[int, ...]
    red_lower2: tuple[int, ...]
    red_upper2: tuple[int, ...]
    green_lower: tuple[int, ...]
    green_upper: tuple[int, ...]
    kernel_size: int
    close_iterations: int
    dilate_iterations: int
    remove_fringe: bool
    fringe_zone_kernel_size: int
    fringe_zone_iterations: int
    fringe_lightness_max: int
    fringe_min_component_area: int
    fill_color: tuple[int, ...]


@dataclass(frozen=True)
class PreprocessConfig:
    min_area: int
    min_contrast_gap: float


@dataclass(frozen=True)
class AnnotationDetectorConfig:
    min_width: int
    min_height: int
    padding: int
    merge_dist: int
    min_confident_area: int
    min_confident_dim: int
    min_ink_pixels: int
    min_fill_ratio: float
    row_y_tolerance: float

    reject_above_top_line: bool
    top_line_search_frac: float
    top_line_min_len_ratio: float
    top_line_margin: int

    exclude_sparse_strokes: bool
    sparse_stroke_density_max: float
    sparse_stroke_min_dim: int

    exclude_long_vertical_strips: bool
    long_strip_max_width: int
    long_strip_min_height: int

    refine_height: int
    valley_threshold: float
    min_valley_width: int
    min_segment_height: int
    refine_blur_ksize: int

    line_kernel_min: int
    line_kernel_divisor: int
    line_dilate_kernel: int


@dataclass(frozen=True)
class VisualizationConfig:
    """Colours (BGR) and thicknesses of the debug overlays."""

    separator_candidate_color: tuple[int, ...]
    separator_candidate_thickness: int
    separator_selected_color: tuple[int, ...]
    separator_selected_thickness: int
    roi_color: tuple[int, ...]
    roi_thickness: int


# ======================================================================
# Noise classifier (pre-OCR triage)
# ======================================================================

@dataclass(frozen=True)
class NoiseClassifierConfig:
    # ResNet-18 crop classifier trained in the trocr-handwriting-v2 project
    # (src/noise_classifier/train.py there) on annotated ROI crops; a crop
    # is "noise" if it was never given a usable transcription. This
    # project's own venv has no torch/torchvision, so the classifier runs
    # as a subprocess under the PARSeq venv instead, exactly like
    # ParseqBackend -- venv_python normally points at the same interpreter
    # as ocr.parseq.venv_python.
    venv_python: Path
    checkpoint: Path
    device: str                              # "auto" | "cpu" | "cuda"
    # The model outputs a single noise_score in [0, 1] = P(noise). An ROI
    # is "noise" if noise_score >= this, "clean" if noise_score <= 1 - this,
    # else "uncertain" (the symmetric band around 0.5 in between). 0.7 keeps
    # 88.6% of ROIs out of that band at 96.2% accuracy on those kept (vs
    # 92.9% accuracy with the band empty at 0.5), per the held-out test
    # split in the source project.
    confidence_threshold: float
    # Only "noise"-bucket ROIs are dropped before OCR by default. Set true
    # to also drop "uncertain" ones for more aggressive noise reduction, at
    # the cost of risking real annotations the model isn't sure about.
    drop_uncertain: bool
    shutdown_timeout: float


# ======================================================================
# OCR backend
# ======================================================================

@dataclass(frozen=True)
class ParseqConfig:
    venv_python: Path
    checkpoint: Path
    device: str                              # "auto" | "cpu" | "cuda"
    norm_mean: float
    norm_std: float
    shutdown_timeout: float


@dataclass(frozen=True)
class OcrConfig:
    backend: str                             # "parseq" (only backend wired up for v1)
    parseq: ParseqConfig


# ======================================================================
# Annotation assembly / question mapping
# ======================================================================

@dataclass(frozen=True)
class AssemblerConfig:
    export_version: int


@dataclass(frozen=True)
class QuestionMappingConfig:
    # NNa pattern: two-digit number + one lowercase letter, e.g. "07b".
    override_file: Path                      # {question_paper_id: {question_id: lookup_tag}}
    # When true, a bare numeral label ("7", "10", no sub-part letter)
    # resolves directly to a zero-padded lookup_tag ("07", "10") instead
    # of falling through to the override file / review flag. Turn off
    # once every question paper in use follows the strict NNa scheme, to
    # go back to flagging anything that isn't "07b"-shaped for review.
    allow_bare_numerals: bool


# ======================================================================
# Root
# ======================================================================

@dataclass(frozen=True)
class OcrEngineConfig:
    root: Path                               # folder containing the YAML (injected)
    pipeline: PipelineConfig
    deskew: DeskewConfig
    vertical: VerticalConfig
    separator: SeparatorConfig
    crop: CropConfig
    ink_removal: InkRemovalConfig
    preprocess: PreprocessConfig
    annotation_detector: AnnotationDetectorConfig
    visualization: VisualizationConfig
    noise_classifier: NoiseClassifierConfig
    ocr: OcrConfig
    assembler: AssemblerConfig
    question_mapping: QuestionMappingConfig


# ======================================================================
# Loader / validator (identical mechanics to D:\OCR_codes\src\config.py)
# ======================================================================

def _coerce(value, tp, where, root):

    origin = typing.get_origin(tp)

    if origin in (typing.Union, types.UnionType):
        args = typing.get_args(tp)
        if value is None:
            if type(None) in args:
                return None
            raise ConfigError(f"{where}: must not be null")
        inner = [a for a in args if a is not type(None)]
        return _coerce(value, inner[0], where, root)

    if is_dataclass(tp):
        return _build(tp, value, where, root)

    if tp is bool:
        if not isinstance(value, bool):
            raise ConfigError(f"{where}: expected true/false, got {value!r}")
        return value

    if tp is int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ConfigError(f"{where}: expected an integer, got {value!r}")
        return value

    if tp is float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ConfigError(f"{where}: expected a number, got {value!r}")
        return float(value)

    if tp is str:
        if not isinstance(value, str):
            raise ConfigError(f"{where}: expected text, got {value!r}")
        return value

    if tp is Path:
        if not isinstance(value, str):
            raise ConfigError(f"{where}: expected a path string, got {value!r}")
        path = Path(value)
        return path if path.is_absolute() else (root / path)

    if origin is tuple:
        if not isinstance(value, (list, tuple)):
            raise ConfigError(f"{where}: expected a list, got {value!r}")
        item_type = typing.get_args(tp)[0]
        return tuple(
            _coerce(v, item_type, f"{where}[{i}]", root)
            for i, v in enumerate(value)
        )

    raise ConfigError(f"{where}: unsupported config type {tp!r}")


def _build(cls, data, where, root):

    if not isinstance(data, dict):
        raise ConfigError(f"{where}: expected a section (mapping), got {data!r}")

    hints = typing.get_type_hints(cls)
    names = [f.name for f in fields(cls)]

    unknown = sorted(set(data) - set(names))
    if unknown:
        raise ConfigError(
            f"{where}: unknown key(s) {unknown} (valid: {names})"
        )

    missing = [n for n in names if n not in data]
    if missing:
        raise ConfigError(f"{where}: missing key(s) {missing}")

    return cls(**{
        n: _coerce(data[n], hints[n], f"{where}.{n}", root)
        for n in names
    })


def load_ocr_engine_config() -> OcrEngineConfig:

    if "ocr_engine" not in CONFIG:
        raise ConfigError(
            f"{CONFIG_PATH}: missing top-level 'ocr_engine' section"
        )

    root = CONFIG_PATH.parent

    return _build(
        OcrEngineConfig,
        {**CONFIG["ocr_engine"], "root": str(root)},
        "ocr_engine",
        root,
    )


ocr_engine_config = load_ocr_engine_config()
