#!/bin/bash
# Script to echo the manual reload command for Ghidra TCP server

# Calculate the relative path from this script's location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RELATIVE_PY_PATH="src/python/ghidra_tcp_server_reloader_jython.py"

echo "Ghidra TCP Server Manual Reload Command"
echo "======================================="
echo
echo "To start/reload the Ghidra TCP server, copy and paste this command"
echo "into the Ghidra Jython console:"
echo
echo "exec(open('$RELATIVE_PY_PATH').read()) ; start_server(9003)"
echo
echo "Instructions:"
echo "1. Open Ghidra"
echo "2. Go to the Python interpreter (bottom of CodeBrowser window)"
echo "3. Copy and paste the above command"
echo "4. Press Enter to execute"
echo
echo "For reloading after changes, use one of these approaches:"
echo "- stop_server() ; exec(open('$RELATIVE_PY_PATH').read()) ; start_server(9003)"
echo "- reload_server(9003) after loading the enhanced server script"
echo "- Use the auto_reload_checker() and remote client to reload automatically"
echo "- Use the remote_reload.py script from command line"