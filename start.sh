#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────
#  Climate Hazard Trend Analyzer — One-command startup
# ──────────────────────────────────────────────────────────────
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

info()  { echo -e "${CYAN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
ok()    { echo -e "${GREEN}[ OK ]${NC}  $*"; }
fail()  { echo -e "${RED}[FAIL]${NC}  $*"; exit 1; }

# ── Detect OS & set Docker command ────────────────────────────
DOCKER="docker"
DOCKER_COMPOSE="docker compose"

# Check for WSL (reports as Linux but needs .exe to reach Docker Desktop)
if grep -qi "microsoft\|WSL" /proc/version 2>/dev/null; then
    DOCKER="docker.exe"
    DOCKER_COMPOSE="docker.exe compose"
else
    case "$(uname -s)" in
        MINGW*|MSYS*|CYGWIN*|Windows_NT)
            DOCKER="docker.exe"
            DOCKER_COMPOSE="docker.exe compose"
            ;;
    esac
fi

# ── Pre-flight checks ─────────────────────────────────────────
info "Running pre-flight checks..."

command -v $DOCKER >/dev/null 2>&1 || fail "Docker is not installed. Install it from https://docker.com"
$DOCKER info >/dev/null 2>&1      || fail "Docker daemon is not running. Start Docker Desktop first."
$DOCKER_COMPOSE version >/dev/null 2>&1 || fail "'docker compose' plugin not found."

ok "Docker is ready"

# ── Create .env if missing ─────────────────────────────────────
if [ ! -f backend/.env ]; then
    if [ -f backend/.env.example ]; then
        cp backend/.env.example backend/.env
        warn "Created backend/.env from .env.example — edit it to add your OPENAI_API_KEY (optional)"
    else
        warn "No backend/.env or .env.example found; backend will use defaults"
    fi
else
    ok "backend/.env exists"
fi

# ── Build & start ──────────────────────────────────────────────
# Disable BuildKit — it fails on paths with spaces (e.g. "Full-Stack Developer")
export DOCKER_BUILDKIT=0
info "Building and starting all services..."
$DOCKER_COMPOSE up -d --build

# ── Wait for health ────────────────────────────────────────────
info "Waiting for services to become healthy..."

MAX_WAIT=60
elapsed=0
until $DOCKER_COMPOSE ps --format '{{.Health}}' 2>/dev/null | grep -q "healthy" || [ $elapsed -ge $MAX_WAIT ]; do
    sleep 2
    elapsed=$((elapsed + 2))
    printf "."
done
echo ""

# ── Status report ──────────────────────────────────────────────
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Climate Hazard Trend Analyzer is running!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${CYAN}Frontend${NC}       →  http://localhost:3000"
echo -e "  ${CYAN}Backend API${NC}    →  http://localhost:8000/docs"
echo -e "  ${CYAN}MongoDB${NC}        →  localhost:27017"
echo ""
echo -e "  ${YELLOW}Useful commands:${NC}"
echo "    docker compose logs -f          # stream logs"
echo "    docker compose down             # stop everything"
echo "    docker compose up -d --build    # rebuild & restart"
echo ""

$DOCKER_COMPOSE ps
