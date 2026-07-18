# 08 — Artifact Lifecycle

> **Purpose**: Define the lifecycle states for every document in the repository.

## Lifecycle Diagram

```
     ┌──────────┐
     │  Draft   │  Initial creation
     └────┬─────┘
          │ submit
          ▼
     ┌──────────┐
     │  Review  │  Under human evaluation
     └────┬─────┘
          │        ┌──────────┐
          ├── reject ──→│  Draft   │  (revise)
          │ approve     └──────────┘
          ▼
     ┌──────────┐
     │ Approved │  Active source of truth
     └────┬─────┘
          │
          ├── supersede ──→ ┌────────────┐
          │                 │ Superseded │  Replaced by newer version
          │                 └──────┬─────┘
          │ freeze                │
          ▼                       ▼
     ┌──────────┐          ┌──────────┐
     │  Frozen  │          │ Archived │  No longer relevant
     └──────────┘          └──────────┘
```

## State Definitions

### Draft

| Attribute | Value |
|-----------|-------|
| **Definition** | Document is being created or revised |
| **Allowed** | Any modification, restructuring, or deletion |
| **Forbidden** | (nothing — draft is free-form) |
| **Transition to** | Review (when author submits for evaluation) |

A draft is not yet authoritative. It represents work in progress.

---

### Review

| Attribute | Value |
|-----------|-------|
| **Definition** | Document is under human evaluation |
| **Allowed** | Minor corrections, clarification edits in response to feedback |
| **Forbidden** | Substantive content changes without re-submission |
| **Transition to** | Approved (human accepts) or Draft (human requests changes) |

During review, the document is considered provisional. No implementation work depends on a document in Review state.

---

### Approved

| Attribute | Value |
|-----------|-------|
| **Definition** | Document is the active source of truth |
| **Allowed** | Minor corrections (typos, formatting, broken links) |
| **Forbidden** | Substantive changes to requirements, design, or scope |
| **Transition to** | Frozen (when stability is required) or Superseded (when replaced) |

An approved document may be used as the basis for implementation. It is the single source of truth for its scope.

---

### Frozen

| Attribute | Value |
|-----------|-------|
| **Definition** | Document is locked against any modification |
| **Allowed** | (nothing — frozen documents are immutable) |
| **Forbidden** | Any change, including minor corrections |
| **Transition to** | Superseded (only by formal exception process) |

Freezing is used to lock a baseline. A frozen document can only be replaced, not modified.

---

### Superseded

| Attribute | Value |
|-----------|-------|
| **Definition** | Document has been replaced by a newer version |
| **Allowed** | Metadata updates (superseded-by link, archival notes) |
| **Forbidden** | Content changes |
| **Transition to** | Archived (when no longer needed for reference) |

A superseded document is kept for historical reference. It is marked with a pointer to the replacement document.

---

### Archived

| Attribute | Value |
|-----------|-------|
| **Definition** | Document is no longer relevant |
| **Allowed** | (nothing — archived documents are read-only) |
| **Forbidden** | Any modification |
| **Transition to** | (no forward transitions — archival is terminal) |

Archived documents are preserved for audit trail but are not expected to be read during normal work.

## State Transition Rules

| From | To | Trigger | Required Approval |
|------|----|---------|-------------------|
| Draft | Review | Author submits for evaluation | Author |
| Review | Draft | Reviewer requests changes | Human |
| Review | Approved | Reviewer accepts | Human |
| Approved | Frozen | Baseline is locked | Human |
| Approved | Superseded | Replacement document is approved | Human |
| Frozen | Superseded | Formal exception process | Human |
| Superseded | Archived | Document is no longer referenced | Human |
| Superseded | Draft | (not allowed — create a new document) | — |
| Archived | (any) | (not allowed — archival is terminal) | — |

## Applicability

This lifecycle applies to:

- All documents in `docs/`
- All specification documents in `.specs/`
- All runtime documents in `docs/runtime/`
- Any future document that serves as a source of truth

This lifecycle does not apply to:

- Source code (follows its own development cycle)
- Temporary or working files
- Generated output
