#!/usr/bin/env python3
"""
Client script to remotely reload the Ghidra TCP server
"""
import socket
import sys
import subprocess
import os

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

def reload_from_client(host='localhost', port=9003):
    """
    Send a restart command to the server, which will prepare for restart
    """
    print(f'Sending restart command to Ghidra TCP Server at {host}:{port}...')
    
    response = send_command(host, port, 'RESTART')
    print(f'Server response: {response}')
    
    if 'RESTARTING' in response or 'restart' in response.lower():
        print('Server acknowledged restart request. The server should now be ready for reload.')
        print('In Ghidra console, run: reload_server()')
        return True
    else:
        print('Server did not acknowledge restart request')
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 reload_client.py <port> [host]")
        print("Example: python3 reload_client.py 9003")
        sys.exit(1)

    port = int(sys.argv[1])
    host = sys.argv[2] if len(sys.argv) > 2 else 'localhost'
    
    reload_from_client(host, port)

if __name__ == '__main__':
    main()