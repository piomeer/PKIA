# 05 — Review

> **Purpose**: Define verification gates.

## Gate 1 — Architecture Consistency

Verify that the implementation matches the architecture design:

- Do new files follow the established directory structure?
- Do new modules follow the established layering (controller → service → core)?
- Are dependencies pointing in the correct direction?

## Gate 2 — Cross-Reference Checking

Verify that references are correct:

- Do imports point to existing modules?
- Are all referenced file paths valid?
- Are all function calls matched to their definitions?

## Gate 3 — Broken Link Checking

For documentation:

- Are all `[link](path)` references valid?
- Are all relative paths correct?
- Are all document cross-references (e.g., `§4.2`) accurate?

## Gate 4 — Documentation Consistency

Verify that documentation matches code:

- Do docstrings or comments reflect what the code actually does?
- Are interface descriptions accurate?
- Have `.specs/` documents been updated to reflect decisions made during implementation?

## Gate 5 — Specification Compliance

Verify that the implementation satisfies the spec:

- Does every task checkbox in `.specs/tasks.md` that should be `[x]` reflect reality?
- Are all acceptance criteria from `.specs/design.md` met?
- Are there any unimplemented requirements?
- Are there any implemented features that were not specified?

## Gate 6 — Commit Readiness

Final gate before declaring DONE:

- [ ] All tests pass
- [ ] No linting errors
- [ ] No type errors
- [ ] `.specs/tasks.md` checkboxes are up to date
- [ ] `progress/<namespace>.md` is updated
- [ ] Human has been notified of completion
- [ ] No secrets or credentials in the diff

## Verification Flow

```
Verification requested
         │
         ▼
Gate 1: Architecture Consistency ── Fail ──→ Report to human
         │ Pass
         ▼
Gate 2: Cross-Reference Check ── Fail ──→ Report to human
         │ Pass
         ▼
Gate 3: Broken Link Check ── Fail ──→ Fix and re-check
         │ Pass
         ▼
Gate 4: Documentation Consistency ── Fail ──→ Update docs
         │ Pass
         ▼
Gate 5: Spec Compliance ── Fail ──→ Pause, request direction
         │ Pass
         ▼
Gate 6: Commit Readiness ── Fail ──→ Fix and re-check
         │ Pass
         ▼
         DONE
```

If any gate fails, the agent does not claim completion. The agent either fixes the issue or reports to the human.

---

> **See also**: [06_development_constitution.md](06_development_constitution.md) for immutable rules that govern the entire lifecycle.
