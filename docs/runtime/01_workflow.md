# 01 — Workflow

> **Purpose**: Describe the complete lifecycle of one task.

## Runtime Lifecycle

Every task follows a linear lifecycle with two possible replanning loops:

```
User Request
     │
     ▼
┌─────────────┐
│  PLANNING   │ ◄───────────┐
│  (OpenSpec) │             │
└──────┬──────┘             │
       │                    │
       ▼                    │
┌─────────────┐             │
│  APPROVAL   │  ── Reject ─┤
│  (Human)    │             │
└──────┬──────┘             │
       │ Approved           │
       ▼                    │
┌─────────────┐             │
│  EXECUTING  │  ── Request ─┤
│ (Superpowers)│  Replan     │
└──────┬──────┘             │
       │                    │
       ▼                    │
┌─────────────┐             │
│ VERIFYING   │  ── Fail ───┤
│  (Review)   │             │
└──────┬──────┘             │
       │ Pass               │
       ▼                    │
┌─────────────┐             │
│    DONE     │             │
└─────────────┘             │
                            │
  Replan triggers:          │
  - Requirements change     │
  - Architecture issue      │
  - Verification failure    │
  - Human direction         │
```

### State Transitions

| From | To | Trigger | Actor |
|------|----|---------|-------|
| REQUEST | PLANNING | User submits request | Human |
| PLANNING | APPROVAL | Specs produced | Agent (OpenSpec) |
| APPROVAL | PLANNING | Rejected / changes requested | Human |
| APPROVAL | EXECUTING | Approved | Human |
| EXECUTING | PLANNING | Replan requested | Agent (Superpowers) |
| EXECUTING | VERIFYING | Implementation complete | Agent (Superpowers) |
| VERIFYING | PLANNING | Verification failed | Agent (Review) |
| VERIFYING | DONE | All gates pass | Agent (Review) |

## Human Responsibilities

1. **Submit requests** — define what needs to be done
2. **Review specs** — approve or reject OpenSpec proposals
3. **Provide direction** — clarify ambiguous requirements
4. **Request replanning** — when scope or priorities change
5. **Accept completion** — confirm work meets expectations

Humans do not specify implementation details. They specify intent.

## Agent Responsibilities

1. **Explore** — understand the codebase before planning
2. **Plan** — produce complete specifications (OpenSpec)
3. **Execute** — implement following TDD (Superpowers)
4. **Verify** — run all gates before claiming completion
5. **Report** — communicate status, blockers, results

Agents do not skip steps. Every task passes through all lifecycle states.

## Failure Handling

| Failure Mode | Response |
|-------------|----------|
| Spec rejected | Return to PLANNING, revise, re-submit |
| Test fails | Fix implementation, do not skip tests |
| Verification fails | Return to EXECUTING or PLANNING depending on root cause |
| Requirements change mid-task | Pause execution, request replanning |
| Architecture conflict | Request replanning from PLANNING phase |
| Blocking dependency | Report to human, wait for direction |

A task is never committed unless DONE is reached with all verification gates closed.

---

> **Next**: See [02_planning.md](02_planning.md) for the planning phase specification. See [03_execution.md](03_execution.md) for the execution phase specification.
