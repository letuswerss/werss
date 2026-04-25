# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Project Overview

WeRSS is a full-stack WeChat public account aggregation and analysis system.

Current stack:

- Python 3.11+
- FastAPI backend
- SQLAlchemy models and DB utilities
- APScheduler-style job system in `jobs/`
- React 18 + TypeScript + Vite frontend in `web_ui/`
- Playwright-based browser automation for scraping

This workspace appears to be a local working copy rather than a normal git clone. Assume local data and config files are meaningful and avoid changing them casually.

## Repository Layout

Top-level areas you will touch most often:

- `main.py`: process entrypoint and uvicorn launcher
- `web.py`: FastAPI app, middleware, router registration, health endpoints
- `apis/`: HTTP route layer
- `core/`: configuration, DB, models, business logic, middleware
- `jobs/`: scheduled task registration and execution
- `driver/`: browser automation
- `web_ui/`: React frontend
- `docs/`: deployment, quick start, API notes

## Important Reality Checks

- The frontend is React. Ignore older references to Vue in stale docs.
- Frontend dev server runs on port `5174`.
- Backend default port is `8001`.
- Health endpoint is `/api/health`.
- `web_ui/scripts/copy-build.ts` copies frontend build output into backend `static/`.

## Files To Treat Carefully

Avoid changing these unless the user explicitly wants it:

- `.env`
- `config.yaml`
- `data/`
- `static/`
- local logs and screenshots

These are local state, deployment state, or generated artifacts.

## Setup And Run

Preferred Python environment flow:

```bash
uv venv
source .venv/bin/activate
uv sync
```

Initialize DB / tables:

```bash
python main.py -init True
```

Run backend:

```bash
python main.py -job True -init False
```

Run frontend:

```bash
cd web_ui
pnpm install
pnpm dev
```

Build frontend and copy into backend static assets:

```bash
cd web_ui
pnpm build:deploy
```

## Change Guidance

- Backend endpoint changes usually require edits in both `apis/` and `core/`
- Data model changes may require reviewing code paths in `core/models/`, DB initialization, and any consumers in API handlers
- Config changes should be checked against `.env.example`, `config.example.yaml`, and runtime resolution behavior
- Frontend changes should be checked for whether backend-served static output must be refreshed
- Deployment-related changes should stay aligned with `docs/DEPLOYMENT.md`

## Validation Guidance

Use targeted validation.

- For backend routing or startup changes, verify `python main.py -init True` still works if relevant
- For API changes, smoke test `/api/health` and the touched endpoint
- For frontend changes, run `pnpm build` or `pnpm build:deploy` when the task affects shipped assets
- For Playwright or scraping changes, avoid broad live runs unless the user asked for them

## Documentation Hygiene

If you update repository guidance, keep this file aligned with `AGENTS.md`.
