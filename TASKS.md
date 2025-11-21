# Ghidra TCP Server - Detailed Development Tasks

## Phase 1: Navigation & Enhancement

### Task 1.1: Code Traversal Enhancement
- [ ] Add `NAVIGATE-TO <address_or_function>` - Jump to specific location
- [ ] Add `NAVIGATE-STACK` - Show navigation history stack
- [ ] Add `NAVIGATE-BACK` - Go back in navigation history
- [ ] Add `NAVIGATE-FORWARD` - Go forward in navigation history
- [x] Add `BOOKMARK-LIST` - List all bookmarks ✓ COMPLETED
- [x] Add `BOOKMARK-SET <name> [address_or_function]` - Set bookmark at location ✓ COMPLETED
- [x] Add `BOOKMARK-GOTO <name>` - Go to bookmark ✓ COMPLETED
- [ ] Add `BOOKMARK-DELETE <name>` - Delete bookmark

### Task 1.2: Enhanced Renaming & Retyping
- [ ] Add `FUN-NAME-SET-CASCADE <old_name> <new_name>` - Rename across all references
- [ ] Add `VAR-NAME-SET-CASCADE <old_name> <new_name>` - Rename variable across all scopes
- [ ] Add `TYPE-APPLY-GLOBAL <old_type> <new_type>` - Apply type changes globally
- [ ] Add `REFACTOR-APPLY-TO-ALL-CALLS <function_name>` - Apply function signature to all calls

### Task 1.3: Note-Taking & Comment Management
- [x] Add `NOTE-ADD <location> <note_text>` - Add analysis note to location ✓ COMPLETED
- [x] Add `NOTE-LIST [location]` - List all notes (or at specific location) ✓ COMPLETED
- [ ] Add `NOTE-GET <note_id>` - Retrieve specific note
- [ ] Add `NOTE-DELETE <note_id>` - Delete specific note
- [x] Add `NOTE-SEARCH <search_term>` - Search notes by content ✓ COMPLETED
- [ ] Add `COMMENT-TEMPLATE-ADD <name> <template>` - Add reusable comment templates
- [ ] Add `COMMENT-TEMPLATE-APPLY <name> <location>` - Apply comment template

### Task 1.4: Location & Session Management
- [ ] Add `SESSION-SAVE <name>` - Save current analysis session
- [ ] Add `SESSION-LOAD <name>` - Load analysis session
- [ ] Add `SESSION-LIST` - List saved sessions
- [ ] Add `SESSION-DELETE <name>` - Delete session
- [x] Add `LOCATION-GET` - Get current analysis location ✓ COMPLETED
- [x] Add `LOCATION-SAVE <name>` - Save current location with name ✓ COMPLETED

### Task 1.5: Advanced Decompilation Options
- [ ] Add `DECOMPILE-STREAM <function_name> <chunk_size>` - Stream decompiled function in chunks
- [x] Add `DECOMPILE-CFG <function_name>` - Get control flow graph representation ✓ COMPLETED
- [ ] Add `DECOMPILE-AST <function_name>` - Get abstract syntax tree representation
- [ ] Add `DECOMPILE-UNOPTIMIZED <function_name>` - Get unoptimized decompilation
- [x] Add `DECOMPILE-CONTEXT <function_name> <depth>` - Get decompilation with callers/callees context ✓ COMPLETED

## Phase 2: Structure Management

### Task 2.1: Structure and Enum Management
- [ ] Add `STRUCT-DEFINE <name> {<field_spec>, ...}` command
- [ ] Add `STRUCT-FIELD-SET <struct_name> <field_idx> <new_spec>` command
- [ ] Add `STRUCT-USAGES <struct_name>` - Find all usages of structure
- [ ] Add `ENUM-DEFINE <name> {<item_spec>, ...}` command
- [ ] Add `ENUM-VALUE-SET <enum_name> <item_name> <value>` command
- [ ] Add `ENUM-USAGES <enum_name>` - Find all usages of enum

### Task 2.2: Type Hierarchy Management
- [ ] Add `TYPE-HIERARCHY <type_name>` to show inheritance
- [ ] Add `TYPE-USAGES <type_name>` to find all usages
- [ ] Add `TYPE-RENAME-IN-ALL-FUNCTIONS <old_type> <new_type>` for global type renaming
- [ ] Add `TYPE-PROPAGATE <function_name>` to propagate types through code

### Task 2.3: Batch Operations
- [ ] Add `BATCH-BEGIN` and `BATCH-END` commands for transaction groups
- [ ] Add `BATCH-EXECUTE <list_of_commands>` for bulk operations
- [ ] Add `BATCH-REVERT` for rollback functionality
- [ ] Add `BATCH-QUEUE <command>` for command queuing

### Task 2.4: Pattern-Based Operations
- [ ] Add `PATTERN-RENAME-FUNCTIONS <regex_pattern> <replacement>` - Batch rename functions by pattern
- [ ] Add `PATTERN-RENAME-VARIABLES <regex_pattern> <replacement>` - Batch rename variables by pattern
- [ ] Add `PATTERN-SET-TYPE <regex_pattern> <new_type>` - Set types by pattern
- [ ] Add `PATTERN-FIND-UNNAMED <function_pattern>` - Find unnamed functions matching pattern

### Task 2.5: Symbolic Execution Integration
- [ ] Add `DECOMPILE-WITH-PATH <function> <input_constraints>` - Decompile with specific input assumptions
- [ ] Add `SYMBOLIC-TRACE <function> <input_values>` - Generate symbolic execution trace
- [ ] Add `PATH-CONDITIONS <function> <address>` - Get path conditions for specific address
- [ ] Add `EXECUTION-PATHS <function>` - Enumerate possible execution paths

## Phase 3: Task & Roadmap Management

### Task 3.1: Personal Roadmap Features
- [ ] Add `ROADMAP-ADD <title> <description>` - Add roadmap item
- [ ] Add `ROADMAP-LIST [status]` - List roadmap items (all or by status)
- [ ] Add `ROADMAP-UPDATE <id> <field> <value>` - Update roadmap item
- [ ] Add `ROADMAP-DELETE <id>` - Delete roadmap item
- [ ] Add `ROADMAP-PRIORITIZE <id> <priority>` - Set priority level
- [ ] Add `ROADMAP-STATUS <id> <status>` - Update status (todo, in-progress, done)

### Task 3.2: Task Management System
- [ ] Add `TASK-ADD <title> <description> [parent_task]` - Add new task
- [ ] Add `TASK-LIST [status] [assignee]` - List tasks with filters
- [ ] Add `TASK-ASSIGN <task_id> <assignee>` - Assign task to person
- [ ] Add `TASK-UPDATE <task_id> <field> <value>` - Update task field
- [ ] Add `TASK-DELETE <task_id>` - Delete task
- [ ] Add `TASK-DEPENDENCY-ADD <task_id> <dependency_id>` - Add task dependency
- [ ] Add `TASK-PARENT-SET <child_task> <parent_task>` - Set parent-child relationship

### Task 3.3: Progress Tracking
- [ ] Add `PROGRESS-SNAPSHOT` - Create progress snapshot
- [ ] Add `PROGRESS-COMPARE <snapshot1> <snapshot2>` - Compare progress snapshots
- [ ] Add `PROGRESS-REPORT` - Generate progress report
- [ ] Add `PROGRESS-METRICS` - Show analysis metrics (functions renamed, types set, etc.)

### Task 3.4: Analysis Session Management
- [ ] Add `SESSION-START <project_name>` - Start new analysis session
- [ ] Add `SESSION-CONTINUE <session_id>` - Continue previous session
- [ ] Add `SESSION-SUMMARY` - Get current session summary
- [ ] Add `SESSION-EXPORT <format>` - Export session data in various formats

### Task 3.5: Patch/Modification Tracking
- [ ] Add `DECOMPILE-PATCHED <function_name>` - Get decompilation with patches applied
- [ ] Add `GET-PATCHES [function_name]` - Get list of applied patches
- [ ] Add `APPLY-PATCH <function_name> <patch_data>` - Apply decompilation patch
- [ ] Add `PATCH-HISTORY <function_name>` - Show patch history for function
- [ ] Add `PATCH-REVERT <function_name> <patch_id>` - Revert specific patch

## Phase 4: Advanced Analysis Tools

### Task 4.1: Complex Refactoring
- [ ] Add `REFACTOR-EXTRACT-FUNCTION <start_addr> <end_addr> <new_name>` - Extract function
- [ ] Add `REFACTOR-INLINE-FUNCTION <function_name>` - Inline function
- [ ] Add `REFACTOR-RESTRUCTURE-CODE <function_name>` - Restructure code for readability
- [ ] Add `REFACTOR-CLEAN-UP-UNNAMED` - Clean up unnamed functions/variables systematically

### Task 4.2: Analysis History Tracking
- [ ] Add `HISTORY-LIST [limit]` - List recent analysis actions
- [ ] Add `HISTORY-UNDO <action_id>` - Undo specific action
- [ ] Add `HISTORY-REDO <action_id>` - Redo undone action
- [ ] Add `HISTORY-COMPARE <function_before> <function_after>` - Compare states

### Task 4.3: Custom Analysis Workflows
- [ ] Add `WORKFLOW-DEFINE <name> <list_of_commands>` - Define custom workflow
- [ ] Add `WORKFLOW-EXECUTE <name> [params]` - Execute custom workflow
- [ ] Add `WORKFLOW-LIST` - List available workflows
- [ ] Add `WORKFLOW-DELETE <name>` - Delete workflow

### Task 4.4: Advanced Visualization Tools
- [ ] Add `GRAPH-EXPORT-DOT <function_name>` - Export graph in DOT format
- [ ] Add `CALLGRAPH-EXPORT <format>` - Export call graph
- [ ] Add `FLOWGRAPH-EXPORT <function_name> <format>` - Export control flow
- [ ] Add `DEPENDENCY-VIEW <function_name>` - Show function dependencies visually

### Task 4.5: Performance Analytics
- [ ] Add `ANALYZE-DECOMPILATION-PERFORMANCE <function_name>` - Get performance metrics for decompilation
- [ ] Add `FUNCTION-COMPLEXITY-ANALYZE <function_name>` - Analyze function complexity
- [ ] Add `TIMING-STATS` - Get timing statistics for server operations
- [ ] Add `RESOURCE-USAGE` - Get resource usage statistics

### Task 4.6: Interactive Refinement
- [ ] Add `REFINEMENT-SESSION-START <function_name>` - Start interactive refinement session
- [ ] Add `REFINEMENT-UPDATE-VARNAME <var_id> <new_name>` - Update variable name in current session
- [ ] Add `REFINEMENT-UPDATE-TYPE <var_id> <new_type>` - Update variable type in current session
- [ ] Add `REFINEMENT-GET-UPDATED` - Get decompilation with current refinements
- [ ] Add `REFINEMENT-SESSION-END` - End refinement session and apply changes

## Immediate Priorities (Next 2 Weeks)

1. Enhance note-taking functionality: `NOTE-ADD`, `NOTE-LIST` ✓ COMPLETED
2. Add bookmark management: `BOOKMARK-SET`, `BOOKMARK-GOTO`, `BOOKMARK-LIST` ✓ COMPLETED
3. Implement simple roadmap system: `ROADMAP-ADD`, `ROADMAP-LIST`
4. Add navigation commands: `NAVIGATE-TO`, `NAVIGATE-BACK`
5. Enhance session management: `SESSION-SAVE`, `SESSION-LOAD`
6. Add basic decompilation enhancements: `DECOMPILE-CFG`, `DECOMPILE-CONTEXT` ✓ COMPLETED