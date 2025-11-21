#!/usr/bin/env python3
"""
Test client for the Ghidra TCP server
"""
import socket
import sys

def test_connection(host='localhost', port=9003):
    """Test connection to the Ghidra TCP server"""
    try:
        # Create a TCP/IP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Connect the socket to the port where the server is listening
        server_address = (host, port)
        print(f'Connecting to {host} port {port}')
        sock.connect(server_address)

        try:
            # Send data
            message = 'HELP\n'
            print(f'Sending: {message}')
            sock.sendall(message.encode('utf-8'))

            # Look for the response
            amount_received = 0
            amount_expected = 1024  # We expect at least this much data

            while amount_received < amount_expected:
                data = sock.recv(4096)
                if not data:
                    break
                print(f'Received: {data.decode("utf-8")}')
                amount_received += len(data)
                break  # Just get the first response

        finally:
            print('Closing socket')
            sock.close()

    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    test_connection()