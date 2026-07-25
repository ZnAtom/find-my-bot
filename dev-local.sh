#!/usr/bin/env bash
#
# dev-local.sh - Linux local development helper.
#
# Default layout:
#   - PostgreSQL + pgvector: docker compose db service on 127.0.0.1:5433
#   - Backend: local Python virtualenv at backend/.venv
#   - Frontend: local npm/Vite with hot reload
#
# Usage:
#   bash dev-local.sh setup
#   bash dev-local.sh start
#   bash dev-local.sh stop
#   bash dev-local.sh restart
#   bash dev-local.sh status
#   bash dev-local.sh logs
#   bash dev-local.sh db
#   bash dev-local.sh support-import
#
# Useful overrides:
#   ENV_FILE=.env.local
#   DB_MODE=docker|local|skip
#   DEV_PYTHON=/path/to/python
#   DB_HOST=127.0.0.1 DB_PORT=5433 DB_USER=appuser DB_PASSWORD=password DB_NAME=lostfound
#   BACKEND_PORT=8000 FRONTEND_PORT=5173
#   BACKEND_RELOAD=1
#   INSTALL_EMBEDDING_DEPS=1 EMBEDDING_ENABLED=1
#   EMBEDDING_MODEL_PATH=model/models--Qwen--Qwen3-VL-Embedding-2B
#   SUPPORT_AUTO_IMPORT=0
#
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
LOCAL_DIR="$ROOT_DIR/.local"
RUN_DIR="$LOCAL_DIR/run"
LOG_DIR="$LOCAL_DIR/logs"
VENV_DIR="$BACKEND_DIR/.venv"
PYTHON_USERBASE="$LOCAL_DIR/python-user"

mkdir -p "$RUN_DIR" "$LOG_DIR"

BACKEND_PID="$RUN_DIR/backend.pid"
FRONTEND_PID="$RUN_DIR/frontend.pid"
BACKEND_LOG="$LOG_DIR/backend.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"
DB_INIT_LOG="$LOG_DIR/db-init.log"

PYTHON_BIN=""
FMB_ENV_FILE=""

have() {
  command -v "$1" >/dev/null 2>&1
}

truthy() {
  case "${1:-}" in
    1|true|TRUE|yes|YES|on|ON) return 0 ;;
    *) return 1 ;;
  esac
}

usage() {
  cat <<'USAGE'
dev-local.sh - Linux local development helper.

Default layout:
  - PostgreSQL + pgvector: docker compose db service on 127.0.0.1:5433
  - Backend: local Python virtualenv at backend/.venv
  - Frontend: local npm/Vite with hot reload

Usage:
  bash dev-local.sh setup
  bash dev-local.sh start
  bash dev-local.sh stop
  bash dev-local.sh restart
  bash dev-local.sh status
  bash dev-local.sh logs
  bash dev-local.sh db
  bash dev-local.sh support-import

Useful overrides:
  ENV_FILE=.env.local
  DB_MODE=docker|local|skip
  DEV_PYTHON=/path/to/python
  DB_HOST=127.0.0.1 DB_PORT=5433 DB_USER=appuser DB_PASSWORD=password DB_NAME=lostfound
  BACKEND_PORT=8000 FRONTEND_PORT=5173
  BACKEND_RELOAD=1
  INSTALL_EMBEDDING_DEPS=1 EMBEDDING_ENABLED=1
  EMBEDDING_MODEL_PATH=model/models--Qwen--Qwen3-VL-Embedding-2B
  SUPPORT_AUTO_IMPORT=0
USAGE
}

resolve_env_file() {
  local configured="${ENV_FILE:-.env}"
  case "$configured" in
    /*) FMB_ENV_FILE="$configured" ;;
    *) FMB_ENV_FILE="$ROOT_DIR/$configured" ;;
  esac
}

resolve_project_path() {
  local value="${1:-}"
  case "$value" in
    "") return 1 ;;
    /*) printf '%s\n' "$value" ;;
    "~") printf '%s\n' "$HOME" ;;
    "~/"*) printf '%s/%s\n' "$HOME" "${value#~/}" ;;
    *) printf '%s/%s\n' "$ROOT_DIR" "$value" ;;
  esac
}

ensure_env_file() {
  resolve_env_file
  if [ -f "$FMB_ENV_FILE" ]; then
    return 0
  fi

  if [ "$FMB_ENV_FILE" = "$ROOT_DIR/.env" ] && [ -f "$ROOT_DIR/.env.example" ]; then
    cp "$ROOT_DIR/.env.example" "$ROOT_DIR/.env"
    echo "[env] created .env from .env.example"
    return 0
  fi

  echo "[env] config file not found: $FMB_ENV_FILE"
  echo "[env] Create it from .env.example, or pass ENV_FILE=.env.example for read-only checks."
  return 1
}

load_env() {
  ensure_env_file
  local override_names=(
    DB_MODE DEV_PYTHON DB_HOST DB_PORT DB_USER DB_PASSWORD DB_NAME
    BACKEND_HOST BACKEND_PORT BACKEND_RELOAD FRONTEND_HOST FRONTEND_PORT VITE_PROXY_TARGET
    INSTALL_EMBEDDING_DEPS EMBEDDING_ENABLED EMBEDDING_MODEL_PATH HF_LOCAL_ONLY
    SUPPORT_DOCS_DIR SUPPORT_AUTO_IMPORT HF_ENDPOINT VECTOR_DIM
  )
  local name override_name
  for name in "${override_names[@]}"; do
    if [ "${!name+x}" = "x" ]; then
      export "FMB_OVERRIDE_$name=${!name}"
    fi
  done

  if [ -f "$FMB_ENV_FILE" ]; then
    set -a
    # shellcheck disable=SC1091
    source "$FMB_ENV_FILE"
    set +a
  fi
  for name in "${override_names[@]}"; do
    override_name="FMB_OVERRIDE_$name"
    if [ "${!override_name+x}" = "x" ]; then
      export "$name=${!override_name}"
      unset "$override_name"
    fi
  done

  export DB_MODE="${DB_MODE:-docker}"
  export DB_USER="${DB_USER:-appuser}"
  export DB_PASSWORD="${DB_PASSWORD:-password}"
  export DB_NAME="${DB_NAME:-lostfound}"

  case "$DB_MODE" in
    docker)
      export DB_HOST="127.0.0.1"
      export DB_PORT="${DB_PORT:-5433}"
      ;;
    local)
      export DB_HOST="${DB_HOST:-127.0.0.1}"
      export DB_PORT="${DB_PORT:-5432}"
      ;;
    skip)
      export DB_HOST="${DB_HOST:-127.0.0.1}"
      export DB_PORT="${DB_PORT:-5432}"
      ;;
    *)
      echo "[config] unsupported DB_MODE=$DB_MODE, use docker, local, or skip"
      exit 1
      ;;
  esac

  export DATABASE_URL="postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"
  export BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
  export BACKEND_PORT="${BACKEND_PORT:-8000}"
  export BACKEND_RELOAD="${BACKEND_RELOAD:-0}"
  export FRONTEND_HOST="${FRONTEND_HOST:-127.0.0.1}"
  export FRONTEND_PORT="${FRONTEND_PORT:-5173}"
  export VITE_PROXY_TARGET="${VITE_PROXY_TARGET:-http://127.0.0.1:$BACKEND_PORT}"
  export INSTALL_EMBEDDING_DEPS="${INSTALL_EMBEDDING_DEPS:-0}"
  export EMBEDDING_ENABLED="${EMBEDDING_ENABLED:-0}"
  export EMBEDDING_MODEL_PATH="${EMBEDDING_MODEL_PATH:-model/models--Qwen--Qwen3-VL-Embedding-2B}"
  export EMBEDDING_MODEL_PATH="$(resolve_project_path "$EMBEDDING_MODEL_PATH")"
  export HF_LOCAL_ONLY="${HF_LOCAL_ONLY:-1}"
  export SUPPORT_DOCS_DIR="${SUPPORT_DOCS_DIR:-doc/support}"
  export SUPPORT_DOCS_DIR="$(resolve_project_path "$SUPPORT_DOCS_DIR")"
  export SUPPORT_AUTO_IMPORT="${SUPPORT_AUTO_IMPORT:-1}"
  export HF_ENDPOINT="${HF_ENDPOINT:-https://hf-mirror.com}"
  export VECTOR_DIM="${VECTOR_DIM:-1536}"
}

select_python() {
  if [ -n "${DEV_PYTHON:-}" ]; then
    PYTHON_BIN="$DEV_PYTHON"
  elif [ -x "$VENV_DIR/bin/python" ]; then
    PYTHON_BIN="$VENV_DIR/bin/python"
  elif have python3.12; then
    PYTHON_BIN="$(command -v python3.12)"
  elif have python3; then
    PYTHON_BIN="$(command -v python3)"
  else
    echo "[backend] python3 not found"
    return 1
  fi

  if [ ! -x "$PYTHON_BIN" ]; then
    echo "[backend] python is not executable: $PYTHON_BIN"
    return 1
  fi
}

compose() {
  if have docker && docker compose version >/dev/null 2>&1; then
    docker compose "$@"
  elif have docker-compose; then
    docker-compose "$@"
  else
    echo "[docker] docker compose is not installed"
    return 127
  fi
}

ensure_docker() {
  if ! have docker; then
    echo "[docker] docker is not installed"
    return 1
  fi
  if docker info >/dev/null 2>&1; then
    return 0
  fi

  echo "[docker] Docker daemon is not running or current user cannot access it."
  echo "[docker] On Linux, try:"
  echo "  sudo systemctl start docker"
  echo "  sudo usermod -aG docker \$USER   # then log out and log back in"
  return 1
}

setup_backend() {
  select_python
  if [ ! -x "$VENV_DIR/bin/python" ]; then
    echo "[backend] creating virtualenv: $VENV_DIR"
    if ! "$PYTHON_BIN" -m venv --clear "$VENV_DIR"; then
      echo "[backend] python venv module unavailable, trying local virtualenv"
      if PYTHONUSERBASE="$PYTHON_USERBASE" "$PYTHON_BIN" -m virtualenv --clear "$VENV_DIR"; then
        :
      else
        echo "[backend] failed to create virtualenv"
        echo "[backend] Install python3-venv, or bootstrap virtualenv into $PYTHON_USERBASE."
        return 1
      fi
    fi
  fi
  PYTHON_BIN="$VENV_DIR/bin/python"

  local pip_index="${PIP_INDEX_URL:-https://pypi.tuna.tsinghua.edu.cn/simple}"
  local pip_cache="$ROOT_DIR/.local/pip-cache"
  echo "[backend] installing Python dependencies"
  PIP_CACHE_DIR="$pip_cache" "$PYTHON_BIN" -m pip install --upgrade pip setuptools wheel -i "$pip_index"
  PIP_CACHE_DIR="$pip_cache" "$PYTHON_BIN" -m pip install -r "$BACKEND_DIR/requirements.txt" -i "$pip_index"

  if truthy "$INSTALL_EMBEDDING_DEPS"; then
    echo "[backend] installing embedding dependencies"
    PIP_CACHE_DIR="$pip_cache" "$PYTHON_BIN" -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
    PIP_CACHE_DIR="$pip_cache" "$PYTHON_BIN" -m pip install -r "$BACKEND_DIR/requirements-embedding.txt" -i "$pip_index"
  fi
}

setup_frontend() {
  if ! have npm; then
    echo "[frontend] npm not found"
    return 1
  fi

  local npm_registry="${NPM_REGISTRY:-https://registry.npmmirror.com}"
  local npm_cache="$ROOT_DIR/.local/npm-cache"
  echo "[frontend] installing npm dependencies"
  if [ -f "$FRONTEND_DIR/package-lock.json" ]; then
    (cd "$FRONTEND_DIR" && npm ci --registry="$npm_registry" --cache "$npm_cache")
  else
    (cd "$FRONTEND_DIR" && npm install --registry="$npm_registry" --cache "$npm_cache")
  fi
}

setup_all() {
  load_env
  setup_backend
  setup_frontend
  echo "[setup] done"
}

check_backend_deps() {
  select_python
  if ! "$PYTHON_BIN" -c "import fastapi, uvicorn, psycopg2, dotenv, PIL, httpx, aiofiles, jwt, jieba, rank_bm25" >/dev/null 2>&1; then
    echo "[backend] Python dependencies are missing for $PYTHON_BIN"
    echo "[backend] Run: bash dev-local.sh setup"
    return 1
  fi

  if truthy "$EMBEDDING_ENABLED"; then
    if ! "$PYTHON_BIN" -c "import torch, sentence_transformers" >/dev/null 2>&1; then
      echo "[backend] embedding dependencies are missing"
      echo "[backend] Run: INSTALL_EMBEDDING_DEPS=1 bash dev-local.sh setup"
      return 1
    fi
  fi
}

check_frontend_deps() {
  if ! have npm; then
    echo "[frontend] npm not found. Install Node.js 22+ and npm."
    return 1
  fi
  if [ ! -x "$FRONTEND_DIR/node_modules/.bin/vite" ]; then
    echo "[frontend] node_modules missing"
    echo "[frontend] Run: bash dev-local.sh setup"
    return 1
  fi
}

pid_alive() {
  [ -f "$1" ] && kill -0 "$(cat "$1")" 2>/dev/null
}

db_reachable() {
  if [ "$DB_MODE" = "skip" ]; then
    return 0
  fi

  if have psql; then
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c '\q' >/dev/null 2>&1
    return $?
  fi

  if [ "$DB_MODE" = "docker" ] && have docker; then
    (cd "$ROOT_DIR" && compose exec -T db pg_isready -U "$DB_USER" -d "$DB_NAME") >/dev/null 2>&1
    return $?
  fi

  return 1
}

start_db() {
  case "$DB_MODE" in
    skip)
      echo "[db] skipped by DB_MODE=skip"
      return 0
      ;;
    local)
      if db_reachable; then
        echo "[db] local PostgreSQL ready at $DB_HOST:$DB_PORT/$DB_NAME"
        return 0
      fi
      echo "[db] local PostgreSQL is not reachable at $DB_HOST:$DB_PORT/$DB_NAME"
      echo "[db] Start PostgreSQL and create role/db, or use DB_MODE=docker."
      return 1
      ;;
    docker)
      if db_reachable; then
        echo "[db] docker PostgreSQL ready at $DB_HOST:$DB_PORT/$DB_NAME"
        return 0
      fi
      ensure_docker
      echo "[db] starting docker compose db service"
      (cd "$ROOT_DIR" && compose up -d db)
      printf "[db] waiting"
      for _ in $(seq 1 60); do
        if db_reachable; then
          echo " ready at $DB_HOST:$DB_PORT/$DB_NAME"
          return 0
        fi
        printf "."
        sleep 1
      done
      echo ""
      echo "[db] timeout. Check: docker compose logs db"
      return 1
      ;;
  esac
}

run_schema_sql() {
  if have psql; then
    PGPASSWORD="$DB_PASSWORD" psql -v ON_ERROR_STOP=1 -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$BACKEND_DIR/schema.sql"
    return $?
  fi

  if [ "$DB_MODE" = "docker" ]; then
    (cd "$ROOT_DIR" && compose exec -T db psql -v ON_ERROR_STOP=1 -U "$DB_USER" -d "$DB_NAME") < "$BACKEND_DIR/schema.sql"
    return $?
  fi

  echo "[db] psql client is required for DB_MODE=$DB_MODE"
  return 1
}

init_schema() {
  if [ "$DB_MODE" = "skip" ]; then
    echo "[db] schema skipped by DB_MODE=skip"
    return 0
  fi

  check_backend_deps
  echo "[db] applying schema and migrations"
  {
    echo "===== $(date '+%F %T') schema ====="
    run_schema_sql
    echo "===== migrate_auth.py ====="
    (cd "$BACKEND_DIR" && "$PYTHON_BIN" migrate_auth.py)
    echo "===== migrate_item_state.py ====="
    (cd "$BACKEND_DIR" && "$PYTHON_BIN" migrate_item_state.py)
    echo "===== migrate_flow_fields.py ====="
    (cd "$BACKEND_DIR" && "$PYTHON_BIN" migrate_flow_fields.py)
  } >>"$DB_INIT_LOG" 2>&1
  echo "[db] schema done, log=$DB_INIT_LOG"
  sync_support_knowledge
}

run_support_import() {
  local force="${1:-0}"
  local args=(--docs-dir "$SUPPORT_DOCS_DIR")
  if truthy "$force"; then
    args+=(--force)
  fi
  (cd "$BACKEND_DIR" && "$PYTHON_BIN" import_support_knowledge.py "${args[@]}")
}

sync_support_knowledge() {
  if ! truthy "$SUPPORT_AUTO_IMPORT"; then
    echo "[support] auto import skipped by SUPPORT_AUTO_IMPORT=$SUPPORT_AUTO_IMPORT"
    return 0
  fi
  if [ "$DB_MODE" = "skip" ]; then
    echo "[support] auto import skipped by DB_MODE=skip"
    return 0
  fi

  echo "[support] syncing knowledge from $SUPPORT_DOCS_DIR"
  {
    echo "===== $(date '+%F %T') support knowledge ====="
    run_support_import 0
  } >>"$DB_INIT_LOG" 2>&1
  echo "[support] knowledge synced, log=$DB_INIT_LOG"
}

import_support_knowledge() {
  load_env
  check_backend_deps
  if [ "$DB_MODE" != "skip" ]; then
    start_db
  fi
  echo "[support] importing knowledge from $SUPPORT_DOCS_DIR"
  run_support_import 1
}

start_backend() {
  if pid_alive "$BACKEND_PID"; then
    echo "[backend] already running pid=$(cat "$BACKEND_PID")"
    return 0
  fi

  check_backend_deps
  echo "[backend] starting http://$BACKEND_HOST:$BACKEND_PORT"
  local reload_args=()
  if truthy "$BACKEND_RELOAD"; then
    reload_args=(--reload)
  fi
  (
    cd "$BACKEND_DIR"
    nohup setsid env PYTHONUNBUFFERED=1 "$PYTHON_BIN" -m uvicorn app:app --host "$BACKEND_HOST" --port "$BACKEND_PORT" "${reload_args[@]}" \
      >"$BACKEND_LOG" 2>&1 < /dev/null &
    echo $! >"$BACKEND_PID"
  )
  echo "[backend] pid=$(cat "$BACKEND_PID") log=$BACKEND_LOG"
}

start_frontend() {
  if pid_alive "$FRONTEND_PID"; then
    echo "[frontend] already running pid=$(cat "$FRONTEND_PID")"
    return 0
  fi

  check_frontend_deps
  echo "[frontend] starting http://$FRONTEND_HOST:$FRONTEND_PORT"
  (
    cd "$FRONTEND_DIR"
    nohup setsid env VITE_PROXY_TARGET="$VITE_PROXY_TARGET" npm run dev -- --host "$FRONTEND_HOST" --port "$FRONTEND_PORT" \
      >"$FRONTEND_LOG" 2>&1 < /dev/null &
    echo $! >"$FRONTEND_PID"
  )
  echo "[frontend] pid=$(cat "$FRONTEND_PID") log=$FRONTEND_LOG"
}

kill_port() {
  local port="$1"
  if have fuser; then
    fuser -k "${port}/tcp" >/dev/null 2>&1 || true
  elif have lsof; then
    local pid
    for pid in $(lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true); do
      kill "$pid" 2>/dev/null || true
      sleep 1
      kill -9 "$pid" 2>/dev/null || true
    done
  fi
}

stop_one() {
  local name="$1"
  local pid_file="$2"

  if pid_alive "$pid_file"; then
    local pid
    pid="$(cat "$pid_file")"
    kill "$pid" 2>/dev/null || true
    sleep 1
    kill -9 "$pid" 2>/dev/null || true
    echo "[$name] stopped pid=$pid"
  fi
  rm -f "$pid_file"
}

stop_db() {
  if [ "$DB_MODE" != "docker" ]; then
    echo "[db] not stopping DB_MODE=$DB_MODE"
    return 0
  fi
  if ! have docker || ! docker info >/dev/null 2>&1; then
    echo "[db] docker unavailable, skip"
    return 0
  fi
  echo "[db] stopping docker compose db service"
  (cd "$ROOT_DIR" && compose stop db >/dev/null 2>&1 || true)
}

start_all() {
  load_env
  start_db
  init_schema
  start_backend
  start_frontend
  echo ""
  echo "Services:"
  echo "  frontend: http://$FRONTEND_HOST:$FRONTEND_PORT"
  echo "  backend:  http://$BACKEND_HOST:$BACKEND_PORT/docs"
  echo "  db:       $DB_MODE $DB_HOST:$DB_PORT/$DB_NAME"
  echo ""
  echo "Logs:"
  echo "  bash dev-local.sh logs"
  echo "  tail -f $BACKEND_LOG"
}

stop_all() {
  load_env
  stop_one frontend "$FRONTEND_PID"
  stop_one backend "$BACKEND_PID"
  kill_port "$FRONTEND_PORT"
  kill_port "$BACKEND_PORT"
  stop_db
}

restart_all() {
  stop_all
  sleep 1
  start_all
}

status() {
  load_env
  if db_reachable; then
    echo "[db] ok ($DB_MODE $DB_HOST:$DB_PORT/$DB_NAME)"
  else
    echo "[db] not reachable ($DB_MODE $DB_HOST:$DB_PORT/$DB_NAME)"
  fi

  if pid_alive "$BACKEND_PID"; then
    echo "[backend] ok pid=$(cat "$BACKEND_PID") :$BACKEND_PORT"
  else
    echo "[backend] stopped"
  fi

  if pid_alive "$FRONTEND_PID"; then
    echo "[frontend] ok pid=$(cat "$FRONTEND_PID") :$FRONTEND_PORT"
  else
    echo "[frontend] stopped"
  fi
}

logs() {
  echo "==================== db init ($DB_INIT_LOG) ===================="
  tail -80 "$DB_INIT_LOG" 2>/dev/null || echo "(empty)"
  echo ""
  echo "==================== backend ($BACKEND_LOG) ===================="
  tail -80 "$BACKEND_LOG" 2>/dev/null || echo "(empty)"
  echo ""
  echo "==================== frontend ($FRONTEND_LOG) ===================="
  tail -50 "$FRONTEND_LOG" 2>/dev/null || echo "(empty)"
}

case "${1:-start}" in
  setup) setup_all ;;
  start) start_all ;;
  stop) stop_all ;;
  restart) restart_all ;;
  status) status ;;
  logs) logs ;;
  db) load_env; start_db; init_schema ;;
  support-import) import_support_knowledge ;;
  help|-h|--help) usage ;;
  *) usage; exit 1 ;;
esac
