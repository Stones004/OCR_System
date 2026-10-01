"""
Config loader, ported from D:\\OMR_System\\app\\core\\config\\config_loader.py
with two deliberate fixes made while porting:

1. The original's PATH_KEYS list said "manifests_dir" (plural) while the
   YAML key is "manifest_dir" (singular), so that path was silently never
   normalized to an absolute path -- it only worked because the container
   always ran with CWD == BASE_DIR. Fixed here to the real key name.
2. All paths are BASE_DIR-relative now. The original mixed relative paths
   with hardcoded "/workspace/..." absolute paths (Docker-only) for some
   keys; since this also needs to run natively (not just in Docker), every
   path key is plain-relative and resolved against BASE_DIR uniformly.
"""

from pathlib import Path
import yaml
import os


# =========================================================
# BASE DIRECTORY
# =========================================================

BASE_DIR = (
    Path(__file__)
    .resolve()
    .parents[3]
)


# =========================================================
# CONFIG PATH
# =========================================================

CONFIG_PATH = (
    Path(__file__)
    .resolve()
    .parent
    / "config.yaml"
)


def env_or_config(
    env_name: str,
    config_value
):
    return os.getenv(
        env_name,
        config_value
    )

# =========================================================
# LOAD YAML
# =========================================================

try:

    with open(

        CONFIG_PATH,

        "r",

        encoding="utf-8"

    ) as f:

        CONFIG = yaml.safe_load(f)

except Exception as e:

    raise RuntimeError(

        f"FAILED TO LOAD CONFIG: "
        f"{CONFIG_PATH}"

    ) from e


# =========================================================
# REQUIRED SECTIONS
# =========================================================

REQUIRED_SECTIONS = [

    "paths",

    "runtime",

    "ocr_engine",

    "visualization",

    "logging"
]


# =========================================================
# VALIDATE CONFIG
# =========================================================

for section in REQUIRED_SECTIONS:

    if section not in CONFIG:

        raise RuntimeError(

            f"MISSING CONFIG SECTION: "
            f"{section}"
        )


# =========================================================
# NORMALIZE PATHS
# =========================================================

PATH_KEYS = [

    "incoming_dir",

    "accepted_dir",

    "processed_dir",

    "review_dir",

    "needs_rescan_dir",

    "exports_dir",

    "reports_dir",

    "manifest_dir",

    "ui_output_dir",

    "debug_output_dir",

    "logs_dir",

    "temp_pages_dir",

    "page_cache_dir"
]

for key in PATH_KEYS:

    if key in CONFIG["paths"]:

        resolved = (
            BASE_DIR /

            CONFIG["paths"][key]
        ).resolve()

        # Self-healing: these are plain data directories (scan intake,
        # manifests, caches, ...), not git-tracked -- a fresh clone or a
        # wiped runtime/ volume must not need a manual mkdir step before
        # e.g. runtime_watcher's incoming_dir.iterdir() will work.
        resolved.mkdir(
            parents=True,
            exist_ok=True
        )

        CONFIG["paths"][key] = str(
            resolved
        )
