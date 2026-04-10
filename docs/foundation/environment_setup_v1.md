# RefurbOps Environment Setup v1

## Locked local stack

- Backend: Python + FastAPI
- Frontend: React + TypeScript + Vite
- Database: MongoDB
- Repo style: single repository
- IDE split: PyCharm for backend, VS Code for frontend

## Locked versions

- Python **3.14.3** for backend
- Node.js **22.12+ minimum** because Vite requires at least 20.19+ or 22.12+
- Recommended Node.js: **22 LTS** or **24 LTS**
- MongoDB local for now

## Backend setup in PyCharm

1. Open `backend/` in PyCharm.
2. Create a new virtual environment at `backend/.venv` using the **Python 3.14.3** interpreter.
3. Copy `.env.example` to `.env`.
4. Install: `requirements.txt` and `requirements-dev.txt`.
5. Add a run configuration:
   - Run type: Python module
   - Module name: `uvicorn`
   - Parameters: `app.main:app --reload --host 127.0.0.1 --port 8000`
   - Working directory: `backend/`
6. Start the backend.

## Frontend setup in VS Code

1. Open the repo root or `frontend/` in VS Code.
2. Install recommended extensions from `.vscode/extensions.json`.
3. Copy `.env.example` to `.env`.
4. Run `npm install`.
5. Run `npm run dev`.

## Mongo setup

### Option A: local Mongo

Use `mongodb://localhost:27017` with the database name `refurbops_dev`.

### Option B: MongoDB Atlas

The scaffold also works with Atlas later because the Mongo connection comes from environment variables.

## Immediate next step after setup

Once both apps start locally, the next move is Module 01:

- inbound sync skeleton
- arrived action
- device creation
- device ID generation
- label generation flow
