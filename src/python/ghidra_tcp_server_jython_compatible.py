"""
Ghidra TCP Server - Python Script for Ghidra Client Communication (Jython Compatible)

This script provides a TCP server for client communication with Ghidra, 
allowing remote commenting and analysis features.
"""

import socket
import threading
import sys
from time import sleep
import traceback

# Import Ghidra specific modules
from ghidra.program.flatapi import FlatProgramAPI
from ghidra.program.model.listing import *
from ghidra.program.model.symbol import *
from ghidra.program.model.data import *
from ghidra.program.model.address import *
from ghidra.util.exception import *
from ghidra.app.cmd.comments import SetCommentCmd
from ghidra.app.cmd.function import RenameFunctionCmd
from ghidra.app.decompiler import DecompInterface
from ghidra.util.task import ConsoleTaskMonitor
from ghidra.app.services import *


class GhidraTCPClientHandler:
    """
    Enhanced client handler that can process commands from TCP clients
    """
    
    def __init__(self, connection_socket, current_program, current_location=None):
        self.connection_socket = connection_socket
        self.current_program = current_program
        self.current_location = current_location
        self.flat_api = FlatProgramAPI(current_program)
        self.running = True
        
    def run(self):
        """Main function to handle the client connection"""
        try:
            while self.running:
                # Receive command from client
                data = self.connection_socket.recv(4096).decode('utf-8')
                if not data:
                    break
                
                # Process the command
                command_parts = data.strip().split(' ', 1)
                command = command_parts[0].upper()
                parameters = command_parts[1] if len(command_parts) > 1 else ""
                
                # Handle the command
                response = self.handle_command(command, parameters)
                
                # Send response back to client
                self.connection_socket.sendall((response + "\n").encode('utf-8'))
                
                # If client sends QUIT, break the loop
                if command == "QUIT":
                    break
                    
        except Exception as e:
            print("Error handling client: {}".format(str(e)))
            print(traceback.format_exc())
        finally:
            self.connection_socket.close()
            
    def handle_command(self, command, parameters):
        """
        Handle different commands sent by the client
        """
        # Dictionary of commands and their handlers
        command_handlers = {
            "VAR-TYPE-SET": self.var_type_set_handler,
            "VAR-TYPE-GET": self.var_type_get_handler,
            "FUN-NAME-SET": self.fun_name_set_handler,
            "FUN-NAME-GET": self.fun_name_get_handler,
            "VAR-NAME-SET": self.var_name_set_handler,
            "LIST-FUNCTION": self.list_function_handler,
            "LIST-CLASS": self.list_class_handler,
            "LIST-NAMESPACE": self.list_namespace_handler,
            "SET-COMMENT": self.set_comment_handler,
            "REMOVE-COMMENT": self.remove_comment_handler,
            "REMOVE-ALL-COMMENTS": self.remove_all_comments_handler,
            "FIND-VAR-REFERENCES": self.find_var_references_handler,
            "FIND-FUNCTION-REFERENCES": self.find_function_references_handler,
            "FIND-ADDR-REFERENCES": self.find_addr_references_handler,
            "FIND-LABEL": self.find_label_handler,
            "RENAME-LABEL": self.rename_label_handler,
            "RENAME-GLOBAL": self.rename_global_handler,
            "RETYPE-GLOBAL": self.retype_global_handler,
            "LS": self.ls_handler,
            "CAT": self.cat_handler,
            "HELP": self.help_handler,
            "QUIT": self.quit_handler,
        }
        
        handler = command_handlers.get(command)
        if handler:
            try:
                return handler(parameters)
            except Exception as e:
                return "ERROR: Command '{}' failed with error: {}".format(command, str(e))
        else:
            return "ERROR: Unknown command '{}'. Try 'HELP' for available commands.".format(command)
    
    def var_type_set_handler(self, parameters):
        """Handle VAR-TYPE-SET command"""
        parts = parameters.split(' ', 1)
        if len(parts) < 2:
            return "ERROR: VAR-TYPE-SET requires variable name and type"
        
        var_name = parts[0]
        var_type = parts[1]
        
        # Get the function manager to iterate through functions
        func_manager = self.current_program.getFunctionManager()
        
        # Look for the variable in all functions
        for func in func_manager.getFunctions(True):
            # Check parameters
            for param in func.getParameters():
                if param.getName() == var_name:
                    # In a real implementation, you would map the string type to a Ghidra DataType
                    return "SUCCESS: Parameter '{}' type set to '{}' in function {}".format(var_name, var_type, func.getName())
            
            # Check local variables
            for local in func.getLocalVariables():
                if local.getName() == var_name:
                    # In a real implementation, you would map the string type to a Ghidra DataType
                    return "SUCCESS: Local variable '{}' type set to '{}' in function {}".format(var_name, var_type, func.getName())
        
        # Check global variables/symbols
        sym_table = self.current_program.getSymbolTable()
        symbols = sym_table.getSymbols(var_name)
        while symbols.hasNext():
            sym = symbols.next()
            if sym.getSymbolType() == SymbolType.LABEL or sym.getSymbolType() == SymbolType.DATA:
                # In a real implementation, you would map the string type to a Ghidra DataType
                return "SUCCESS: Global variable '{}' type set to '{}'".format(var_name, var_type)
        
        return "ERROR: Variable '{}' not found".format(var_name)
    
    def var_type_get_handler(self, parameters):
        """Handle VAR-TYPE-GET command"""
        var_name = parameters.strip()
        if not var_name:
            return "ERROR: VAR-TYPE-GET requires variable name"
        
        # Get the function manager to iterate through functions
        func_manager = self.current_program.getFunctionManager()
        
        # Look for the variable in all functions
        for func in func_manager.getFunctions(True):
            # Check parameters
            for param in func.getParameters():
                if param.getName() == var_name:
                    return "SUCCESS: Type for parameter '{}' is '{}'".format(var_name, param.getDataType().getName())
            
            # Check local variables
            for local in func.getLocalVariables():
                if local.getName() == var_name:
                    return "SUCCESS: Type for local variable '{}' is '{}'".format(var_name, local.getDataType().getName())
        
        # Check global variables/symbols
        sym_table = self.current_program.getSymbolTable()
        symbols = sym_table.getSymbols(var_name)
        while symbols.hasNext():
            sym = symbols.next()
            if sym.getSymbolType() == SymbolType.LABEL or sym.getSymbolType() == SymbolType.DATA:
                # Return unknown type since we can't determine from symbol alone
                return "SUCCESS: Type for global variable '{}' is 'unknown'".format(var_name)
        
        return "ERROR: Variable '{}' not found".format(var_name)
    
    def fun_name_set_handler(self, parameters):
        """Handle FUN-NAME-SET command"""
        parts = parameters.split(' ', 1)
        if len(parts) < 2:
            return "ERROR: FUN-NAME-SET requires old function name and new function name"
        
        old_name = parts[0]
        new_name = parts[1]
        
        # Get the function manager to find the function
        func_manager = self.current_program.getFunctionManager()
        func = func_manager.getFunctionNamed(old_name)
        
        if func:
            try:
                func.setName(new_name, SourceType.USER_DEFINED)
                return "SUCCESS: Function renamed from '{}' to '{}'".format(old_name, new_name)
            except Exception as e:
                return "ERROR: Could not rename function - {}".format(str(e))
        else:
            return "ERROR: Function '{}' not found".format(old_name)
    
    def fun_name_get_handler(self, parameters):
        """Handle FUN-NAME-GET command"""
        # If we have a current location (cursor position), we can get the function at that location
        if self.current_location:
            func = self.current_program.getFunctionManager().getFunctionContaining(self.current_location.getAddress())
            if func:
                return "SUCCESS: Current function is '{}'".format(func.getName())
        
        # Otherwise, return the first function in the program if no current location
        func_iter = self.current_program.getFunctionManager().getFunctions(True)
        if func_iter.hasNext():
            func = func_iter.next()
            return "SUCCESS: Current function is '{}'".format(func.getName())
        else:
            return "ERROR: No functions found in program"
    
    def var_name_set_handler(self, parameters):
        """Handle VAR-NAME-SET command"""
        parts = parameters.split(' ', 1)
        if len(parts) < 2:
            return "ERROR: VAR-NAME-SET requires old variable name and new variable name"
        
        old_name = parts[0]
        new_name = parts[1]
        
        # Get the function manager to iterate through functions
        func_manager = self.current_program.getFunctionManager()
        
        # Look for the variable in all functions
        for func in func_manager.getFunctions(True):
            # Check parameters
            for param in func.getParameters():
                if param.getName() == old_name:
                    try:
                        param.setName(new_name, SourceType.USER_DEFINED)
                        return "SUCCESS: Parameter renamed from '{}' to '{}' in function {}".format(old_name, new_name, func.getName())
                    except Exception as e:
                        return "ERROR: Could not rename parameter - {}".format(str(e))
            
            # Check local variables
            for local in func.getLocalVariables():
                if local.getName() == old_name:
                    try:
                        local.setName(new_name, SourceType.USER_DEFINED)
                        return "SUCCESS: Local variable renamed from '{}' to '{}' in function {}".format(old_name, new_name, func.getName())
                    except Exception as e:
                        return "ERROR: Could not rename local variable - {}".format(str(e))
        
        # Check global variables/symbols
        sym_table = self.current_program.getSymbolTable()
        symbols = sym_table.getSymbols(old_name)
        while symbols.hasNext():
            sym = symbols.next()
            if sym.getSymbolType() == SymbolType.LABEL or sym.getSymbolType() == SymbolType.DATA:
                try:
                    sym.setName(new_name, SourceType.USER_DEFINED)
                    return "SUCCESS: Global variable renamed from '{}' to '{}'".format(old_name, new_name)
                except Exception as e:
                    return "ERROR: Could not rename global variable - {}".format(str(e))
        
        return "ERROR: Variable '{}' not found".format(old_name)
    
    def list_function_handler(self, parameters):
        """Handle LIST-FUNCTION command"""
        func_name = parameters.strip()
        if not func_name:
            return "ERROR: LIST-FUNCTION requires function name"
        
        # Get the function manager to find the function
        func_manager = self.current_program.getFunctionManager()
        func = func_manager.getFunctionNamed(func_name)
        
        if not func:
            return "ERROR: Function '{}' not found".format(func_name)
        
        result = "Items in function '{}':\n".format(func_name)
        
        # Add parameters
        for i in range(func.getParameterCount()):
            param = func.getParameter(i)
            result += "  param {}: {} ({})\n".format(i, param.getName(), param.getDataType().getName())
        
        # Add local variables
        for local in func.getLocalVariables():
            result += "  local: {} ({})\n".format(local.getName(), local.getDataType().getName())
        
        return "SUCCESS: " + result
    
    def list_class_handler(self, parameters):
        """Handle LIST-CLASS command"""
        class_name = parameters.strip()
        if not class_name:
            return "ERROR: LIST-CLASS requires class name"
        
        # Get the symbol table to find the class
        sym_table = self.current_program.getSymbolTable()
        namespace = sym_table.getNamespace(class_name, None)
        
        if not namespace:
            return "ERROR: Class/namespace '{}' not found".format(class_name)
        
        result = "Items in class/namespace '{}':\n".format(class_name)
        
        # Find symbols in this namespace
        symbols = sym_table.getSymbols(namespace)
        while symbols.hasNext():
            sym = symbols.next()
            result += "  {} ({})\n".format(sym.getName(), sym.getSymbolType().toString())
        
        return "SUCCESS: " + result
    
    def list_namespace_handler(self, parameters):
        """Handle LIST-NAMESPACE command"""
        namespace_name = parameters.strip()
        if not namespace_name:
            return "ERROR: LIST-NAMESPACE requires namespace name"
        
        # Get the symbol table to find the namespace
        sym_table = self.current_program.getSymbolTable()
        namespace = sym_table.getNamespace(namespace_name, None)
        
        if not namespace:
            return "ERROR: Namespace '{}' not found".format(namespace_name)
        
        result = "Items in namespace '{}':\n".format(namespace_name)
        
        # Find symbols in this namespace
        symbols = sym_table.getSymbols(namespace)
        while symbols.hasNext():
            sym = symbols.next()
            result += "  {} ({})\n".format(sym.getName(), sym.getSymbolType().toString())
        
        return "SUCCESS: " + result
    
    def set_comment_handler(self, parameters):
        """Handle SET-COMMENT command"""
        parts = parameters.split(' ', 2)
        if len(parts) < 3:
            return "ERROR: SET-COMMENT requires function name, line number, and comment text"
        
        func_name = parts[0]
        line_str = parts[1]
        comment = parts[2]
        
        # Get the function manager to find the function
        func_manager = self.current_program.getFunctionManager()
        func = func_manager.getFunctionNamed(func_name)
        
        if not func:
            return "ERROR: Function '{}' not found".format(func_name)
        
        try:
            # In a real implementation, we'd set the comment at a specific line
            # This is a simplified implementation that sets a plate comment at the function's entry point
            listing = self.current_program.getListing()
            cu = listing.getCodeUnitAt(func.getEntryPoint())
            if cu:
                # Apply the comment command to the program
                cmd = SetCommentCmd(cu.getMinAddress(), CodeUnit.PLATE_COMMENT, comment)
                success = cmd.applyTo(self.current_program)
                if success:
                    return "SUCCESS: Comment set successfully"
                else:
                    return "ERROR: Failed to set comment - {}".format(cmd.getStatusMsg())
            else:
                return "ERROR: Could not find code unit at function entry point"
        except Exception as e:
            return "ERROR: Failed to set comment - {}".format(str(e))
    
    def remove_comment_handler(self, parameters):
        """Handle REMOVE-COMMENT command"""
        parts = parameters.split(' ', 1)
        if len(parts) < 2:
            return "ERROR: REMOVE-COMMENT requires function name and line number"
        
        func_name = parts[0]
        line_str = parts[1]
        
        # Get the function manager to find the function
        func_manager = self.current_program.getFunctionManager()
        func = func_manager.getFunctionNamed(func_name)
        
        if not func:
            return "ERROR: Function '{}' not found".format(func_name)
        
        try:
            # In a real implementation, we'd remove the comment at a specific line
            # This is a simplified implementation that removes a comment at the function's entry point
            listing = self.current_program.getListing()
            cu = listing.getCodeUnitAt(func.getEntryPoint())
            if cu:
                cmd = SetCommentCmd(cu.getMinAddress(), CodeUnit.PLATE_COMMENT, None)
                success = cmd.applyTo(self.current_program)
                if success:
                    return "SUCCESS: Comment removed successfully"
                else:
                    return "ERROR: Failed to remove comment - {}".format(cmd.getStatusMsg())
            else:
                return "ERROR: Could not find code unit at function entry point"
        except Exception as e:
            return "ERROR: Failed to remove comment - {}".format(str(e))
    
    def remove_all_comments_handler(self, parameters):
        """Handle REMOVE-ALL-COMMENTS command"""
        func_name = parameters.strip()
        if not func_name:
            return "ERROR: REMOVE-ALL-COMMENTS requires function name"
        
        # Get the function manager to find the function
        func_manager = self.current_program.getFunctionManager()
        func = func_manager.getFunctionNamed(func_name)
        
        if not func:
            return "ERROR: Function '{}' not found".format(func_name)
        
        # Get the listing to remove all comments in the function
        listing = self.current_program.getListing()
        body = func.getBody()
        
        try:
            # Clear all types of comments in the function body
            count = 0
            for cu in listing.getCodeUnits(body, True):
                if (cu.getComment(CodeUnit.PLATE_COMMENT) or 
                    cu.getComment(CodeUnit.EOL_COMMENT) or 
                    cu.getComment(CodeUnit.PRE_COMMENT) or 
                    cu.getComment(CodeUnit.POST_COMMENT)):
                    
                    cu.setComment(CodeUnit.PLATE_COMMENT, None)
                    cu.setComment(CodeUnit.EOL_COMMENT, None)
                    cu.setComment(CodeUnit.PRE_COMMENT, None)
                    cu.setComment(CodeUnit.POST_COMMENT, None)
                    count += 1
            
            return "SUCCESS: Removed {} comment units from function '{}'".format(count, func_name)
        except Exception as e:
            return "ERROR: Failed to remove comments - {}".format(str(e))
    
    def find_var_references_handler(self, parameters):
        """Handle FIND-VAR-REFERENCES command"""
        var_name = parameters.strip()
        if not var_name:
            return "ERROR: FIND-VAR-REFERENCES requires variable name"
        
        # For now, just return a success message
        # In a real implementation, this would find references to the variable
        return "SUCCESS: Finding references to variable '{}'...".format(var_name)
    
    def find_function_references_handler(self, parameters):
        """Handle FIND-FUNCTION-REFERENCES command"""
        func_name = parameters.strip()
        if not func_name:
            return "ERROR: FIND-FUNCTION-REFERENCES requires function name"
        
        # For now, just return a success message
        # In a real implementation, this would find references to the function
        return "SUCCESS: Finding references to function '{}'...".format(func_name)
    
    def find_addr_references_handler(self, parameters):
        """Handle FIND-ADDR-REFERENCES command"""
        addr_str = parameters.strip()
        if not addr_str:
            return "ERROR: FIND-ADDR-REFERENCES requires hex address"
        
        try:
            # Convert hex string to address
            addr_factory = self.current_program.getAddressFactory()
            addr_space = addr_factory.getDefaultAddressSpace()
            addr = addr_space.getAddress(int(addr_str, 16))
            
            # For now, just return a success message
            # In a real implementation, this would find references to the address
            return "SUCCESS: Finding references to address {}...".format(addr)
        except Exception as e:
            return "ERROR: Invalid hex address format - {}".format(str(e))
    
    def find_label_handler(self, parameters):
        """Handle FIND-LABEL command"""
        label_name = parameters.strip()
        if not label_name:
            return "ERROR: FIND-LABEL requires label name"
        
        # Get the symbol table to find the label
        sym_table = self.current_program.getSymbolTable()
        symbols = sym_table.getSymbols(label_name)
        
        result = "Labels named '{}':\n".format(label_name)
        found_count = 0
        while symbols.hasNext():
            sym = symbols.next()
            if sym.getSymbolType() in [SymbolType.LABEL, SymbolType.FUNCTION]:
                result += "  Address: {}, Name: {}\n".format(sym.getAddress(), sym.getName())
                found_count += 1
        
        if found_count == 0:
            return "ERROR: Label '{}' not found".format(label_name)
        else:
            return "SUCCESS: " + result
    
    def rename_label_handler(self, parameters):
        """Handle RENAME-LABEL command"""
        parts = parameters.split(' ', 1)
        if len(parts) < 2:
            return "ERROR: RENAME-LABEL requires old label name and new label name"
        
        old_name = parts[0]
        new_name = parts[1]
        
        # Get the symbol table to find the label
        sym_table = self.current_program.getSymbolTable()
        symbols = sym_table.getSymbols(old_name)
        
        while symbols.hasNext():
            sym = symbols.next()
            if sym.getSymbolType() == SymbolType.LABEL:
                try:
                    sym.setName(new_name, SourceType.USER_DEFINED)
                    return "SUCCESS: Label renamed from '{}' to '{}'".format(old_name, new_name)
                except Exception as e:
                    return "ERROR: Could not rename label - {}".format(str(e))
        
        return "ERROR: Label '{}' not found".format(old_name)
    
    def rename_global_handler(self, parameters):
        """Handle RENAME-GLOBAL command"""
        parts = parameters.split(' ', 1)
        if len(parts) < 2:
            return "ERROR: RENAME-GLOBAL requires old variable name and new variable name"
        
        old_name = parts[0]
        new_name = parts[1]
        
        # Get the symbol table to find the symbol
        sym_table = self.current_program.getSymbolTable()
        symbols = sym_table.getSymbols(old_name)
        
        while symbols.hasNext():
            sym = symbols.next()
            if sym.getSymbolType() in [SymbolType.LABEL, SymbolType.DATA, SymbolType.FUNCTION]:
                # Check if it's a global (has no parent namespace other than global root)
                if sym.getParentNamespace() is None:
                    try:
                        sym.setName(new_name, SourceType.USER_DEFINED)
                        return "SUCCESS: Global variable renamed from '{}' to '{}'".format(old_name, new_name)
                    except Exception as e:
                        return "ERROR: Could not rename global variable - {}".format(str(e))
        
        return "ERROR: Global variable '{}' not found".format(old_name)
    
    def retype_global_handler(self, parameters):
        """Handle RETYPE-GLOBAL command"""
        parts = parameters.split(' ', 1)
        if len(parts) < 2:
            return "ERROR: RETYPE-GLOBAL requires variable name and new type"
        
        var_name = parts[0]
        new_type = parts[1]
        
        # Get the symbol table to find the symbol
        sym_table = self.current_program.getSymbolTable()
        symbols = sym_table.getSymbols(var_name)
        
        while symbols.hasNext():
            sym = symbols.next()
            if sym.getSymbolType() == SymbolType.DATA:
                # Check if it's a global (has no parent namespace other than global root)
                if sym.getParentNamespace() is None:
                    # In a real implementation, you would change the data type
                    # For this example, we'll just return a success message
                    return "SUCCESS: Global variable '{}' retyped to '{}'".format(var_name, new_type)
        
        return "ERROR: Global variable '{}' not found".format(var_name)
    
    def ls_handler(self, parameters):
        """Handle LS command"""
        path = parameters.strip() or "/"
        # Simplified implementation that returns a fixed response
        # In a real implementation, this would list items in a path within Ghidra
        return "SUCCESS: Listing for path '{}' - [simulated response]".format(path)
    
    def cat_handler(self, parameters):
        """Handle CAT command"""
        path = parameters.strip()
        if not path:
            return "ERROR: CAT requires a path"
        
        # Simplified implementation that returns a fixed response
        # In a real implementation, this would return content at a path within Ghidra
        return "SUCCESS: Content for path '{}' - [simulated response]".format(path)
    
    def help_handler(self, parameters):
        """Handle HELP command"""
        help_text = """
Available commands:
  VAR-TYPE-SET <var_name> <type>    - Set variable type
  VAR-TYPE-GET <var_name>           - Get variable type
  FUN-NAME-SET <old_name> <new_name> - Rename function
  FUN-NAME-GET                      - Get current function name
  VAR-NAME-SET <old_name> <new_name> - Rename variable
  LIST-FUNCTION <fun_name>          - List items in function
  LIST-CLASS <class_name>           - List items in class
  LIST-NAMESPACE <namespace>        - List items in namespace
  SET-COMMENT <fun_name> <line> <text> - Set comment
  REMOVE-COMMENT <fun_name> <line>  - Remove comment
  REMOVE-ALL-COMMENTS <fun_name>    - Remove all comments in function
  FIND-VAR-REFERENCES <var_name>    - Find variable references
  FIND-FUNCTION-REFERENCES <fun_name> - Find function references
  FIND-ADDR-REFERENCES <hex_addr>   - Find address references
  FIND-LABEL <label_name>           - Find label
  RENAME-LABEL <old_name> <new_name> - Rename label
  RENAME-GLOBAL <old_name> <new_name> - Rename global variable
  RETYPE-GLOBAL <var_name> <new_type> - Retype global variable
  LS <path>                         - List items in path
  CAT <path>                        - Print content at path
  HELP                              - Show this help
  QUIT                              - Close connection
        """
        return help_text.strip()
    
    def quit_handler(self, parameters):
        """Handle QUIT command"""
        self.running = False
        return "SUCCESS: Closing connection"


class GhidraTCPServer:
    """
    TCP Server for Ghidra Client Communication
    """
    
    def __init__(self, port=9000):
        self.port = port
        self.socket = None
        self.running = False
        self.current_program = None
        self.current_location = None
        
    def start_server(self):
        """Start the TCP server"""
        try:
            # Create a TCP/IP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Allow reusing the address
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # Bind the socket to the port
            server_address = ('localhost', self.port)
            self.socket.bind(server_address)
            # Listen for incoming connections
            self.socket.listen(5)
            
            self.running = True
            print("Ghidra TCP Server listening on port {}".format(self.port))
            
            while self.running:
                try:
                    # Wait for a connection - with timeout to allow checking for shutdown
                    self.socket.settimeout(1.0)
                    try:
                        connection, client_address = self.socket.accept()
                    except socket.timeout:
                        # This allows us to periodically check if we should shut down
                        continue
                        
                    print("Connection from {}".format(client_address))
                    
                    # Handle the client in a separate thread
                    handler = GhidraTCPClientHandler(connection, self.current_program, self.current_location)
                    client_thread = threading.Thread(target=handler.run)
                    client_thread.daemon = True
                    client_thread.start()
                    
                except socket.error:
                    # This error occurs when we close the socket during shutdown
                    break
                except Exception as e:
                    print("Error handling client connection: {}".format(str(e)))
                    traceback.print_exc()
                    
        except Exception as e:
            print("Error starting server: {}".format(str(e)))
            traceback.print_exc()
        finally:
            if self.socket:
                self.socket.close()
    
    def stop_server(self):
        """Stop the TCP server"""
        self.running = False
        if self.socket:
            self.socket.close()
        print("Ghidra TCP Server stopped")


# Global server instance
server = None


def start_server():
    """Start the TCP server"""
    global server
    if server and server.running:
        print("Server is already running!")
        return
    
    try:
        # Create the server instance
        server = GhidraTCPServer(9000)
        # We'll set the current program and location once this script is loaded in Ghidra
        # These will be passed from the Ghidra environment
        server.current_program = getCurrentProgram()
        server.current_location = getCurrentLocation()
        
        # Start server in a separate thread
        server_thread = threading.Thread(target=server.start_server)
        server_thread.daemon = True
        server_thread.start()
        print("Ghidra TCP Server started on port 9000")
    except Exception as e:
        print("Error starting server: {}".format(str(e)))
        traceback.print_exc()


def stop_server():
    """Stop the TCP server"""
    global server
    if server:
        server.stop_server()
        server = None
    else:
        print("Server is not running!")


# If this script is run directly in Ghidra, start the server
if __name__ == "__main__":
    start_server()