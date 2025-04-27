#!/bin/bash

# Ship Enrichment System Startup Script
# This script starts all required components for the Ship Enrichment System
# in the correct order:
# 1. Temporal Server
# 2. AIS Mock Server
# 3. Temporal Worker
# 4. Main Server

set -e  # Exit on error

# Colors for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Python version
check_python_version() {
    if ! command_exists python3; then
        echo -e "${RED}Python 3 is not installed. Please install Python 3.9 or higher.${NC}"
        exit 1
    fi
    
    # Get Python version
    python_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    python_major=$(echo $python_version | cut -d. -f1)
    python_minor=$(echo $python_version | cut -d. -f2)
    
    if [ "$python_major" -lt 3 ] || ([ "$python_major" -eq 3 ] && [ "$python_minor" -lt 9 ]); then
        echo -e "${RED}Python 3.9 or higher is required. Found Python $python_version.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Found Python $python_version.${NC}"
}

# Function to check Temporal CLI
check_temporal_cli() {
    if ! command_exists temporal; then
        echo -e "${RED}Temporal CLI is not installed. Please install it from https://docs.temporal.io/cli#install${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Found Temporal CLI.${NC}"
}

# Function to check if port is available and by whom
check_port_available() {
    local port=$1
    local expected_process="$2" # Optional: expected process name (e.g., python, temporal)
    if command_exists lsof; then
        local lsof_output
        lsof_output=$(lsof -i :$port -sTCP:LISTEN -Fp,c | head -n 2)
        if [[ -n "$lsof_output" ]]; then
            local pid=$(echo "$lsof_output" | grep '^p' | cut -c2-)
            local command=$(echo "$lsof_output" | grep '^c' | cut -c2-)
            if [[ -n "$expected_process" && "$command" == *"$expected_process"* ]]; then
                echo -e "${YELLOW}Port $port is in use by expected process '$command' (PID $pid). Service may already be running. Skipping start.${NC}"
                return 2
            else
                echo -e "${RED}Port $port is in use by another process ('$command', PID $pid). Skipping start of this service.${NC}"
                return 3
            fi
        fi
    elif command_exists netstat; then
        if netstat -tulnp 2>/dev/null | grep -q ":$port "; then
            echo -e "${RED}Port $port is already in use. Skipping start of this service.${NC}"
            return 3
        fi
    else
        echo -e "${YELLOW}Cannot check if port $port is available. Proceeding anyway.${NC}"
    fi
    return 0
}

# Function to create and activate virtual environment
setup_venv() {
    local dir=$1
    local venv_path="$dir/.venv"
    
    echo -e "${BLUE}Setting up virtual environment in $dir...${NC}"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "$venv_path" ]; then
        echo -e "${BLUE}Creating virtual environment...${NC}"
        python3 -m venv "$venv_path"
    fi
    
    # Activate virtual environment
    source "$venv_path/bin/activate"
    
    # Install requirements if requirements.txt exists
    if [ -f "$dir/requirements.txt" ]; then
        echo -e "${BLUE}Installing requirements...${NC}"
        pip install -r "$dir/requirements.txt"
    fi
    
    echo -e "${GREEN}Virtual environment setup complete.${NC}"
}

# Function to start Temporal server
start_temporal_server() {
    echo -e "${BLUE}Starting Temporal server...${NC}"
    if check_port_available 7234 temporal; then
        : # Port is free, continue
    elif [[ $? -eq 2 ]]; then
        return # Already running
    else
        return # Port conflict
    fi
    cd temporals
    temporal server start-dev --port 7234 > temporal_server.log 2>&1 &
    TEMPORAL_PID=$!
    echo -e "${BLUE}Waiting for Temporal server to start...${NC}"
    sleep 5
    if kill -0 $TEMPORAL_PID 2>/dev/null; then
        echo -e "${GREEN}Temporal server started with PID $TEMPORAL_PID.${NC}"
        echo $TEMPORAL_PID > temporal_server.pid
    else
        echo -e "${RED}Failed to start Temporal server. Check temporal_server.log for details.${NC}"
        exit 1
    fi
    cd ..
}

# Function to start AIS mock server
start_ais_mock_server() {
    echo -e "${BLUE}Starting AIS mock server...${NC}"
    if check_port_available 8000 python; then
        :
    elif [[ $? -eq 2 ]]; then
        return
    else
        return
    fi
    cd scripts/ais_mock
    setup_venv .
    if [ ! -f "AIS_2024_05_05.csv" ]; then
        echo -e "${BLUE}Downloading AIS data...${NC}"
        if [ -f "dl_ais_data.sh" ]; then
            bash dl_ais_data.sh
        else
            echo -e "${YELLOW}dl_ais_data.sh not found. Please download AIS data manually.${NC}"
        fi
    fi
    python main.py > ais_mock_server.log 2>&1 &
    AIS_MOCK_PID=$!
    echo -e "${BLUE}Waiting for AIS mock server to start...${NC}"
    sleep 5
    if kill -0 $AIS_MOCK_PID 2>/dev/null; then
        echo -e "${GREEN}AIS mock server started with PID $AIS_MOCK_PID.${NC}"
        echo $AIS_MOCK_PID > ais_mock_server.pid
    else
        echo -e "${RED}Failed to start AIS mock server. Check ais_mock_server.log for details.${NC}"
        exit 1
    fi
    deactivate
    cd ../..
}

# Function to start Temporal worker
start_temporal_worker() {
    echo -e "${BLUE}Starting Temporal worker...${NC}"
    
    # Set up virtual environment
    cd temporals/base
    setup_venv .
    
    # Start Temporal worker in background
    echo -e "${BLUE}Starting Temporal worker...${NC}"
    python worker.py > temporal_worker.log 2>&1 &
    TEMPORAL_WORKER_PID=$!
    
    # Wait for worker to start
    echo -e "${BLUE}Waiting for Temporal worker to start...${NC}"
    sleep 5
    
    # Check if worker started successfully
    if kill -0 $TEMPORAL_WORKER_PID 2>/dev/null; then
        echo -e "${GREEN}Temporal worker started with PID $TEMPORAL_WORKER_PID.${NC}"
        echo $TEMPORAL_WORKER_PID > temporal_worker.pid
    else
        echo -e "${RED}Failed to start Temporal worker. Check temporal_worker.log for details.${NC}"
        exit 1
    fi
    
    deactivate
    cd ../..
}

# Function to start main server
start_main_server() {
    echo -e "${BLUE}Starting main server...${NC}"
    if check_port_available 8001 python; then
        :
    elif [[ $? -eq 2 ]]; then
        return
    else
        return
    fi
    cd temporals/base
    setup_venv .
    
    # Start main server in background
    echo -e "${BLUE}Starting main server...${NC}"
    python server.py > main_server.log 2>&1 &
    MAIN_SERVER_PID=$!
    
    # Wait for server to start
    echo -e "${BLUE}Waiting for main server to start...${NC}"
    sleep 5
    
    # Check if server started successfully
    if kill -0 $MAIN_SERVER_PID 2>/dev/null; then
        echo -e "${GREEN}Main server started with PID $MAIN_SERVER_PID.${NC}"
        echo $MAIN_SERVER_PID > main_server.pid
    else
        echo -e "${RED}Failed to start main server. Check main_server.log for details.${NC}"
        exit 1
    fi
    
    deactivate
    cd ../..
}

# Function to stop all components
stop_all() {
    echo -e "${BLUE}Stopping all components...${NC}"
    
    # Stop main server
    if [ -f "temporals/base/main_server.pid" ]; then
        MAIN_SERVER_PID=$(cat temporals/base/main_server.pid)
        if kill -0 $MAIN_SERVER_PID 2>/dev/null; then
            echo -e "${BLUE}Stopping main server (PID $MAIN_SERVER_PID)...${NC}"
            kill $MAIN_SERVER_PID
            echo -e "${GREEN}Main server stopped.${NC}"
        fi
        rm temporals/base/main_server.pid
    fi
    
    # Stop Temporal worker
    if [ -f "temporals/base/temporal_worker.pid" ]; then
        TEMPORAL_WORKER_PID=$(cat temporals/base/temporal_worker.pid)
        if kill -0 $TEMPORAL_WORKER_PID 2>/dev/null; then
            echo -e "${BLUE}Stopping Temporal worker (PID $TEMPORAL_WORKER_PID)...${NC}"
            kill $TEMPORAL_WORKER_PID
            echo -e "${GREEN}Temporal worker stopped.${NC}"
        fi
        rm temporals/base/temporal_worker.pid
    fi
    
    # Stop AIS mock server
    if [ -f "scripts/ais_mock/ais_mock_server.pid" ]; then
        AIS_MOCK_PID=$(cat scripts/ais_mock/ais_mock_server.pid)
        if kill -0 $AIS_MOCK_PID 2>/dev/null; then
            echo -e "${BLUE}Stopping AIS mock server (PID $AIS_MOCK_PID)...${NC}"
            kill $AIS_MOCK_PID
            echo -e "${GREEN}AIS mock server stopped.${NC}"
        fi
        rm scripts/ais_mock/ais_mock_server.pid
    fi
    
    # Stop Temporal server
    if [ -f "temporals/temporal_server.pid" ]; then
        TEMPORAL_PID=$(cat temporals/temporal_server.pid)
        if kill -0 $TEMPORAL_PID 2>/dev/null; then
            echo -e "${BLUE}Stopping Temporal server (PID $TEMPORAL_PID)...${NC}"
            kill $TEMPORAL_PID
            echo -e "${GREEN}Temporal server stopped.${NC}"
        fi
        rm temporals/temporal_server.pid
    fi
    
    echo -e "${GREEN}All components stopped.${NC}"
}

# Trap Ctrl+C and call stop_all
trap stop_all INT

# Function to print usage information
help() {
    echo "Usage: $0 {start|stop|restart|-h|--help}"
    echo "Commands:"
    echo "  start     Start the Ship Enrichment System (default if no command)"
    echo "  stop      Stop all running components"
    echo "  restart   Restart all components"
    echo "  -h, --help  Show this help message"
}

# Main function
main() {
    echo -e "${BLUE}Starting Ship Enrichment System...${NC}"
    
    # Check prerequisites
    check_python_version
    check_temporal_cli
    
    # Start all components in order
    start_temporal_server
    start_ais_mock_server
    start_temporal_worker
    start_main_server
    
    echo -e "${GREEN}Ship Enrichment System started successfully.${NC}"
    echo -e "\n${YELLOW}Access the running services at the following URLs:${NC}"
    echo -e "  - Temporal Server:         http://localhost:7234"
    echo -e "  - Temporal Web UI:         http://localhost:8233"
    echo -e "  - AIS Mock Server (API):   http://localhost:8000"
    echo -e "  - Main Server (Web UI):    http://localhost:8001  ${GREEN}<-- Web UI${NC}"
    
    # Keep script running until interrupted
    while true; do
        sleep 1
    done
}

# Parse command-line arguments
case "$1" in
    start|"")
        main
        ;;
    stop)
        stop_all
        ;;
    restart)
        stop_all
        main
        ;;
    -h|--help)
        help
        ;;
    *)
        echo "Unknown command: $1"
        help
        exit 1
        ;;
esac