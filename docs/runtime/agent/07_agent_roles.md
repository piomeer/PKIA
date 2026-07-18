# 07 — Agent Roles

> **Purpose**: Define the responsibilities and boundaries of each agent role.

## Role Overview

```
User Request
     │
     ▼
┌──────────────┐
│  OpenSpec    │  Plans what to build
└──────┬───────┘
       │ specs
       ▼
┌──────────────┐
│   Human      │  Approves or rejects
└──────┬───────┘
       │ approved
       ▼
┌──────────────┐
│ Superpowers  │  Implements via TDD
└──────┬───────┘
       │ verified code
       ▼
┌──────────────┐
│   Future     │  Extensibility slot
│   Agent      │
└──────────────┘
```

Each role has a strict boundary. No role performs another role's work.

---

## OpenSpec

The planning role. Transforms user intent into executable specifications.

| Attribute | Value |
|-----------|-------|
| **Purpose** | Analyze requirements and produce specifications |
| **Input** | User request, existing codebase |
| **Output** | `.specs/exploration.md`, `.specs/design.md`, `.specs/tasks.md` |
| **Can** | Read any file, analyze architecture, trace dependencies, produce specs |
| **Cannot** | Write implementation code, modify `.py`, `.ts`, `.tsx`, `.js`, or any source files |
| **Typical Deliverables** | Exploration analysis, design document, task breakdown |

**Entry trigger**: User submits a planning request ("design...", "plan...", "analyze...")

**Exit condition**: `.specs/tasks.md` is complete and handed to human for approval.

---

## Superpowers

The execution role. Implements approved specifications through strict TDD.

| Attribute | Value |
|-----------|-------|
| **Purpose** | Implement approved specifications |
| **Input** | Approved `.specs/tasks.md`, `.specs/design.md` |
| **Output** | Implementation code, passing tests |
| **Can** | Write code, run tests, refactor within spec scope, verify gates |
| **Cannot** | Redesign architecture, change scope, skip tests, implement without a spec |
| **Typical Deliverables** | Source files, test files, updated progress documents |

**Entry trigger**: Human approval of `.specs/tasks.md`.

**Exit condition**: All verification gates pass and work is declared DONE.

---

## Human

The decision role. Provides direction and exercises authority over the lifecycle.

| Attribute | Value |
|-----------|-------|
| **Purpose** | Provide direction, make approval decisions |
| **Input** | Specifications, status reports, completion reports |
| **Output** | Approvals, rejections, guidance, requirement changes |
| **Can** | Approve or reject any spec, change requirements, cancel tasks |
| **Cannot** | (unconstrained — human has ultimate authority) |
| **Typical Deliverables** | Approval signals, feedback, priority decisions |

**Entry trigger**: A specification or completion report is presented.

**Exit condition**: Task is either approved, rejected, or redirected.

---

## Future Agent

The extensibility slot. Reserved for roles not yet defined.

| Attribute | Value |
|-----------|-------|
| **Purpose** | Placeholder for future automation roles |
| **Input** | (undefined) |
| **Output** | (undefined) |
| **Can** | (defined when the role is created) |
| **Cannot** | (defined when the role is created) |
| **Typical Deliverables** | (defined when the role is created) |

Future Agent roles follow the same role contract pattern: purpose, input, output, can, cannot, deliverables.

---

## Role Contracts Summary

| Aspect | OpenSpec | Superpowers | Human |
|--------|----------|-------------|-------|
| Specialization | Analysis & planning | Implementation & testing | Decision & direction |
| Output type | Specifications | Working code | Approvals |
| Reads | All files | Specs + relevant source | Summaries |
| Writes | `.specs/*.md` | Source + test files | Nothing (decisions only) |
| Approval needed | Human | OpenSpec spec | None |
| Can be automated | Yes | Yes | No |
