# AGENTS.md

# 核心开发规范

本项目采用 OpenSpec + Superpowers 的双轨制 SDD 工作流。

## 角色切换规则

1. **当收到规划类指令时（如"设计..."、"规划..."、"分析需求"）**：
   - 必须严格遵循 `.opencode/rules/openspec.md` 的规范。
   - 所有的输出必须以 Markdown 格式保存在 `.specs/` 目录下。
   - 严禁在此阶段修改源码。

2. **当收到执行类指令时（如"实现 tasks.md 中的任务 1"、"写代码"）**：
   - 必须严格遵循 `.opencode/rules/superpowers.md` 的规范。
   - 必须先在测试目录编写单元测试，运行失败后再编写业务代码。
   - 每完成一个任务，请更新 `.specs/tasks.md` 中的复选框状态 [x]。

---

## Project Overview

Dify is an open-source platform for developing LLM applications with an intuitive interface combining agentic AI workflows, RAG pipelines, agent capabilities, and model management.

The codebase is split into:

- **Backend API** (`/api`): Python Flask application organized with Domain-Driven Design
- **Frontend Web** (`/web`): Next.js application using TypeScript and React
- **Docker deployment** (`/docker`): Containerized deployment configurations

## Backend Workflow

- Read `api/AGENTS.md` for details
- Run backend CLI commands through `uv run --project api <command>`.
- Integration tests are CI-only and are not expected to run in the local environment.

## Frontend Workflow

- Read `web/AGENTS.md` for details

## Testing & Quality Practices

- Follow TDD: red → green → refactor.
- Use `pytest` for backend tests with Arrange-Act-Assert structure.
- Enforce strong typing; avoid `Any` and prefer explicit type annotations.
- Write self-documenting code; only add comments that explain intent.

## Language Style

- **Python**: Keep type hints on functions and attributes, and implement relevant special methods (e.g., `__repr__`, `__str__`). Prefer `TypedDict` over `dict` or `Mapping` for type safety and better code documentation.
- **TypeScript**: Use the strict config, rely on ESLint (`pnpm lint:fix` preferred) plus `pnpm type-check`, and avoid `any` types.

## General Practices

- Prefer editing existing files; add new documentation only when requested.
- Inject dependencies through constructors and preserve clean architecture boundaries.
- Handle errors with domain-specific exceptions at the correct layer.

## Agent Runtime

The Agent Runtime Layer (`docs/runtime/agent/01_workflow.md` through `docs/runtime/agent/06_development_constitution.md`) defines how AI agents operate in this repository. Read `docs/runtime/agent/01_workflow.md` first for the complete task lifecycle.

## Project Conventions

- Backend architecture adheres to DDD and Clean Architecture principles.
- Async work runs through Celery with Redis as the broker.
- Frontend user-facing strings must use `web/i18n/en-US/`; avoid hardcoded text.
