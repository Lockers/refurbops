# RefurbOps Starter Scaffold

This scaffold sets up the agreed RefurbOps base repository so you can start development immediately with **PyCharm for the backend** and **VS Code for the frontend**.

## Included

- single-repo structure
- backend FastAPI skeleton
- frontend React + TypeScript + Vite skeleton
- docs folder populated with current project source documents
- local setup scripts for PowerShell and Bash
- environment example files
- VS Code workspace and recommended extensions

## Locked local versions

- Python: **3.14.3**
- Node.js: **22.12+ minimum**
- Recommended Node.js: **22 LTS** or **24 LTS**
- npm: bundled with Node.js
- MongoDB: local instance for development

## Repository layout

```text
refurbops/
  backend/
  frontend/
  docs/
  scripts/
```

## First-run setup

### Backend (PyCharm)

1. Open the `backend/` folder in **PyCharm**.
2. Create a new virtual environment named `.venv` using **Python 3.14.3**.
3. Copy `.env.example` to `.env`.
4. Install dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

5. Add a PyCharm run configuration:
   - **Run type:** Python module
   - **Module name:** `uvicorn`
   - **Parameters:** `app.main:app --reload --host 127.0.0.1 --port 8000`
   - **Working directory:** `backend/`

You can also run manually from the backend terminal:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend (VS Code)

1. Open the repo root or `frontend/` in **VS Code**.
2. Copy `.env.example` to `.env`.
3. Install dependencies and start the dev server:

```bash
cd frontend
npm install
npm run dev
```

The frontend expects the API at `http://127.0.0.1:8000` by default.

## IDE usage

### PyCharm

Use PyCharm only for `backend/`. Keep the interpreter pinned to the local `.venv` created from Python 3.14.3.

### VS Code

Open `refurbops.code-workspace` from the repo root. It includes both backend and frontend folders, but the intended use is mainly frontend and general repo navigation.

## Current purpose of this scaffold

This is intentionally a clean base, not the full app. It is for:

1. locking the repo structure
2. locking the local environment
3. getting PyCharm and VS Code working cleanly
4. starting Module 01 from a stable base

## Next implementation slice

The first real slice remains:

Inbound page -> click Arrived -> create device -> generate `device_id` -> generate/print label -> open device record.

## Standalone learning scraper

This repository also includes a standalone `learning_scraper/` package that demonstrates HTTP and browser-backed scrape -> judge -> retry workflows for educational use, including JavaScript rendering and network-call-aware judgement. See `learning_scraper/README.md` and `docs/learning_scraper_architecture.md` for details.
