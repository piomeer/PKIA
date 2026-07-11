# Exploration — Agent Runtime Layer

## Existing Architecture

The project uses a dual-track SDD workflow:
- **OpenSpec** (Architect role): analyzes, plans, designs — outputs to `.specs/`
- **Superpowers** (Developer role): implements in TDD cycles — respects `.specs/tasks.md`

A PKIA-specific runtime already exists at `docs/runtime/` (7 documents covering Dify Workflow node mapping, data flow, failure handling, deployment). This is **not** the target of this proposal.

## The Gap

There is no formal description of **how an AI agent moves through its lifecycle** in this repository. Key unanswered questions:

- When does an agent start by exploring vs. start by implementing?
- Where does human approval fit in the workflow?
- What triggers replanning?
- What constitutes "done" for a task?
- What documents must an agent always load? What documents are task-specific?

The existing documents describe PKIA pipeline architecture but not the agent operating model.

## Discovery

Four architectural layers exist conceptually:
1. **Philosophy** — Why we build (principles, values)
2. **Behavior** — What we do (patterns, workflows)
3. **Runtime** — How agents operate (THIS PROPOSAL)
4. **Implementation** — Concrete code and configuration

Only layers 3 (PKIA pipeline) and 4 (PKIA code) have concrete files. The Agent Runtime Layer is entirely new.

## Design Constraints

- Must not modify existing Philosophy, Behavior, or Implementation
- Must not rename existing files
- Must be reusable across Personal Wiki, PKIA, and future agent projects
- Must describe a **general** agent operating model, not a project-specific workflow
