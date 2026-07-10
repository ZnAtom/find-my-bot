#!/usr/bin/env bash
# sudo systemctl start postgresql
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
RUN_DIR="${RUN_DIR:-/tmp/foundit}"

BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
BACKEND_HOST="${BACKEND_HOST:-0.0.0.0}"
FRONTEND_HOST="${FRONTEND_HOST:-0.0.0.0}"

BACKEND_LOG="${BACKEND_LOG:-/tmp/foundit-backend.log}"
FRONTEND_LOG="${FRONTEND_LOG:-/tmp/foundit-frontend.log}"
BACKEND_PID_FILE="$RUN_DIR/backend.pid"
FRONTEND_PID_FILE="$RUN_DIR/frontend.pid"
KILL_STALE_PORTS="${KILL_STALE_PORTS:-1}"
REQUIRE_DB="${REQUIRE_DB:-1}"

mkdir -p "$RUN_DIR"

load_env() {
  if [ -f "$ROOT_DIR/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    source "$ROOT_DIR/.env"
    set +a
  fi

  export HF_LOCAL_ONLY="${HF_LOCAL_ONLY:-1}"
  export HF_HUB_OFFLINE="${HF_HUB_OFFLINE:-1}"
  export HF_ENDPOINT="${HF_ENDPOINT:-https://hf-mirror.com}"
  export VITE_PROXY_TARGET="${VITE_PROXY_TARGET:-http://127.0.0.1:$BACKEND_PORT}"
}

pid_alive() {
  local pid="${1:-}"
  [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null
}

pid_from_file() {
  local file="$1"
  [ -f "$file" ] && tr -d '[:space:]' < "$file" || true
}

port_pids() {
  local port="$1"
  if command -v lsof >/dev/null 2>&1; then
    lsof -ti:"$port" 2>/dev/null || true
  else
    true
  fi
}

stop_pid_file() {
  local name="$1"
  local file="$2"
  local pid
  pid="$(pid_from_file "$file")"
  if pid_alive "$pid"; then
    kill "$pid" 2>/dev/null || true
    sleep 1
    if pid_alive "$pid"; then
      kill -9 "$pid" 2>/dev/null || true
    fi
    echo "[$name] stopped pid=$pid"
  fi
  rm -f "$file"
}

stop_port() {
  local name="$1"
  local port="$2"
  local pids
  pids="$(port_pids "$port")"
  if [ -n "$pids" ]; then
    kill $pids 2>/dev/null || true
    sleep 1
    local remaining
    remaining="$(port_pids "$port")"
    if [ -n "$remaining" ]; then
      kill -9 $remaining 2>/dev/null || true
      sleep 1
    fi
    echo "[$name] released port :$port"
  fi
}

check_database() {
  local db_host="${DB_HOST:-127.0.0.1}"
  local db_port="${DB_PORT:-5432}"
  local db_user="${DB_USER:-appuser}"
  local db_name="${DB_NAME:-lostfound}"

  if command -v pg_isready >/dev/null 2>&1; then
    if PGPASSWORD="${DB_PASSWORD:-password}" pg_isready -h "$db_host" -p "$db_port" -U "$db_user" -d "$db_name" >/dev/null 2>&1; then
      echo "[db] ready at $db_host:$db_port/$db_name"
      return 0
    fi
  elif command -v nc >/dev/null 2>&1; then
    if nc -z "$db_host" "$db_port" >/dev/null 2>&1; then
      echo "[db] port open at $db_host:$db_port"
      return 0
    fi
  fi

  echo "[db] not ready at $db_host:$db_port/$db_name"
  return 1
}

start_database() {
  load_env
  local db_host="${DB_HOST:-127.0.0.1}"
  local db_port="${DB_PORT:-5432}"

  # 已经可用就不动
  if check_database; then
    return 0
  fi

  # 尝试启动 Docker PostgreSQL（仅本地开发）
  local container_name="foundit-pg"
  if command -v docker >/dev/null 2>&1; then
    if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^${container_name}$"; then
      echo "[db] Docker container $container_name is running but not reachable at $db_host:$db_port"
      echo "[db] check DB_HOST/DB_PORT in .env — container exposes 5432 internally"
    elif docker ps -a --format '{{.Names}}' 2>/dev/null | grep -q "^${container_name}$"; then
      echo "[db] starting existing Docker container $container_name ..."
      docker start "$container_name" >/dev/null
      sleep 3
    else
      echo "[db] creating Docker PostgreSQL container on port $db_port ..."
      docker rm -f "$container_name" 2>/dev/null || true
      docker run -d --name "$container_name" \
        -e POSTGRES_USER="${DB_USER:-appuser}" \
        -e POSTGRES_PASSWORD="${DB_PASSWORD:-password}" \
        -e POSTGRES_DB="${DB_NAME:-lostfound}" \
        -p "127.0.0.1:${db_port}:5432" \
        finging-db:latest >/dev/null 2>&1 || {
          echo "[db] no finging-db image, trying postgres:16 ..."
          docker run -d --name "$container_name" \
            -e POSTGRES_USER="${DB_USER:-appuser}" \
            -e POSTGRES_PASSWORD="${DB_PASSWORD:-password}" \
            -e POSTGRES_DB="${DB_NAME:-lostfound}" \
            -p "127.0.0.1:${db_port}:5432" \
            postgres:16 >/dev/null 2>&1
        }
    fi

    # 等待就绪
    echo "[db] waiting for PostgreSQL to be ready ..."
    local i
    for i in $(seq 1 15); do
      if check_database; then
        return 0
      fi
      sleep 1
    done
    echo "[db] still not ready after 15s"
    return 1
  fi

  echo "[db] start your local PostgreSQL/pgvector first, or adjust DB_HOST/DB_PORT in .env"
  return 1
}

init_db() {
  load_env
  local db_host="${DB_HOST:-127.0.0.1}"
  local db_port="${DB_PORT:-5432}"
  local db_user="${DB_USER:-appuser}"
  local db_name="${DB_NAME:-lostfound}"

  if ! command -v psql >/dev/null 2>&1; then
    echo "[db] psql not found, skip schema init"
    return 0
  fi

  if ! check_database; then
    return 1
  fi

  echo "[db] applying schema.sql"
  PGPASSWORD="${DB_PASSWORD:-password}" psql -h "$db_host" -p "$db_port" -U "$db_user" -d "$db_name" -f "$BACKEND_DIR/schema.sql" >/dev/null

  if [ -f "$BACKEND_DIR/venv/bin/activate" ]; then
    echo "[db] running migrate_auth.py"
    (
      cd "$BACKEND_DIR"
      # shellcheck disable=SC1091
      source venv/bin/activate
      python migrate_auth.py
    )
  fi
}

start_backend() {
  load_env
  if [ ! -f "$BACKEND_DIR/venv/bin/activate" ]; then
    echo "[backend] missing venv: $BACKEND_DIR/venv"
    echo "[backend] create it first, then install requirements.txt"
    return 1
  fi

  local pid
  pid="$(pid_from_file "$BACKEND_PID_FILE")"
  if pid_alive "$pid"; then
    echo "[backend] already running pid=$pid"
    return 0
  fi

  if [ -n "$(port_pids "$BACKEND_PORT")" ]; then
    if [ "$KILL_STALE_PORTS" = "1" ]; then
      echo "[backend] port :$BACKEND_PORT is occupied, releasing stale process"
      stop_port backend "$BACKEND_PORT"
    else
      echo "[backend] port :$BACKEND_PORT is occupied. Use './start.sh restart' or './start.sh stop' first."
      return 1
    fi
  fi

  echo "[backend] starting on http://127.0.0.1:$BACKEND_PORT"
  (
    cd "$BACKEND_DIR"
    # shellcheck disable=SC1091
    source venv/bin/activate
    nohup uvicorn app:app --host "$BACKEND_HOST" --port "$BACKEND_PORT" > "$BACKEND_LOG" 2>&1 &
    echo $! > "$BACKEND_PID_FILE"
  )
  echo "[backend] pid=$(cat "$BACKEND_PID_FILE") log=$BACKEND_LOG"
}

start_frontend() {
  load_env
  if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    echo "[frontend] missing node_modules. Run: cd $FRONTEND_DIR && npm install"
    return 1
  fi

  local pid
  pid="$(pid_from_file "$FRONTEND_PID_FILE")"
  if pid_alive "$pid"; then
    echo "[frontend] already running pid=$pid"
    return 0
  fi

  if [ -n "$(port_pids "$FRONTEND_PORT")" ]; then
    if [ "$KILL_STALE_PORTS" = "1" ]; then
      echo "[frontend] port :$FRONTEND_PORT is occupied, releasing stale process"
      stop_port frontend "$FRONTEND_PORT"
    else
      echo "[frontend] port :$FRONTEND_PORT is occupied. Use './start.sh restart' or './start.sh stop' first."
      return 1
    fi
  fi

  echo "[frontend] starting on http://127.0.0.1:$FRONTEND_PORT"
  (
    cd "$FRONTEND_DIR"
    nohup npm run dev -- --host "$FRONTEND_HOST" --port "$FRONTEND_PORT" > "$FRONTEND_LOG" 2>&1 &
    echo $! > "$FRONTEND_PID_FILE"
  )
  echo "[frontend] pid=$(cat "$FRONTEND_PID_FILE") log=$FRONTEND_LOG"
}

wait_http() {
  local name="$1"
  local url="$2"
  local seconds="${3:-20}"
  local i
  for i in $(seq 1 "$seconds"); do
    if curl -s "$url" >/dev/null 2>&1; then
      echo "[$name] ready: $url"
      return 0
    fi
    sleep 1
  done
  echo "[$name] not ready after ${seconds}s: $url"
  return 1
}

smoke() {
  echo "=== /api/me (without browser cookie, 401 is expected) ==="
  curl -s "http://127.0.0.1:$BACKEND_PORT/api/me" || true
  echo ""
  echo "=== /api/me/items (without browser cookie, 401 is expected) ==="
  curl -s "http://127.0.0.1:$BACKEND_PORT/api/me/items" || true
  echo ""
  echo "=== backend log tail ==="
  tail -8 "$BACKEND_LOG" 2>/dev/null || true
}

start_all() {
  load_env
  if ! start_database; then
    if [ "$REQUIRE_DB" = "1" ]; then
      echo "[start] database is required. Fix DB_HOST/DB_PORT or start PostgreSQL, then rerun ./start.sh"
      echo "[start] to start without database for static frontend/debug only: REQUIRE_DB=0 ./start.sh"
      exit 1
    fi
    echo "[start] continuing without database because REQUIRE_DB=0"
  else
    init_db
  fi
  start_backend
  start_frontend
  wait_http backend "http://127.0.0.1:$BACKEND_PORT/docs" 30 || true
  wait_http frontend "http://127.0.0.1:$FRONTEND_PORT" 30 || true
  echo ""
  echo "=== started ==="
  echo "frontend: http://127.0.0.1:$FRONTEND_PORT"
  echo "backend:  http://127.0.0.1:$BACKEND_PORT"
  echo "docs:     http://127.0.0.1:$BACKEND_PORT/docs"
  echo ""
  smoke
}

stop_all() {
  stop_pid_file frontend "$FRONTEND_PID_FILE"
  stop_pid_file backend "$BACKEND_PID_FILE"
  stop_port frontend "$FRONTEND_PORT"
  stop_port backend "$BACKEND_PORT"
}

status() {
  local backend_pid frontend_pid
  local backend_port_pids frontend_port_pids
  backend_pid="$(pid_from_file "$BACKEND_PID_FILE")"
  frontend_pid="$(pid_from_file "$FRONTEND_PID_FILE")"
  backend_port_pids="$(port_pids "$BACKEND_PORT")"
  frontend_port_pids="$(port_pids "$FRONTEND_PORT")"
  if pid_alive "$backend_pid"; then
    echo "[backend] running pid=$backend_pid http://127.0.0.1:$BACKEND_PORT"
  elif [ -n "$backend_port_pids" ]; then
    echo "[backend] stopped by script, but port :$BACKEND_PORT is occupied by pid(s): $backend_port_pids"
  else
    echo "[backend] stopped"
  fi
  if pid_alive "$frontend_pid"; then
    echo "[frontend] running pid=$frontend_pid http://127.0.0.1:$FRONTEND_PORT"
  elif [ -n "$frontend_port_pids" ]; then
    echo "[frontend] stopped by script, but port :$FRONTEND_PORT is occupied by pid(s): $frontend_port_pids"
  else
    echo "[frontend] stopped"
  fi
}

logs() {
  echo "=== backend: $BACKEND_LOG ==="
  tail -40 "$BACKEND_LOG" 2>/dev/null || true
  echo ""
  echo "=== frontend: $FRONTEND_LOG ==="
  tail -40 "$FRONTEND_LOG" 2>/dev/null || true
}

usage() {
  echo "Usage: $0 {start|stop|restart|status|logs|smoke|init-db}"
}

case "${1:-start}" in
  start)
    start_all
    ;;
  stop)
    stop_all
    ;;
  restart)
    stop_all
    sleep 2
    start_all
    ;;
  status)
    status
    ;;
  logs)
    logs
    ;;
  smoke)
    load_env
    smoke
    ;;
  init-db)
    init_db
    ;;
  *)
    usage
    exit 1
    ;;
esac
