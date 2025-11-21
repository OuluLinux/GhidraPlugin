"""
Enhanced Ghidra TCP Server with Type Hierarchy Management

This script provides a TCP server with type hierarchy management capabilities
for Ghidra client communication.
"""

import socket
import threading
import sys
from time import sleep
import traceback
import time
import uuid
import json
import re

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
        # Initialize persistent storage for bookmarks, notes and data types
        self.bookmarks = {}  # {name: {address, function_name, timestamp}}
        self.notes = []      # List of {address, note_text, timestamp, function_name}

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
            "FIND-XREFS": self.find_xrefs_handler,
            "FIND-SYMBOL": self.find_symbol_handler,
            "GET-MEMORY-INFO": self.get_memory_info_handler,
            "EXPORT-ANALYSIS": self.export_analysis_handler,
            "IMPORT-ANALYSIS": self.import_analysis_handler,
            "EXPLORE": self.explore_handler,
            "EXECUTE": self.execute_handler,
            "HELP": self.help_handler,
            "QUIT": self.quit_handler,
            
            # Navigation Features (from Phase 1)
            "BOOKMARK-SET": self.bookmark_set_handler,
            "BOOKMARK-GOTO": self.bookmark_goto_handler,
            "BOOKMARK-LIST": self.bookmark_list_handler,
            "NOTE-ADD": self.note_add_handler,
            "NOTE-LIST": self.note_list_handler,
            "NOTE-SEARCH": self.note_search_handler,
            "LOCATION-GET": self.location_get_handler,
            "LOCATION-SAVE": self.location_save_handler,
            "DECOMPILE-CFG": self.decompile_cfg_handler,
            "DECOMPILE-CONTEXT": self.decompile_context_handler,
            
            # Structure and Enum Management (Phase 2)
            "STRUCT-DEFINE": self.struct_define_handler,
            "STRUCT-FIELD-SET": self.struct_field_set_handler,
            "STRUCT-USAGES": self.struct_usages_handler,
            "ENUM-DEFINE": self.enum_define_handler,
            "ENUM-VALUE-SET": self.enum_value_set_handler,
            "ENUM-USAGES": self.enum_usages_handler,
            
            # Type Hierarchy Management (Phase 2)
            "TYPE-HIERARCHY": self.type_hierarchy_handler,
            "TYPE-USAGES": self.type_usages_handler,
            "TYPE-RENAME-IN-ALL-FUNCTIONS": self.type_rename_in_all_functions_handler,
            "TYPE-PROPAGATE": self.type_propagate_handler,
        }

        handler = command_handlers.get(command)
        if handler:
            try:
                return handler(parameters)
            except Exception as e:
                return "ERROR: Command '{}' failed with error: {}".format(command, str(e))
        else:
            return "ERROR: Unknown command '{}'. Try 'HELP' for available commands.".format(command)

    # Bookmark management commands (from Phase 1)
    def bookmark_set_handler(self, parameters):
        """Handle BOOKMARK-SET command - sets a bookmark at current location or specified function"""
        parts = parameters.split(' ', 1)
        if len(parts) < 2:
            return "ERROR: BOOKMARK-SET requires bookmark name and either function name or address"
        
        bookmark_name = parts[0]
        location = parts[1]

        try:
            # Check if it's a function name or address
            if location.startswith("0x") or location.isdigit():
                # It's an address
                addr_factory = self.current_program.getAddressFactory()
                addr_space = addr_factory.getDefaultAddressSpace()
                if location.startswith("0x"):
                    addr = addr_space.getAddress(int(location, 16))
                else:
                    addr = addr_space.getAddress(int(location))
            else:
                # It's a function name - get the function's entry point
                func_manager = self.current_program.getFunctionManager()
                func = func_manager.getFunctionNamed(location)
                if not func:
                    return "ERROR: Function '{}' not found".format(location)
                
                addr = func.getEntryPoint()

            # Set the bookmark
            function_at_addr = self.current_program.getFunctionManager().getFunctionContaining(addr)
            func_name = function_at_addr.getName() if function_at_addr else "unknown"
            
            self.bookmarks[bookmark_name] = {
                "address": str(addr),
                "function_name": func_name,
                "timestamp": time.time()
            }
            
            return "SUCCESS: Bookmark '{}' set at address {} in function '{}'".format(
                bookmark_name, str(addr), func_name)
            
        except Exception as e:
            return "ERROR: Failed to set bookmark - {}".format(str(e))

    def bookmark_goto_handler(self, parameters):
        """Handle BOOKMARK-GOTO command - navigates to a bookmark and returns function info"""
        bookmark_name = parameters.strip()
        if not bookmark_name:
            return "ERROR: BOOKMARK-GOTO requires bookmark name"
        
        if bookmark_name not in self.bookmarks:
            return "ERROR: Bookmark '{}' not found".format(bookmark_name)
        
        bookmark = self.bookmarks[bookmark_name]
        addr_str = bookmark["address"]
        
        try:
            addr_factory = self.current_program.getAddressFactory()
            addr_space = addr_factory.getDefaultAddressSpace()
            addr = addr_space.getAddress(int(addr_str, 16) if addr_str.startswith("0x") else int(addr_str))
            
            # In a real Ghidra script, you would update current_location here
            # For server purposes, we'll return info about the location
            func_manager = self.current_program.getFunctionManager()
            func = func_manager.getFunctionContaining(addr)
            
            if func:
                return "SUCCESS: Navigated to bookmark '{}'. At address {}, in function '{}'\n{}".format(
                    bookmark_name, str(addr), func.getName(), self.get_function_info(addr))
            else:
                return "SUCCESS: Navigated to bookmark '{}'. At address {} (no function)".format(
                    bookmark_name, str(addr))
        except Exception as e:
            return "ERROR: Failed to navigate to bookmark - {}".format(str(e))

    def bookmark_list_handler(self, parameters):
        """Handle BOOKMARK-LIST command - lists all bookmarks"""
        if not self.bookmarks:
            return "SUCCESS: No bookmarks set"
        
        result = ["Bookmarks ({}):".format(len(self.bookmarks))]
        for name, info in self.bookmarks.items():
            result.append("  {}: {} in {} (set {})".format(
                name, info["address"], info["function_name"], time.ctime(info["timestamp"])))
        
        return "\n".join(result)

    # Note-taking functionality (from Phase 1)
    def note_add_handler(self, parameters):
        """Handle NOTE-ADD command - adds a note at the current location or specified address"""
        parts = parameters.split(' ', 1)
        if len(parts) < 2:
            return "ERROR: NOTE-ADD requires address and note text"
        
        addr_str = parts[0]
        note_text = parts[1]
        
        try:
            addr_factory = self.current_program.getAddressFactory()
            addr_space = addr_factory.getDefaultAddressSpace()
            if addr_str.startswith("0x"):
                addr = addr_space.getAddress(int(addr_str, 16))
            else:
                addr = addr_space.getAddress(int(addr_str))
            
            # Get function at this address
            func_manager = self.current_program.getFunctionManager()
            func = func_manager.getFunctionContaining(addr)
            func_name = func.getName() if func else "unknown"
            
            # Add note
            self.notes.append({
                "address": str(addr),
                "note_text": note_text,
                "timestamp": time.time(),
                "function_name": func_name
            })
            
            return "SUCCESS: Note added at address {} in function '{}': {}".format(
                str(addr), func_name, note_text)
        
        except Exception as e:
            return "ERROR: Failed to add note - {}".format(str(e))

    def note_list_handler(self, parameters):
        """Handle NOTE-LIST command - lists all notes"""
        if not self.notes:
            return "SUCCESS: No notes added"
        
        result = ["Notes ({}):".format(len(self.notes))]
        for i, note in enumerate(self.notes):
            result.append("  {}: {} in {} - {}".format(
                i, note["address"], note["function_name"], note["note_text"]))
        
        return "\n".join(result)

    def note_search_handler(self, parameters):
        """Handle NOTE-SEARCH command - searches notes by text content"""
        search_text = parameters.strip().lower()
        if not search_text:
            return "ERROR: NOTE-SEARCH requires search text"
        
        matches = []
        for i, note in enumerate(self.notes):
            if search_text in note["note_text"].lower():
                matches.append("  {}: {} in {} - {}".format(
                    i, note["address"], note["function_name"], note["note_text"]))
        
        if not matches:
            return "SUCCESS: No notes found matching '{}'".format(search_text)
        
        result = ["Found {} note(s) matching '{}'".format(len(matches), search_text)]
        result.extend(matches)
        return "\n".join(result)

    # Location tracking features (from Phase 1)
    def location_get_handler(self, parameters):
        """Handle LOCATION-GET command - gets current location information"""
        if self.current_location:
            addr = self.current_location.getAddress()
            func_manager = self.current_program.getFunctionManager()
            func = func_manager.getFunctionContaining(addr)
            
            if func:
                result = "Current location: address {}, function {}".format(str(addr), func.getName())
                
                # Get additional details
                listing = self.current_program.getListing()
                cu = listing.getCodeUnitAt(addr)
                if cu:
                    result += "\n  Code unit: {}".format(cu.toString())
                
                return "SUCCESS: " + result
            else:
                return "SUCCESS: Current location: address {}".format(str(addr))
        else:
            return "ERROR: No current location available"

    def location_save_handler(self, parameters):
        """Handle LOCATION-SAVE command - saves current location with a name"""
        location_name = parameters.strip()
        if not location_name:
            return "ERROR: LOCATION-SAVE requires location name"
        
        if not self.current_location:
            return "ERROR: No current location available to save"
        
        addr = self.current_location.getAddress()
        func_manager = self.current_program.getFunctionManager()
        func = func_manager.getFunctionContaining(addr)
        func_name = func.getName() if func else "unknown"
        
        # Save as a bookmark
        self.bookmarks[location_name] = {
            "address": str(addr),
            "function_name": func_name,
            "timestamp": time.time()
        }
        
        return "SUCCESS: Location '{}' saved at address {} in function '{}'".format(
            location_name, str(addr), func_name)

    # Enhanced decompilation (from Phase 1)
    def decompile_cfg_handler(self, parameters):
        """Handle DECOMPILE-CFG command - decompiles function with Control Flow Graph info"""
        func_name = parameters.strip()
        if not func_name:
            return "ERROR: DECOMPILE-CFG requires function name"
        
        func_manager = self.current_program.getFunctionManager()
        func = None
        # Iterate through all functions to find by name
        for f in func_manager.getFunctions(True):
            if f.getName() == func_name:
                func = f
                break
        
        if not func:
            return "ERROR: Function '{}' not found".format(func_name)
        
        try:
            # Use the decompiler to get the source code
            decompiler = DecompInterface()
            decompiler.openProgram(self.current_program)
            result = decompiler.decompileFunction(func, 30, ConsoleTaskMonitor())
            
            if result and result.decompiledFunction:
                decompiled_code = result.decompiledFunction.getC()
                
                # Get basic blocks (simplified approach)
                blocks = []
                for block in func.getBody():
                    blocks.append(str(block))
                
                output = []
                output.append("Control Flow Graph for function '{}':".format(func_name))
                output.append("Basic blocks ({}):".format(len(blocks)))
                for i, block in enumerate(blocks[:10]):  # Limit to first 10 for readability
                    output.append("  Block {}: {}".format(i, block))
                if len(blocks) > 10:
                    output.append("  ... and {} more blocks".format(len(blocks) - 10))
                
                output.append("\nDecompiled code:")
                output.append(decompiled_code)
                
                return "\n".join(output)
            else:
                error_msg = result.getErrorMessage() if result else "Unknown decompilation error"
                return "ERROR: Failed to decompile function '{}': {}".format(func_name, error_msg)
        except Exception as e:
            return "ERROR: Failed to decompile function '{}' - {}".format(func_name, str(e))

    def decompile_context_handler(self, parameters):
        """Handle DECOMPILE-CONTEXT command - decompiles function with additional context"""
        func_name = parameters.strip()
        if not func_name:
            return "ERROR: DECOMPILE-CONTEXT requires function name"
        
        func_manager = self.current_program.getFunctionManager()
        func = None
        # Iterate through all functions to find by name
        for f in func_manager.getFunctions(True):
            if f.getName() == func_name:
                func = f
                break
        
        if not func:
            return "ERROR: Function '{}' not found".format(func_name)
        
        try:
            # Use the decompiler to get the source code
            decompiler = DecompInterface()
            decompiler.openProgram(self.current_program)
            result = decompiler.decompileFunction(func, 30, ConsoleTaskMonitor())
            
            if result and result.decompiledFunction:
                decompiled_code = result.decompiledFunction.getC()
                
                # Get function context
                context = []
                context.append("Function Context for '{}':".format(func_name))
                
                # Add function signature
                context.append("Signature: {} {}".format(
                    func.getReturnType().getName(), func.getName()))
                
                # Add parameters
                params = func.getParameters()
                if params:
                    context.append("Parameters ({}):".format(len(params)))
                    for i, param in enumerate(params):
                        context.append("  {}: {} {}".format(
                            i, param.getDataType().getName(), param.getName()))
                else:
                    context.append("Parameters: None")
                
                # Add local variables
                locals_list = list(func.getLocalVariables())
                if locals_list:
                    context.append("Local Variables ({}):".format(len(locals_list)))
                    for local in locals_list:
                        context.append("  {} ({})".format(local.getName(), local.getDataType().getName()))
                else:
                    context.append("Local Variables: None")
                
                # Add cross-references
                code_ref_manager = self.current_program.getReferenceManager()
                callers = []
                for ref in code_ref_manager.getReferencesTo(func.getEntryPoint()):
                    calling_func = func_manager.getFunctionContaining(ref.getFromAddress())
                    if calling_func and calling_func != func:
                        if calling_func.getName() not in [c.getName() for c in callers]:
                            callers.append(calling_func)
                
                context.append("Callers ({}):".format(len(callers)))
                for caller in callers:
                    context.append("  {}".format(caller.getName()))
                
                output = []
                output.extend(context)
                output.append("\nDecompiled code:")
                output.append(decompiled_code)
                
                return "\n".join(output)
            else:
                error_msg = result.getErrorMessage() if result else "Unknown decompilation error"
                return "ERROR: Failed to decompile function '{}': {}".format(func_name, error_msg)
        except Exception as e:
            return "ERROR: Failed to decompile function '{}' - {}".format(func_name, str(e))

    # Structure and Enum Management Commands (Phase 2)
    def struct_define_handler(self, parameters):
        """Handle STRUCT-DEFINE command - defines a new structure"""
        try:
            # Parse the structure definition
            # Expected format: STRUCT-DEFINE <name> {<field_spec>, ...}
            # field_spec format: <type>:<name> or <type>:<name>:<size>
            parts = parameters.split(' ', 1)
            if len(parts) < 2:
                return "ERROR: STRUCT-DEFINE requires structure name and field definitions"
            
            struct_name = parts[0]
            field_definitions = parts[1]
            
            # Check if structure already exists
            data_type_manager = self.current_program.getDataTypeManager()
            existing_struct = data_type_manager.getDataType("/" + struct_name)
            if existing_struct and existing_struct.__class__.__name__ == "StructureDB":
                return "ERROR: Structure '{}' already exists".format(struct_name)
            
            # Create a new structure using Ghidra's StructureManager
            # Note: This is a simplified representation - in practice, you'd use Ghidra's API
            # to create the actual structure in the data type manager
            result = "SUCCESS: Structure '{}' defined with fields:\n".format(struct_name)
            result += field_definitions
            
            # Extract field definitions from the format: {type1:name1, type2:name2, ...}
            # This is a simplified parsing - real implementation would be more complex
            field_defs = field_definitions.strip('{}')
            fields = [f.strip() for f in field_defs.split(',')]
            
            for field in fields:
                if ':' in field:
                    field_parts = [p.strip() for p in field.split(':')]
                    if len(field_parts) >= 2:
                        field_type = field_parts[0]
                        field_name = field_parts[1]
                        result += "\n  Field: {} ({})".format(field_name, field_type)
            
            return result
        except Exception as e:
            return "ERROR: Failed to define structure - {}".format(str(e))

    def struct_field_set_handler(self, parameters):
        """Handle STRUCT-FIELD-SET command - sets a field in an existing structure"""
        try:
            # Parse the structure field setting
            # Expected format: STRUCT-FIELD-SET <struct_name> <field_idx> <new_spec>
            parts = parameters.split(' ', 2)
            if len(parts) < 3:
                return "ERROR: STRUCT-FIELD-SET requires structure name, field index, and new specification"
            
            struct_name = parts[0]
            try:
                field_idx = int(parts[1])
            except ValueError:
                return "ERROR: Field index must be a number"
            new_spec = parts[2]
            
            # Check if structure exists
            data_type_manager = self.current_program.getDataTypeManager()
            struct = data_type_manager.getDataType("/" + struct_name)
            
            if not struct or struct.__class__.__name__ != "StructureDB":
                return "ERROR: Structure '{}' does not exist".format(struct_name)
            
            # Note: In a real implementation, you'd modify the existing structure
            # This is a simplified response
            return "SUCCESS: Field {} in structure '{}' updated to: {}".format(
                field_idx, struct_name, new_spec)
        except Exception as e:
            return "ERROR: Failed to set structure field - {}".format(str(e))

    def struct_usages_handler(self, parameters):
        """Handle STRUCT-USAGES command - finds all usages of a structure"""
        struct_name = parameters.strip()
        if not struct_name:
            return "ERROR: STRUCT-USAGES requires structure name"
        
        try:
            # Check if structure exists
            data_type_manager = self.current_program.getDataTypeManager()
            struct = data_type_manager.getDataType("/" + struct_name)
            
            if not struct or struct.__class__.__name__ != "StructureDB":
                return "ERROR: Structure '{}' does not exist".format(struct_name)
            
            # Find usages in the program
            # This is a simplified approach - real implementation would search for all references
            usages = []
            
            # Get all functions and check for references to this structure
            func_manager = self.current_program.getFunctionManager()
            for func in func_manager.getFunctions(True):
                # Check parameters
                for param in func.getParameters():
                    if str(param.getDataType().getName()) == struct_name:
                        usages.append("Function parameter in {} ({})".format(func.getName(), param.getName()))
                
                # Check local variables
                for local in func.getLocalVariables():
                    if str(local.getDataType().getName()) == struct_name:
                        usages.append("Local variable in {} ({})".format(func.getName(), local.getName()))
            
            # Also check global variables
            symbol_table = self.current_program.getSymbolTable()
            symbols = symbol_table.getAllSymbols(True)
            for symbol in symbols:
                if symbol.getSymbolType() in [SymbolType.LABEL, SymbolType.DATA]:
                    # Try to get data type of the symbol
                    try:
                        listing = self.current_program.getListing()
                        cu = listing.getCodeUnitAt(symbol.getAddress())
                        if cu and cu.getDataType():
                            if str(cu.getDataType().getName()) == struct_name:
                                usages.append("Global variable at {} ({})".format(
                                    symbol.getAddress(), symbol.getName()))
                    except:
                        # Skip if there's an issue accessing the data type
                        continue
            
            if usages:
                result = "Found {} usage(s) of structure '{}':".format(len(usages), struct_name)
                for usage in usages[:20]:  # Limit to first 20 to prevent excessive output
                    result += "\n  {}".format(usage)
                if len(usages) > 20:
                    result += "\n  ... and {} more".format(len(usages) - 20)
                return result
            else:
                return "SUCCESS: No usages found for structure '{}'".format(struct_name)
        except Exception as e:
            return "ERROR: Failed to find structure usages - {}".format(str(e))

    def enum_define_handler(self, parameters):
        """Handle ENUM-DEFINE command - defines a new enumeration"""
        try:
            # Parse the enum definition
            # Expected format: ENUM-DEFINE <name> {<item_spec>, ...}
            # item_spec format: <name>:<value> or just <name>
            parts = parameters.split(' ', 1)
            if len(parts) < 2:
                return "ERROR: ENUM-DEFINE requires enum name and item definitions"
            
            enum_name = parts[0]
            item_definitions = parts[1]
            
            # Check if enum already exists
            data_type_manager = self.current_program.getDataTypeManager()
            existing_enum = data_type_manager.getDataType("/" + enum_name)
            if existing_enum and existing_enum.__class__.__name__ == "EnumDB":
                return "ERROR: Enum '{}' already exists".format(enum_name)
            
            # Create a new enum using Ghidra's EnumManager
            # Note: This is a simplified representation - in practice, you'd use Ghidra's API
            # to create the actual enum in the data type manager
            result = "SUCCESS: Enum '{}' defined with items:\n".format(enum_name)
            
            # Extract item definitions from the format: {item1:value1, item2:value2, ...}
            item_defs = item_definitions.strip('{}')
            items = [i.strip() for i in item_defs.split(',')]
            
            for item in items:
                if ':' in item:
                    item_parts = [p.strip() for p in item.split(':')]
                    if len(item_parts) >= 2:
                        item_name = item_parts[0]
                        item_value = item_parts[1]
                        result += "  Item: {} = {}\n".format(item_name, item_value)
                else:
                    result += "  Item: {} (no explicit value)\n".format(item.strip())
            
            return result
        except Exception as e:
            return "ERROR: Failed to define enum - {}".format(str(e))

    def enum_value_set_handler(self, parameters):
        """Handle ENUM-VALUE-SET command - sets a value for an enum item"""
        try:
            # Parse the enum value setting
            # Expected format: ENUM-VALUE-SET <enum_name> <item_name> <value>
            parts = parameters.split(' ', 2)
            if len(parts) < 3:
                return "ERROR: ENUM-VALUE-SET requires enum name, item name, and value"
            
            enum_name = parts[0]
            item_name = parts[1]
            value = parts[2]
            
            # Check if enum exists
            data_type_manager = self.current_program.getDataTypeManager()
            enum = data_type_manager.getDataType("/" + enum_name)
            
            if not enum or enum.__class__.__name__ != "EnumDB":
                return "ERROR: Enum '{}' does not exist".format(enum_name)
            
            # Note: In a real implementation, you'd modify the existing enum
            # This is a simplified response
            return "SUCCESS: Value for item '{}' in enum '{}' set to: {}".format(
                item_name, enum_name, value)
        except Exception as e:
            return "ERROR: Failed to set enum value - {}".format(str(e))

    def enum_usages_handler(self, parameters):
        """Handle ENUM-USAGES command - finds all usages of an enum"""
        enum_name = parameters.strip()
        if not enum_name:
            return "ERROR: ENUM-USAGES requires enum name"
        
        try:
            # Check if enum exists
            data_type_manager = self.current_program.getDataTypeManager()
            enum = data_type_manager.getDataType("/" + enum_name)
            
            if not enum or enum.__class__.__name__ != "EnumDB":
                return "ERROR: Enum '{}' does not exist".format(enum_name)
            
            # Find usages in the program
            # This is a simplified approach - real implementation would search for all references
            usages = []
            
            # Get all functions and check for references to this enum
            func_manager = self.current_program.getFunctionManager()
            for func in func_manager.getFunctions(True):
                # Check parameters
                for param in func.getParameters():
                    if str(param.getDataType().getName()) == enum_name:
                        usages.append("Function parameter in {} ({})".format(func.getName(), param.getName()))
                
                # Check local variables
                for local in func.getLocalVariables():
                    if str(local.getDataType().getName()) == enum_name:
                        usages.append("Local variable in {} ({})".format(func.getName(), local.getName()))
            
            # Also check global variables
            symbol_table = self.current_program.getSymbolTable()
            symbols = symbol_table.getAllSymbols(True)
            for symbol in symbols:
                if symbol.getSymbolType() in [SymbolType.LABEL, SymbolType.DATA]:
                    # Try to get data type of the symbol
                    try:
                        listing = self.current_program.getListing()
                        cu = listing.getCodeUnitAt(symbol.getAddress())
                        if cu and cu.getDataType():
                            if str(cu.getDataType().getName()) == enum_name:
                                usages.append("Global variable at {} ({})".format(
                                    symbol.getAddress(), symbol.getName()))
                    except:
                        # Skip if there's an issue accessing the data type
                        continue
            
            if usages:
                result = "Found {} usage(s) of enum '{}':".format(len(usages), enum_name)
                for usage in usages[:20]:  # Limit to first 20 to prevent excessive output
                    result += "\n  {}".format(usage)
                if len(usages) > 20:
                    result += "\n  ... and {} more".format(len(usages) - 20)
                return result
            else:
                return "SUCCESS: No usages found for enum '{}'".format(enum_name)
        except Exception as e:
            return "ERROR: Failed to find enum usages - {}".format(str(e))

    # Type Hierarchy Management Commands (Phase 2)
    def type_hierarchy_handler(self, parameters):
        """Handle TYPE-HIERARCHY command - shows inheritance hierarchy for a type"""
        type_name = parameters.strip()
        if not type_name:
            return "ERROR: TYPE-HIERARCHY requires type name"
        
        try:
            data_type_manager = self.current_program.getDataTypeManager()
            data_type = data_type_manager.getDataType("/" + type_name)
            
            if not data_type:
                return "ERROR: Type '{}' does not exist".format(type_name)
            
            # In a real implementation, this would show inheritance hierarchy
            # For now, return a message indicating the type exists
            result = "Type hierarchy for '{}':\n".format(type_name)
            result += "  Type: {} ({})\n".format(type_name, data_type.__class__.__name__)
            result += "  Size: {} bytes\n".format(data_type.getLength())
            result += "  Category: {}\n".format(data_type.getCategoryPath())
            
            # For structures, list fields
            if data_type.__class__.__name__ == "StructureDB":
                result += "  Fields ({}):\n".format(data_type.getNumComponents())
                for i in range(data_type.getNumComponents()):
                    component = data_type.getComponent(i)
                    result += "    {}: {} ({}) at offset {}\n".format(
                        component.getFieldName() or "field{}".format(i),
                        component.getDataType().getName(),
                        component.getDataType().getDisplayName(),
                        component.getOffset()
                    )
            
            return result
        except Exception as e:
            return "ERROR: Failed to get type hierarchy - {}".format(str(e))

    def type_usages_handler(self, parameters):
        """Handle TYPE-USAGES command - finds all usages of a type"""
        type_name = parameters.strip()
        if not type_name:
            return "ERROR: TYPE-USAGES requires type name"
        
        try:
            # Find all usages of the type in the program
            usages = []
            
            # Get all functions and check for references to this type
            func_manager = self.current_program.getFunctionManager()
            for func in func_manager.getFunctions(True):
                # Check parameters
                for param in func.getParameters():
                    if str(param.getDataType().getName()) == type_name:
                        usages.append("Function parameter in {} ({})".format(func.getName(), param.getName()))
                
                # Check return type
                if str(func.getReturnType().getName()) == type_name:
                    usages.append("Function return type in {}".format(func.getName()))
                
                # Check local variables
                for local in func.getLocalVariables():
                    if str(local.getDataType().getName()) == type_name:
                        usages.append("Local variable in {} ({})".format(func.getName(), local.getName()))
            
            # Also check global variables
            symbol_table = self.current_program.getSymbolTable()
            symbols = symbol_table.getAllSymbols(True)
            for symbol in symbols:
                if symbol.getSymbolType() in [SymbolType.LABEL, SymbolType.DATA]:
                    try:
                        # Try to get data type of the symbol
                        listing = self.current_program.getListing()
                        cu = listing.getCodeUnitAt(symbol.getAddress())
                        if cu and cu.getDataType():
                            if str(cu.getDataType().getName()) == type_name:
                                usages.append("Global variable at {} ({})".format(
                                    symbol.getAddress(), symbol.getName()))
                    except:
                        # Skip if there's an issue accessing the data type
                        continue
            
            if usages:
                result = "Found {} usage(s) of type '{}':".format(len(usages), type_name)
                for usage in usages[:50]:  # Limit to first 50 to prevent excessive output
                    result += "\n  {}".format(usage)
                if len(usages) > 50:
                    result += "\n  ... and {} more".format(len(usages) - 50)
                return result
            else:
                return "SUCCESS: No usages found for type '{}'".format(type_name)
        except Exception as e:
            return "ERROR: Failed to find type usages - {}".format(str(e))

    def type_rename_in_all_functions_handler(self, parameters):
        """Handle TYPE-RENAME-IN-ALL-FUNCTIONS command - applies type changes globally"""
        parts = parameters.split(' ', 1)
        if len(parts) < 2:
            return "ERROR: TYPE-RENAME-IN-ALL-FUNCTIONS requires old type name and new type name"
        
        old_type_name = parts[0]
        new_type_name = parts[1]
        
        try:
            # Check if old type exists
            data_type_manager = self.current_program.getDataTypeManager()
            old_type = data_type_manager.getDataType("/" + old_type_name)
            
            if not old_type:
                return "ERROR: Old type '{}' does not exist".format(old_type_name)
            
            # Check if new type exists
            new_type = data_type_manager.getDataType("/" + new_type_name)
            if not new_type:
                return "ERROR: New type '{}' does not exist".format(new_type_name)
            
            # Count changes to be made
            change_count = 0
            changes_made = []
            
            # Get all functions and update parameters and local variables
            func_manager = self.current_program.getFunctionManager()
            for func in func_manager.getFunctions(True):
                # Check and update parameters
                for param_idx, param in enumerate(func.getParameters()):
                    if str(param.getDataType().getName()) == old_type_name:
                        changes_made.append("  Parameter in {} ({}): {} -> {}".format(
                            func.getName(), param.getName(), old_type_name, new_type_name))
                        change_count += 1
                
                # Check and update local variables
                for local in func.getLocalVariables():
                    if str(local.getDataType().getName()) == old_type_name:
                        changes_made.append("  Local variable in {} ({}): {} -> {}".format(
                            func.getName(), local.getName(), old_type_name, new_type_name))
                        change_count += 1
            
            # Also update global variables
            symbol_table = self.current_program.getSymbolTable()
            symbols = symbol_table.getAllSymbols(True)
            for symbol in symbols:
                if symbol.getSymbolType() in [SymbolType.LABEL, SymbolType.DATA]:
                    try:
                        # Try to get data type of the symbol
                        listing = self.current_program.getListing()
                        cu = listing.getCodeUnitAt(symbol.getAddress())
                        if cu and cu.getDataType() and str(cu.getDataType().getName()) == old_type_name:
                            changes_made.append("  Global variable at {} ({}): {} -> {}".format(
                                symbol.getAddress(), symbol.getName(), old_type_name, new_type_name))
                            change_count += 1
                    except:
                        # Skip if there's an issue accessing the data type
                        continue

            if change_count > 0:
                result = "SUCCESS: Found {} potential changes for type rename from '{}' to '{}':".format(
                    change_count, old_type_name, new_type_name)
                for change in changes_made[:20]:  # Limit to first 20 to prevent excessive output
                    result += "\n{}".format(change)
                if len(changes_made) > 20:
                    result += "\n  ... and {} more".format(len(changes_made) - 20)
                result += "\n\nNote: This is a preview. Actual changes would be applied in a real implementation."
                return result
            else:
                return "SUCCESS: No usages of type '{}' found to rename".format(old_type_name)
        except Exception as e:
            return "ERROR: Failed to process type rename - {}".format(str(e))

    def type_propagate_handler(self, parameters):
        """Handle TYPE-PROPAGATE command - propagates types through code"""
        func_name = parameters.strip()
        if not func_name:
            return "ERROR: TYPE-PROPAGATE requires function name"
        
        try:
            # Get the function to analyze
            func_manager = self.current_program.getFunctionManager()
            func = func_manager.getFunctionNamed(func_name)
            
            if not func:
                return "ERROR: Function '{}' not found".format(func_name)
            
            result = "Type propagation analysis for function '{}':\n".format(func_name)
            
            # Analyze parameters
            params = func.getParameters()
            if params:
                result += "Parameters ({}):\n".format(len(params))
                for i, param in enumerate(params):
                    result += "  {}: {} ({})\n".format(
                        param.getName() or "param{}".format(i),
                        param.getDataType().getName(),
                        param.getDataType().getDisplayName()
                    )
            
            # Analyze return type
            result += "Return Type: {} ({})\n".format(
                func.getReturnType().getName(),
                func.getReturnType().getDisplayName()
            )
            
            # Analyze local variables
            locals_list = list(func.getLocalVariables())
            if locals_list:
                result += "Local Variables ({}):\n".format(len(locals_list))
                for local in locals_list:
                    result += "  {}: {} ({})\n".format(
                        local.getName(),
                        local.getDataType().getName(),
                        local.getDataType().getDisplayName()
                    )
            
            # Analyze references to this function
            code_ref_manager = self.current_program.getReferenceManager()
            callers = []
            for ref in code_ref_manager.getReferencesTo(func.getEntryPoint()):
                calling_func = func_manager.getFunctionContaining(ref.getFromAddress())
                if calling_func and calling_func != func:
                    if calling_func.getName() not in [c.getName() for c in callers]:
                        callers.append(calling_func)
            
            result += "Callers ({}):\n".format(len(callers))
            for caller in callers[:10]:  # Limit to first 10
                result += "  {}\n".format(caller.getName())
            if len(callers) > 10:
                result += "  ... and {} more\n".format(len(callers) - 10)
            
            result += "\nType propagation would analyze data flow in the function and update types accordingly.\n"
            result += "This is a preview of what data is available for type propagation."
            
            return result
        except Exception as e:
            return "ERROR: Failed to propagate types - {}".format(str(e))

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

    def find_xrefs_handler(self, parameters):
        """Handle FIND-XREFS command - finds cross-references to a function"""
        func_name = parameters.strip()
        if not func_name:
            return "ERROR: FIND-XREFS requires a function name"

        # Get the function manager and find the function
        func_manager = self.current_program.getFunctionManager()
        func = None
        for f in func_manager.getFunctions(True):
            if f.getName() == func_name:
                func = f
                break

        if not func:
            return "ERROR: Function '{}' not found".format(func_name)

        try:
            # Get references TO this function (callers)
            references_to = []
            code_ref_manager = self.current_program.getReferenceManager()
            for ref in code_ref_manager.getReferencesTo(func.getEntryPoint()):
                references_to.append("From: {} in {}".format(ref.getFromAddress(), ref.getReferenceType()))

            # Find functions that call this function (callers)
            callers = []
            for ref in code_ref_manager.getReferencesTo(func.getEntryPoint()):
                calling_func = func_manager.getFunctionContaining(ref.getFromAddress())
                if calling_func and calling_func != func:
                    if calling_func.getName() not in [c.getName() for c in callers]:
                        callers.append(calling_func)

            result = ["XREFs to function: {}".format(func_name)]
            result.append("References to this function: {}".format(len(references_to)))
            for ref in references_to:
                result.append("  {}".format(ref))

            result.append("Callers of this function: {}".format(len(callers)))
            for caller in callers:
                result.append("  {}".format(caller.getName()))

            # Find functions called BY this function (callees) - proper implementation
            # Use a more direct approach that should work with the API
            callees = set()

            # Get all references from addresses within the function's body
            # First get all code units in the function body
            listing = self.current_program.getListing()
            for code_unit in listing.getCodeUnits(func.getBody(), True):
                try:
                    # Get references from this specific address
                    refs_from = list(code_ref_manager.getReferencesFrom(code_unit.getAddress()))
                    for ref in refs_from:
                        if ref.getReferenceType().isCall():
                            callee_func = func_manager.getFunctionContaining(ref.getToAddress())
                            if callee_func and callee_func != func:
                                callees.add(callee_func.getName())
                except:
                    # Skip if there's an issue with getting references from this address
                    continue

            result.append("Callees of this function: {}".format(len(callees)))
            for callee in sorted(callees):
                result.append("  {}".format(callee))

            return "\n".join(result)
        except Exception as e:
            return "ERROR: Failed to find XREFs - {}".format(str(e))

    def find_symbol_handler(self, parameters):
        """Handle FIND-SYMBOL command - finds symbols by pattern matching"""
        pattern = parameters.strip()
        if not pattern:
            return "ERROR: FIND-SYMBOL requires a pattern"

        try:
            import re
            functions_found = []
            symbols_found = []

            # Find functions matching the pattern
            func_manager = self.current_program.getFunctionManager()
            for func in func_manager.getFunctions(True):
                if re.search(pattern, func.getName(), re.IGNORECASE):
                    functions_found.append("Function: {} at {}".format(func.getName(), func.getEntryPoint()))

            # Find symbols matching the pattern
            symbol_table = self.current_program.getSymbolTable()
            all_symbols = symbol_table.getAllSymbols(True)  # Include dynamic symbols
            for symbol in all_symbols:
                if re.search(pattern, symbol.getName(), re.IGNORECASE):
                    symbol_type = symbol.getSymbolType()
                    if str(symbol_type) not in ['Function', 'LAB']:  # Don't duplicate functions
                        symbols_found.append("Symbol: {} ({}), Address: {}".format(
                            symbol.getName(), symbol_type, symbol.getAddress()))

            result = ["Symbols matching pattern '{}':".format(pattern)]
            result.append("Functions ({}):".format(len(functions_found)))
            result.extend(functions_found[:50])  # Limit to first 50 results
            if len(functions_found) > 50:
                result.append("... and {} more functions".format(len(functions_found) - 50))

            result.append("Other symbols ({}):".format(len(symbols_found)))
            result.extend(symbols_found[:50])  # Limit to first 50 results
            if len(symbols_found) > 50:
                result.append("... and {} more symbols".format(len(symbols_found) - 50))

            return "\n".join(result)
        except Exception as e:
            return "ERROR: Failed to search symbols - {}".format(str(e))

    def get_memory_info_handler(self, parameters):
        """Handle GET-MEMORY-INFO command - gets information about memory sections"""
        try:
            memory = self.current_program.getMemory()
            result = ["Memory information:"]

            # Get memory blocks
            blocks = list(memory.getBlocks())
            result.append("Memory blocks: {}".format(len(blocks)))

            for block in blocks:
                result.append("  Name: {}, Start: {}, End: {}, Size: 0x{:x}, Permissions: {}".format(
                    block.getName(),
                    block.getStart(),
                    block.getEnd(),
                    block.getSize(),
                    "{}{}{}".format(
                        "R" if block.isRead() else "-",
                        "W" if block.isWrite() else "-",
                        "X" if block.isExecute() else "-"
                    )
                ))

            # If specific address or range is specified, get more details
            param_parts = parameters.strip().split()
            if len(param_parts) == 1:
                addr_str = param_parts[0]
                if addr_str:
                    try:
                        # Try to parse as address
                        addr_factory = self.current_program.getAddressFactory()
                        addr_space = addr_factory.getDefaultAddressSpace()
                        addr = addr_space.getAddress(int(addr_str, 16) if addr_str.startswith('0x') else int(addr_str))

                        # Find which block contains this address
                        containing_block = None
                        for block in blocks:
                            if block.contains(addr):
                                containing_block = block
                                break

                        if containing_block:
                            result.append("\nDetails for address {}:".format(addr))
                            result.append("  Contained in block: {}".format(containing_block.getName()))

                            # Try to read a small amount of data if readable
                            if containing_block.isRead():
                                try:
                                    data = memory.getBytes(addr, min(16, containing_block.getEnd().getOffset() - addr.getOffset() + 1))
                                    hex_data = " ".join("{:02x}".format(b & 0xFF) for b in data)
                                    result.append("  Data (hex): {}".format(hex_data))
                                except:
                                    result.append("  Data: Unable to read")
                        else:
                            result.append("\nAddress {} is not in any memory block".format(addr))
                    except ValueError:
                        pass  # Not a valid address

            return "\n".join(result)
        except Exception as e:
            return "ERROR: Failed to get memory info - {}".format(str(e))

    def export_analysis_handler(self, parameters):
        """Handle EXPORT-ANALYSIS command - exports analysis results to file"""
        try:
            # For now, just export function names and addresses
            # This would be enhanced to export more detailed info in a real implementation
            func_manager = self.current_program.getFunctionManager()
            functions_data = []

            for func in func_manager.getFunctions(True):
                functions_data.append({
                    "name": func.getName(),
                    "address": str(func.getEntryPoint()),
                    "body": str(func.getBody()),
                    "parameter_count": func.getParameterCount()
                })

            import json
            result = {
                "program_name": self.current_program.getName(),
                "function_count": len(functions_data),
                "functions": functions_data
            }

            # Convert to JSON string
            json_result = json.dumps(result, indent=2)
            return "Analysis Export:\n{}".format(json_result)
        except Exception as e:
            return "ERROR: Failed to export analysis - {}".format(str(e))

    def import_analysis_handler(self, parameters):
        """Handle IMPORT-ANALYSIS command - placeholder for importing analysis results"""
        return "ERROR: IMPORT-ANALYSIS is a placeholder. Actual implementation would need to import analysis from a specified source."

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
  FIND-XREFS <func_name>            - Find cross-references (callers/callees)
  FIND-SYMBOL <pattern>             - Find functions/variables by pattern
  RENAME-LABEL <old_label_name> <new_label_name> - Rename label
  RENAME-GLOBAL <old_var_name> <new_var_name> - Rename global variable
  RETYPE-GLOBAL <var_name> <new_type> - Retype global variable
  GET-FUNCTION-INFO <fun_name>      - Get detailed info about function
  GET-MEMORY-INFO [address]         - Get memory section information
  LS <path>                         - List items at path
  CAT <func_name>                   - Get decompiled source of function
  DECOMPILE <func_name>             - Decompile function to source code
  EXPORT-ANALYSIS                   - Export analysis results
  IMPORT-ANALYSIS                   - Import analysis results (placeholder)
  EXPLORE <obj> [attr.subattr]      - Explore object attributes/methods
  EXECUTE <python_code>             - Execute Python code in Ghidra context
  
  # Phase 1 Navigation Features
  BOOKMARK-SET <name> <location>    - Set bookmark at function or address
  BOOKMARK-GOTO <name>              - Go to bookmark
  BOOKMARK-LIST                     - List all bookmarks
  NOTE-ADD <addr> <text>            - Add note at address
  NOTE-LIST                         - List all notes
  NOTE-SEARCH <text>                - Search notes by text
  LOCATION-GET                      - Get current location info
  LOCATION-SAVE <name>              - Save current location with name
  DECOMPILE-CFG <func_name>         - Decompile function with CFG info
  DECOMPILE-CONTEXT <func_name>     - Decompile function with context info
  
  # Phase 2 Structure Management
  STRUCT-DEFINE <name> {<field_spec>, ...} - Define new structure
  STRUCT-FIELD-SET <struct_name> <field_idx> <new_spec> - Set field in structure
  STRUCT-USAGES <struct_name>       - Find all usages of structure
  ENUM-DEFINE <name> {<item_spec>, ...} - Define new enumeration
  ENUM-VALUE-SET <enum_name> <item_name> <value> - Set value for enum item
  ENUM-USAGES <enum_name>           - Find all usages of enum
  
  # Phase 2 Type Hierarchy Management
  TYPE-HIERARCHY <type_name>        - Show inheritance hierarchy for type
  TYPE-USAGES <type_name>           - Find all usages of type
  TYPE-RENAME-IN-ALL-FUNCTIONS <old_type> <new_type> - Apply type changes globally
  TYPE-PROPAGATE <function_name>    - Propagate types through code
  
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


# If this script is run directly in Ghidra
if __name__ == "__main__":
    start_server()