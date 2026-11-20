#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="$PROJECT_ROOT/src/db/docker/docker-compose.yml"
API_PID_FILE="$PROJECT_ROOT/.api.pid"
FRONTEND_PID_FILE="$PROJECT_ROOT/.frontend.pid"

function display_usage {
    echo -e "${YELLOW}Usage: $0 [command]${NC}"
    echo ""
    echo -e "${BLUE}Database commands:${NC}"
    echo -e "  ${GREEN}db:start${NC}    - Start the PostgreSQL container"
    echo -e "  ${GREEN}db:stop${NC}     - Stop the PostgreSQL container"
    echo -e "  ${GREEN}db:restart${NC}  - Restart the PostgreSQL container"
    echo -e "  ${GREEN}db:status${NC}   - Check container status"
    echo -e "  ${GREEN}db:logs${NC}     - Show container logs"
    echo -e "  ${GREEN}db:psql${NC}     - Open psql shell"
    echo -e "  ${GREEN}db:build${NC}    - Build the PostgreSQL container image"
    echo -e "  ${GREEN}db:clean${NC}    - Remove container and volumes (destructive)"
    echo -e "  ${GREEN}db:migrate${NC}  - Run Alembic migrations"
    echo ""
    echo -e "${BLUE}API commands:${NC}"
    echo -e "  ${GREEN}api:start${NC}   - Start the FastAPI server (background)"
    echo -e "  ${GREEN}api:stop${NC}    - Stop the FastAPI server"
    echo -e "  ${GREEN}api:restart${NC} - Restart the FastAPI server"
    echo -e "  ${GREEN}api:logs${NC}    - Tail API server log"
    echo -e "  ${GREEN}api:test${NC}    - Run API pytest suite"
    echo ""
    echo -e "${BLUE}Frontend commands:${NC}"
    echo -e "  ${GREEN}fe:start${NC}    - Start the frontend dev server (background)"
    echo -e "  ${GREEN}fe:stop${NC}     - Stop the frontend dev server"
    echo -e "  ${GREEN}fe:restart${NC}  - Restart the frontend dev server"
    echo -e "  ${GREEN}fe:test${NC}     - Run frontend test suite"
    echo -e "  ${GREEN}fe:build${NC}    - Build frontend for production"
    echo ""
    echo -e "${BLUE}Stack commands:${NC}"
    echo -e "  ${GREEN}start${NC}       - Start entire stack (db + api + frontend)"
    echo -e "  ${GREEN}stop${NC}        - Stop entire stack"
    echo -e "  ${GREEN}restart${NC}     - Restart entire stack"
    echo -e "  ${GREEN}status${NC}      - Show status of all components"
    echo -e "  ${GREEN}test${NC}        - Run all test suites"
}

# --- Prerequisite checks ---

if ! command -v podman &> /dev/null; then
    echo -e "${RED}Error: podman is not installed.${NC}"
    exit 1
fi

# --- DB functions ---

function db_start {
    echo -e "${YELLOW}Starting PostgreSQL container...${NC}"
    podman-compose -f "$COMPOSE_FILE" up -d postgres
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}PostgreSQL started.${NC}"
    else
        echo -e "${RED}Failed to start PostgreSQL.${NC}"; exit 1
    fi
}

function db_stop {
    echo -e "${YELLOW}Stopping PostgreSQL container...${NC}"
    podman-compose -f "$COMPOSE_FILE" down
    echo -e "${GREEN}PostgreSQL stopped.${NC}"
}

function db_restart {
    db_stop
    db_start
}

function db_status {
    podman ps -a --filter "name=instructor_db"
}

function db_logs {
    podman logs -f instructor_db
}

function db_psql {
    podman exec -it instructor_db psql -U postgres -d instructor_db
}

function db_build {
    echo -e "${YELLOW}Building PostgreSQL container image...${NC}"
    podman-compose -f "$COMPOSE_FILE" build postgres
}

function db_clean {
    echo -e "${RED}Removing PostgreSQL container and volumes...${NC}"
    podman-compose -f "$COMPOSE_FILE" down -v
    echo -e "${GREEN}Done.${NC}"
}

function db_migrate {
    echo -e "${YELLOW}Running Alembic migrations...${NC}"
    cd "$PROJECT_ROOT"
    conda run -n instructor_assignments alembic -c src/db/alembic.ini upgrade head
}

# --- API functions ---

API_LOG="$PROJECT_ROOT/.api.log"

function api_start {
    if [ -f "$API_PID_FILE" ] && kill -0 "$(cat "$API_PID_FILE")" 2>/dev/null; then
        echo -e "${YELLOW}API server already running (PID $(cat "$API_PID_FILE")).${NC}"
        return
    fi
    echo -e "${YELLOW}Starting API server...${NC}"
    cd "$PROJECT_ROOT"
    conda run -n instructor_assignments uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload \
        > "$API_LOG" 2>&1 &
    echo $! > "$API_PID_FILE"
    echo -e "${GREEN}API server started (PID $(cat "$API_PID_FILE")). Log: $API_LOG${NC}"
}

function api_stop {
    if [ -f "$API_PID_FILE" ]; then
        PID=$(cat "$API_PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo -e "${YELLOW}Stopping API server (PID $PID)...${NC}"
            kill "$PID"
        fi
        rm -f "$API_PID_FILE"
        echo -e "${GREEN}API server stopped.${NC}"
    else
        echo -e "${YELLOW}API server not running.${NC}"
    fi
}

function api_restart {
    api_stop
    api_start
}

function api_logs {
    if [ -f "$API_LOG" ]; then
        tail -f "$API_LOG"
    else
        echo -e "${RED}No API log found.${NC}"
    fi
}

function api_test {
    echo -e "${YELLOW}Running API tests...${NC}"
    cd "$PROJECT_ROOT"
    conda run -n instructor_assignments pytest src/api/tests/ -v
}

# --- Frontend functions ---

FE_LOG="$PROJECT_ROOT/.frontend.log"

function fe_start {
    if [ -f "$FRONTEND_PID_FILE" ] && kill -0 "$(cat "$FRONTEND_PID_FILE")" 2>/dev/null; then
        echo -e "${YELLOW}Frontend dev server already running (PID $(cat "$FRONTEND_PID_FILE")).${NC}"
        return
    fi
    echo -e "${YELLOW}Starting frontend dev server...${NC}"
    cd "$PROJECT_ROOT/src/frontend"
    npm run dev > "$FE_LOG" 2>&1 &
    echo $! > "$FRONTEND_PID_FILE"
    echo -e "${GREEN}Frontend started (PID $(cat "$FRONTEND_PID_FILE")). Log: $FE_LOG${NC}"
}

function fe_stop {
    if [ -f "$FRONTEND_PID_FILE" ]; then
        PID=$(cat "$FRONTEND_PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo -e "${YELLOW}Stopping frontend (PID $PID)...${NC}"
            kill "$PID"
        fi
        rm -f "$FRONTEND_PID_FILE"
        echo -e "${GREEN}Frontend stopped.${NC}"
    else
        echo -e "${YELLOW}Frontend not running.${NC}"
    fi
}

function fe_restart {
    fe_stop
    fe_start
}

function fe_test {
    echo -e "${YELLOW}Running frontend tests...${NC}"
    cd "$PROJECT_ROOT/src/frontend"
    npm test -- --run
}

function fe_build {
    echo -e "${YELLOW}Building frontend for production...${NC}"
    cd "$PROJECT_ROOT/src/frontend"
    npm run build
}

# --- DB tests ---

function db_test {
    echo -e "${YELLOW}Running DB tests...${NC}"
    cd "$PROJECT_ROOT"
    conda run -n instructor_assignments pytest src/db/tests/ -v
}

# --- Stack functions ---

function stack_start {
    db_start
    sleep 2
    api_start
    fe_start
}

function stack_stop {
    fe_stop
    api_stop
    db_stop
}

function stack_restart {
    stack_stop
    stack_start
}

function stack_status {
    echo -e "${BLUE}=== PostgreSQL ===${NC}"
    db_status
    echo ""
    echo -e "${BLUE}=== API Server ===${NC}"
    if [ -f "$API_PID_FILE" ] && kill -0 "$(cat "$API_PID_FILE")" 2>/dev/null; then
        echo -e "${GREEN}Running (PID $(cat "$API_PID_FILE"))${NC}"
    else
        echo -e "${RED}Not running${NC}"
    fi
    echo ""
    echo -e "${BLUE}=== Frontend ===${NC}"
    if [ -f "$FRONTEND_PID_FILE" ] && kill -0 "$(cat "$FRONTEND_PID_FILE")" 2>/dev/null; then
        echo -e "${GREEN}Running (PID $(cat "$FRONTEND_PID_FILE"))${NC}"
    else
        echo -e "${RED}Not running${NC}"
    fi
}

function stack_test {
    db_test
    api_test
    fe_test
}

# --- Dispatch ---

if [ $# -eq 0 ]; then
    display_usage
    exit 1
fi

case "$1" in
    # DB
    db:start)   db_start ;;
    db:stop)    db_stop ;;
    db:restart) db_restart ;;
    db:status)  db_status ;;
    db:logs)    db_logs ;;
    db:psql)    db_psql ;;
    db:build)   db_build ;;
    db:clean)   db_clean ;;
    db:migrate) db_migrate ;;
    db:test)    db_test ;;
    # API
    api:start)   api_start ;;
    api:stop)    api_stop ;;
    api:restart) api_restart ;;
    api:logs)    api_logs ;;
    api:test)    api_test ;;
    # Frontend
    fe:start)   fe_start ;;
    fe:stop)    fe_stop ;;
    fe:restart) fe_restart ;;
    fe:test)    fe_test ;;
    fe:build)   fe_build ;;
    # Stack
    start)   stack_start ;;
    stop)    stack_stop ;;
    restart) stack_restart ;;
    status)  stack_status ;;
    test)    stack_test ;;
    *)
        echo -e "${RED}Unknown command: '$1'${NC}"
        display_usage
        exit 1
        ;;
esac

exit 0
