#!/usr/bin/env python3
# Ghidra TCP Server Startup Script
# This script is intended to be run from within Ghidra's scripting environment

# Import required modules
from ghidra_tcp_server_fixed import start_server

# Start the server
if __name__ == "__main__":
    print("Starting Ghidra TCP Server...")
    start_server()
    print("Server should now be running. Press Ctrl+C to stop.")