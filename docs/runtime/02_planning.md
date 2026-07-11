# 02 — Planning

> **Purpose**: Define what OpenSpec is responsible for.

## Mission

OpenSpec transforms user requests into executable specifications. It answers what must be built and why, never how to build it.

## Requirements

A complete plan must include:

1. **Exploration** — what exists, what the current code does
2. **Problem analysis** — what needs to change and why
3. **Scope** — what is in scope and what is explicitly out of scope
4. **Constraints** — technical, architectural, and process limitations

## Constraints

- OpenSpec never writes implementation code
- OpenSpec never modifies `.py`, `.ts`, `.tsx`, `.js`, or any source files
- All planning output must be saved as Markdown in `.specs/`
- Plans must reference specific file paths and line numbers when analyzing existing code

## Deliverables

| Artifact | Content | Location |
|----------|---------|----------|
| exploration.md | Codebase analysis, problem identification | `.specs/exploration.md` |
| design.md | Technical approach, architecture decisions | `.specs/design.md` |
| tasks.md | Breakdown of independent work units | `.specs/tasks.md` |

## Acceptance Criteria for a Plan

A plan is complete when:

- [ ] The problem is clearly stated
- [ ] Existing code has been read and referenced
- [ ] The proposed change is scoped (in/out)
- [ ] Tasks are independent and ordered by dependency
- [ ] Each task has clear acceptance criteria
- [ ] Risks and unknowns are documented
- [ ] Human can approve or reject with confidence

## Risk Assessment

Every plan must identify:

- **Known risks**: issues visible from current code
- **Unknowns**: areas where more exploration is needed
- **Dependencies**: what must exist before work can start
- **Fallback paths**: what to do if the primary approach fails

## Dependency Analysis

Plans must map task dependencies:

```
Task A ───→ Task B ───→ Task C
                  │
                  └──→ Task D
```

No task should depend on a task that has not been planned.

---

> **OpenSpec produces specifications. OpenSpec never implements.**
>
> **Next**: See [03_execution.md](03_execution.md) for how approved plans are executed.
