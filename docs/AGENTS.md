# AGENTS

## Scope
- Applies to this Java-based Ghidra plugin project and its subdirectories

## Overview
This is a Java project for creating a Ghidra plugin with TCP server functionality for client communication.

## Build System
- **Type**: Gradle (standard for Ghidra plugins)
- **Build file**: build.gradle
- **Build commands**: gradle build, gradle run, gradle install

## Code Conventions

### Java Standard Libraries
This project uses standard Java libraries and Ghidra APIs:
- `String` for strings
- `List<T>`, `ArrayList<T>` for collections
- `Map<K,V>`, `HashMap<K,V>` for associative collections
- Standard Java streams and utilities from java.util.*

### Modern Java Features
Use modern Java features when appropriate:
- Enhanced for loops: `for (T item : collection)`
- Lambda expressions: `(param) -> expression`
- Optional<T> for nullable values
- Try-with-resources for automatic resource management
- var for type inference (Java 10+)

### Memory Management
- Rely on Java garbage collection
- Close resources with try-with-resources or close() in finally blocks
- Be mindful of object lifecycle in Ghidra's context

### Naming Conventions
Follow Java standard naming conventions:
- **Classes**: `PascalCase` (MyClass)
- **Methods/Variables**: `camelCase` (myMethod, myVariable)
- **Constants**: `UPPER_SNAKE_CASE` (MY_CONSTANT)
- **Packages**: `lowercase` (com.example.plugin)

### File Organization
- Source files: `.java` in `src/main/java/` directory
- Resources: in `src/main/resources/` directory
- Test files: `.java` in `src/test/java/` directory

## Common Patterns

### Stream API Usage
```java
// Processing collections with streams
List<String> items = Arrays.asList("a", "b", "c");
List<String> upperCaseItems = items.stream()
    .map(String::toUpperCase)
    .collect(Collectors.toList());
```

### String Operations
```java
String str = "hello world";
if (str.contains("world")) {
    // found
}
String sub = str.substring(0, 5);  // "hello"

// Safe null handling
Optional<String> optStr = Optional.ofNullable(maybeNullString);
String result = optStr.orElse("default");
```

### Collection Operations
```java
List<Integer> numbers = new ArrayList<>();
numbers.add(42);

Map<String, Integer> map = new HashMap<>();
map.put("key", value);
Integer value = map.get("key");  // Returns null if not found
// Or use map.getOrDefault("key", defaultValue)
```

### TCP Server Pattern
```java
try (ServerSocket serverSocket = new ServerSocket(port)) {
    while (!Thread.currentThread().isInterrupted()) {
        Socket clientSocket = serverSocket.accept();
        // Handle client in separate thread
        executor.submit(() -> handleClient(clientSocket));
    }
}
```

## Building and Testing

### Building with Gradle
- Compile: `./gradlew compileJava`
- Build: `./gradlew build`
- Install to Ghidra: `./gradlew install`

### Testing
- JUnit 5 for unit testing
- Ghidra's test framework for integration tests
- Mockito for mocking dependencies

## Dependencies

Ghidra plugin dependencies are typically managed in:
- build.gradle - Gradle dependencies
- gradle.properties - Gradle settings and Ghidra paths
- extensions.xml - Plugin extension configuration

## Documentation

- Code comments should explain "why", not "what"
- JavaDoc for public APIs
- Keep README.md updated with build and installation instructions

## Testing

If the project has tests:
- Unit tests in `src/test/java/` directory
- Integration tests using Ghidra's testing framework
- Run tests with `./gradlew test`

## Workflow and Project Organization

See `agents/common-workflow.md` for complete workflow patterns.

### Task Tracking
- Use `TASKS.md` for task tracking with sections: TODO, IN_PROGRESS, DONE
- Tasks belong to phases (Phase 1, Phase 2, etc.)
- Update TASKS.md after every completed task
- **CRITICAL**: When you discover new tasks during work, ADD them to TASKS.md immediately
  - Don't wait - document new tasks as soon as you realize they're needed
  - Examples: "Need password reset", "Found security issue", "Missing tests"
  - Add to appropriate phase in TODO section

### Git Workflow - ALWAYS commit after successful completion
- BEFORE committing: Run build and test scripts if they exist
- Commit format: `Task X.Y: Description`
- ALWAYS push after commit

### Documentation: Use docs/ with PlantUML (.puml → .png)

### Roadmap: Use roadmap/ directory (v1.0.0.md, etc.)

### Pseudocode: Use pseudocode/ directory before implementation

## References

- [Java Documentation](https://docs.oracle.com/en/java/javase/)
- [Ghidra Plugin Development Guide](https://ghidra.re/courses/plugin_dev/)
- Project-specific documentation in README.md

