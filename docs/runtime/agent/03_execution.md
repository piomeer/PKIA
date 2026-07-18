# 03 — Execution

> **Purpose**: Define Superpowers responsibilities.

## How Execution Starts

Execution begins when:

1. A plan exists in `.specs/tasks.md` with checked-off dependencies
2. The plan has been approved by human review
3. The current task's checkbox is `[ ]` (not started)

The agent loads the task description, acceptance criteria, and affected files, then enters the TDD loop.

## Task Decomposition

Superpowers follows `.specs/tasks.md` strictly:

- One task at a time, in order
- Each task runs a full TDD cycle: RED → GREEN → REFACTOR
- No task is started until its dependencies are complete

```
Task N:
  1. Write test (RED)
  2. Confirm test fails
  3. Write minimal implementation (GREEN)
  4. Confirm test passes
  5. Refactor if needed
  6. Run all tests (no regression)
  7. Mark task complete [x]
  ──→ Move to Task N+1
```

## Progress Tracking

| Artifact | Update Rule |
|----------|------------|
| `.specs/tasks.md` | Checkbox `[x]` after each completed task |
| `progress/<namespace>.md` | Update after each task or state change |
| Completion gate log | Record before claiming task done |

## When Execution Pauses

Execution pauses when:

- A task requires information not available in the codebase
- A task reveals an undocumented dependency
- A verification gate fails
- The agent detects an architecture inconsistency

During a pause, the agent reports to the human with:
- What was found
- What is blocked
- What is needed to continue

## When Execution Aborts

Execution aborts when:

- The human explicitly cancels the task
- The requirements have fundamentally changed
- The implementation approach is proven infeasible

On abort, the agent:
1. Reports current state
2. Preserves any partial work
3. Waits for human direction

## When Execution Requests Replanning

The agent requests replanning when:

- Implementation reveals the specification is incomplete or incorrect
- An architecture constraint makes the specified approach impossible
- A better approach is discovered that changes scope or interfaces
- Task dependencies form a cycle that was not anticipated

Replanning returns to OpenSpec (PLANNING state). The agent does not design — it reports what was found and waits.

---

> **Execution never redesigns architecture. Execution follows approved specifications.**
>
> **Previous**: See [02_planning.md](02_planning.md) for how plans are produced and approved.
