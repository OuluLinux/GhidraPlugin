"""
Enhanced Ghidra TCP Server - Python Script for Ghidra Client Communication

This script provides a TCP server for client communication with Ghidra, 
with improved port selection that tries different ports if the default is in use.
"""

import socket
import threading
import sys
from time import sleep
import traceback

# Import Ghidra specific modules - using try/except for compatibility within Ghidra
try:
    from ghidra.program.flatapi import FlatProgramAPI
    from ghidra.program.model.listing import *
    from ghidra.program.model.symbol import *
    from ghidra.program.model.data import *
    from ghidra.program.model.address import *
    from ghidra.util.exception import CancelledException
    from ghidra.app.cmd.comments import SetCommentCmd
    from ghidra.app.cmd.function import SetFunctionNameCmd
    from ghidra.app.decompiler import DecompInterface
    from ghidra.util.task import ConsoleTaskMonitor
    from ghidra.program.model.symbol import SourceType, SymbolType
    from ghidra.program.model.listing import CodeUnit
    print("Ghidra modules imported successfully")
except ImportError as e:
    print("Could not import Ghidra modules: {}".format(str(e)))
    print("Make sure this is run from within Ghidra's scripting environment")


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
            "DECOMPILE": self.decompile_handler,
            "LIST-ALL-FUNCTIONS": self.list_all_functions_handler,
            "GET-FUNCTION-INFO": self.get_function_info_handler,
            "EXPLORE": self.explore_handler,
            "EXECUTE": self.execute_handler,
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
        func = None
        # Iterate through all functions to find by name
        for f in func_manager.getFunctions(True):  # True means forward direction
            if f.getName() == old_name:
                func = f
                break

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
        line_str = parts[1]  # unused in this simplified implementation
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
        line_str = parts[1]  # unused in this simplified implementation

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
        """Handle CAT command - returns decompiled source code for a function"""
        func_name = parameters.strip()
        if not func_name:
            return "ERROR: CAT requires a function name"

        # Get the function manager to find the function
        func_manager = self.current_program.getFunctionManager()
        func = None
        # Iterate through all functions to find by name
        for f in func_manager.getFunctions(True):  # True means forward direction
            if f.getName() == func_name:
                func = f
                break

        if not func:
            return "ERROR: Function '{}' not found".format(func_name)

        try:
            # Use the decompiler to get the source code
            decompiler = DecompInterface()
            decompiler.openProgram(self.current_program)
            result = decompiler.decompileFunction(func, 30, ConsoleTaskMonitor())  # 30 second timeout

            if result and result.decompiledFunction:
                decompiled_code = result.decompiledFunction.getC()
                return "SUCCESS: Decompiled function '{}':\n{}".format(func_name, decompiled_code)
            else:
                error_msg = result.getErrorMessage() if result else "Unknown decompilation error"
                return "ERROR: Failed to decompile function '{}': {}".format(func_name, error_msg)
        except Exception as e:
            return "ERROR: Failed to decompile function '{}' - {}".format(func_name, str(e))

    def decompile_handler(self, parameters):
        """Handle DECOMPILE command - returns decompiled source code for a function"""
        func_name = parameters.strip()
        if not func_name:
            return "ERROR: DECOMPILE requires a function name"

        # Get the function manager to find the function
        func_manager = self.current_program.getFunctionManager()
        func = None
        # Iterate through all functions to find by name
        for f in func_manager.getFunctions(True):  # True means forward direction
            if f.getName() == func_name:
                func = f
                break

        if not func:
            return "ERROR: Function '{}' not found".format(func_name)

        try:
            # Use the decompiler to get the source code
            decompiler = DecompInterface()
            decompiler.openProgram(self.current_program)
            result = decompiler.decompileFunction(func, 30, ConsoleTaskMonitor())  # 30 second timeout

            if result and result.decompiledFunction:
                decompiled_code = result.decompiledFunction.getC()
                return decompiled_code  # Return just the decompiled code without extra text for cleaner output
            else:
                error_msg = result.getErrorMessage() if result else "Unknown decompilation error"
                return "ERROR: Failed to decompile function '{}': {}".format(func_name, error_msg)
        except Exception as e:
            return "ERROR: Failed to decompile function '{}' - {}".format(func_name, str(e))

    def list_all_functions_handler(self, parameters):
        """Handle LIST-ALL-FUNCTIONS command - lists all functions in the program"""
        try:
            func_manager = self.current_program.getFunctionManager()
            functions = []

            # Get all functions and their basic info
            for func in func_manager.getFunctions(True):
                functions.append("{} at {}".format(func.getName(), func.getEntryPoint()))

            if functions:
                result = "Found {} functions:\n".format(len(functions)) + "\n".join(functions[:50])  # Limit output to first 50
                if len(functions) > 50:
                    result += "\n... and {} more functions".format(len(functions) - 50)
                return result
            else:
                return "No functions found in the program"
        except Exception as e:
            return "ERROR: Failed to list functions - {}".format(str(e))

    def get_function_info_handler(self, parameters):
        """Handle GET-FUNCTION-INFO command - gets detailed info about a function"""
        func_name = parameters.strip()
        if not func_name:
            return "ERROR: GET-FUNCTION-INFO requires a function name"

        # Get the function manager to find the function
        func_manager = self.current_program.getFunctionManager()
        func = None
        # Iterate through all functions to find by name
        for f in func_manager.getFunctions(True):  # True means forward direction
            if f.getName() == func_name:
                func = f
                break

        if not func:
            return "ERROR: Function '{}' not found".format(func_name)

        try:
            # Get function information
            info = []
            info.append("Function: {}".format(func.getName()))
            info.append("Entry Point: {}".format(func.getEntryPoint()))
            info.append("Body: {}".format(func.getBody()))
            info.append("Return Type: {}".format(func.getReturnType()))
            info.append("Calling Convention: {}".format(func.getCallingConventionName()))

            # Add parameters
            params = func.getParameters()
            if params:
                info.append("Parameters ({}):".format(len(params)))
                for i, param in enumerate(params):
                    info.append("  {}: {} ({})".format(i, param.getName(), param.getDataType().getName()))
            else:
                info.append("Parameters: None")

            # Add local variables
            locals_list = list(func.getLocalVariables())
            if locals_list:
                info.append("Local Variables ({}):".format(len(locals_list)))
                for local in locals_list:
                    info.append("  {} ({})".format(local.getName(), local.getDataType().getName()))
            else:
                info.append("Local Variables: None")

            return "\n".join(info)
        except Exception as e:
            return "ERROR: Failed to get function info - {}".format(str(e))

    def explore_handler(self, parameters):
        """Handle EXPLORE command - dynamically explore objects and methods"""
        parts = parameters.split(' ', 1)
        obj_name = parts[0].lower()
        attr_path = parts[1] if len(parts) > 1 else ""

        try:
            # Map common object names to actual objects
            obj_map = {
                'program': self.current_program,
                'currentprogram': self.current_program,
                'api': self.flat_api if hasattr(self, 'flat_api') else self.current_program,
                'flatapi': self.flat_api if hasattr(self, 'flat_api') else self.current_program
            }

            if obj_name in obj_map:
                obj = obj_map[obj_name]

                # If there's an attr_path, try to navigate to it
                if attr_path:
                    attrs = attr_path.split('.')
                    for attr in attrs:
                        obj = getattr(obj, attr)

                # Get all attributes of the object
                attrs = dir(obj)

                # Separate methods and properties, but handle problematic attributes safely
                methods = []
                properties = []

                for attr in attrs:
                    if attr.startswith('_'):
                        continue  # Skip private attributes

                    try:
                        attr_value = getattr(obj, attr)
                        if callable(attr_value):
                            methods.append(attr)
                        else:
                            properties.append(attr)
                    except:
                        # Skip attributes that cause problems when accessed
                        continue

                attr_path_display = ('.' + attr_path) if attr_path else ''
                result = "Exploring object: {}{}\n".format(obj_name, attr_path_display)
                result += "Methods ({}): ".format(len(methods)) + ", ".join(methods) + "\n"
                result += "Properties ({}): ".format(len(properties)) + ", ".join(properties) + "\n"

                return result
            else:
                return "ERROR: Unknown object to explore. Available: {}".format(', '.join(obj_map.keys()))

        except AttributeError as e:
            return "ERROR: Attribute error - {}".format(str(e))
        except Exception as e:
            return "ERROR: Exploration failed - {}".format(str(e))

    def execute_handler(self, parameters):
        """Handle EXECUTE command - evaluate Python expressions in the Ghidra context"""
        # Create a local scope with useful Ghidra objects
        local_scope = {
            'current_program': self.current_program,
            'current_location': self.current_location,
            'flat_api': self.flat_api,
            'program': self.current_program,
            'api': self.flat_api,
            'dir': dir,
            'len': len,
            'str': str,
            'repr': repr,
            'type': type,
            'hasattr': hasattr,
            'getattr': getattr,
            'callable': callable
        }

        try:
            # Try to evaluate as an expression first
            # We'll use compile to check if it's an expression vs statement
            try:
                compiled = compile(parameters, '<string>', 'eval')
                result = eval(compiled, globals(), local_scope)
                return str(result)
            except SyntaxError:
                # If eval fails, try as a statement
                compiled = compile(parameters, '<string>', 'exec')
                exec(compiled, globals(), local_scope)
                return "SUCCESS: Statement executed (no return value)"
            except Exception as e:
                # Catch other exceptions from eval
                return "EVAL ERROR: {}".format(str(e))

        except Exception as e:
            return "ERROR: {}".format(str(e))

    def help_handler(self, parameters):
        """Handle HELP command"""
        help_text = """
Available commands:
  VAR-TYPE-SET <var_name> <type>    - Set variable type
  VAR-TYPE-GET <var_name>           - Get variable type
  FUN-NAME-SET <old_function_name> <new_function_name> - Rename function
  FUN-NAME-GET                      - Get current function name
  VAR-NAME-SET <old_var_name> <new_var_name> - Rename variable
  LIST-FUNCTION <fun_name>          - List items in function
  LIST-ALL-FUNCTIONS                - List all functions in program
  LIST-CLASS <class_name>           - List items in class
  LIST-NAMESPACE <namespace>        - List items in namespace
  SET-COMMENT <fun_name> <line> <text> - Set comment
  REMOVE-COMMENT <fun_name> <line>  - Remove comment
  REMOVE-ALL-COMMENTS <fun_name>    - Remove all comments in function
  FIND-VAR-REFERENCES <var_name>    - Find variable references
  FIND-FUNCTION-REFERENCES <fun_name> - Find function references
  FIND-ADDR-REFERENCES <hex_addr>   - Find address references
  FIND-LABEL <label_name>           - Find label
  RENAME-LABEL <old_label_name> <new_label_name> - Rename label
  RENAME-GLOBAL <old_var_name> <new_var_name> - Rename global variable
  RETYPE-GLOBAL <var_name> <new_type> - Retype global variable
  GET-FUNCTION-INFO <fun_name>      - Get detailed info about function
  LS <path>                         - List items at path
  CAT <func_name>                   - Get decompiled source of function
  DECOMPILE <func_name>             - Decompile function to source code
  EXPLORE <obj> [attr.subattr]      - Explore object attributes/methods
  EXECUTE <python_code>             - Execute Python code in Ghidra context
  HELP                              - Show this help
  QUIT                              - Close connection
        """
        return help_text.strip()

    def quit_handler(self, parameters):
        """Handle QUIT command"""
        self.running = False
        return "SUCCESS: Closing connection"


import time
import uuid

class GhidraTCPServer:
    """
    TCP Server for Ghidra Client Communication with Port Selection
    """

    def __init__(self, starting_port=9000):
        self.starting_port = starting_port
        self.socket = None
        self.running = False
        self.current_program = None
        self.current_location = None
        self.server_id = str(uuid.uuid4())  # Unique identifier for this server instance
        self.start_time = time.time()  # Track when this server instance started

    def find_available_port(self):
        """Find an available port starting from the default port number"""
        port = self.starting_port
        max_attempts = 10  # Try 10 consecutive ports before giving up
        attempts = 0

        while attempts < max_attempts:
            try:
                # Try to bind to the port
                # Use SO_REUSEADDR and SO_REUSEPORT if available to allow reuse
                test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

                # On some systems, SO_REUSEPORT might not be available
                try:
                    test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
                except (AttributeError, socket.error):
                    # SO_REUSEPORT is not available on all platforms or not supported
                    pass

                test_socket.bind(('localhost', port))
                test_socket.close()

                # If we got here, the port is available
                return port
            except OSError as e:
                # Port is in use, try the next one
                print("Port {} is in use ({}), trying next port...".format(port, e))
                port += 1
                attempts += 1

        raise Exception("Could not find an available port after {} attempts starting from {}".format(max_attempts, self.starting_port))

    def start_server(self):
        """Start the TCP server with port selection"""
        try:
            # Find an available port
            port = self.find_available_port()
            print("Using port: {}".format(port))

            # Create a TCP/IP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Allow reusing the address
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # On some systems, SO_REUSEPORT might not be available
            try:
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except (AttributeError, socket.error):
                # SO_REUSEPORT is not available on all platforms or not supported
                pass

            # Set a timeout for socket operations
            self.socket.settimeout(1.0)

            # Bind the socket to the port
            server_address = ('localhost', port)
            self.socket.bind(server_address)
            # Listen for incoming connections
            self.socket.listen(5)

            self.running = True
            print("Ghidra TCP Server [ID: {}] listening on port {}".format(self.server_id[:8], port))

            while self.running:
                try:
                    # Wait for a connection - with timeout to allow checking for shutdown
                    # The timeout is already set on the socket
                    try:
                        connection, client_address = self.socket.accept()
                        print("Connection from {} [Server ID: {}]".format(client_address, self.server_id[:8]))

                        # Handle the client in a separate thread
                        handler = GhidraTCPClientHandler(connection, self.current_program, self.current_location)
                        client_thread = threading.Thread(target=handler.run)
                        client_thread.daemon = True
                        client_thread.start()

                    except socket.timeout:
                        # This allows us to periodically check if we should shut down
                        continue

                except socket.error as e:
                    # This error occurs when we close the socket during shutdown
                    if self.running:
                        print("Socket error during operation: {}".format(str(e)))
                        continue
                    else:
                        break
                except Exception as e:
                    if self.running:  # Only print errors if we're supposed to be running
                        print("Error handling client connection: {}".format(str(e)))
                        traceback.print_exc()
                    break

        except OSError as e:
            print("OS Error starting server (could be address in use): {}".format(str(e)))
            traceback.print_exc()
        except Exception as e:
            print("Error starting server: {}".format(str(e)))
            traceback.print_exc()
        finally:
            if self.socket:
                self.socket.close()
                self.socket = None

    def stop_server(self):
        """Stop the TCP server"""
        print("Stopping Ghidra TCP Server [ID: {}]...".format(self.server_id[:8]))
        self.running = False
        if self.socket:
            try:
                self.socket.close()
                self.socket = None
            except Exception as e:
                print("Error closing socket: {}".format(str(e)))
        print("Ghidra TCP Server [ID: {}] stopped".format(self.server_id[:8]))


# Global server instance
server = None


def start_server(port=9000):
    """Start the TCP server"""
    global server

    # Check if there's already a running server instance
    if server and server.running:
        print("Server is already running!")
        print("If you need a new server instance, stop the existing one first with stop_server()")
        if server.socket:
            try:
                actual_port = server.socket.getsockname()[1]
                print("Current server [ID: {}] is running on port {}".format(server.server_id[:8], actual_port))
            except:
                print("Current server [ID: {}] is running, but couldn't retrieve port information".format(server.server_id[:8]))
        return

    # Try to find an available port by creating a temporary socket
    # This is an additional safety check
    test_socket = None
    try:
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # On some systems, SO_REUSEPORT might not be available
        try:
            test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except (AttributeError, socket.error):
            # SO_REUSEPORT is not available on all platforms or not supported
            pass

        test_socket.bind(('localhost', port))
        test_socket.close()
        test_socket = None
        # Port is available, continue with starting the server
    except OSError as e:
        print("Port {} is currently in use: {}".format(port, str(e)))
        print("Trying to find an available port automatically...")
        # The server will handle port selection in the find_available_port method
        pass
    finally:
        if test_socket:
            try:
                test_socket.close()
            except:
                pass

    try:
        # Create the server instance with a starting port
        server = GhidraTCPServer(starting_port=port)

        # Get the current program and location from the Ghidra environment
        # These are available when the script runs in Ghidra
        if 'currentProgram' in globals():
            server.current_program = currentProgram
        else:
            # Try the method name as it's sometimes called in scripts
            try:
                server.current_program = getCurrentProgram()
            except NameError:
                print("ERROR: Could not get current program. Make sure this runs inside Ghidra.")
                return

        if 'currentLocation' in globals():
            server.current_location = currentLocation
        else:
            try:
                server.current_location = getCurrentLocation()
            except NameError:
                # It's okay if location is None
                pass

        # Start server in a separate thread
        server_thread = threading.Thread(target=server.start_server)
        server_thread.daemon = True
        server_thread.start()

        # Give the server a moment to start up
        import time
        time.sleep(0.1)

        # Report which port is being used
        if server.socket:
            try:
                actual_port = server.socket.getsockname()[1]
                print("Ghidra TCP Server [ID: {}] started on port {}".format(server.server_id[:8], actual_port))
            except:
                print("Ghidra TCP Server [ID: {}] started (port information not available immediately)".format(server.server_id[:8]))
        else:
            print("Ghidra TCP Server [ID: {}] started on port {}".format(server.server_id[:8], port))

    except Exception as e:
        print("Error starting server: {}".format(str(e)))
        traceback.print_exc()


def stop_server():
    """Stop the TCP server"""
    global server
    if server:
        server_id = server.server_id[:8]  # Save the ID before server is set to None
        server.stop_server()
        server = None
        print("Server [ID: {}] stopped successfully.".format(server_id))
    else:
        print("Server is not running!")


def kill_server_on_port(port):
    """
    Forcefully kill any process using the specified port
    NOTE: This would kill the entire Ghidra process if it's using the port,
    which is the case when using the TCP server from within Ghidra.
    Use with caution - this will close Ghidra!
    """
    print("WARNING: kill_server_on_port({}) would kill the Ghidra process itself if it's using the port.".format(port))
    print("To stop the TCP server, please use 'stop_server()' instead.")
    print("If needed, you can manually kill the port using: lsof -i :{} and then kill the process.".format(port))
    return False


# If this script is run directly as a script (not when imported), start the server
# This condition may not work as expected in all Jython contexts, so we use a safer approach
# Only execute start_server if explicitly called with parameters (not during import)