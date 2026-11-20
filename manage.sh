#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_PID_FILE="$PROJECT_ROOT/.api.pid"
FRONTEND_PID_FILE="$PROJECT_ROOT/.frontend.pid"

EMULATOR_CONTAINER="aws-emulator"
EMULATOR_PORT="9297"
TF_DIR="$PROJECT_ROOT"

# Postgres sidecar — the AWS emulator provides RDS API emulation only (no real
# PostgreSQL wire endpoint). A postgres:16 container acts as the data layer.
# Port 5432 is taken by podman's gvproxy on macOS, so we use 5433.
PG_CONTAINER="instructor_postgres"
PG_PORT="5433"
PG_IMAGE="docker.io/library/postgres:16"

function display_usage {
    echo -e "${YELLOW}Usage: $0 [command]${NC}"
    echo ""
    echo -e "${BLUE}Emulator commands:${NC}"
    echo -e "  ${GREEN}emulator:build${NC}   - Build the AWS emulator container image"
    echo -e "  ${GREEN}emulator:start${NC}   - Start the AWS emulator container"
    echo -e "  ${GREEN}emulator:stop${NC}    - Stop the AWS emulator container"
    echo -e "  ${GREEN}emulator:status${NC}  - Show emulator container status"
    echo -e "  ${GREEN}emulator:login${NC}   - Run aws login against the emulator"
    echo ""
    echo -e "${BLUE}Infrastructure commands:${NC}"
    echo -e "  ${GREEN}infra:init${NC}       - Initialize Terraform"
    echo -e "  ${GREEN}infra:up${NC}         - Apply Terraform (provision all AWS resources)"
    echo -e "  ${GREEN}infra:down${NC}       - Destroy all Terraform-managed resources"
    echo -e "  ${GREEN}infra:status${NC}     - Show current Terraform state"
    echo -e "  ${GREEN}infra:output${NC}     - Show Terraform outputs"
    echo ""
    echo -e "${BLUE}Database commands:${NC}"
    echo -e "  ${GREEN}db:init${NC}          - Create instructor_test_db on RDS"
    echo -e "  ${GREEN}db:migrate${NC}       - Run Alembic migrations against RDS"
    echo ""
    echo -e "${BLUE}API commands:${NC}"
    echo -e "  ${GREEN}api:build${NC}        - Build the API Docker image"
    echo -e "  ${GREEN}api:push${NC}         - Push the API image to ECR"
    echo -e "  ${GREEN}api:start${NC}        - Start the FastAPI server locally (background)"
    echo -e "  ${GREEN}api:stop${NC}         - Stop the FastAPI server"
    echo -e "  ${GREEN}api:restart${NC}      - Restart the FastAPI server"
    echo -e "  ${GREEN}api:logs${NC}         - Tail API server log"
    echo -e "  ${GREEN}api:test${NC}         - Run API pytest suite against RDS"
    echo ""
    echo -e "${BLUE}Frontend commands:${NC}"
    echo -e "  ${GREEN}fe:start${NC}         - Start the frontend dev server (background)"
    echo -e "  ${GREEN}fe:stop${NC}          - Stop the frontend dev server"
    echo -e "  ${GREEN}fe:restart${NC}       - Restart the frontend dev server"
    echo -e "  ${GREEN}fe:test${NC}          - Run frontend test suite"
    echo -e "  ${GREEN}fe:build${NC}         - Build frontend for production"
    echo -e "  ${GREEN}fe:deploy${NC}        - Build and deploy frontend to S3/CloudFront"
    echo ""
    echo -e "${BLUE}Stack commands:${NC}"
    echo -e "  ${GREEN}start${NC}            - Start entire stack (emulator + infra + db + api + frontend)"
    echo -e "  ${GREEN}stop${NC}             - Stop entire stack"
    echo -e "  ${GREEN}restart${NC}          - Restart entire stack"
    echo -e "  ${GREEN}status${NC}           - Show status of all components"
    echo -e "  ${GREEN}test${NC}             - Run all test suites"
}

# --- Prerequisite checks ---

if ! command -v podman &> /dev/null; then
    echo -e "${RED}Error: podman is not installed.${NC}"
    exit 1
fi

# --- Emulator functions ---

function emulator_build {
    echo -e "${YELLOW}Building AWS emulator container image...${NC}"
    podman build -t aws-emulator "$PROJECT_ROOT"
}

function emulator_start {
    # Postgres sidecar (real PostgreSQL — emulator RDS is API-only)
    echo -e "${YELLOW}Starting postgres sidecar on port ${PG_PORT}...${NC}"
    podman rm -f "$PG_CONTAINER" 2>/dev/null || true
    local pg_pass="${TF_VAR_db_password:-instructor_pass_local}"
    podman run -d --name "$PG_CONTAINER" \
        -e POSTGRES_USER=postgres \
        -e POSTGRES_PASSWORD="$pg_pass" \
        -e POSTGRES_DB=instructor_db \
        -p "127.0.0.1:${PG_PORT}:5432" \
        "$PG_IMAGE"

    # AWS emulator
    echo -e "${YELLOW}Starting AWS emulator on port ${EMULATOR_PORT}...${NC}"
    podman rm -f "$EMULATOR_CONTAINER" 2>/dev/null || true
    mkdir -p "$HOME/.aws/emulator"
    podman run -d --name "$EMULATOR_CONTAINER" \
        --memory=2g --memory-swap=2g \
        -p "127.0.0.1:${EMULATOR_PORT}:${EMULATOR_PORT}" \
        -e HOME="$HOME" \
        -v "$HOME/.aws/emulator:$HOME/.aws/emulator" \
        aws-emulator -p "${EMULATOR_PORT}"

    echo -e "${YELLOW}Waiting for services to be ready...${NC}"
    sleep 5
    echo -e "${GREEN}Emulator ready. Source localENV, then run: aws login${NC}"
}

function emulator_stop {
    echo -e "${YELLOW}Stopping AWS emulator...${NC}"
    podman stop "$EMULATOR_CONTAINER" 2>/dev/null; podman rm "$EMULATOR_CONTAINER" 2>/dev/null || true
    echo -e "${YELLOW}Stopping postgres sidecar...${NC}"
    podman stop "$PG_CONTAINER" 2>/dev/null; podman rm "$PG_CONTAINER" 2>/dev/null || true
    echo -e "${GREEN}All containers stopped.${NC}"
}

function emulator_status {
    podman ps --filter "name=$EMULATOR_CONTAINER"
}

function emulator_login {
    source "$PROJECT_ROOT/localENV" && aws login
}

# --- Infra functions ---

function infra_init {
    source "$PROJECT_ROOT/localENV"
    cd "$TF_DIR"
    tofu init
}

function infra_up {
    source "$PROJECT_ROOT/localENV"
    cd "$TF_DIR"
    tofu apply -auto-approve \
        -var="db_password=${TF_VAR_db_password:-instructor_pass_local}" \
        -var="jwt_secret_key=${TF_VAR_jwt_secret_key:-change-me-in-production}"
}

function infra_down {
    source "$PROJECT_ROOT/localENV"
    cd "$TF_DIR"
    tofu destroy -auto-approve
}

function infra_status {
    source "$PROJECT_ROOT/localENV"
    cd "$TF_DIR"
    tofu show
}

function infra_output {
    source "$PROJECT_ROOT/localENV"
    cd "$TF_DIR"
    tofu output
}

# --- DB URL helpers ---

function get_rds_db_url {
    local pg_pass="${TF_VAR_db_password:-instructor_pass_local}"
    echo "postgresql+psycopg2://postgres:${pg_pass}@127.0.0.1:${PG_PORT}/instructor_db"
}

function get_rds_test_url {
    local pg_pass="${TF_VAR_db_password:-instructor_pass_local}"
    echo "postgresql+psycopg2://postgres:${pg_pass}@127.0.0.1:${PG_PORT}/instructor_test_db"
}

# --- DB functions ---

function db_migrate {
    local db_url
    db_url="$(get_rds_db_url)"
    echo -e "${YELLOW}Running Alembic migrations against postgres sidecar...${NC}"
    cd "$PROJECT_ROOT"
    conda run -n instructor_assignments \
        env DATABASE_URL="$db_url" \
        alembic -c src/db/alembic.ini upgrade head
}

function db_init {
    local base_url
    base_url="$(get_rds_db_url)"
    base_url="${base_url/instructor_db/postgres}"
    echo -e "${YELLOW}Creating instructor_test_db on postgres sidecar...${NC}"
    conda run -n instructor_assignments python -c "
import sqlalchemy, time
for attempt in range(10):
    try:
        engine = sqlalchemy.create_engine('${base_url}', isolation_level='AUTOCOMMIT')
        with engine.connect() as c:
            try:
                c.execute(sqlalchemy.text('CREATE DATABASE instructor_test_db'))
                print('Created instructor_test_db')
            except Exception as e:
                print('instructor_test_db already exists' if 'already exists' in str(e) else f'Error: {e}')
        engine.dispose()
        break
    except Exception:
        print(f'Waiting for postgres... (attempt {attempt+1})')
        time.sleep(2)
" 2>&1
    echo -e "${GREEN}Done.${NC}"
}

# --- API functions ---

API_LOG="$PROJECT_ROOT/.api.log"

function api_build {
    echo -e "${YELLOW}Building API Docker image...${NC}"
    podman build -f src/api/Dockerfile -t instructor-api:latest "$PROJECT_ROOT"
}

function api_push {
    source "$PROJECT_ROOT/localENV"
    cd "$TF_DIR"
    ECR_URL=$(tofu output -raw ecr_repository_url 2>/dev/null)
    if [ -z "$ECR_URL" ]; then
        echo -e "${RED}ECR URL not found. Run infra:up first.${NC}"; exit 1
    fi
    echo -e "${YELLOW}Pushing API image to ECR...${NC}"
    aws ecr get-login-password | podman login --username AWS --password-stdin "$ECR_URL"
    podman tag instructor-api:latest "${ECR_URL}:latest"
    podman push "${ECR_URL}:latest"
}

function api_start {
    if [ -f "$API_PID_FILE" ] && kill -0 "$(cat "$API_PID_FILE")" 2>/dev/null; then
        echo -e "${YELLOW}API server already running (PID $(cat "$API_PID_FILE")).${NC}"
        return
    fi
    DB_URL=$(get_rds_db_url)
    echo -e "${YELLOW}Starting API server...${NC}"
    cd "$PROJECT_ROOT"
    conda run -n instructor_assignments \
        env DATABASE_URL="${DB_URL}" \
        uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload \
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
    DB_URL=$(get_rds_db_url)
    TEST_URL=$(get_rds_test_url)
    echo -e "${YELLOW}Running API tests against RDS...${NC}"
    cd "$PROJECT_ROOT"
    conda run -n instructor_assignments \
        env DATABASE_URL="$DB_URL" TEST_DATABASE_URL="$TEST_URL" \
        pytest src/api/tests/ -v
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

function fe_deploy {
    source "$PROJECT_ROOT/localENV"
    cd "$TF_DIR"
    BUCKET=$(tofu output -raw frontend_bucket 2>/dev/null)
    CF_ID=$(tofu output -raw cloudfront_distribution_id 2>/dev/null)
    if [ -z "$BUCKET" ]; then
        echo -e "${RED}Frontend bucket not found. Run infra:up first.${NC}"; exit 1
    fi
    echo -e "${YELLOW}Building frontend...${NC}"
    cd "$PROJECT_ROOT/src/frontend"
    npm run build
    echo -e "${YELLOW}Syncing to S3...${NC}"
    aws s3 sync dist/ "s3://$BUCKET/" --delete
    if [ -n "$CF_ID" ]; then
        echo -e "${YELLOW}Invalidating CloudFront cache...${NC}"
        aws cloudfront create-invalidation --distribution-id "$CF_ID" --paths "/*"
    fi
    echo -e "${GREEN}Frontend deployed.${NC}"
}

# --- DB tests ---

function db_test {
    echo -e "${YELLOW}Running DB tests...${NC}"
    cd "$PROJECT_ROOT"
    conda run -n instructor_assignments pytest src/db/tests/ -v
}

# --- Stack functions ---

function stack_start {
    emulator_start
    sleep 5
    infra_up
    db_init
    db_migrate
    api_start
    fe_start
}

function stack_stop {
    fe_stop
    api_stop
    infra_down
    emulator_stop
}

function stack_restart {
    stack_stop
    stack_start
}

function stack_status {
    echo -e "${BLUE}=== AWS Emulator ===${NC}"
    emulator_status
    echo ""
    echo -e "${BLUE}=== Infrastructure ===${NC}"
    infra_output
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
    # Emulator
    emulator:build)  emulator_build ;;
    emulator:start)  emulator_start ;;
    emulator:stop)   emulator_stop ;;
    emulator:status) emulator_status ;;
    emulator:login)  emulator_login ;;
    # Infra
    infra:init)   infra_init ;;
    infra:up)     infra_up ;;
    infra:down)   infra_down ;;
    infra:status) infra_status ;;
    infra:output) infra_output ;;
    # DB
    db:init)    db_init ;;
    db:migrate) db_migrate ;;
    db:test)    db_test ;;
    # API
    api:build)   api_build ;;
    api:push)    api_push ;;
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
    fe:deploy)  fe_deploy ;;
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
