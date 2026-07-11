# Runtime Documentation

This directory contains two independent runtime architectures:

## Agent Runtime Layer

Describes how AI agents operate in this repository. Defines the lifecycle, planning, execution, context, review, and constitutional rules for agent-driven development.

| Document | Purpose | Role |
|----------|---------|------|
| [01_workflow.md](01_workflow.md) | Task lifecycle & state machine | Entry point |
| [02_planning.md](02_planning.md) | OpenSpec specification production | Architect |
| [03_execution.md](03_execution.md) | Superpowers TDD execution | Developer |
| [04_context.md](04_context.md) | Context loading policy | Both |
| [05_review.md](05_review.md) | Verification gates | Review |
| [06_development_constitution.md](06_development_constitution.md) | Immutable development rules | All |

## PKIA Pipeline Runtime

Describes the PKIA data pipeline runtime — Dify Workflow node mapping, data flow, failure handling, and deployment for the GitHub Trending scoring pipeline.

See [runtime_architecture_overview_v1.md](runtime_architecture_overview_v1.md) for the complete PKIA Runtime Architecture overview, topology diagram, and document index.
