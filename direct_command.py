#!/usr/bin/env python3

import socket
import sys
import time

def send_command_to_server(command, host='localhost', port=9003):
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

            # Receive the response
            response = b""
            sock.settimeout(5)  # 5 second timeout
            while True:
                try:
                    data = sock.recv(4096)
                    if not data:
                        break
                    response += data
                except socket.timeout:
                    break  # Timeout reached, assume complete response

            return response.decode('utf-8')

        finally:
            sock.close()

    except Exception as e:
        return f'Error: {e}'

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 direct_command.py '<command>' [port] [host]")
        print("Example: python3 direct_command.py 'HELP' 9003")
        sys.exit(1)

    command = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 9003
    host = sys.argv[3] if len(sys.argv) > 3 else 'localhost'

    response = send_command_to_server(command, host, port)
    print(f"Response: {response}")