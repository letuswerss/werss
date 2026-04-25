# WeRSS Agent Notes

## Repo Scope

This directory is the standalone `werss` project workspace.

- Backend: FastAPI + SQLAlchemy + APScheduler
- Frontend: React 18 + TypeScript + Vite in `web_ui/`
- Browser automation and scraping logic live under `driver/` and `core/wx/`
- Deployment files live at repo root: `docker-compose.yml`, `docker-compose.app-only.yml`, `docker-compose.dev.yml`

Important: this working directory currently does not appear to be a git checkout. Treat it as a local working copy with real runtime state.

## Local State To Protect

Be careful with files and directories that likely contain machine-local state or generated outputs:

- `.env`
- `config.yaml`
- `data/`
- `static/`
- `*.log`
- local screenshots such as `responsive_*.png` and `audit_login_final.png`

Do not rewrite or delete those unless the user explicitly asks.

## Actual Architecture

Use the current codebase, not stale docs, as the source of truth.

- The frontend is React, not Vue
- Backend entrypoint is `main.py`
- FastAPI app wiring is in `web.py`
- API routes are under `apis/`
- Core business logic is under `core/`
- Scheduled jobs are under `jobs/`
- Frontend source is under `web_ui/src/`

## Common Commands

Backend setup with `uv`:

```bash
uv venv
source .venv/bin/activate
uv sync
```

Backend init and run:

```bash
python main.py -init True
python main.py -job True -init False
```

Frontend dev:

```bash
cd web_ui
pnpm install
pnpm dev
```

Frontend production asset sync back into backend `static/`:

```bash
cd web_ui
pnpm build:deploy
```

## Working Rules

- If a task changes API behavior, inspect both `apis/` and the corresponding logic in `core/`
- If a task changes frontend behavior, check whether backend-served static assets also need refresh via `pnpm build:deploy`
- If a task touches config resolution, read `.env.example`, `config.example.yaml`, and `core/config.py`
- Prefer environment variables and templates over hardcoding secrets
- Keep Docker deployment assumptions aligned with `docs/DEPLOYMENT.md`

## Validation Guidance

- Backend smoke check: verify `/api/health`
- API docs are served at `/api/docs`
- Frontend local dev default port is `5174`
- Backend default port is `8001`

When making code changes, validate the smallest relevant surface first instead of running broad workflows by default.
