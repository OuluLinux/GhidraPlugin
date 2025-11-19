# QWEN - Simple Guide for Java Ghidra Plugin Project

**Project**: .
**Type**: Java-based Ghidra Plugin
**Build System**: Gradle
**For**: Qwen AI - Simple, clear instructions

---

## STEP 1: Read AGENTS.md First!

**IMPORTANT**: Read the AGENTS.md file in this directory first!
It has all the detailed rules for this Java Ghidra plugin project.

---

## STEP 2: Understanding This Project

This is a **Java-based Ghidra plugin project** that will implement TCP server functionality for client communication.

### What is Ghidra?
- Software reverse engineering (SRE) platform
- Developed by NSA
- Written in Java
- Allows plugins to extend functionality

### Plugin Purpose:
- Open a TCP server for clients to communicate
- Act as a directory service similar to Ghidra's CodeBrowser
- Allow remote commenting and collaboration features

---

## STEP 3: Important Java/Ghidra Rules

### Rule #1: Use Standard Java Types

This project uses **standard Java types**:

| Type | Example |
|------|---------|
| String | `String name = "hello";` |
| List | `List<Integer> numbers = new ArrayList<>();` |
| Map | `Map<String, Integer> ages = new HashMap<>();` |
| Optional | `Optional<String> value = Optional.ofNullable(str);` |

### Rule #2: Import Statements Correctly

```java
// Java standard library imports
import java.util.*;
import java.io.*;
import java.net.*;

// Ghidra imports
import ghidra.*;
import ghidra.app.plugin.*;
import ghidra.framework.plugintool.*;
```

### Rule #3: Follow Ghidra Plugin Architecture

```java
// Plugin class should extend Plugin or CommonPlugin
public class MyGhidraPlugin extends Plugin {
    // Plugin implementation
}

// Or extend CommonPluginTool
public class MyGhidraPlugin extends CommonPluginTool {
    // Plugin tool implementation
}
```

### Rule #4: Use Modern Java Features

```java
// OLD WAY (don't use):
for (int i = 0; i < list.size(); i++) {
    System.out.println(list.get(i));
}

// NEW WAY (do use):
for (String item : list) {
    System.out.println(item);
}

// Or even better with streams:
list.forEach(System.out::println);
```

---

## STEP 4: Common Operations

### Working with Strings
```java
String str = "hello world";

// Find substring
if (str.contains("world")) {
    // found
}

// Get substring
String sub = str.substring(0, 5);  // "hello"

// Safe null handling
Optional<String> optStr = Optional.ofNullable(maybeNullString);
String result = optStr.orElse("default");
```

### Working with Collections
```java
List<Integer> numbers = new ArrayList<>();

// Add items
numbers.add(1);
numbers.add(2);

// Iterate
for (int num : numbers) {
    System.out.println(num);
}

// Check size
if (!numbers.isEmpty()) {
    System.out.println("Size: " + numbers.size());
}

// Java 8+ approach
numbers.stream()
    .filter(n -> n > 0)
    .forEach(System.out::println);
```

### Working with Maps
```java
Map<String, Integer> ages = new HashMap<>();

// Add items
ages.put("Alice", 30);
ages.put("Bob", 25);

// Get item safely
Integer aliceAge = ages.getOrDefault("Alice", 0);

// Iterate
ages.forEach((name, age) -> System.out.println(name + " is " + age));
```

### Creating TCP Server (Basic Example)
```java
try (ServerSocket serverSocket = new ServerSocket(port)) {
    while (!Thread.currentThread().isInterrupted()) {
        Socket clientSocket = serverSocket.accept();
        // Handle client in a separate thread
        executor.submit(() -> handleClient(clientSocket));
    }
} catch (IOException e) {
    // Handle exception
}
```

---

## STEP 5: Building and Testing

### Build with Gradle
```bash
# Compile
./gradlew compileJava

# Build plugin
./gradlew build

# Install to Ghidra
./gradlew install
```

### Running Tests
```bash
# Run tests
./gradlew test

# Run with specific Ghidra installation
./gradlew -PghidraInstallDir=/path/to/ghidra test
```

---

## STEP 6: Common Mistakes

### Mistake 1: Forgetting Resource Management
```java
// WRONG - Resource leak!
ServerSocket serverSocket = new ServerSocket(port);
// ... use socket ...

// RIGHT - Automatic resource management
try (ServerSocket serverSocket = new ServerSocket(port)) {
    // ... use socket ...
}
```

### Mistake 2: Not Handling Threading Properly in Ghidra
```java
// WRONG - May block Ghidra UI
// In plugin action:
SwingUtilities.invokeAndWait(() -> {
    // Long-running operation
});

// RIGHT - Use appropriate thread
SwingUtilities.invokeLater(() -> {
    // UI updates only
});

// For long operations, use separate thread
executor.submit(() -> {
    // Long-running operation
});
```

### Mistake 3: Not Following Ghidra Plugin Patterns
```java
// WRONG - Direct access to Ghidra internals
// Direct access to program state without proper checks

// RIGHT - Use Ghidra's API properly
Program currentProgram = getState().getCurrentProgram();
if (currentProgram != null) {
    // Safe to use program
}
```

---

## STEP 7: Quick Reference

### Important Imports
```java
import java.util.*;        // Collections, utilities
import java.io.*;         // File I/O
import java.net.*;        // Network operations
import java.util.concurrent.*;  // Threading
import ghidra.app.*;      // Ghidra application
import ghidra.app.plugin.*;  // Plugin framework
import ghidra.framework.plugintool.*;  // Plugin tool
import ghidra.program.model.listing.*; // Program access
```

### Modern Java Features
- Use enhanced for loops
- Use lambda expressions and streams
- Use Optional for nullable values
- Use try-with-resources for automatic resource management
- Use var for type inference (Java 10+)

---

## Quick Checklist

Before you write code:
- [ ] Did I read AGENTS.md?
- [ ] Am I using Java standard types (String, List, Map)?
- [ ] Am I following Ghidra plugin architecture patterns?
- [ ] Am I using modern Java features properly?
- [ ] Am I managing resources with try-with-resources?
- [ ] Am I handling threading correctly in Ghidra context?

**If NO to any: STOP and fix it!**

---

## STEP 8: Where to Get Help

1. **Read AGENTS.md** in this directory
2. **Read project README.md** for specific instructions
3. **Check Java Documentation**: https://docs.oracle.com/en/java/javase/
4. **Check Ghidra Plugin Dev Guide**: https://ghidra.re/courses/plugin_dev/
5. **Look at existing code** in the project for examples

---

## Remember

**Three most important things:**

1. **Follow Ghidra plugin architecture** (extend Plugin, CommonPluginTool, etc.)
2. **Use proper resource management** (try-with-resources, etc.)
3. **Use modern Java** (streams, lambda, Optional, etc.)

---

**Read AGENTS.md for complete details!**
