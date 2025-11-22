#!/bin/bash
# Script to echo the manual reload command for Ghidra TCP server

# Calculate the relative path from this script's location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RELATIVE_PY_PATH_RELOADER="src/python/ghidra_tcp_server_reloader_jython.py"
RELATIVE_PY_PATH_ENHANCED="src/python/ghidra_tcp_server_symbolic_exec.py"

echo "Ghidra TCP Server Manual Start Commands"
echo "======================================="
echo
echo "To start the Ghidra TCP server, copy and paste one of these commands"
echo "into the Ghidra Jython console:"
echo
echo "1. For basic server with reload functionality:"
echo "   exec(open('$RELATIVE_PY_PATH_RELOADER').read()) ; start_server(9003)"
echo
echo "2. For enhanced server with ALL Phase 2 features (recommended for development):"
echo "   exec(open('$RELATIVE_PY_PATH_ENHANCED').read()) ; start_server(9003)"
echo
echo "Instructions:"
echo "1. Open Ghidra"
echo "2. Go to the Python interpreter (Script Manager or bottom of CodeBrowser window)"
echo "3. Copy and paste the command you want to use"
echo "4. Press Enter to execute"
echo
echo "For reloading after changes, use one of these approaches:"
echo "- stop_server() ; exec(open('$RELATIVE_PY_PATH_RELOADER').read()) ; start_server(9003)"
echo "- reload_server(9003) after loading the reloader server script"
echo "- reload_server(9003) after loading the enhanced server script"
echo "- Use the auto_reload_checker() and remote client to reload automatically"
echo "- Use the remote_reload.py script from command line"
echo
echo "Note: The enhanced server (option 2) includes all Phase 2 features including:"
echo "      STRUCT-DEFINE, ENUM-DEFINE, TYPE-HIERARCHY, BATCH operations,"
echo "      PATTERN operations, and SYMBOLIC execution integration"