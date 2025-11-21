# Ghidra TCP Server with Full Remote Reload Functionality

This project provides a TCP server for client communication with Ghidra, with complete reload functionality that allows reloading from both the Ghidra console and remotely from clients.

## New Features

### Reload Functionality from Ghidra Console
Instead of running the full command:
```python
stop_server() ; exec(open('/common/active/sblo/Dev/GhidraPlugin/ghidra_tcp_server_enhanced.py').read()) ; start_server(9003)
```

Now you can simply run:
```python
reload_server(9003)
```

This function will:
1. Stop the currently running server (if any)
2. Reload the server script automatically
3. Start the server again on the specified port

### Client-Initiated Reload (NEW!)
The server now supports a `RELOAD` command that can be sent from the client to trigger an immediate server reload:
```
RELOAD
```

To use this functionality effectively, run the auto-reload checker in the Ghidra console:
```python
auto_reload_checker()
```

This will start a background process that checks for reload requests from clients and automatically reloads the server when requested.

### Alternative: Remote Reload Script
For a simpler approach without running the checker, use the `remote_reload.py` script:
```bash
python3 /common/active/sblo/Dev/GhidraPlugin/src/python/remote_reload.py 9003
```

## Usage

### Option 1: Auto-reload Checker (Recommended for Development)

1. In Ghidra's Python Console:
```python
exec(open('/common/active/sblo/Dev/GhidraPlugin/src/python/ghidra_tcp_server_with_reload_cmd.py').read())
start_server(9003)
auto_reload_checker()  # This will run continuously, checking for reload requests
```

2. From client:
```bash
# Send the reload command from client
echo "RELOAD" | nc localhost 9003
```

Or use the remote reload script:
```bash
python3 /common/active/sblo/Dev/GhidraPlugin/src/python/remote_reload.py 9003
```

### Option 2: Manual Reload Process

1. In Ghidra's Python Console:
```python
exec(open('/common/active/sblo/Dev/GhidraPlugin/src/python/ghidra_tcp_server_with_reload_cmd.py').read())
start_server(9003)
```

2. From client:
```bash
# Send the restart command from client
echo "RESTART" | nc localhost 9003
```

3. In Ghidra's Python Console (after client sends RESTART):
```python
reload_server(9003)
```

### Option 3: Using the Remote Reload Script

```bash
# From command line:
python3 /common/active/sblo/Dev/GhidraPlugin/src/python/remote_reload.py 9003
```

## Available Commands

In addition to the original commands like `SET-COMMENT`, `FIND-LABEL`, etc., the server now supports:

- `RESTART` - Request server restart (requires manual reload from Ghidra console)
- `RELOAD` - Request immediate server reload (use with auto_reload_checker())

## Example Usage

### Development with Auto-Reload:
```python
# In Ghidra Python console
exec(open('/common/active/sblo/Dev/GhidraPlugin/src/python/ghidra_tcp_server_with_reload_cmd.py').read())
start_server(9003)
auto_reload_checker()  # Now the server will auto-reload when requested from client
```

```bash
# From your development environment
python3 /common/active/sblo/Dev/GhidraPlugin/src/python/remote_reload.py 9003
```

This setup allows you to make changes to your server script and reload it completely from the client side without touching the Ghidra console.

### Simple One-Time Reload:
```python
# In Ghidra Python console
exec(open('/common/active/sblo/Dev/GhidraPlugin/src/python/ghidra_tcp_server_with_reload_cmd.py').read())
start_server(9003)

# When you need to reload, just run:
reload_server(9003)
```

This significantly simplifies the development workflow by eliminating the need to retype the full command sequence every time.