#!/bin/bash
# Client script to interact with the Ghidra TCP server

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
DEFAULT_HOST="localhost"
DEFAULT_PORT="9003"
CLIENT_SCRIPT="tests/python/demo_client.py"

# Function to display help
show_help() {
    echo "Ghidra TCP Server Client"
    echo "========================"
    echo "Usage: $0 [OPTIONS] [COMMAND]"
    echo ""
    echo "Options:"
    echo "  -h, --host HOST     Server host (default: localhost)"
    echo "  -p, --port PORT     Server port (default: 9003)"
    echo "  -i, --interactive   Run in interactive mode"
    echo "  --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 HELP                           # Send HELP command"
    echo "  $0 -p 9004 LIST-ALL-FUNCTIONS     # Send command to port 9004"
    echo "  $0 -p 9005 LIST-ALL-FUNCTIONS     # Send command to port 9005"
    echo "  $0 -i                             # Start interactive mode"
    echo "  $0 -p 9004 -i                     # Start interactive mode on port 9004"
    echo ""
    echo "Note: Commonly used ports are 9003, 9004, 9005, etc."
    echo "      Make sure the server is running on the specified port."
    echo ""
}

# Parse command line arguments
HOST="$DEFAULT_HOST"
PORT="$DEFAULT_PORT"
INTERACTIVE=false
COMMAND=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--host)
            HOST="$2"
            shift 2
            ;;
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        -i|--interactive)
            INTERACTIVE=true
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            if [ -z "$COMMAND" ]; then
                COMMAND="$1"
            else
                COMMAND="$COMMAND $1"
            fi
            shift
            ;;
    esac
done

# Determine the project root (where this script is located)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"  # The script is in the project root already

# Check if the client script exists
CLIENT_SCRIPT_PATH="$PROJECT_ROOT/$CLIENT_SCRIPT"
if [ ! -f "$CLIENT_SCRIPT_PATH" ]; then
    echo -e "${RED}Error: Client script not found at $CLIENT_SCRIPT_PATH${NC}"
    exit 1
fi

# Validate port number
if ! [[ "$PORT" =~ ^[0-9]+$ ]] || [ "$PORT" -lt 1 ] || [ "$PORT" -gt 65535 ]; then
    echo -e "${RED}Error: Invalid port number '$PORT'${NC}"
    exit 1
fi

echo -e "${GREEN}Connecting to Ghidra TCP Server at $HOST:$PORT${NC}"

# Run the client script
if [ "$INTERACTIVE" = true ]; then
    echo -e "${YELLOW}Starting interactive mode...${NC}"
    python3 "$CLIENT_SCRIPT_PATH" interactive "$PORT" "$HOST"
else
    if [ -z "$COMMAND" ]; then
        echo -e "${YELLOW}No command provided. Starting interactive mode...${NC}"
        python3 "$CLIENT_SCRIPT_PATH" interactive "$PORT" "$HOST"
    else
        echo -e "${YELLOW}Sending command: $COMMAND${NC}"
        python3 "$CLIENT_SCRIPT_PATH" "$COMMAND" "$PORT" "$HOST"
    fi
fi