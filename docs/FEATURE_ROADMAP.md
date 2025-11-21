# Code Roadmap by Implementation Language

This document lists the code files and features by their implementation language.

## Recommended Main Approach: Python (Jython)
The Python approach is now recommended as the main implementation route because:
- Easier to develop and test
- Direct integration with Ghidra's scripting environment
- Faster iteration and debugging process
- No complex module build requirements
- Automatic port selection to avoid conflicts

## Java Implementation: Alternative Route
The Java approach remains as an alternative for formal plugin deployment:
- Better for production environments when properly configured
- Full Ghidra plugin lifecycle management
- Automatic startup when Ghidra launches

## Python (Jython)-Specific Code (Main Route)
| File | Description | Role |
|------|-------------|------|
| `ghidra_tcp_server_enhanced.py` | Main TCP server implementation in Python (Jython compatible, with port selection) | Core Plugin |
| `run_tcp_server.py` | Entry point script to start the TCP server | Core Functionality |
| `start_ghidra_with_tcp_server.sh` | Script to launch Ghidra with instructions | Infrastructure |

## Java-Specific Code (Alternative Route)
| File | Description | Role |
|------|-------------|------|
| `build.gradle` | Gradle build configuration | Build System |
| `build.sh` | Build script for Java implementation | Build System |
| `GhidraModule.xml` | Module metadata for Ghidra integration | Plugin Infrastructure |
| `src/main/java/GhidraTCPCommentingPlugin.java` | Main plugin class extending ProgramPlugin | Core Plugin |
| `src/main/java/ClientHandler.java` | Command handler implementation | Core Functionality |
| `src/main/java/ClientDirectoryManager.java` | Directory management | Core Functionality |
| `src/main/java/GhidraPathNavigator.java` | Path navigation implementation | Core Functionality |
| `extension.properties` | Extension properties for Ghidra recognition | Plugin Infrastructure |

## Common/Shared Functionality
These features are implemented in both languages with equivalent functionality:

| Feature | Description | Implementation Status |
|---------|-------------|---------------------|
| TCP Server | Listen on port 9000 (or available port) for client connections | ✅ Both Routes |
| VAR-TYPE-SET | Change variable type | ✅ Both Routes |
| VAR-TYPE-GET | Get variable type | ✅ Both Routes |
| FUN-NAME-SET | Rename function | ✅ Both Routes |
| FUN-NAME-GET | Get current function name | ✅ Both Routes |
| VAR-NAME-SET | Rename variable | ✅ Both Routes |
| LIST-FUNCTION | List items in function | ✅ Both Routes |
| LIST-CLASS | List items in class | ✅ Both Routes |
| LIST-NAMESPACE | List items in namespace | ✅ Both Routes |
| SET-COMMENT | Add comment | ✅ Both Routes |
| REMOVE-COMMENT | Remove comment | ✅ Both Routes |
| REMOVE-ALL-COMMENTS | Remove all comments in function | ✅ Both Routes |
| FIND-VAR-REFERENCES | Find variable references | ✅ Both Routes |
| FIND-FUNCTION-REFERENCES | Find function references | ✅ Both Routes |
| FIND-ADDR-REFERENCES | Find address references | ✅ Both Routes |
| FIND-LABEL | Find label | ✅ Both Routes |
| RENAME-LABEL | Rename label | ✅ Both Routes |
| RENAME-GLOBAL | Rename global variable | ✅ Both Routes |
| RETYPE-GLOBAL | Retype global variable | ✅ Both Routes |
| LS | List items at path | ✅ Both Routes |
| CAT | Print content at path | ✅ Both Routes |
| HELP | Show help | ✅ Both Routes |
| QUIT | Close connection | ✅ Both Routes |

## Enhanced Features
The enhanced Python implementation includes these additional features:

| Enhancement | Description | Status |
|-------------|-------------|--------|
| Port Selection | Automatically finds available port if default is in use | ✅ Implemented |
| Graceful Handling | Proper error handling for Ghidra API calls | ✅ Implemented |
| Threaded Connections | Handles multiple clients simultaneously | ✅ Implemented |
| Robust Architecture | Proper separation of concerns in design | ✅ Implemented |