#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

if command -v python3.14 >/dev/null 2>&1; then
  PYTHON_BIN="python3.14"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
else
  echo "python3.14 or python3 not found"
  exit 1
fi

"$PYTHON_BIN" -m venv "$BACKEND_DIR/.venv"
source "$BACKEND_DIR/.venv/bin/activate"
pip install --upgrade pip
pip install -r "$BACKEND_DIR/requirements.txt"
pip install -r "$BACKEND_DIR/requirements-dev.txt"

echo "Backend setup complete."

cd "$FRONTEND_DIR"
npm install

echo "Frontend setup complete."
echo "Run backend with: cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
echo "Run frontend with: cd frontend && npm run dev"
