---
name: always-read-code
description: MUST USE when answering code questions without having read the current source files first. Triggers on: "this code", "this bug", "fix this", "how to modify", "why error", "not working", file/function/class references, or writing code that calls existing APIs.
---

# Always Read Code

## Overview

The only trusted source for answering code questions is the actual file contents returned by `read_file`. Training data, session memory, and reasoning are unreliable—code may have been modified.

## When to Use

Trigger on ANY of the following:

- "this code" / "this bug" / "this error"
- "help me fix" / "how to modify" / "fix this"
- "this function" / "this class" / "this file"
- "why error" / "not working"
- File paths, function names, class names, path references
- Requests to write new code that may call existing APIs

## Execution Flow

```
User question → Identify relevant files → read_file → Answer based on actual content with line references
```

## Cross-Platform Tool Mapping

| Operation | opencode |
|-----------|----------|
| Read file | `read_file` |
| Search content | `search_files` |
| List files | `list_dir` |

## Red Lines

The following behaviors mean you haven't read the actual file—results may be wrong:

| Forbidden | Required Alternative |
|-----------|---------------------|
| "This file appears to..." | `read_file` first, then quote actual content |
| "Based on context..." | Verify function signatures are still correct |
| "I recall from last session..." | Re-read the file |
| "The standard signature is..." | Project may have monkey-patches |
| "The error means..." without reading file | Read error file context first |

**Each violation = go read the file.**

## Common Mistakes

- **User pasted code snippet, skipped reading** — Snippet may be incomplete, missing imports, inheritance, context
- **Just read it, assume unchanged** — User may have modified file between turns
- **Unclear file path, gave up** — Use search tools to find it, don't guess
- **Skipped reading to save tokens** — One wrong suggestion costs far more than one `read_file` call
