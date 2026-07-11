# Design — Agent Runtime Layer

## Architecture Position

```
┌─────────────────────────────────────┐
│           Philosophy                │  ← Principles: why we build
├─────────────────────────────────────┤
│            Behavior                 │  ← Patterns: what we do
├─────────────────────────────────────┤
│        Agent Runtime Layer          │  ← THIS: how agents operate
│   ┌─────────────────────────────┐   │
│   │  01_workflow.md             │   │  Task lifecycle & state machine
│   │  02_planning.md             │   │  OpenSpec: spec production
│   │  03_execution.md            │   │  Superpowers: TDD execution
│   │  04_context.md              │   │  Context loading policy
│   │  05_review.md               │   │  Verification gates
│   │  06_development_constitution│   │  Immutable rules
│   └─────────────────────────────┘   │
├─────────────────────────────────────┤
│          Implementation             │  ← Concrete code & config
└─────────────────────────────────────┘
```

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Document naming | Numbered prefix (01_, 02_) | Establishes reading order without external index |
| Lifecycle model | Linear with replanning loops | Matches OpenSpec → Human → Superpowers pattern |
| State machine | 6 states: REQUEST → PLANNING → APPROVED → EXECUTING → VERIFYING → DONE | Covers full lifecycle with clear transition rules |
| Context loading | Always-loaded + task-specific + priority order | Balances principle of maximum context with minimum context |
| Review scope | 6 gates: from architecture to commit readiness | Follows the twin verification gates from existing Memory Governance |

## Document Relationships

```
01_workflow.md  (the lifecycle)
     ↓
02_planning.md  ←→  03_execution.md  (two sides of the lifecycle)
     ↓                    ↓
04_context.md   ←    (loaded by both)
     ↓
05_review.md    (closes the lifecycle)
     ↓
06_development_constitution.md  (applies to all)
```
