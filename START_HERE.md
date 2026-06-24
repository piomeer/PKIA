# Workspace Entry Point

> **版本**: v1.0  
> **用途**: 新 Cline Agent 附着记忆系统的入口文档

---

## Purpose

This file is the first entry point for any new Cline Agent.

Before performing implementation work:

1. Read `.cursorrules`
2. Execute Agent Bootstrap Protocol
3. Determine namespace
4. Load namespace progress file
5. Review relevant L2 memory
6. Generate Bootstrap Summary
7. Begin work

---

## Memory Architecture

```
L1  — 宪法层
   .cursorrules

L2  — 图谱层
   cursor-memory.json
   pkia_memory/ (Governor API)

L3  — 进度层
   progress/
```

---

## Available Namespaces

| Namespace | File | Purpose |
|-----------|------|---------|
| `workspace` | `progress/workspace.md` | Workspace 级开发管理，架构决策跟踪 |
| `pkia_mvp` | `progress/pkia_mvp.md` | PKIA MVP 产品开发进度 |
| `pkia_memory` | `progress/pkia_memory.md` | Memory 模块进度（已冻结） |
| `mukg` | `progress/mukg.md` | MuKG 遗留项目（只读） |

---

## Core Documents

| Document | Purpose |
|----------|---------|
| `docs/bootstrap_protocol_v1.1.md` | Bootstrap 生命周期定义（v1.1 增强版） |
| `docs/memory_sync_protocol_v1.0.md` | L2 ↔ L3 同步机制 |
| `docs/memory_sync_enforcement_v1.0.md` | 强制执行规则 + Completion Gate |
| `docs/memory_sync_audit_v1.0.md` | 证据链 + Receipt 机制 |
| `docs/memory_governance_freeze_v1.0.md` | 冻结范围 + 允许/禁止变更 |
| `docs/memory_boundary_v1.0.md` | Workspace vs User Memory 定义 |
| `docs/l3_namespace_architecture_v1.0.md` | L3 命名空间架构 |

---

## New Agent Startup Command

Read this file, then execute Agent Bootstrap Protocol v1.1 before starting work.
