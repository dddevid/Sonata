#!/usr/bin/env bash
# setup.sh — One-shot setup for Sonata music streaming server
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

info()  { echo -e "${GREEN}[setup]${NC} $*"; }
warn()  { echo -e "${YELLOW}[warn]${NC}  $*"; }

# ── 1. Python backend ────────────────────────────────────────────────────────
info "Setting up Python virtual environment…"
if ! command -v python3 &>/dev/null; then
  echo "Error: python3 not found. Please install Python 3.11+." >&2; exit 1
fi

cd backend
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
info "Python dependencies installed."

# Copy .env if missing
if [ ! -f ".env" ]; then
  cp .env.example .env
  warn ".env created from .env.example — edit it before production use."
fi

info "Running Django migrations…"
python manage.py migrate --run-syncdb

info "Collecting static files…"
python manage.py collectstatic --noinput --verbosity 0 2>/dev/null || true

deactivate
cd ..

# ── 2. Frontend ──────────────────────────────────────────────────────────────
info "Building frontend…"
if ! command -v node &>/dev/null; then
  echo "Error: node not found. Please install Node.js 18+." >&2; exit 1
fi

cd frontend
if ! command -v pnpm &>/dev/null; then
  npm install --legacy-peer-deps --silent
  npm run build -- --outDir ../backend/static
else
  pnpm install --silent
  pnpm build --outDir ../backend/static
fi
cd ..
info "Frontend built and placed in backend/static."

# ── 3. Go scanner ────────────────────────────────────────────────────────────
info "Building Go scanner service…"
if command -v go &>/dev/null; then
  cd scanner
  go build -o ../sonata-scanner ./... 
  cd ..
  info "Scanner binary: ./sonata-scanner"
else
  warn "go not found — skipping scanner build. Install Go 1.21+ and run: cd scanner && go build -o ../sonata-scanner ./..."
fi

# ── Done ─────────────────────────────────────────────────────────────────────
echo ""
info "Setup complete! To start Sonata:"
echo ""
echo "  Terminal 1 (backend):  cd backend && source .venv/bin/activate && python manage.py runserver 0.0.0.0:8000"
echo "  Terminal 2 (scanner):  DJANGO_URL=http://localhost:8000 ./sonata-scanner"
echo "  Frontend (dev):        cd frontend && npm run dev"
echo ""
echo "  Or use Docker Compose: docker compose up --build"
