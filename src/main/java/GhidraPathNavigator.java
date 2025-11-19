import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;
import ghidra.util.task.TaskMonitor;
import ghidra.util.task.TaskLauncher;
import ghidra.app.util.exporter.CppExporter;
import ghidra.framework.model.DomainFile;
import java.io.*;
import java.util.*;

/**
 * GhidraPathNavigator provides filesystem-like navigation within Ghidra's data structures
 * It allows clients to navigate and access Ghidra's data using path-like syntax
 */
public class GhidraPathNavigator {
	
	private Program currentProgram;
	
	public GhidraPathNavigator(Program program) {
		this.currentProgram = program;
	}
	
	/**
	 * Parse a path string and navigate to the corresponding element in Ghidra
	 * @param path The path string to navigate to
	 * @return Information about the path element
	 */
	public PathElement navigateToPath(String path) {
		if (currentProgram == null) {
			return new PathElement(false, "No program loaded", PathType.NONE, null);
		}
		
		// Parse the path to determine what to look for
		String[] segments = path.split("::");
		if (segments.length == 0) {
			return new PathElement(false, "Invalid path format", PathType.NONE, null);
		}
		
		// Determine the entity type from the first segment
		String entityType = segments[0].toUpperCase();
		
		switch (entityType) {
			case "FUN":
			case "FUNCTION":
				return navigateToFunction(segments.length > 1 ? segments[1] : "");
			case "VAR":
			case "VARIABLE":
				return navigateToVariable(segments.length > 1 ? segments[1] : "");
			case "LABEL":
				return navigateToLabel(segments.length > 1 ? segments[1] : "");
			case "NAMESPACE":
			case "NS":
				return navigateToNamespace(segments.length > 1 ? segments[1] : "");
			case "CLASS":
			case "STRUCT":
				return navigateToClass(segments.length > 1 ? segments[1] : "");
			default:
				return navigateToDefaultPath(path);
		}
	}
	
	/**
	 * Navigate to a function by name
	 */
	private PathElement navigateToFunction(String functionName) {
		if (functionName.isEmpty()) {
			return new PathElement(false, "Function name not specified", PathType.FUNCTION, null);
		}
		
		FunctionManager funcMgr = currentProgram.getFunctionManager();
		Function func = funcMgr.getFunctionNamed(functionName);
		
		if (func != null) {
			return new PathElement(true, "Found function: " + functionName, PathType.FUNCTION, func);
		} else {
			return new PathElement(false, "Function not found: " + functionName, PathType.FUNCTION, null);
		}
	}
	
	/**
	 * Navigate to a variable by name
	 */
	private PathElement navigateToVariable(String variableName) {
		if (variableName.isEmpty()) {
			return new PathElement(false, "Variable name not specified", PathType.VARIABLE, null);
		}
		
		// Search for global variables first
		SymbolTable symTable = currentProgram.getSymbolTable();
		Iterator<Symbol> symbols = symTable.getSymbols(variableName);
		
		while (symbols.hasNext()) {
			Symbol sym = symbols.next();
			if (sym.getSymbolType() == SymbolType.DATA) {
				return new PathElement(true, "Found variable: " + variableName, PathType.VARIABLE, sym.getObject());
			}
		}
		
		// If not found globally, might be a local variable in functions
		FunctionManager funcMgr = currentProgram.getFunctionManager();
		for (Function func : funcMgr.getFunctions(true)) {
			// Look for parameter or local variable
			for (Variable param : func.getParameters()) {
				if (param.getName().equals(variableName)) {
					return new PathElement(true, "Found parameter: " + variableName, PathType.PARAMETER, param);
				}
			}
			
			// Check local variables
			Variable[] locals = func.getLocalVariables();
			for (Variable local : locals) {
				if (local.getName().equals(variableName)) {
					return new PathElement(true, "Found local variable: " + variableName, PathType.LOCAL_VARIABLE, local);
				}
			}
		}
		
		return new PathElement(false, "Variable not found: " + variableName, PathType.VARIABLE, null);
	}
	
	/**
	 * Navigate to a label by name
	 */
	private PathElement navigateToLabel(String labelName) {
		if (labelName.isEmpty()) {
			return new PathElement(false, "Label name not specified", PathType.LABEL, null);
		}
		
		SymbolTable symTable = currentProgram.getSymbolTable();
		Iterator<Symbol> symbols = symTable.getSymbols(labelName);
		
		if (symbols.hasNext()) {
			Symbol sym = symbols.next();
			return new PathElement(true, "Found label: " + labelName, PathType.LABEL, sym.getAddress());
		} else {
			return new PathElement(false, "Label not found: " + labelName, PathType.LABEL, null);
		}
	}
	
	/**
	 * Navigate to a namespace by name
	 */
	private PathElement navigateToNamespace(String namespaceName) {
		if (namespaceName.isEmpty()) {
			return new PathElement(false, "Namespace name not specified", PathType.NAMESPACE, null);
		}
		
		Namespace ns = currentProgram.getSymbolTable().getNamespace(namespaceName, null);
		if (ns != null) {
			return new PathElement(true, "Found namespace: " + namespaceName, PathType.NAMESPACE, ns);
		} else {
			return new PathElement(false, "Namespace not found: " + namespaceName, PathType.NAMESPACE, null);
		}
	}
	
	/**
	 * Navigate to a class by name
	 */
	private PathElement navigateToClass(String className) {
		if (className.isEmpty()) {
			return new PathElement(false, "Class name not specified", PathType.CLASS, null);
		}
		
		// In Ghidra, classes are represented as namespaces or structures
		// Look for a namespace first
		Namespace cls = currentProgram.getSymbolTable().getNamespace(className, null);
		if (cls != null) {
			return new PathElement(true, "Found class/structure: " + className, PathType.CLASS, cls);
		}
		
		// If not found as namespace, look for data types
		ghidra.program.model.data.DataTypeManager dtm = currentProgram.getDataTypeManager();
		ghidra.program.model.data.DataType dt = dtm.getDataType("/" + className);
		if (dt != null) {
			return new PathElement(true, "Found data type: " + className, PathType.DATATYPE, dt);
		}
		
		return new PathElement(false, "Class/structure not found: " + className, PathType.CLASS, null);
	}
	
	/**
	 * Default path navigation for simple paths (e.g., just function names)
	 */
	private PathElement navigateToDefaultPath(String path) {
		// Try to find a function with this name first
		FunctionManager funcMgr = currentProgram.getFunctionManager();
		Function func = funcMgr.getFunctionNamed(path);
		
		if (func != null) {
			return new PathElement(true, "Found function: " + path, PathType.FUNCTION, func);
		}
		
		// Then try to find a label
		SymbolTable symTable = currentProgram.getSymbolTable();
		Iterator<Symbol> symbols = symTable.getSymbols(path);
		
		if (symbols.hasNext()) {
			Symbol sym = symbols.next();
			return new PathElement(true, "Found symbol: " + path, PathType.LABEL, sym.getAddress());
		}
		
		return new PathElement(false, "Path not found: " + path, PathType.NONE, null);
	}
	
	/**
	 * List items in a path
	 */
	public String listPath(String path) {
		if (currentProgram == null) {
			return "No program loaded";
		}
		
		// For root level, list all functions
		if (path.isEmpty() || path.equals("/")) {
			StringBuilder result = new StringBuilder("Functions in program:\n");
			FunctionManager funcMgr = currentProgram.getFunctionManager();
			
			for (Function func : funcMgr.getFunctions(true)) {
				result.append("  ").append(func.getName()).append(" (").append(func.getEntryPoint()).append(")\n");
			}
			
			return result.toString().trim();
		}
		
		// Navigate to the specified path
		PathElement element = navigateToPath(path);
		
		if (!element.found) {
			return element.message;
		}
		
		switch (element.type) {
			case FUNCTION:
				Function func = (Function) element.object;
				StringBuilder result = new StringBuilder("Items in function " + func.getName() + ":\n");
				
				// Add parameters
				for (Variable param : func.getParameters()) {
					result.append("  param: ").append(param.getName()).append(" (").append(param.getDataType().getName()).append(")\n");
				}
				
				// Add local variables
				Variable[] locals = func.getLocalVariables();
				for (Variable local : locals) {
					result.append("  local: ").append(local.getName()).append(" (").append(local.getDataType().getName()).append(")\n");
				}
				
				return result.toString().trim();
				
			case NAMESPACE:
				Namespace ns = (Namespace) element.object;
				result = new StringBuilder("Items in namespace " + ns.getName() + ":\n");
				
				// Find symbols in this namespace
				SymbolTable symTable = currentProgram.getSymbolTable();
				Iterator<Symbol> symbols = symTable.getSymbols(ns);
				
				while (symbols.hasNext()) {
					Symbol sym = symbols.next();
					result.append("  ").append(sym.getName()).append(" (").append(sym.getSymbolType().name()).append(")\n");
				}
				
				return result.toString().trim();
				
			default:
				return "Cannot list items in: " + path + " (not a container)";
		}
	}
	
	/**
	 * Get content of a path (like cat command)
	 */
	public String getContent(String path) {
		if (currentProgram == null) {
			return "No program loaded";
		}
		
		PathElement element = navigateToPath(path);
		
		if (!element.found) {
			return element.message;
		}
		
		switch (element.type) {
			case FUNCTION:
				Function func = (Function) element.object;
				return "Function: " + func.getName() + "\n" +
				       "Address: " + func.getEntryPoint() + "\n" +
				       "Parameters: " + func.getParameterCount() + "\n" +
				       "Body: [Function body would be displayed here]";
				
			case VARIABLE:
			case PARAMETER:
			case LOCAL_VARIABLE:
				Object varObj = element.object;
				return "Variable: " + (varObj instanceof Variable ? ((Variable) varObj).getName() : "unknown") + "\n" +
				       "Type: " + (varObj instanceof Variable ? ((Variable) varObj).getDataType().getName() : "unknown") + "\n" +
				       "Value: [Value would be displayed here]";
				
			default:
				return "Content for path '" + path + "' of type " + element.type + ": [Content here]";
		}
	}
	
	/**
	 * Enum to represent different types of path elements
	 */
	public enum PathType {
		FUNCTION,
		VARIABLE,
		PARAMETER,
		LOCAL_VARIABLE,
		LABEL,
		NAMESPACE,
		CLASS,
		DATATYPE,
		NONE
	}
	
	/**
	 * Class to represent an element found at a path
	 */
	public static class PathElement {
		public boolean found;
		public String message;
		public PathType type;
		public Object object;  // The actual Ghidra object (Function, Variable, etc.)
		
		public PathElement(boolean found, String message, PathType type, Object object) {
			this.found = found;
			this.message = message;
			this.type = type;
			this.object = object;
		}
	}
}