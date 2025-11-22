#!/usr/bin/env python3
"""
Utility script to fix the Ghidra TCP Server implementation by correcting the function name lookup bug.

The issue: Several commands use func_manager.getFunctionNamed() which is not a valid Ghidra API method.
The solution: Replace with the proper pattern of iterating through all functions to find by name.
"""

import re

def fix_server_implementation(file_path):
    """Fix the server implementation by correcting function name lookup bugs"""
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Store original content to compare later
    original_content = content
    
    # Replace all instances of the incorrect method with proper function-finding logic
    # Pattern: func_manager.getFunctionNamed(variable)
    # Should become: find_function_by_name(func_manager, variable)
    content = re.sub(
        r'(\w+)\.getFunctionNamed\(([^)]+)\)',
        r'find_function_by_name(\1, \2)',
        content
    )
    
    # Now add the helper function if it's not already in the file
    if 'def find_function_by_name(' not in content:
        # Insert the helper function near the beginning of the class
        class_start = content.find('\nclass GhidraTCPClientHandler:')
        if class_start != -1:
            # Find the first method in the class to insert after
            first_method = content.find('\n    def ', class_start)
            if first_method != -1:
                # Find the end of the line containing 'def' to insert after
                end_of_line = content.find('\n', first_method)
                if end_of_line != -1:
                    # Add our helper function
                    helper_func = '''
    
    def find_function_by_name(self, func_manager, func_name):
        """Helper function to find a function by name using the appropriate API"""
        for func in func_manager.getFunctions(True):
            if func.getName() == func_name:
                return func
        return None
'''
                    content = content[:end_of_line+1] + helper_func + content[end_of_line+1:]
    
    # Write the corrected content back to the file
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"Fixed function name lookup issues in {file_path}")
    
    if content != original_content:
        print("Changes were made to fix the implementation.")
    else:
        print("No changes needed or pattern not found.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python3 fix_server_bugs.py <server_file_path>")
        sys.exit(1)
    
    fix_server_implementation(sys.argv[1])