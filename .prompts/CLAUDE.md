# Bamboo Engine - Rebranding Guidelines & Constraints

## Core Mission
We are rebranding Godot Engine (C++ codebase) to "Bamboo Engine" while maintaining full MIT license compliance and backward compatibility.

## STRICT SAFETY RULES (NEVER VIOLATE)
1. **License & Attribution Integrity**:
   - Godot is licensed under the MIT License. You MUST NEVER delete or alter original copyright notices in existing source file headers (`// Copyright (c) 2014-present Godot Engine contributors...`).
   - NEVER touch or rename anything inside `thirdparty/` directory. All submodules and bundled libraries must preserve their original names, headers, and licenses.
   - Any new/modified branding must state: "Bamboo Engine is based on Godot Engine".

2. **Scope Boundaries**:
   - Focus ONLY on: Engine name, versioning, editor branding/UI, window titles, executable naming, and config directories.
   - DO NOT rename internal API classes, GDScript core types (e.g., keep `Node`, `Resource`, `GodotPhysics` unless explicitly told), or serialization IDs to avoid breaking existing projects.
   - Keep build system stability: Test changes with `scons` dry-run or target checks.

3. **Workflow**:
   - Perform atomic edits per task.
   - Always verify git diff before committing.
