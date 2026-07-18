# 04 — Context

> **Purpose**: Define context loading policy.

## Always-Loaded Documents

These documents are loaded at the start of every task, regardless of scope:

| Document | Purpose |
|----------|---------|
| `AGENTS.md` | Role routing, project conventions, workflow dispatch |
| `.opencode/rules/openspec.md` | Planning phase rules |
| `.opencode/rules/superpowers.md` | Execution phase rules |
| `docs/runtime/06_development_constitution.md` | Immutable development rules |
| `progress/<namespace>.md` | Current phase, active decisions, blockers |

## Task-Specific Documents

Depending on the task, additional documents are loaded:

| Task Type | Documents to Load |
|-----------|------------------|
| Planning | `.specs/exploration.md`, `.specs/design.md`, all relevant source files |
| Implementation | `.specs/tasks.md`, relevant source files, related specs |
| Review | `.specs/` directory, `docs/runtime/05_review.md`, all changed files |

## Maximum Context Principle

The agent must load enough context to:

- Understand what exists before planning changes
- Understand how existing code works before modifying it
- Understand what was specified before implementing it
- Understand what was implemented before verifying it

Loading context is not optional. Every task begins with exploration.

## Minimal Context Principle

The agent must not load documents that are:

- Unrelated to the current task
- Belonging to a different namespace
- Superseded or deprecated (unless explicitly relevant)

## Priority Order

Context is loaded in this priority order:

1. **Constitutional**: AGENTS.md, development rules, runtime docs
2. **Project metadata**: progress files, active decisions
3. **Task specification**: `.specs/tasks.md`, current task details
4. **Relevant source**: files listed in the task's "affected files"
5. **Reference**: style guides, glossaries, schemas

## Stopping Rules

Stop loading context when:

- The task's acceptance criteria are understood
- The relevant source files have been read
- The existing patterns are clear
- Adding more context would not change the implementation approach

If the agent cannot determine relevance, load first and discard if unused. It is better to load too much than too little.
