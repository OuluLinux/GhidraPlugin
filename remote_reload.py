#!/usr/bin/env python3
"""
Client script to remotely trigger a Ghidra TCP server reload

NOTES:
- This script sends RELOAD/RESTART commands to a running server
- For Phase 2 features (STRUCT-DEFINE, BATCH-EXECUTE, etc.), the enhanced server
  must be loaded in Ghidra: exec(open('src/python/ghidra_tcp_server_symbolic_exec.py').read())
"""
import socket
import sys
import time

def send_command(host='localhost', port=9003, command='HELP'):
    """Send a command to the Ghidra TCP server and return the response"""
    try:
        # Create a TCP/IP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connect the socket to the port where the server is listening
        server_address = (host, port)
        sock.connect(server_address)

        try:
            # Send command
            message = f'{command}\n'
            sock.sendall(message.encode('utf-8'))

            # Get the response (may be multi-line)
            response = ""
            buffer = ""
            while True:
                data = sock.recv(4096)
                if not data:
                    break
                buffer += data.decode('utf-8')

                # Look for the end of response marker (a line with just a newline or end of data)
                lines = buffer.split('\n')
                # Process all complete lines
                for line in lines[:-1]:  # All but the last (potentially incomplete) line
                    response += line + '\n'

                # If the last part ends with a newline, we have a complete response
                if buffer.endswith('\n'):
                    # Add the last line if it's not empty
                    if lines[-1]:
                        response += lines[-1] + '\n'
                    break
                # Otherwise, keep the incomplete last line in buffer for next recv

            return response

        finally:
            sock.close()

    except Exception as e:
        return f'Error: {e}'

def trigger_reload(host='localhost', port=9003):
    """
    Send a reload command to the server using the special RELOAD command
    """
    print(f'Sending reload command to Ghidra TCP Server at {host}:{port}...')

    response = send_command(host, port, 'RELOAD')
    print(f'Server response: {response}')

    if 'RELOADING' in response or 'reload' in response.lower():
        print('Server acknowledged reload request.')
        return True
    else:
        print('Server did not acknowledge reload request, trying RESTART command...')
        response = send_command(host, port, 'RESTART')
        print(f'Server response to RESTART: {response}')
        return 'restart' in response.lower() or 'RESTARTING' in response

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 remote_reload.py <port> [host]")
        print("Example: python3 remote_reload.py 9003")
        print("")
        print("NOTES:")
        print("- This script sends RELOAD/RESTART commands to a running server")
        print("- For Phase 2 features (STRUCT-DEFINE, BATCH-EXECUTE, etc.), the enhanced server")
        print("  must be loaded in Ghidra:")
        print("  exec(open('src/python/ghidra_tcp_server_symbolic_exec.py').read()); start_server(9003)")
        sys.exit(1)

    port = int(sys.argv[1])
    host = sys.argv[2] if len(sys.argv) > 2 else 'localhost'

    success = trigger_reload(host, port)

    if success:
        print("\nServer reload triggered successfully!")
        print("The server is now ready to reload - run 'reload_server()' in Ghidra console")
    else:
        print("\nFailed to trigger server reload")

if __name__ == '__main__':
    main()