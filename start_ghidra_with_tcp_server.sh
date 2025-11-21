#!/bin/bash

# Script to launch Ghidra with instructions to load the TCP server script
# This script starts Ghidra and provides instructions for how to activate the TCP server

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Ghidra is already installed
if [ ! -f "/home/sblo/xtra/linux/Ohjelmat/ghidra_11.4.2_PUBLIC/ghidraRun" ]; then
    echo -e "${RED}Error: Ghidra installation not found at /home/sblo/xtra/linux/Ohjelmat/ghidra_11.4.2_PUBLIC${NC}"
    exit 1
fi

echo -e "${GREEN}Starting Ghidra...${NC}"

# Start Ghidra
/home/sblo/xtra/linux/Ohjelmat/ghidra_11.4.2_PUBLIC/ghidraRun &

GHIDRA_PID=$!

# Wait a little bit for Ghidra to start
sleep 3

echo -e "${GREEN}Ghidra started with PID ${GHIDRA_PID}${NC}"

# Instructions for using the TCP server
echo -e "${YELLOW}To activate the TCP server:${NC}"
echo -e "${YELLOW}1. Once Ghidra is running, open Script Manager (Window -> Script Manager)${NC}"
echo -e "${YELLOW}2. Navigate to the directory containing these files: ${PWD}${NC}"
echo -e "${YELLOW}3. Load and run 'run_tcp_server.py' or 'ghidra_tcp_server_fixed.py'${NC}"
echo -e "${YELLOW}4. The TCP server will start and listen on port 9000${NC}"
echo -e "${YELLOW}5. You can then connect a TCP client to localhost:9000${NC}"

# Keep this terminal alive while Ghidra is running
wait $GHIDRA_PID