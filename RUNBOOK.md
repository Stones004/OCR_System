# Running the OCR Answer-Script Scanner

Step-by-step instructions for starting every piece of this repo and
where to find it once it's up: the backend API, the two Celery workers,
Flower, the scanner web app, and monitoring (Prometheus + OpenTelemetry/
OpenObserve).

Two ways to run it:

- **[Native](#native-run-recommended-for-development)** — each piece in
  its own terminal, using the local `venv`. Best for development; what
  every command below assumes unless marked "(Docker)".
- **[Docker Compose](#docker-compose-run-all-in-one)** — one command
  builds and starts everything in containers, PARSeq included. This is
  the equivalent of D:\OMR_System's "Option A", their one fully working
  path (see the "how was the old system started" discussion this repo's
  history carries — their Option B and native-dev instructions were
  both actually broken). Best for a fresh machine or a from-scratch
  demo.

---

## Prerequisites (one-time)

Already done if you're working in this checkout, listed here so a fresh
clone knows what's needed:

| Requirement | Where | Needed for |
|---|---|---|
| Python 3.12 venv with `requirements.txt` installed | `venv/` | Native |
| Node.js 18+, frontend deps installed (`npm install` in `frontend/`) | `frontend/node_modules/` | Native |
| Frontend built (`npm run build` in `frontend/`) | `frontend/dist/` — the backend only serves the scanner app at `/` if this exists | Native |
| PARSeq venv (torch/strhub) | `venv_parseq/` — a self-contained copy inside this repo (path set in `app/core/config/config.yaml` → `ocr_engine.ocr.parseq.venv_python`); also doubles as the runtime for the optional noise classifier (`ocr_engine.noise_classifier`) | Native only — Docker builds its own, see below |
| PARSeq checkpoint | `weights/parseq_base_mix_v2.ckpt` (already present in this checkout) | Native + Docker both read it from here |
| Noise classifier checkpoint (optional, off by default) | `weights/noise_classifier/best.pt` (already present in this checkout) | Native only — enable via `ocr_engine.pipeline.use_noise_classifier` in config.yaml |
| Docker Desktop | — | Redis (native), and the full Compose stack |

If `frontend/dist/` doesn't exist yet:

```powershell
cd frontend
npm install
npm run build
cd ..
```

---

## Native run (recommended for development)

Everything below runs from the repo root (`D:\OCR_System`), using
`venv\Scripts\python.exe`. Open a separate terminal per numbered step —
they're all long-running processes.

### 1. Start Redis

Redis is the Celery broker *and* the event bus (job progress, page
results, WebSocket fan-out all flow through it).

```powershell
docker run -d --name ocr-redis -p 6379:6379 redis:7-alpine
```

Leave it running; `docker start ocr-redis` brings it back after a reboot
instead of re-running the line above.

### 2. Start the two Celery workers

There are exactly two worker roles — see the note at the bottom of this
section for why it's two and not one or several.

**Worker A — job orchestration** (validates pages, submits them for OCR,
collects results, writes the export). Safe to run with real concurrency,
since it never touches the OCR engine directly. This is also the *only*
process that ever records the pipeline metrics in
`app/monitoring/metrics.py` (PDF counts, validation/GPU/export timing) --
`$env:METRICS_PORT` tells it to serve them on :8002, since the API
process's own :8001 never sees this work (see step 5 below for why):

```powershell
$env:METRICS_PORT="8002"
venv\Scripts\python.exe -m celery -A app.workers.celery_app worker --pool=threads --concurrency=3 -Q celery -n cpu-worker@%h --loglevel=info
```

**Worker B — OCR inference** (runs the deskew → separator → ink-removal →
label-detection → PARSeq pipeline per page). Must stay `--pool=solo` —
this is the one process that owns the single PARSeq subprocess:

```powershell
venv\Scripts\python.exe -m celery -A app.workers.celery_app worker --pool=solo -Q gpu_inference -n ocr-worker@%h --loglevel=info
```

The **first** task Worker B picks up takes ~8–15 seconds while it loads
the PARSeq checkpoint; every task after that is fast. This is normal, not
a hang.

> **Why two workers, and why is Worker B stuck at one process?**
> PARSeq runs as a subprocess with a single stdin/stdout pipe — it can't
> be shared across processes, so only one worker may ever consume the
> `gpu_inference` queue. Job orchestration (Worker A) has no such
> constraint, so it runs with real concurrency (3 threads) to handle
> multiple PDFs' bookkeeping at once, even though actual OCR compute is
> always serialized through Worker B, one page at a time.

### 3. Start the backend (FastAPI)

```powershell
venv\Scripts\python.exe -m uvicorn app.api.main:app --host 0.0.0.0 --port 8000
```

This single process serves the REST API, the WebSocket endpoint, **and**
the scanner web app itself (from `frontend/dist/`, if built) — you don't
run the frontend separately for normal use. It also starts the
Prometheus metrics server (port 8001) and the `runtime_watcher` background
task (polls `scans/incoming/` for new PDFs every 2s) automatically on
startup.

**Access:**

| What | URL |
|---|---|
| Scanner web app | http://localhost:8000/ |
| REST API | http://localhost:8000 |
| Health check | http://localhost:8000/health |
| WebSocket (live job/page events) | ws://localhost:8000/ws |

### 4. Start Flower (Celery monitoring UI)

Shows queued/active/completed tasks per worker, live.

```powershell
venv\Scripts\python.exe -m celery -A app.workers.celery_app flower --port=5555
```

**Access:** http://localhost:5555

### 5. Monitoring

**Prometheus metrics** — split across two ports, because the numbers are
recorded in two different processes:

| Port | Process | What's actually there |
|---|---|---|
| http://localhost:8001/metrics | Backend (step 3) | Process/library-level default metrics only. The pipeline never runs here. |
| http://localhost:8002/metrics | Worker A / cpu-worker (step 2) | The metrics that matter — `pdf_processed_total`, `pdf_failed_total`, `active_jobs`, `validation_seconds`, `gpu_total_seconds`, `visualization_seconds`, `pdf_duration_seconds`, `gpu_queue_wait_seconds` (full list in `app/monitoring/metrics.py`). This is where `app/pipeline/processing_pipeline.py` actually calls `.inc()`/`.observe()`, since job orchestration runs as a Celery task inside Worker A's process. |

Both start automatically — step 3 starts the first, step 2's
`$env:METRICS_PORT="8002"` starts the second (see
`app/workers/celery_app.py`'s `_init_metrics`). If you only check :8001
you'll see the metric names registered but every value stuck at zero,
no matter how many PDFs you process — that's not a hang, it's just the
wrong port.

**OpenTelemetry tracing → OpenObserve** — off by default
(`observability.enabled: false` in `app/core/config/config.yaml`), since
it needs a running OpenObserve instance. To turn it on:

```powershell
docker run -d --name openobserve -p 5080:5080 `
  -e ZO_ROOT_USER_EMAIL=admin@example.com `
  -e ZO_ROOT_USER_PASSWORD=Admin@123 `
  public.ecr.aws/zinclabs/openobserve:latest
```

(OpenObserve rejects weaker passwords outright — needs 8-128 chars with
at least one lowercase, one uppercase, one digit, and one special
character. This must also match `app/core/config/config.yaml`'s
`observability.password`, since that's the same root user the app
authenticates trace ingestion with.)

Then set `observability.enabled: true` in `app/core/config/config.yaml`
and restart the backend and both workers (tracing initializes once at
process startup).

**Access:** http://localhost:5080 (login with the email/password above)

### 6. Frontend dev server (optional — only for editing the frontend)

Skip this for normal use — step 3 already serves the built app. Use this
only when actively changing frontend code, for hot reload:

```powershell
cd frontend
npm run dev
```

**Access:** http://localhost:5173 (proxies `/config`, `/jobs`, `/process`,
`/health` to `:8000` — see `frontend/vite.config.js`; images and the
WebSocket connect to `:8000` directly from the browser)

### 7. Submit a PDF

Either:

- Drop a PDF into `scans/incoming/` — the watcher (started in step 3)
  picks it up within ~2 seconds, or
- `POST http://localhost:8000/runtime/process` — processes whatever's
  already sitting in `scans/incoming/`, synchronously, without waiting
  for the watcher's poll cycle.

Watch it move through `scans/incoming/` → (renamed `*.processing.pdf`) →
`scans/processed/` (status `PASS`) or `scans/review/` (status `REVIEW`) or
`scans/needs_rescan/` (status `RESCAN`), with the export JSON landing in
`scans/exports/<booklet_id>_ocr_min.json`. Live progress streams over the
WebSocket to the scanner app; job state is also queryable via
`GET /jobs/{job_id}`.

### 8. Shutting down

Ctrl+C each terminal (backend, both workers, Flower), then:

```powershell
docker stop ocr-redis
docker stop openobserve   # only if you started it
```

---

## Docker Compose run (all-in-one)

This is the equivalent of D:\OMR_System's "Option A" — one command starts
everything: API+frontend, both workers, Redis, OpenObserve, and Flower,
as containers. Verified working end-to-end (submitted a real PDF through
the containerized stack, got the correct export JSON back) — this isn't
aspirational.

Unlike the native run, **PARSeq doesn't need to be set up separately
first**: the image builds its own Linux-native PARSeq venv at build time
(torch CPU + strhub — see `Dockerfile`'s `parseq-builder` stage and
`docker/parseq_requirements.txt`), instead of using the repo's own
Windows-only `venv_parseq/` the way the native run does. The one thing
Compose still needs from the host is the checkpoint file itself (see
step 1) — the ~91 MB weight isn't baked into the image, the same way
D:\OMR_System kept its YOLOX weights in a mounted `./weights/` folder
rather than inside the image.

### 1. Prerequisites

- `./weights/parseq_base_mix_v2.ckpt` must exist (already present in
  this checkout). If it's missing, copy it there before starting the
  stack; `ocr-worker` will fail on its first task without it.
- `.env` must exist (see step 2) — Compose refuses to start *any*
  service with a missing `env_file`, even one you don't need to
  customize.

### 2. Create `.env`

```powershell
copy .env.example .env
```

### 3. Build and start the stack

```powershell
docker compose up -d --build
```

First build takes a few minutes (downloads CPU torch + builds strhub
from git for the PARSeq venv, plus the frontend `npm ci`/`npm run
build`). Subsequent runs reuse Docker's layer cache and start in
seconds.

### 4. Access

| Component | URL |
|---|---|
| Scanner app + API | http://localhost:8000/ |
| Prometheus metrics (API process — mostly empty, see below) | http://localhost:8001/metrics |
| Prometheus metrics (cpu-worker — the real pipeline numbers) | http://localhost:8002/metrics |
| Flower | http://localhost:5555 |
| OpenObserve | http://localhost:5080 |
| Redis | `redis://localhost:6379` (for a client, not a browser) |

Same split as the native run's step 5: the pipeline metrics
(`pdf_processed_total`, `gpu_total_seconds`, etc.) are only ever recorded
inside the `cpu-worker` container, since that's where
`app/pipeline/processing_pipeline.py` actually runs as a Celery task —
:8001 on `ocr-system` never sees that work. `cpu-worker`'s
`METRICS_PORT=8002` env var (set in `docker-compose.yml`) is what makes
:8002 available.

### 5. Submit a PDF

Drop it into the host's `./scans/incoming/` — it's bind-mounted into the
container, so the watcher picks it up the same as in the native run.
Everything from here on (status folders, export JSON, WebSocket events)
behaves identically to the native run — see step 7 of the native section
above.

### 6. Config changes

Unlike D:\OMR_System, the config directory isn't bind-mounted into the
container (see `app/core/config/config.docker.yaml`'s header comment for
why — the host's `config.yaml` has Windows-only PARSeq paths that would
break the container if mounted straight in). To change a Docker-side
setting, edit `app/core/config/config.docker.yaml` and re-run
`docker compose up -d --build` — the Settings drawer's save button won't
persist across a container restart in this mode.

### 7. Shutting down

```powershell
docker compose down
```

---

## Quick reference

| Process | Native command | Docker Compose service | Port | URL |
|---|---|---|---|---|
| Redis | `docker run ... redis:7-alpine` | `redis` | 6379 | — |
| Worker A (orchestration) | `celery ... --pool=threads --concurrency=3 -Q celery` | `cpu-worker` | 8002 | http://localhost:8002/metrics |
| Worker B (OCR/PARSeq) | `celery ... --pool=solo -Q gpu_inference` | `ocr-worker` | — | — |
| Backend + scanner app + metrics | `uvicorn app.api.main:app` | `ocr-system` | 8000, 8001 | http://localhost:8000/ |
| Flower | `celery ... flower` | `flower` | 5555 | http://localhost:5555 |
| OpenObserve (optional) | `docker run ... openobserve` | `openobserve` | 5080 | http://localhost:5080 |
| Frontend dev server (optional, native only) | `npm run dev` in `frontend/` | — | 5173 | http://localhost:5173 |

One command for all six Docker Compose rows: `docker compose up -d --build`.

## Verifying everything is healthy

```powershell
curl http://localhost:8000/health
```

Returns `{"api", "redis", "gpu_worker", "telemetry"}`, each `healthy` or
`offline`. `gpu_worker` here means Worker B specifically (see
`app/services/gpu_service.py`'s docstring for why it's still named that);
`telemetry` only reports `healthy` if OpenObserve is running and
`observability.enabled: true`.
