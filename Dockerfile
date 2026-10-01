# ==========================================
# STAGE 1: Build the React Frontend
# ==========================================
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# ==========================================
# STAGE 2: Build PARSeq's venv (Linux, CPU)
# ==========================================
# D:\OCR_codes's PARSeq venv on the dev machine is a Windows torch+cu128
# build and can't run in this container. This stage builds a second,
# Linux-native venv for it instead -- same reason the native setup keeps
# PARSeq in its own venv (torch/strhub deps don't mix cleanly with the
# root app's numpy 2.x / opencv 5.x), just built here instead of assumed
# to already exist on the host.
FROM python:3.12-slim AS parseq-builder
WORKDIR /opt/parseq-src

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY docker/parseq_requirements.txt ./requirements.txt

RUN python -m venv /opt/parseq-venv && \
    /opt/parseq-venv/bin/pip install --no-cache-dir --upgrade pip && \
    /opt/parseq-venv/bin/pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu && \
    /opt/parseq-venv/bin/pip install --no-cache-dir -r requirements.txt

# ==========================================
# STAGE 3: Python FastAPI Backend & Server
# ==========================================
FROM python:3.12-slim
WORKDIR /workspace

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN mkdir -p \
    /workspace/runtime \
    /workspace/runtime/prometheus

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY main.py ./main.py
COPY data/overrides/ ./data/overrides/

# PARSeq's Linux venv from STAGE 2
COPY --from=parseq-builder /opt/parseq-venv /opt/parseq-venv

# The Docker-appropriate config REPLACES the native one baked from the
# repo (see config.docker.yaml's own header comment for why it isn't
# just volume-mounted the way D:\OMR_System did it).
COPY app/core/config/config.docker.yaml ./app/core/config/config.yaml

# Built frontend from STAGE 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

EXPOSE 8000
EXPOSE 8001

VOLUME ["/workspace/scans", "/workspace/reports", "/workspace/logs", "/workspace/output", "/workspace/weights"]

CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
