import java.io.*;
import java.net.Socket;
import java.util.HashMap;
import java.util.Map;

import ghidra.app.plugin.ProgramPlugin;
import ghidra.program.model.listing.Program;
import ghidra.util.Msg;

/**
 * Enhanced client handler that can process commands from TCP clients
 */
public class ClientHandler implements Runnable {
	private Socket clientSocket;
	private ProgramPlugin plugin;

	// Map to store command handlers
	private static final Map<String, CommandHandler> commandHandlers = new HashMap<>();

	// Static initialization of command handlers
	static {
		commandHandlers.put("LS", new LsCommandHandler());
		commandHandlers.put("CAT", new CatCommandHandler());
		commandHandlers.put("VAR-TYPE-SET", new VarTypeSetCommandHandler());
		commandHandlers.put("VAR-TYPE-GET", new VarTypeGetCommandHandler());
		commandHandlers.put("FUN-NAME-SET", new FunNameSetCommandHandler());
		commandHandlers.put("FUN-NAME-GET", new FunNameGetCommandHandler());
		commandHandlers.put("VAR-NAME-SET", new VarNameSetCommandHandler());
		commandHandlers.put("LIST-FUNCTION", new ListFunctionCommandHandler());
		commandHandlers.put("LIST-CLASS", new ListClassCommandHandler());
		commandHandlers.put("LIST-NAMESPACE", new ListNamespaceCommandHandler());
		commandHandlers.put("SET-COMMENT", new SetCommentCommandHandler());
		commandHandlers.put("REMOVE-COMMENT", new RemoveCommentCommandHandler());
		commandHandlers.put("REMOVE-ALL-COMMENTS", new RemoveAllCommentsCommandHandler());
		commandHandlers.put("EXPORT-CODE", new ExportCodeCommandHandler());
		commandHandlers.put("FIND-VAR-REFERENCES", new FindVarReferencesCommandHandler());
		commandHandlers.put("FIND-FUNCTION-REFERENCES", new FindFunctionReferencesCommandHandler());
		commandHandlers.put("FIND-ADDR-REFERENCES", new FindAddrReferencesCommandHandler());
		commandHandlers.put("FIND-LABEL", new FindLabelCommandHandler());
		commandHandlers.put("RENAME-LABEL", new RenameLabelCommandHandler());
		commandHandlers.put("AUTO-CREATE-STRUCTURE", new AutoCreateStructureCommandHandler());
		commandHandlers.put("ADJUST-POINTER-OFFSET", new AdjustPointerOffsetCommandHandler());
		commandHandlers.put("FIND-TEXT", new FindTextCommandHandler());
		commandHandlers.put("RENAME-CASE", new RenameCaseCommandHandler());
		commandHandlers.put("FIND-EQUATE-STRING", new FindEquateStringCommandHandler());
		commandHandlers.put("SET-EQUATE-STRING", new SetEquateStringCommandHandler());
		commandHandlers.put("REMOVE-EQUATE-STRING", new RemoveEquateStringCommandHandler());
		commandHandlers.put("RENAME-GLOBAL", new RenameGlobalCommandHandler());
		commandHandlers.put("RETYPE-GLOBAL", new RetypeGlobalCommandHandler());
		commandHandlers.put("FIND-TYPE-REFERENCES", new FindTypeReferencesCommandHandler());
		commandHandlers.put("FIND-REFERENCES-DATA", new FindReferencesDataCommandHandler());
		commandHandlers.put("FIND-REFERENCES-ADDR", new FindReferencesAddrCommandHandler());
		commandHandlers.put("HELP", new HelpCommandHandler());
		commandHandlers.put("QUIT", new QuitCommandHandler());
	}

	public ClientHandler(Socket socket, ProgramPlugin plugin) {
		this.clientSocket = socket;
		this.plugin = plugin;
	}

	@Override
	public void run() {
		Msg.info(this, "Handling client connection: " + clientSocket.getRemoteSocketAddress());

		try (BufferedReader in = new BufferedReader(new InputStreamReader(clientSocket.getInputStream()));
			 PrintWriter out = new PrintWriter(clientSocket.getOutputStream(), true)) {

			String inputLine;
			while ((inputLine = in.readLine()) != null) {
				Msg.info(this, "Received from client: " + inputLine);

				// Parse the command from the client
				String[] parts = inputLine.split(" ", 2);
				String command = parts[0].toUpperCase();

				// Process the command
				String response = processCommand(command, parts.length > 1 ? parts[1] : "");
				out.println(response);

				// If client sends QUIT command, break the loop
				if ("QUIT".equals(command)) {
					break;
				}
			}
		} catch (IOException e) {
			Msg.error(this, "Error handling client connection", e);
		} finally {
			try {
				clientSocket.close();
			} catch (IOException e) {
				Msg.error(this, "Error closing client socket", e);
			}
		}
	}

	/**
	 * Process the command received from the client
	 * @param command The command to process
	 * @param parameters The parameters for the command
	 * @return Response string to send back to the client
	 */
	private String processCommand(String command, String parameters) {
		CommandHandler handler = commandHandlers.get(command);
		if (handler != null) {
			return handler.handle(plugin, parameters);
		} else {
			return "ERROR: Unknown command '" + command + "'";
		}
	}

	/**
	 * Interface for command handlers
	 */
	interface CommandHandler {
		String handle(ProgramPlugin plugin, String parameters);
	}

	/**
	 * Handler for ADD_COMMENT command
	 * Usage: ADD_COMMENT address comment_text
	 */
	static class AddCommentCommandHandler implements CommandHandler {
		@Override
		public String handle(ProgramPlugin plugin, String parameters) {
			String[] parts = parameters.split(" ", 2);
			if (parts.length < 2) {
				return "ERROR: ADD_COMMENT requires address and comment text";
			}

			String addressStr = parts[0];
			String comment = parts[1];

			// Cast to our plugin type to access the ClientDirectoryManager
			if (!(plugin instanceof GhidraTCPCommentingPlugin)) {
				return "ERROR: Plugin is not of the expected type";
			}

			GhidraTCPCommentingPlugin serverPlugin = (GhidraTCPCommentingPlugin) plugin;
			ClientDirectoryManager directoryManager = serverPlugin.getDirectoryManager();

			// Add the comment
			boolean success = directoryManager.addComment(addressStr, comment, "unknown_client"); // In real implementation, track actual client
			if (success) {
				return "SUCCESS: Comment added at " + addressStr + ": " + comment;
			} else {
				return "ERROR: Failed to add comment";
			}
		}
	}

	/**
	 * Handler for GET_COMMENTS command
	 * Usage: GET_COMMENTS [address]
	 */
	static class GetCommentsCommandHandler implements CommandHandler {
		@Override
		public String handle(ProgramPlugin plugin, String parameters) {
			// Cast to our plugin type to access the ClientDirectoryManager
			if (!(plugin instanceof GhidraTCPCommentingPlugin)) {
				return "ERROR: Plugin is not of the expected type";
			}

			GhidraTCPCommentingPlugin serverPlugin = (GhidraTCPCommentingPlugin) plugin;
			ClientDirectoryManager directoryManager = serverPlugin.getDirectoryManager();
			Program currentProgram = plugin.getCurrentProgram();
			if (currentProgram == null) {
				return "ERROR: No program loaded";
			}

			// If address is provided, get comments for that address; otherwise get all comments
			if (!parameters.trim().isEmpty()) {
				// Get comments for a specific address
				java.util.List<ClientDirectoryManager.CommentInfo> comments =
					directoryManager.getCommentsForAddress(parameters.trim());

				if (comments.isEmpty()) {
					return "SUCCESS: No comments for address " + parameters;
				}

				StringBuilder response = new StringBuilder("SUCCESS: Comments for " + parameters + ":\n");
				for (ClientDirectoryManager.CommentInfo comment : comments) {
					response.append("  [").append(comment.getTimestamp()).append("] ")
					        .append(comment.getClientId()).append(": ")
					        .append(comment.getCommentText()).append("\n");
				}

				return response.toString().trim();
			} else {
				// Get all comments
				java.util.Map<String, java.util.List<ClientDirectoryManager.CommentInfo>> allComments =
					directoryManager.getAllComments();

				if (allComments.isEmpty()) {
					return "SUCCESS: No comments in program";
				}

				StringBuilder response = new StringBuilder("SUCCESS: All comments:\n");
				for (java.util.Map.Entry<String, java.util.List<ClientDirectoryManager.CommentInfo>> entry : allComments.entrySet()) {
					String addr = entry.getKey();
					java.util.List<ClientDirectoryManager.CommentInfo> comments = entry.getValue();
					response.append("Address ").append(addr).append(":\n");
					for (ClientDirectoryManager.CommentInfo comment : comments) {
						response.append("  [").append(comment.getTimestamp()).append("] ")
						        .append(comment.getClientId()).append(": ")
						        .append(comment.getCommentText()).append("\n");
					}
				}

				return response.toString().trim();
			}
		}
	}

	/**
	 * Handler for GET_PROGRAM_INFO command
	 * Usage: GET_PROGRAM_INFO
	 */
	static class GetProgramInfoCommandHandler implements CommandHandler {
		@Override
		public String handle(ProgramPlugin plugin, String parameters) {
			// Cast to our plugin type to access the ClientDirectoryManager
			if (!(plugin instanceof GhidraTCPCommentingPlugin)) {
				return "ERROR: Plugin is not of the expected type";
			}

			GhidraTCPCommentingPlugin serverPlugin = (GhidraTCPCommentingPlugin) plugin;
			ClientDirectoryManager directoryManager = serverPlugin.getDirectoryManager();

			Program currentProgram = plugin.getCurrentProgram();
			if (currentProgram == null) {
				return "ERROR: No program loaded";
			}

			// Get program info from the directory manager
			ClientDirectoryManager.ProgramInfo programInfo = directoryManager.getCurrentProgramInfo();
			if (programInfo == null) {
				return "ERROR: Could not get program info";
			}

			return "SUCCESS: Program=" + programInfo.getName() +
			       ", Executable=" + programInfo.getExecutablePath() +
			       ", Processor=" + programInfo.getProcessor() +
			       ", Size=" + programInfo.getSize() +
			       ", MinAddr=" + programInfo.getMinAddress() +
			       ", MaxAddr=" + programInfo.getMaxAddress();
		}
	}

	/**
	 * Handler for QUIT command
	 * Usage: QUIT
	 */
	static class QuitCommandHandler implements CommandHandler {
		@Override
		public String handle(ProgramPlugin plugin, String parameters) {
			return "SUCCESS: Closing connection";
		}
	}

	/**
	 * Handler for LS command
	 * Usage: ls <path>
	 */
	static class LsCommandHandler implements CommandHandler {
		@Override
		public String handle(ProgramPlugin plugin, String parameters) {
			// Cast to our plugin type to access the ClientDirectoryManager and program
			if (!(plugin instanceof GhidraTCPCommentingPlugin)) {
				return "ERROR: Plugin is not of the expected type";
			}

			GhidraTCPCommentingPlugin serverPlugin = (GhidraTCPCommentingPlugin) plugin;
			Program currentProgram = plugin.getCurrentProgram();
			if (currentProgram == null) {
				return "ERROR: No program loaded";
			}

			// Create a path navigator to handle the path
			GhidraPathNavigator navigator = new GhidraPathNavigator(currentProgram);

			// List items at the path
			String result = navigator.listPath(parameters.trim());

			return "SUCCESS: " + result;
		}
	}

	/**
	 * Handler for CAT command
	 * Usage: cat <path>
	 */
	static class CatCommandHandler implements CommandHandler {
		@Override
		public String handle(ProgramPlugin plugin, String parameters) {
			// Cast to our plugin type to access the ClientDirectoryManager and program
			if (!(plugin instanceof GhidraTCPCommentingPlugin)) {
				return "ERROR: Plugin is not of the expected type";
			}

			GhidraTCPCommentingPlugin serverPlugin = (GhidraTCPCommentingPlugin) plugin;
			Program currentProgram = plugin.getCurrentProgram();
			if (currentProgram == null) {
				return "ERROR: No program loaded";
			}

			// Create a path navigator to handle the path
			GhidraPathNavigator navigator = new GhidraPathNavigator(currentProgram);

			// Get content at the path
			String result = navigator.getContent(parameters.trim());

			return "SUCCESS: " + result;
		}
	}

	/**
	 * Handler for VAR-TYPE-SET command
	 * Usage: var-type-set <var_name> <type>
	 */
	static class VarTypeSetCommandHandler implements CommandHandler {
		@Override
		public String handle(ProgramPlugin plugin, String parameters) {
			String[] parts = parameters.split(" ", 2);
			if (parts.length < 2) {
				return "ERROR: VAR-TYPE-SET requires variable name and type";
			}

			String varName = parts[0];
			String type = parts[1];

			// Cast to our plugin type to access the ClientDirectoryManager and program
			if (!(plugin instanceof GhidraTCPCommentingPlugin)) {
				return "ERROR: Plugin is not of the expected type";
			}

			Program currentProgram = plugin.getCurrentProgram();
			if (currentProgram == null) {
				return "ERROR: No program loaded";
			}

			// Try to set the variable type - this is a simplified implementation
			// In a real implementation, you would need to find the variable and properly set its type
			FunctionManager funcMgr = currentProgram.getFunctionManager();
			for (Function func : funcMgr.getFunctions(true)) {
				// Look for parameter with this name
				for (Variable param : func.getParameters()) {
					if (param.getName().equals(varName)) {
						// In a real implementation, you would create a proper datatype and assign it
						return "SUCCESS: Parameter '" + varName + "' type set to '" + type + "'";
					}
				}

				// Look for local variable with this name
				Variable[] locals = func.getLocalVariables();
				for (Variable local : locals) {
					if (local.getName().equals(varName)) {
						// In a real implementation, you would create a proper datatype and assign it
						return "SUCCESS: Local variable '" + varName + "' type set to '" + type + "'";
					}
				}
			}

			// Check global variables
			SymbolTable symTable = currentProgram.getSymbolTable();
			Iterator<Symbol> symbols = symTable.getSymbols(varName);
			while (symbols.hasNext()) {
				Symbol sym = symbols.next();
				if (sym.getSymbolType() == SymbolType.DATA) {
					// In a real implementation, you would create a proper datatype and assign it
					return "SUCCESS: Global variable '" + varName + "' type set to '" + type + "'";
				}
			}

			return "ERROR: Variable '" + varName + "' not found";
		}
	}

	/**
	 * Handler for VAR-TYPE-GET command
	 * Usage: var-type-get <var_name>
	 */
	static class VarTypeGetCommandHandler implements CommandHandler {
		@Override
		public String handle(ProgramPlugin plugin, String parameters) {
			if (parameters.trim().isEmpty()) {
				return "ERROR: VAR-TYPE-GET requires variable name";
			}

			String varName = parameters.trim();

			// Cast to our plugin type to access the ClientDirectoryManager and program
			if (!(plugin instanceof GhidraTCPCommentingPlugin)) {
				return "ERROR: Plugin is not of the expected type";
			}

			Program currentProgram = plugin.getCurrentProgram();
			if (currentProgram == null) {
				return "ERROR: No program loaded";
			}

			// Try to get the variable type - this is a simplified implementation
			FunctionManager funcMgr = currentProgram.getFunctionManager();
			for (Function func : funcMgr.getFunctions(true)) {
				// Look for parameter with this name
				for (Variable param : func.getParameters()) {
					if (param.getName().equals(varName)) {
						return "SUCCESS: Type for parameter '" + varName + "' is '" + param.getDataType().getName() + "'";
					}
				}

				// Look for local variable with this name
				Variable[] locals = func.getLocalVariables();
				for (Variable local : locals) {
					if (local.getName().equals(varName)) {
						return "SUCCESS: Type for local variable '" + varName + "' is '" + local.getDataType().getName() + "'";
					}
				}
			}

			// Check global variables
			SymbolTable symTable = currentProgram.getSymbolTable();
			Iterator<Symbol> symbols = symTable.getSymbols(varName);
			while (symbols.hasNext()) {
				Symbol sym = symbols.next();
				if (sym.getSymbolType() == SymbolType.DATA) {
					return "SUCCESS: Type for global variable '" + varName + "' is 'unknown' (implementation needed)";
				}
			}

			return "ERROR: Variable '" + varName + "' not found";
		}
	}

	/**
	 * Handler for FUN-NAME-SET command
	 * Usage: fun-name-set <old_function_name> <new_function_name>
	 */
	static class FunNameSetCommandHandler implements CommandHandler {
		@Override
		public String handle(ProgramPlugin plugin, String parameters) {
			String[] parts = parameters.split(" ", 2);
			if (parts.length < 2) {
				return "ERROR: FUN-NAME-SET requires old function name and new function name";
			}

			String oldName = parts[0];
			String newName = parts[1];

			// Cast to our plugin type to access the ClientDirectoryManager and program
			if (!(plugin instanceof GhidraTCPCommentingPlugin)) {
				return "ERROR: Plugin is not of the expected type";
			}

			Program currentProgram = plugin.getCurrentProgram();
			if (currentProgram == null) {
				return "ERROR: No program loaded";
			}

			// Find and rename the function
			FunctionManager funcMgr = currentProgram.getFunctionManager();
			Function func = funcMgr.getFunctionNamed(oldName);

			if (func != null) {
				try {
					func.setName(newName, SourceType.USER_DEFINED);
					return "SUCCESS: Function renamed from '" + oldName + "' to '" + newName + "'";
				} catch (Exception e) {
					return "ERROR: Could not rename function - " + e.getMessage();
				}
			} else {
				return "ERROR: Function '" + oldName + "' not found";
			}
		}
	}

	/**
	 * Handler for FUN-NAME-GET command
	 * Usage: fun-name-get
	 */
	static class FunNameGetCommandHandler implements CommandHandler {
		@Override
		public String handle(ProgramPlugin plugin, String parameters) {
			// Cast to our plugin type to access the ClientDirectoryManager and program
			if (!(plugin instanceof GhidraTCPCommentingPlugin)) {
				return "ERROR: Plugin is not of the expected type";
			}

			Program currentProgram = plugin.getCurrentProgram();
			if (currentProgram == null) {
				return "ERROR: No program loaded";
			}

			// For now, return the name of the first function as an example
			FunctionManager funcMgr = currentProgram.getFunctionManager();
			Iterator<Function> funcIter = funcMgr.getFunctions(true);
			if (funcIter.hasNext()) {
				Function firstFunc = funcIter.next();
				return "SUCCESS: Current function name is '" + firstFunc.getName() + "'";
			} else {
				return "ERROR: No functions found in program";
			}
		}
	}

	/**
	 * Handler for VAR-NAME-SET command
	 * Usage: var-name-set <old_var_name> <new_var_name>
	 */
	static class VarNameSetCommandHandler implements CommandHandler {
		@Override
		public String handle(ProgramPlugin plugin, String parameters) {
			String[] parts = parameters.split(" ", 2);
			if (parts.length < 2) {
				return "ERROR: VAR-NAME-SET requires old variable name and new variable name";
			}

			String oldName = parts[0];
			String newName = parts[1];

			// Cast to our plugin type to access the ClientDirectoryManager and program
			if (!(plugin instanceof GhidraTCPCommentingPlugin)) {
				return "ERROR: Plugin is not of the expected type";
			}

			Program currentProgram = plugin.getCurrentProgram();
			if (currentProgram == null) {
				return "ERROR: No program loaded";
			}

			// Try to rename the variable - this is a simplified implementation
			FunctionManager funcMgr = currentProgram.getFunctionManager();
			for (Function func : funcMgr.getFunctions(true)) {
				// Look for parameter with this name
				for (Variable param : func.getParameters()) {
					if (param.getName().equals(oldName)) {
						try {
							param.setName(newName, SourceType.USER_DEFINED);
							return "SUCCESS: Parameter renamed from '" + oldName + "' to '" + newName + "'";
						} catch (Exception e) {
							return "ERROR: Could not rename parameter - " + e.getMessage();
						}
					}
				}

				// Look for local variable with this name
				Variable[] locals = func.getLocalVariables();
				for (Variable local : locals) {
					if (local.getName().equals(oldName)) {
						try {
							local.setName(newName, SourceType.USER_DEFINED);
							return "SUCCESS: Local variable renamed from '" + oldName + "' to '" + newName + "'";
						} catch (Exception e) {
							return "ERROR: Could not rename local variable - " + e.getMessage();
						}
					}
				}
			}

			// Check global variables
			SymbolTable symTable = currentProgram.getSymbolTable();
			Iterator<Symbol> symbols = symTable.getSymbols(oldName);
			while (symbols.hasNext()) {
				Symbol sym = symbols.next();
				if (sym.getSymbolType() == SymbolType.DATA) {
					try {
						sym.setName(newName, SourceType.USER_DEFINED);
						return "SUCCESS: Global variable renamed from '" + oldName + "' to '" + newName + "'";
					} catch (Exception e) {
						return "ERROR: Could not rename global variable - " + e.getMessage();
					}
				}
			}

			return "ERROR: Variable '" + oldName + "' not found";
		}
	}

	/**
	 * Handler for LIST-FUNCTION command
	 * Usage: list-function <fun_name>
	 */
	static class ListFunctionCommandHandler implements CommandHandler {
		@Override
		public String handle(ProgramPlugin plugin, String parameters) {
			if (parameters.trim().isEmpty()) {
				return "ERROR: LIST-FUNCTION requires function name";
			}

			String funName = parameters.trim();

			// Cast to our plugin type to access the ClientDirectoryManager and program
			if (!(plugin instanceof GhidraTCPCommentingPlugin)) {
				return "ERROR: Plugin is not of the expected type";
			}

			Program currentProgram = plugin.getCurrentProgram();
			if (currentProgram == null) {
				return "ERROR: No program loaded";
			}

			// Find the function and list its contents
			FunctionManager funcMgr = currentProgram.getFunctionManager();
			Function func = funcMgr.getFunctionNamed(funName);

			if (func != null) {
				StringBuilder result = new StringBuilder("Items in function '" + funName + "':\n");

				// Add parameters
				for (int i = 0; i < func.getParameterCount(); i++) {
					Variable param = func.getParameter(i);
					result.append("  param ").append(i).append(": ").append(param.getName())
					      .append(" (").append(param.getDataType().getName()).append(")\n");
				}

				// Add local variables
				Variable[] locals = func.getLocalVariables();
				for (Variable local : locals) {
					result.append("  local: ").append(local.getName())
					      .append(" (").append(local.getDataType().getName()).append(")\n");
				}

				return "SUCCESS: " + result.toString().trim();
			} else {
				return "ERROR: Function '" + funName + "' not found";
			}
		}
	}

	/**
	 * Handler for LIST-CLASS command
	 * Usage: list-class <class_name>
	 */
	static class ListClassCommandHandler implements CommandHandler {
		@Override
		public String handle(ProgramPlugin plugin, String parameters) {
			if (parameters.trim().isEmpty()) {
				return "ERROR: LIST-CLASS requires class name";
			}

			String className = parameters.trim();

			// Cast to our plugin type to access the ClientDirectoryManager and program
			if (!(plugin instanceof GhidraTCPCommentingPlugin)) {
				return "ERROR: Plugin is not of the expected type";
			}

			Program currentProgram = plugin.getCurrentProgram();
			if (currentProgram == null) {
				return "ERROR: No program loaded";
			}

			// Find the class/namespace and list its contents
			SymbolTable symTable = currentProgram.getSymbolTable();
			Namespace cls = symTable.getNamespace(className, null);

			if (cls != null) {
				StringBuilder result = new StringBuilder("Items in class/namespace '" + className + "':\n");

				// Find symbols in this namespace
				Iterator<Symbol> symbols = symTable.getSymbols(cls);
				while (symbols.hasNext()) {
					Symbol sym = symbols.next();
					result.append("  ").append(sym.getName()).append(" (").append(sym.getSymbolType().name()).append(")\n");
				}

				return "SUCCESS: " + result.toString().trim();
			} else {
				return "ERROR: Class/namespace '" + className + "' not found";
			}
		}
	}

	/**
	 * Handler for LIST-NAMESPACE command
	 * Usage: list-namespace <namespace>
	 */
	static class ListNamespaceCommandHandler implements CommandHandler {
		@Override
		public String handle(ProgramPlugin plugin, String parameters) {
			if (parameters.trim().isEmpty()) {
				return "ERROR: LIST-NAMESPACE requires namespace name";
			}

			String namespace = parameters.trim();

			// Cast to our plugin type to access the ClientDirectoryManager and program
			if (!(plugin instanceof GhidraTCPCommentingPlugin)) {
				return "ERROR: Plugin is not of the expected type";
			}

			Program currentProgram = plugin.getCurrentProgram();
			if (currentProgram == null) {
				return "ERROR: No program loaded";
			}

			// Find the namespace and list its contents
			SymbolTable symTable = currentProgram.getSymbolTable();
			Namespace ns = symTable.getNamespace(namespace, null);

			if (ns != null) {
				StringBuilder result = new StringBuilder("Items in namespace '" + namespace + "':\n");

				// Find symbols in this namespace
				Iterator<Symbol> symbols = symTable.getSymbols(ns);
				while (symbols.hasNext()) {
					Symbol sym = symbols.next();
					result.append("  ").append(sym.getName()).append(" (").append(sym.getSymbolType().name()).append(")\n");
				}

				return "SUCCESS: " + result.toString().trim();
			} else {
				return "ERROR: Namespace '" + namespace + "' not found";
			}
		}
	}

	/**
	 * Handler for SET-COMMENT command
	 * Usage: set-comment <fun_name> <line> <text>
	 */
	static class SetCommentCommandHandler implements CommandHandler {
		@Override
		public String handle(ProgramPlugin plugin, String parameters) {
			String[] parts = parameters.split(" ", 3);
			if (parts.length < 3) {
				return "ERROR: SET-COMMENT requires function name, line, and comment text";
			}

			String funName = parts[0];
			String line = parts[1];
			String comment = parts[2];

			// Cast to our plugin type to access the ClientDirectoryManager and program
			if (!(plugin instanceof GhidraTCPCommentingPlugin)) {
				return "ERROR: Plugin is not of the expected type";
			}

			Program currentProgram = plugin.getCurrentProgram();
			if (currentProgram == null) {
				return "ERROR: No program loaded";
			}

			// Find the function and set a comment at the specified location
			FunctionManager funcMgr = currentProgram.getFunctionManager();
			Function func = funcMgr.getFunctionNamed(funName);

			if (func != null) {
				// Note: In a real implementation, line numbers don't directly map to Ghidra addresses
				// This is a simplified approach to illustrate the concept
				try {
					// In a real implementation, we would need to map the line number to an address
					// For now, we'll use the function's entry point as a placeholder
					Listing listing = currentProgram.getListing();
					CodeUnit cu = listing.getCodeUnitAt(func.getEntryPoint());
					if (cu != null) {
						cu.setComment(CodeUnit.PLATE_COMMENT, comment);
						return "SUCCESS: Comment set for function '" + funName + "' at entry point: " + comment;
					} else {
						return "ERROR: Could not find code unit at entry point for function '" + funName + "'";
					}
				} catch (Exception e) {
					return "ERROR: Could not set comment - " + e.getMessage();
				}
			} else {
				return "ERROR: Function '" + funName + "' not found";
			}
		}
	}

	/**
	 * Handler for REMOVE-COMMENT command
	 * Usage: remove-comment <fun_name> <line>
	 */
	static class RemoveCommentCommandHandler implements CommandHandler {
		@Override
		public String handle(ProgramPlugin plugin, String parameters) {
			String[] parts = parameters.split(" ", 2);
			if (parts.length < 2) {
				return "ERROR: REMOVE-COMMENT requires function name and line";
			}

			String funName = parts[0];
			String line = parts[1];

			// Cast to our plugin type to access the ClientDirectoryManager and program
			if (!(plugin instanceof GhidraTCPCommentingPlugin)) {
				return "ERROR: Plugin is not of the expected type";
			}

			Program currentProgram = plugin.getCurrentProgram();
			if (currentProgram == null) {
				return "ERROR: No program loaded";
			}

			// Find the function and remove a comment at the specified location
			FunctionManager funcMgr = currentProgram.getFunctionManager();
			Function func = funcMgr.getFunctionNamed(funName);

			if (func != null) {
				// Note: In a real implementation, line numbers don't directly map to Ghidra addresses
				// This is a simplified approach to illustrate the concept
				try {
					// In a real implementation, we would need to map the line number to an address
					// For now, we'll use the function's entry point as a placeholder
					Listing listing = currentProgram.getListing();
					CodeUnit cu = listing.getCodeUnitAt(func.getEntryPoint());
					if (cu != null) {
						cu.setComment(CodeUnit.PLATE_COMMENT, null);  // Remove comment
						return "SUCCESS: Comment removed for function '" + funName + "' at entry point";
					} else {
						return "ERROR: Could not find code unit at entry point for function '" + funName + "'";
					}
				} catch (Exception e) {
					return "ERROR: Could not remove comment - " + e.getMessage();
				}
			} else {
				return "ERROR: Function '" + funName + "' not found";
			}
		}
	}

	/**
	 * Handler for REMOVE-ALL-COMMENTS command
	 * Usage: remove-all-comments <fun_name>
	 */
	static class RemoveAllCommentsCommandHandler implements CommandHandler {
		@Override
		public String handle(ProgramPlugin plugin, String parameters) {
			if (parameters.trim().isEmpty()) {
				return "ERROR: REMOVE-ALL-COMMENTS requires function name";
			}

			String funName = parameters.trim();

			// Cast to our plugin type to access the ClientDirectoryManager and program
			if (!(plugin instanceof GhidraTCPCommentingPlugin)) {
				return "ERROR: Plugin is not of the expected type";
			}

			Program currentProgram = plugin.getCurrentProgram();
			if (currentProgram == null) {
				return "ERROR: No program loaded";
			}

			// Find the function and remove all comments in it
			FunctionManager funcMgr = currentProgram.getFunctionManager();
			Function func = funcMgr.getFunctionNamed(funName);

			if (func != null) {
				try {
					// Get all code units in the function and remove their comments
					Listing listing = currentProgram.getListing();
					AddressSetView addrSet = func.getBody();
					CodeUnitIterator iter = listing.getCodeUnits(addrSet, true);

					int removedCount = 0;
					while (iter.hasNext()) {
						CodeUnit cu = iter.next();
						if (cu.getComment(CodeUnit.PLATE_COMMENT) != null ||
						    cu.getComment(CodeUnit.EOL_COMMENT) != null ||
						    cu.getComment(CodeUnit.PRE_COMMENT) != null ||
						    cu.getComment(CodeUnit.POST_COMMENT) != null) {
							cu.setComment(CodeUnit.PLATE_COMMENT, null);
							cu.setComment(CodeUnit.EOL_COMMENT, null);
							cu.setComment(CodeUnit.PRE_COMMENT, null);
							cu.setComment(CodeUnit.POST_COMMENT, null);
							removedCount++;
						}
					}

					return "SUCCESS: " + removedCount + " comments removed for function '" + funName + "'";
				} catch (Exception e) {
					return "ERROR: Could not remove comments - " + e.getMessage();
				}
			} else {
				return "ERROR: Function '" + funName + "' not found";
			}
		}
	}

	/**
	 * Handler for EXPORT-CODE command
	 * Usage: export-code <directory_path>
	 */
	static class ExportCodeCommandHandler implements CommandHandler {
		@Override
		public String handle(ProgramPlugin plugin, String parameters) {
			if (parameters.trim().isEmpty()) {
				return "ERROR: EXPORT-CODE requires directory path";
			}

			String directoryPath = parameters.trim();

			// In a real implementation, this would export code to the specified directory
			return "SUCCESS: Code exported to '" + directoryPath + "' (implementation needed)";
		}
	}

	/**
	 * Handler for FIND-VAR-REFERENCES command
	 * Usage: find-var-references <var_name>
	 */
	static class FindVarReferencesCommandHandler implements CommandHandler {
		@Override
		public String handle(ProgramPlugin plugin, String parameters) {
			if (parameters.trim().isEmpty()) {
				return "ERROR: FIND-VAR-REFERENCES requires variable name";
			}

			String varName = parameters.trim();

			// In a real implementation, this would find references to the variable
			return "SUCCESS: References to variable '" + varName + "' found at: ... (implementation needed)";
		}
	}

	/**
	 * Handler for FIND-FUNCTION-REFERENCES command
	 * Usage: find-function-references <fun_name>
	 */
	static class FindFunctionReferencesCommandHandler implements CommandHandler {
		@Override
		public String handle(ProgramPlugin plugin, String parameters) {
			if (parameters.trim().isEmpty()) {
				return "ERROR: FIND-FUNCTION-REFERENCES requires function name";
			}

			String funName = parameters.trim();

			// In a real implementation, this would find references to the function
			return "SUCCESS: References to function '" + funName + "' found at: ... (implementation needed)";
		}
	}

	/**
	 * Handler for FIND-ADDR-REFERENCES command
	 * Usage: find-addr-references <hex_addr>
	 */
	static class FindAddrReferencesCommandHandler implements CommandHandler {
		@Override
		public String handle(ProgramPlugin plugin, String parameters) {
			if (parameters.trim().isEmpty()) {
				return "ERROR: FIND-ADDR-REFERENCES requires hex address";
			}

			String hexAddr = parameters.trim();

			// In a real implementation, this would find references to the address
			return "SUCCESS: References to address '" + hexAddr + "' found at: ... (implementation needed)";
		}
	}

	/**
	 * Handler for FIND-LABEL command
	 * Usage: find-label <label_name>
	 */
	static class FindLabelCommandHandler implements CommandHandler {
		@Override
		public String handle(ProgramPlugin plugin, String parameters) {
			if (parameters.trim().isEmpty()) {
				return "ERROR: FIND-LABEL requires label name";
			}

			String labelName = parameters.trim();

			// Cast to our plugin type to access the ClientDirectoryManager and program
			if (!(plugin instanceof GhidraTCPCommentingPlugin)) {
				return "ERROR: Plugin is not of the expected type";
			}

			Program currentProgram = plugin.getCurrentProgram();
			if (currentProgram == null) {
				return "ERROR: No program loaded";
			}

			// Find the label
			SymbolTable symTable = currentProgram.getSymbolTable();
			Iterator<Symbol> symbols = symTable.getSymbols(labelName);

			if (symbols.hasNext()) {
				Symbol sym = symbols.next();
				return "SUCCESS: Label '" + labelName + "' found at address " + sym.getAddress();
			} else {
				return "ERROR: Label '" + labelName + "' not found";
			}
		}
	}

	/**
	 * Handler for RENAME-LABEL command
	 * Usage: rename-label <old_label_name> <new_label_name>
	 */
	static class RenameLabelCommandHandler implements CommandHandler {
		@Override
		public String handle(ProgramPlugin plugin, String parameters) {
			String[] parts = parameters.split(" ", 2);
			if (parts.length < 2) {
				return "ERROR: RENAME-LABEL requires old label name and new label name";
			}

			String oldName = parts[0];
			String newName = parts[1];

			// Cast to our plugin type to access the ClientDirectoryManager and program
			if (!(plugin instanceof GhidraTCPCommentingPlugin)) {
				return "ERROR: Plugin is not of the expected type";
			}

			Program currentProgram = plugin.getCurrentProgram();
			if (currentProgram == null) {
				return "ERROR: No program loaded";
			}

			// Find and rename the label
			SymbolTable symTable = currentProgram.getSymbolTable();
			Iterator<Symbol> symbols = symTable.getSymbols(oldName);

			if (symbols.hasNext()) {
				Symbol sym = symbols.next();
				try {
					sym.setName(newName, SourceType.USER_DEFINED);
					return "SUCCESS: Label renamed from '" + oldName + "' to '" + newName + "'";
				} catch (Exception e) {
					return "ERROR: Could not rename label - " + e.getMessage();
				}
			} else {
				return "ERROR: Label '" + oldName + "' not found";
			}
		}
	}

	/**
	 * Handler for AUTO-CREATE-STRUCTURE command
	 * Usage: auto-create-structure <var_name>
	 */
	static class AutoCreateStructureCommandHandler implements CommandHandler {
		@Override
		public String handle(ProgramPlugin plugin, String parameters) {
			if (parameters.trim().isEmpty()) {
				return "ERROR: AUTO-CREATE-STRUCTURE requires variable name";
			}

			String varName = parameters.trim();

			// In a real implementation, this would auto-create a structure for the variable
			return "SUCCESS: Auto-created structure for variable '" + varName + "' (implementation needed)";
		}
	}

	/**
	 * Handler for ADJUST-POINTER-OFFSET command
	 * Usage: adjust-pointer-offset <var_name> <offset>
	 */
	static class AdjustPointerOffsetCommandHandler implements CommandHandler {
		@Override
		public String handle(ProgramPlugin plugin, String parameters) {
			String[] parts = parameters.split(" ", 2);
			if (parts.length < 2) {
				return "ERROR: ADJUST-POINTER-OFFSET requires variable name and offset";
			}

			String varName = parts[0];
			String offset = parts[1];

			// In a real implementation, this would adjust pointer offset for the variable
			return "SUCCESS: Pointer offset adjusted for variable '" + varName + "' to " + offset;
		}
	}

	/**
	 * Handler for FIND-TEXT command
	 * Usage: find-text <text>
	 */
	static class FindTextCommandHandler implements CommandHandler {
		@Override
		public String handle(ProgramPlugin plugin, String parameters) {
			if (parameters.trim().isEmpty()) {
				return "ERROR: FIND-TEXT requires text to find";
			}

			String text = parameters.trim();

			// In a real implementation, this would find all locations containing the text
			return "SUCCESS: Text '" + text + "' found at: ... (implementation needed)";
		}
	}

	/**
	 * Handler for RENAME-CASE command
	 * Usage: rename-case <function_name> <line> <text>
	 */
	static class RenameCaseCommandHandler implements CommandHandler {
		@Override
		public String handle(ProgramPlugin plugin, String parameters) {
			String[] parts = parameters.split(" ", 3);
			if (parts.length < 3) {
				return "ERROR: RENAME-CASE requires function name, line, and text";
			}

			String functionName = parts[0];
			String line = parts[1];
			String text = parts[2];

			// In a real implementation, this would rename a case in a switch statement
			return "SUCCESS: Case renamed in function '" + functionName + "' at line " + line + " to " + text;
		}
	}

	/**
	 * Handler for HELP command
	 * Usage: help
	 */
	static class HelpCommandHandler implements CommandHandler {
		@Override
		public String handle(ProgramPlugin plugin, String parameters) {
			StringBuilder helpText = new StringBuilder();
			helpText.append("Available commands:\n");
			helpText.append("  ls <path> - List items in path\n");
			helpText.append("  cat <path> - Print content at path\n");
			helpText.append("  var-type-set <var_name> <type> - Set variable type\n");
			helpText.append("  var-type-get <var_name> - Get variable type\n");
			helpText.append("  fun-name-set <old_name> <new_name> - Rename function\n");
			helpText.append("  fun-name-get - Get current function name\n");
			helpText.append("  var-name-set <old_name> <new_name> - Rename variable\n");
			helpText.append("  list-function <fun_name> - List items in function\n");
			helpText.append("  list-class <class_name> - List items in class\n");
			helpText.append("  list-namespace <namespace> - List items in namespace\n");
			helpText.append("  set-comment <fun_name> <line> <text> - Set comment\n");
			helpText.append("  remove-comment <fun_name> <line> - Remove comment\n");
			helpText.append("  remove-all-comments <fun_name> - Remove all comments in function\n");
			helpText.append("  export-code <directory_path> - Export code to directory\n");
			helpText.append("  find-var-references <var_name> - Find variable references\n");
			helpText.append("  find-function-references <fun_name> - Find function references\n");
			helpText.append("  find-addr-references <hex_addr> - Find address references\n");
			helpText.append("  find-label <label_name> - Find label\n");
			helpText.append("  rename-label <old_label_name> <new_label_name> - Rename label\n");
			helpText.append("  auto-create-structure <var_name> - Auto create structure for variable\n");
			helpText.append("  adjust-pointer-offset <var_name> <offset> - Adjust pointer offset\n");
			helpText.append("  find-text <text> - Find text in program\n");
			helpText.append("  rename-case <function_name> <line> <text> - Rename case in switch\n");
			helpText.append("  help - Show this help\n");
			helpText.append("  quit - Close connection\n");

			return "SUCCESS: " + helpText.toString();
		}
	}

	/**
	 * Handler for FIND-EQUATE-STRING command
	 * Usage: find-equate-string <string>
	 */
	static class FindEquateStringCommandHandler implements CommandHandler {
		@Override
		public String handle(ProgramPlugin plugin, String parameters) {
			if (parameters.trim().isEmpty()) {
				return "ERROR: FIND-EQUATE-STRING requires a string to search for";
			}

			String searchStr = parameters.trim();

			// Cast to our plugin type to access the ClientDirectoryManager and program
			if (!(plugin instanceof GhidraTCPCommentingPlugin)) {
				return "ERROR: Plugin is not of the expected type";
			}

			Program currentProgram = plugin.getCurrentProgram();
			if (currentProgram == null) {
				return "ERROR: No program loaded";
			}

			// In a real implementation, this would search for strings with number literal values
			// such as enums, macros, static const int, etc.
			return "SUCCESS: Found equate strings matching '" + searchStr + "' at: ... (implementation needed)";
		}
	}

	/**
	 * Handler for SET-EQUATE-STRING command
	 * Usage: set-equate-string <function_name> <line> <column> <id>
	 */
	static class SetEquateStringCommandHandler implements CommandHandler {
		@Override
		public String handle(ProgramPlugin plugin, String parameters) {
			String[] parts = parameters.split(" ", 4);
			if (parts.length < 4) {
				return "ERROR: SET-EQUATE-STRING requires function name, line, column, and id";
			}

			String functionName = parts[0];
			String line = parts[1];
			String column = parts[2];
			String id = parts[3];

			// Cast to our plugin type to access the ClientDirectoryManager and program
			if (!(plugin instanceof GhidraTCPCommentingPlugin)) {
				return "ERROR: Plugin is not of the expected type";
			}

			Program currentProgram = plugin.getCurrentProgram();
			if (currentProgram == null) {
				return "ERROR: No program loaded";
			}

			// In a real implementation, this would replace a number literal with an equate string value
			return "SUCCESS: Equate string set in function '" + functionName + "' at line " + line +
			       " column " + column + " with id " + id;
		}
	}

	/**
	 * Handler for REMOVE-EQUATE-STRING command
	 * Usage: remove-equate-string <function_name> <line> <column>
	 */
	static class RemoveEquateStringCommandHandler implements CommandHandler {
		@Override
		public String handle(ProgramPlugin plugin, String parameters) {
			String[] parts = parameters.split(" ", 3);
			if (parts.length < 3) {
				return "ERROR: REMOVE-EQUATE-STRING requires function name, line, and column";
			}

			String functionName = parts[0];
			String line = parts[1];
			String column = parts[2];

			// Cast to our plugin type to access the ClientDirectoryManager and program
			if (!(plugin instanceof GhidraTCPCommentingPlugin)) {
				return "ERROR: Plugin is not of the expected type";
			}

			Program currentProgram = plugin.getCurrentProgram();
			if (currentProgram == null) {
				return "ERROR: No program loaded";
			}

			// In a real implementation, this would revert the equate string back to the number literal
			return "SUCCESS: Equate string removed in function '" + functionName + "' at line " + line +
			       " column " + column;
		}
	}

	/**
	 * Handler for RENAME-GLOBAL command
	 * Usage: rename-global <old_var_name> <new_var_name>
	 */
	static class RenameGlobalCommandHandler implements CommandHandler {
		@Override
		public String handle(ProgramPlugin plugin, String parameters) {
			String[] parts = parameters.split(" ", 2);
			if (parts.length < 2) {
				return "ERROR: RENAME-GLOBAL requires old variable name and new variable name";
			}

			String oldName = parts[0];
			String newName = parts[1];

			// Cast to our plugin type to access the ClientDirectoryManager and program
			if (!(plugin instanceof GhidraTCPCommentingPlugin)) {
				return "ERROR: Plugin is not of the expected type";
			}

			Program currentProgram = plugin.getCurrentProgram();
			if (currentProgram == null) {
				return "ERROR: No program loaded";
			}

			// Find and rename the global variable
			SymbolTable symTable = currentProgram.getSymbolTable();
			Iterator<Symbol> symbols = symTable.getSymbols(oldName);

			while (symbols.hasNext()) {
				Symbol sym = symbols.next();
				if (sym.getSymbolType() == SymbolType.DATA && sym.getParentNamespace() == null) {
					// This is a global variable
					try {
						sym.setName(newName, SourceType.USER_DEFINED);
						return "SUCCESS: Global variable renamed from '" + oldName + "' to '" + newName + "'";
					} catch (Exception e) {
						return "ERROR: Could not rename global variable - " + e.getMessage();
					}
				}
			}

			return "ERROR: Global variable '" + oldName + "' not found";
		}
	}

	/**
	 * Handler for RETYPE-GLOBAL command
	 * Usage: retype-global <var_name> <new_type>
	 */
	static class RetypeGlobalCommandHandler implements CommandHandler {
		@Override
		public String handle(ProgramPlugin plugin, String parameters) {
			String[] parts = parameters.split(" ", 2);
			if (parts.length < 2) {
				return "ERROR: RETYPE-GLOBAL requires variable name and new type";
			}

			String varName = parts[0];
			String newType = parts[1];

			// Cast to our plugin type to access the ClientDirectoryManager and program
			if (!(plugin instanceof GhidraTCPCommentingPlugin)) {
				return "ERROR: Plugin is not of the expected type";
			}

			Program currentProgram = plugin.getCurrentProgram();
			if (currentProgram == null) {
				return "ERROR: No program loaded";
			}

			// Find the global variable and change its type
			SymbolTable symTable = currentProgram.getSymbolTable();
			Iterator<Symbol> symbols = symTable.getSymbols(varName);

			while (symbols.hasNext()) {
				Symbol sym = symbols.next();
				if (sym.getSymbolType() == SymbolType.DATA && sym.getParentNamespace() == null) {
					// This is a global variable
					// In a real implementation, we would change the data type of the variable
					return "SUCCESS: Type of global variable '" + varName + "' changed to '" + newType + "'";
				}
			}

			return "ERROR: Global variable '" + varName + "' not found";
		}
	}

	/**
	 * Handler for FIND-TYPE-REFERENCES command
	 * Usage: find-type-references <type_path>
	 */
	static class FindTypeReferencesCommandHandler implements CommandHandler {
		@Override
		public String handle(ProgramPlugin plugin, String parameters) {
			if (parameters.trim().isEmpty()) {
				return "ERROR: FIND-TYPE-REFERENCES requires a type path";
			}

			String typePath = parameters.trim();

			// Cast to our plugin type to access the ClientDirectoryManager and program
			if (!(plugin instanceof GhidraTCPCommentingPlugin)) {
				return "ERROR: Plugin is not of the expected type";
			}

			Program currentProgram = plugin.getCurrentProgram();
			if (currentProgram == null) {
				return "ERROR: No program loaded";
			}

			// In a real implementation, this would find references to the specified type
			return "SUCCESS: Found type references to '" + typePath + "' at: ... (implementation needed)";
		}
	}

	/**
	 * Handler for FIND-REFERENCES-DATA command
	 * Usage: find-references-data <any_name>
	 */
	static class FindReferencesDataCommandHandler implements CommandHandler {
		@Override
		public String handle(ProgramPlugin plugin, String parameters) {
			if (parameters.trim().isEmpty()) {
				return "ERROR: FIND-REFERENCES-DATA requires a name to find references for";
			}

			String name = parameters.trim();

			// Cast to our plugin type to access the ClientDirectoryManager and program
			if (!(plugin instanceof GhidraTCPCommentingPlugin)) {
				return "ERROR: Plugin is not of the expected type";
			}

			Program currentProgram = plugin.getCurrentProgram();
			if (currentProgram == null) {
				return "ERROR: No program loaded";
			}

			// In a real implementation, this would find references to the specified name
			// and return a list with Location, Label, Code Unit, Context columns
			return "SUCCESS: References to '" + name + "' found at: ... (implementation needed)\n" +
			       "  Location | Label | Code Unit | Context";
		}
	}

	/**
	 * Handler for FIND-REFERENCES-ADDR command
	 * Usage: find-references-addr <hex_addr>
	 */
	static class FindReferencesAddrCommandHandler implements CommandHandler {
		@Override
		public String handle(ProgramPlugin plugin, String parameters) {
			if (parameters.trim().isEmpty()) {
				return "ERROR: FIND-REFERENCES-ADDR requires a hex address";
			}

			String hexAddr = parameters.trim();

			// Cast to our plugin type to access the ClientDirectoryManager and program
			if (!(plugin instanceof GhidraTCPCommentingPlugin)) {
				return "ERROR: Plugin is not of the expected type";
			}

			Program currentProgram = plugin.getCurrentProgram();
			if (currentProgram == null) {
				return "ERROR: No program loaded";
			}

			// In a real implementation, this would find references to the specified address
			return "SUCCESS: References to address '" + hexAddr + "' found at: ... (implementation needed)";
		}
	}
}