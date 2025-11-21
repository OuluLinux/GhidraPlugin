# Testing Instructions for Ghidra TCP Server Plugin

## How to Start the Server in Ghidra

1. Launch Ghidra
2. Open the Script Manager (Window → Script Manager)
3. Either:
   - Run the script directly in the Script Manager, OR
   - Execute this command in the Python (Jython) console:
   ```
   exec(open('/common/active/sblo/Dev/GhidraPlugin/ghidra_tcp_server_working.py').read())
   start_server()
   ```

## How to Test the Server

Once the server is running in Ghidra, you can test it from another terminal:

1. Make sure you have a program loaded in Ghidra before starting the server
2. The server will start and listen on port 9000
3. Test with a simple client like the demo_client.py

### Simple test command from another terminal:
```bash
telnet localhost 9000
```

Then try sending commands like:
- `HELP` - Shows available commands
- `FUN-NAME-GET` - Gets current function name
- `QUIT` - Close connection

### To test with the demo client:
```bash
cd /common/active/sblo/Dev/GhidraPlugin
python3 demo_client.py
```

## Expected Behavior

The server should:
- Accept connections from TCP clients
- Process various commands for interacting with Ghidra
- Respond appropriately to each command
- Handle multiple clients through threading
- Properly close connections when requested

## Troubleshooting

- If you get "Address already in use" error, another server is already running on port 9000
- Commands will only work properly if there's an active program in Ghidra
- Some commands may require specific program context (loaded binaries, functions, etc.)
- If the server doesn't respond, make sure it's running inside Ghidra and not as a standalone process