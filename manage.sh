#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Function to display usage
function display_usage {
    echo -e "${YELLOW}Usage: $0 [command]${NC}"
    echo -e "Commands:"
    echo -e "  ${GREEN}start${NC}     - Start the database container"
    echo -e "  ${GREEN}stop${NC}      - Stop the database container"
    echo -e "  ${GREEN}restart${NC}   - Restart the database container"
    echo -e "  ${GREEN}status${NC}    - Check the status of the database container"
    echo -e "  ${GREEN}logs${NC}      - Show logs from the database container"
    echo -e "  ${GREEN}psql${NC}      - Connect to PostgreSQL using psql"
    echo -e "  ${GREEN}build${NC}     - Build the database container"
    echo -e "  ${GREEN}clean${NC}     - Remove the database container and volumes"
}

# Check if podman is installed
if ! command -v podman &> /dev/null; then
    echo -e "${RED}Error: podman is not installed. Please install podman first.${NC}"
    exit 1
fi

# Function to start the database container
function start_db {
    echo -e "${YELLOW}Starting database container...${NC}"
    cd /Users/ericstephens/src/instructor_assignments
    podman-compose -f /Users/ericstephens/src/instructor_assignments/src/db/docker/docker-compose.yml up -d postgres
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Database container started successfully.${NC}"
    else
        echo -e "${RED}Failed to start database container.${NC}"
        exit 1
    fi
}

# Function to stop the database container
function stop_db {
    echo -e "${YELLOW}Stopping database container...${NC}"
    cd /Users/ericstephens/src/instructor_assignments
    podman-compose -f /Users/ericstephens/src/instructor_assignments/src/db/docker/docker-compose.yml down
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Database container stopped successfully.${NC}"
    else
        echo -e "${RED}Failed to stop database container.${NC}"
        exit 1
    fi
}

# Function to restart the database container
function restart_db {
    echo -e "${YELLOW}Restarting database container...${NC}"
    stop_db
    start_db
}

# Function to check the status of the database container
function status_db {
    echo -e "${YELLOW}Checking database container status...${NC}"
    podman ps -a --filter "name=instructor_db"
}

# Function to show logs from the database container
function logs_db {
    echo -e "${YELLOW}Showing logs from database container...${NC}"
    podman logs instructor_db
}

# Function to connect to PostgreSQL using psql
function psql_db {
    echo -e "${YELLOW}Connecting to PostgreSQL...${NC}"
    podman exec -it instructor_db psql -U postgres -d instructor_db
}

# Function to build the database container
function build_db {
    echo -e "${YELLOW}Building database container...${NC}"
    cd /Users/ericstephens/src/instructor_assignments
    podman-compose -f /Users/ericstephens/src/instructor_assignments/src/db/docker/docker-compose.yml build postgres
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Database container built successfully.${NC}"
    else
        echo -e "${RED}Failed to build database container.${NC}"
        exit 1
    fi
}

# Function to clean up the database container and volumes
function clean_db {
    echo -e "${YELLOW}Removing database container and volumes...${NC}"
    cd /Users/ericstephens/src/instructor_assignments
    podman-compose -f /Users/ericstephens/src/instructor_assignments/src/db/docker/docker-compose.yml down -v
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Database container and volumes removed successfully.${NC}"
    else
        echo -e "${RED}Failed to remove database container and volumes.${NC}"
        exit 1
    fi
}

# Check if command is provided
if [ $# -eq 0 ]; then
    display_usage
    exit 1
fi

# Execute command
case "$1" in
    start)
        start_db
        ;;
    stop)
        stop_db
        ;;
    restart)
        restart_db
        ;;
    status)
        status_db
        ;;
    logs)
        logs_db
        ;;
    psql)
        psql_db
        ;;
    build)
        build_db
        ;;
    clean)
        clean_db
        ;;
    *)
        echo -e "${RED}Error: Unknown command '$1'${NC}"
        display_usage
        exit 1
        ;;
esac

exit 0
