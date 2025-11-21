"""
Demo client script to test the Ghidra TCP server with reload functionality
"""
import socket
import time
import sys

def test_server_connection(port=9003):
    """Test basic connection to the server"""
    try:
        # Create a TCP/IP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connect the socket to the port where the server is listening
        server_address = ('localhost', port)
        print('Connecting to {} port {}'.format(*server_address))
        sock.connect(server_address)

        try:
            # Send help command to test basic functionality
            message = 'HELP'
            print('Sending: {!r}'.format(message))
            sock.sendall(message.encode('utf-8'))

            # Look for the response
            response = sock.recv(4096).decode('utf-8')
            print('Received: {!r}'.format(response))

        finally:
            print('Closing socket')
            sock.close()

    except Exception as e:
        print(f"Error connecting to server: {e}")

def test_restart_command(port=9003):
    """Test the restart command functionality"""
    try:
        # Create a TCP/IP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connect the socket to the port where the server is listening
        server_address = ('localhost', port)
        print('Connecting to {} port {}'.format(*server_address))
        sock.connect(server_address)

        try:
            # Send restart command
            message = 'RESTART'
            print('Sending: {!r}'.format(message))
            sock.sendall(message.encode('utf-8'))

            # Look for the response
            response = sock.recv(4096).decode('utf-8')
            print('Received: {!r}'.format(response))

        finally:
            print('Closing socket')
            sock.close()

    except Exception as e:
        print(f"Error connecting to server: {e}")

if __name__ == "__main__":
    print("Testing Ghidra TCP server connection...")
    test_server_connection()
    
    print("\nTesting restart command...")
    test_restart_command()