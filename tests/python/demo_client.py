#!/usr/bin/env python3
"""
Demo client for the Ghidra TCP server with decompilation and exploration capabilities
"""
import socket
import sys

def send_command(host='localhost', port=9003, command='HELP'):
    """Send a command to the Ghidra TCP server and return the response"""
    try:
        # Create a TCP/IP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connect the socket to the port where the server is listening
        server_address = (host, port)
        print(f'Connecting to {host} port {port}')
        sock.connect(server_address)

        try:
            # Send command
            message = f'{command}\n'
            print(f'Sending command: {command}')
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

            print(f'Received response ({len(response)} chars):')
            print('-' * 50)
            print(response.rstrip())  # Remove trailing newlines for cleaner output
            print('-' * 50)
            return response

        finally:
            sock.close()

    except Exception as e:
        print(f'Error: {e}')
        return None

def interactive_mode(host='localhost', port=9003):
    """Run in interactive mode to send multiple commands"""
    print(f'Connecting to Ghidra TCP Server at {host}:{port}')
    print('Enter commands (type "quit" to exit, "help" for command list):')

    try:
        while True:
            command = input('> ').strip()
            if not command:
                continue
            if command.lower() in ['quit', 'exit', 'q']:
                break

            send_command(host, port, command)
            print()  # Extra newline for readability

    except KeyboardInterrupt:
        print("\nExiting...")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 demo_client.py <COMMAND> [args...]")
        print("Example: python3 demo_client.py HELP")
        print("Example: python3 demo_client.py DECOMPILE main")
        print("Example: python3 demo_client.py EXPLORE program")
        print("Example: python3 demo_client.py explore program.getMemory")
        print("For interactive mode, run: python3 demo_client.py interactive")
        sys.exit(1)

    if sys.argv[1].lower() == 'interactive':
        interactive_mode()
    else:
        command = ' '.join(sys.argv[1:])  # Join all arguments as a single command
        send_command(command=command)