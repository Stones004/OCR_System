# OCR_System

Dockerised OCR pipeline for scanned exam answer booklets (FastAPI backend in
`app/`, React viewer in `frontend/`). See `RUNBOOK.md` for how to run it.

## Project status (as of 2026-11-26)

- Last built: ROI enhancement stage (`app/engine/stages/roi_enhancer.py`), noise
  classifier and PARSeq worker updates, and image-transport changes in the engine
  pipeline.
- Recent dev changes pushed here: updated engine configs (`config.yaml`,
  `config.docker.yaml`, `ocr_engine_config.py`), deskewer fixes, pipeline and
  `docker-compose.yml` updates.
- Not in the repo (restore locally): `.env` (copy `.env.example`), `weights/`
  (model checkpoints), `scans/`, `runtime/`, `data/`, `output/`, `venv*/`.
