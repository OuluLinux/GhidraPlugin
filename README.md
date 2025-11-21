# Ghidra TCP Commenting Plugin - Implementation Guide

## Overview

We have explored both Java and Jython approaches for implementing a TCP server plugin for Ghidra. Through our investigation, we discovered:

1. Creating a proper Java plugin requires specific extension properties and proper integration with Ghidra's module system to appear in the installation list
2. The Jython approach provides a more accessible and practical way to implement TCP server functionality
3. Both approaches can achieve the same goals, with Jython being easier to develop and test

Based on our analysis, we recommend treating the Python (Jython) approach as the main route for implementing the TCP server, with the Java implementation serving as an alternative for deployment if needed later.

## Repository Structure

The repository follows this organized structure:
- `src/python/` - Python source code files
- `docs/` - Documentation files
- `tests/python/` - Python test files
- `tmp/` - Temporary files (excluded from git)
- Root directory - Build scripts and main project files

## Files in Each Approach

### Python (Jython) Implementation (Main Approach)
- `src/python/ghidra_tcp_server_enhanced.py` : Main implementation of the TCP server (Jython compatible with port selection)
- `src/python/run_tcp_server.py` : Entry point script to start the server
- `start_ghidra_with_tcp_server.sh` : Script to launch Ghidra with instructions

### Java Implementation (Alternative)
- `src/main/java/ClientDirectoryManager.java` : Directory management for clients
- `src/main/java/ClientHandler.java` : Command handler implementation
- `src/main/java/GhidraPathNavigator.java` : Path navigation implementation
- `src/main/java/GhidraTCPCommentingPlugin.java` : Main plugin class
- `build.gradle` : Gradle build configuration
- `build.sh` : Build script for the Java plugin
- `GhidraModule.xml` : Module information for Ghidra integration

## How to Use (Recommended - Python Route)

### 1. Launch Ghidra
```
./start_ghidra_with_tcp_server.sh
```

### 2. Load and Run the Python Script in Ghidra
1. Open Ghidra
2. Go to `Window -> Script Manager`
3. Find and run the `ghidra_tcp_server_working.py` script
4. The TCP server will start and listen on port 9000

### 3. Connect Your Client
Connect your external client to `localhost:9000` to start sending commands to Ghidra.

## Available Commands (Both Routes)

The TCP server supports these commands:

- `VAR-TYPE-SET <var_name> <type>` - Set variable type
- `VAR-TYPE-GET <var_name>` - Get variable type
- `FUN-NAME-SET <old_function_name> <new_function_name>` - Rename function
- `FUN-NAME-GET` - Get current function name
- `VAR-NAME-SET <old_var_name> <new_var_name>` - Rename variable
- `LIST-FUNCTION <fun_name>` - List items in function
- `LIST-CLASS <class_name>` - List items in class
- `LIST-NAMESPACE <namespace>` - List items in namespace
- `SET-COMMENT <fun_name> <line> <text>` - Set comment
- `REMOVE-COMMENT <fun_name> <line>` - Remove comment
- `REMOVE-ALL-COMMENTS <fun_name>` - Remove all comments in function
- `FIND-VAR-REFERENCES <var_name>` - Find variable references
- `FIND-FUNCTION-REFERENCES <fun_name>` - Find function references
- `FIND-ADDR-REFERENCES <hex_addr>` - Find address references
- `FIND-LABEL <label_name>` - Find label
- `RENAME-LABEL <old_label_name> <new_label_name>` - Rename label
- `RENAME-GLOBAL <old_var_name> <new_var_name>` - Rename global variable
- `RETYPE-GLOBAL <var_name> <new_type>` - Retype global variable
- `LS <path>` - List items at path
- `CAT <path>` - Print content at path
- `HELP` - Show help
- `QUIT` - Close connection

## Example Client Usage (Both Routes)

```python
import socket

# Connect to the TCP server
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('localhost', 9000))

# Send a command
client_socket.send(b'FUN-NAME-GET\n')
response = client_socket.recv(4096).decode('utf-8')
print(response)

# Close connection
client_socket.close()
```

## Roadmap by Implementation Language

### Java-Specific Features
- Proper extension.properties file for Ghidra extension recognition
- Full Ghidra plugin lifecycle management
- Integration with Ghidra's plugin installation system
- Better performance in production environments
- More complex setup but cleaner integration with Ghidra

### Python (Jython)-Specific Features
- Simpler development and debugging process
- More accessible for rapid prototyping
- Direct access to Ghidra API through Jython
- Faster iteration cycle during development
- Easier to modify and test functionality

### Features Common to Both Approaches
- TCP server functionality on port 9000
- Support for all specified commands
- Proper error handling and responses
- Integration with Ghidra's internal data structures
- Threaded client handling for multiple connections

## Notes

- The Python approach is recommended as the main implementation path
- The Java approach provides a more formal Ghidra plugin but requires more configuration
- Both approaches achieve the same functionality but through different mechanisms
- The Python script needs to be run from within Ghidra's Script Manager
- Ensure the appropriate ports are available on your system

## Troubleshooting

- If Ghidra gives import errors in Python, ensure you're running the script from within Ghidra's Script Manager
- For Java plugin, make sure the extension.properties file is correctly set up
- Make sure no other services are using port 9000
- Check that your client is connecting to the correct address (localhost:9000)

## Testing the Server

After starting the server from within Ghidra:
1. Make sure your program is loaded in Ghidra
2. Test from another terminal:
   ```bash
   telnet localhost 9000
   ```
3. Or use the demo client:
   ```bash
   cd /common/active/sblo/Dev/GhidraPlugin
   python3 tests/python/demo_client.py
   ```

## Command Examples

Once connected to the server through telnet or a client:
- `HELP` - Shows all available commands
- `FUN-NAME-GET` - Gets the current function name in Ghidra
- `VAR-TYPE-GET variable_name` - Gets the type of the specified variable
- `FUN-NAME-SET old_name new_name` - Renames a function from old_name to new_name
- `QUIT` - Closes the connection to the server

## Recommendation

Use the Python (Jython) approach as the main implementation route for development and testing, with the Java approach available for formal plugin deployment in production environments.

The project is now complete with both implementation approaches ready for use!