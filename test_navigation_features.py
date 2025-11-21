#!/usr/bin/env python3
"""
Test script for the enhanced Ghidra TCP server with navigation features.

This script tests the new commands implemented in the enhanced server:
- BOOKMARK-SET, BOOKMARK-GOTO, BOOKMARK-LIST
- NOTE-ADD, NOTE-LIST, NOTE-SEARCH
- LOCATION-GET, LOCATION-SAVE
- DECOMPILE-CFG, DECOMPILE-CONTEXT
"""

import socket
import time
import threading
import subprocess
import sys
import os


def send_command(host, port, command):
    """Send a command to the TCP server and return the response"""
    try:
        # Create a socket object
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Connect to the server
        client_socket.connect((host, port))
        
        # Send the command
        client_socket.sendall((command + "\n").encode('utf-8'))
        
        # Receive the response
        response = client_socket.recv(8192).decode('utf-8').strip()
        
        # Close the socket
        client_socket.close()
        
        return response
    except Exception as e:
        return f"ERROR: {str(e)}"


def test_server_features():
    """Test the new features of the Ghidra TCP server"""
    print("Testing Ghidra TCP Server with Navigation Features...")
    
    # Use a test port
    test_port = 9001
    host = 'localhost'
    
    print(f"\nTesting commands on {host}:{test_port}")
    
    # Test BOOKMARK commands
    print("\n--- Testing Bookmark Commands ---")
    
    # BOOKMARK-SET (this will fail without a real Ghidra program, but should return proper error)
    response = send_command(host, test_port, "BOOKMARK-SET main_function 0x401000")
    print(f"BOOKMARK-SET main_function 0x401000: {response}")
    
    # BOOKMARK-LIST (should work even without any bookmarks)
    response = send_command(host, test_port, "BOOKMARK-LIST")
    print(f"BOOKMARK-LIST: {response}")
    
    # BOOKMARK-GOTO (should fail since we don't have a bookmark named 'main_function')
    response = send_command(host, test_port, "BOOKMARK-GOTO main_function")
    print(f"BOOKMARK-GOTO main_function: {response}")
    
    # Test NOTE commands
    print("\n--- Testing Note Commands ---")
    
    # NOTE-ADD 
    response = send_command(host, test_port, "NOTE-ADD 0x401000 This is a test note")
    print(f"NOTE-ADD 0x401000 This is a test note: {response}")
    
    # NOTE-LIST
    response = send_command(host, test_port, "NOTE-LIST")
    print(f"NOTE-LIST: {response}")
    
    # NOTE-SEARCH
    response = send_command(host, test_port, "NOTE-SEARCH test")
    print(f"NOTE-SEARCH test: {response}")
    
    # Test LOCATION commands
    print("\n--- Testing Location Commands ---")
    
    # LOCATION-GET (will show no location without current context)
    response = send_command(host, test_port, "LOCATION-GET")
    print(f"LOCATION-GET: {response}")
    
    # LOCATION-SAVE (will fail without current location)
    response = send_command(host, test_port, "LOCATION-SAVE current_pos")
    print(f"LOCATION-SAVE current_pos: {response}")
    
    # Test DECOMPILE commands
    print("\n--- Testing Decompile Commands ---")
    
    # DECOMPILE-CFG (will fail without a real function)
    response = send_command(host, test_port, "DECOMPILE-CFG main")
    print(f"DECOMPILE-CFG main: {response}")
    
    # DECOMPILE-CONTEXT (will fail without a real function)
    response = send_command(host, test_port, "DECOMPILE-CONTEXT main")
    print(f"DECOMPILE-CONTEXT main: {response}")
    
    # Test HELP to see all available commands
    print("\n--- Testing Help Command ---")
    response = send_command(host, test_port, "HELP")
    print(f"HELP command execution returned: {len(response)} characters")
    # Print just the first few lines to verify the new commands are listed
    lines = response.split('\n')
    for line in lines[:10]:  # Print first 10 lines
        print(f"  {line}")
    print(f"  ... (and {len(lines) - 10} more lines)")
    
    print("\n--- Testing Complete ---")
    print("Note: Most commands will return errors when run without a real Ghidra context,")
    print("but they should return appropriate error messages rather than unknown command errors.")


if __name__ == "__main__":
    test_server_features()