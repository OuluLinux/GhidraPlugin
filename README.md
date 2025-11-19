# GhidraTCPCommentingPlugin

## Overview
This is a Ghidra plugin that provides TCP server functionality to allow clients to communicate with and add comments to the binary being analyzed in Ghidra. The plugin creates a server that clients can connect to for collaborative analysis, similar to a directory service like Ghidra's CodeBrowser.

## Features
- TCP server for remote client connections
- Comment management system accessible via client connections
- Integration with Ghidra's CodeBrowser for displaying and managing comments
- Client directory functionality to track connected clients
- Command-based interface for client-server communication
- Support for adding, retrieving, and managing comments remotely

## Requirements
- Java 11 or higher
- Ghidra 10.0 or higher
- Gradle (for building)

## Building
To build the plugin:
```bash
./gradlew build
```

To install the plugin to your local Ghidra installation:
```bash
./gradlew install
```

## Usage
After installation, the plugin will appear in Ghidra's plugin list. Enable it in the CodeBrowser tool, and use the "Tools" menu to start the TCP server. The server will start on port 9000 by default.

## Client Commands
The following commands are supported by the TCP server:

### Navigation & Information Commands
- `ls <path>` - Show all items in the path (like in CodeBrowser)
- `cat <path>` - Print the C/C++ code as in CodeBrowser, if the path is FUN... similar printing for other items
- `help` - Show help information for all commands

### Variable Management Commands
- `var-type-set <var_name> <type>` - Change the type of variable, but check if it is valid first; print errors if not valid
- `var-type-get <var_name>` - Get the type of a variable
- `var-name-set <old_var_name> <new_var_name>` - Rename a variable

### Function Management Commands
- `fun-name-set <old_function_name> <new_function_name>` - Rename a function
- `fun-name-get` - Get the current function name
- `list-function <fun_name>` - Print all items (variables, classes, enums, etc.) in the scope of the function

### Class and Namespace Management Commands
- `list-class <class_name>` - Print all items in class
- `list-namespace <namespace>` - Print all items in namespace

### Comment Management Commands
- `set-comment <fun_name> <line> <text>` - Set text comment to code at the specified line in function
- `remove-comment <fun_name> <line>` - Remove comment at the specified line in function
- `remove-all-comments <fun_name>` - Remove all comments in function

### Code Export Commands
- `export-code <directory_path>` - Export all C/C++ code to the directory

### Reference Finding Commands
- `find-var-references <var_name>` - List all references to a variable (Location, Label, Code Unit, Context)
- `find-function-references <fun_name>` - List all references to a function
- `find-addr-references <hex_addr>` - Find all references to a hex address
- `find-label <label_name>` - Find a label by name

### Label Management Commands
- `rename-label <old_label_name> <new_label_name>` - Rename a label

### Advanced Analysis Commands
- `auto-create-structure <var_name>` - Use Ghidra's "auto create structure" tool for the variable
- `adjust-pointer-offset <var_name> <offset>` - Adjust the pointer offset for the variable
- `find-text <text>` - Find all locations for text (part of a C-string)
- `rename-case <function_name> <line> <text>` - Rename a case in a switch statement. Will return error if the enum or number is not valid
- `find-equate-string <string>` - Search for strings with number literal values (enums, macros, static const int, etc.)
- `set-equate-string <function_name> <line> <column> <id>` - Replace number literal with equate string value
- `remove-equate-string <function_name> <line> <column>` - Revert to the number literal
- `rename-global <old_var_name> <new_var_name>` - Rename global variable
- `retype-global <var_name> <new_type>` - Set global variable's type
- `find-type-references <type_path>` - Find references to type
- `find-references-data <any_name>` - Find references to name. Gives list with columns of Location, Label, Code Unit, Context
- `find-references-addr <hex_addr>` - Find references to address
- `quit` - Close the connection to the server

### Example client usage:
```
> ls FUN::main
SUCCESS: Items in path 'FUN::main': local_var_1, local_var_2, param_1

> cat FUN::main
SUCCESS: Content of path 'FUN::main': int main(int argc, char* argv[]) { ... }

> var-type-set local_var_1 int*
SUCCESS: Type 'int*' set for variable 'local_var_1'

> var-type-get local_var_1
SUCCESS: Type for parameter 'local_var_1' is 'int*'

> fun-name-set current_func new_function_name
SUCCESS: Function renamed from 'current_func' to 'new_function_name'

> fun-name-get
SUCCESS: Current function name is 'new_function_name'

> set-comment main 5 "This is the start of main function"
SUCCESS: Comment set for function 'main' at entry point: This is the start of main function

> remove-comment main 5
SUCCESS: Comment removed for function 'main' at entry point

> remove-all-comments main
SUCCESS: 3 comments removed for function 'main'

> list-function main
SUCCESS: Items in function 'main':
  param 0: argc (int)
  param 1: argv (char**)
  local: localVar (int)

> find-var-references localVar
SUCCESS: References to variable 'localVar' found at: 0x40100a (read), 0x40100f (write)

> find-text "Hello World"
SUCCESS: Text 'Hello World' found at: 0x401500 (string reference), 0x40201a (usage in main)

> find-label my_label
SUCCESS: Label 'my_label' found at address 0x40102a

> rename-label old_label new_label
SUCCESS: Label renamed from 'old_label' to 'new_label'

> help
SUCCESS: Available commands:
  ls <path> - Show all items in the path (like in CodeBrowser)
  cat <path> - Print the C/C++ code as in CodeBrowser...
  ...
  (full command list shown)
```

## Architecture
The plugin follows Ghidra's standard plugin architecture, extending Plugin or CommonPluginTool as appropriate. It implements a TCP server using Java's networking libraries, with proper resource management and threading considerations for the Ghidra environment.

Client connections are handled by the ClientHandler class, which parses commands and responds appropriately. The ClientDirectoryManager maintains information about connected clients and tracks comments in the current program.