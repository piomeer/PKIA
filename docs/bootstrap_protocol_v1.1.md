# Agent Bootstrap Protocol v1.1

> **文档状态**: Architecture Freeze Document  
> **版本**: 1.1 (升级自 v1.0)  
> **更新日期**: 2026-06-23  
> **用途**: 定义新 Cline Agent 如何附着到 Workspace Memory（增强版）

---

## 1. Purpose

### 1.1 v1.0 的不足

| 问题 | v1.0 状态 | v1.1 改进 |
|------|:---------:|-----------|
| L2 记忆审查过于笼统 | 仅审查 slot 计数 | **提取具体 ACTIVE 值到工作上下文** |
| 缺少工作上下文生成 | 无 | **将 ACTIVE 架构决策汇总为可读上下文** |
| 缺少当前约束摘要 | 无 | **提取冻结规则和架构限制** |
| 进度模板缺少记忆索引 | 无 | **增加 Relevant L2 Memories / Active Decisions 板块** |

### 1.2 v1.1 增强

- **Relevant L2 Memory Extraction**: 提取当前命名空间相关的 ACTIVE 架构决策
- **Working Context Generation**: 将 ACTIVE 节点值汇总为可读的工作上下文
- **Current Constraints Summary**: 提取冻结规则、禁止变更、架构锁死等信息
- **Bootstrap Failure Detection**: 缺失关键信息时标记 Bootstrap FAILED

---

## 2. Bootstrap Lifecycle (v1.1)

```
Agent Start
    │
    ▼
┌─────────────────────┐
│  Namespace          │── 确定当前任务属哪个命名空间
│  Resolution         │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Progress           │── 加载 progress/<namespace>.md
│  Discovery          │   如缺失则使用 v1.1 模板创建
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  L2 Review          │── Governor.get_active() 提取
│  (Enhanced)         │   ★ 相关架构决策
│                     │   ★ 当前约束
│                     │   ★ 冻结规则
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Working Context    │── ★ 新增: 生成工作上下文
│  Generation         │   汇总 ACTIVE 决策 → 可读摘要
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  L3 Review          │── 审查阶段/任务/阻塞
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Bootstrap Summary  │── ★ 新增: 完整性检查
│  + Failure Check    │   缺失关键信息 → FAILED
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Task Execution     │── 开始实现工作
└─────────────────────┘
```

---

## 3. Enhanced L2 Review (§5 升级版)

### 3.1 必须提取的内存类别

| 类别 | 提取方法 | 说明 |
|------|---------|------|
| **Relevant Architecture Decisions** | `Governor.get_active("architecture:*@*")` | 所有 ACTIVE 架构决策的值 |
| **Project Facts** | `Governor.get_active("project:*@*")` | 当前项目阶段和配置 |
| **Active Constraints** | 从 `.clinerules` §4 Freeze Scope 提取 | 禁止变更列表 |
| **Governance Status** | `Governor.get_active("architecture:memory_governance_status@global")` | 冻结是否激活 |

### 3.2 提取输出格式

```
# Relevant L2 Memories
<category>:<key>@<context> = <value>
<category>:<key>@<context> = <value>
...

# Active Decisions (extracted from architecture slots)
- <descriptive summary of what each decision means>

# Current Constraints
- <constraint 1>
- <constraint 2>
```

### 3.3 审查失败处理

| 失败模式 | 恢复操作 |
|---------|---------|
| Governor 无法启动 | 从 cline-memory.json 直接读取 JSON Lines |
| cline-memory.json 损坏 | 记录错误，使用空状态继续 |
| 特定 slot 缺失 | 记录缺失但不阻断 |

---

## 4. Working Context Generation (新增)

### 4.1 生成规则

将提取的 L2 内存转换为 Agent 可直接使用的工作上下文：

```
Working Context:
  System State: [基于架构决策的系统状态描述]
  Active Governance: [冻结/非冻结]
  Key Architecture Decisions:
    - [决策 1]
    - [决策 2]
  Current Phase: [项目阶段]
  Constraints:
    - [约束 1]
```

### 4.2 示例

```
Working Context:
  System State: Workspace Memory Governance Feature Complete
  Active Governance: Frozen (Event Sourcing / Transaction Log / Decay 禁止)
  Key Architecture Decisions:
    - L3 使用命名空间文件 (progress/) 而非单文件 PROGRESS.md
    - Governor 直接从 cline-memory.json 读取，不依赖 MCP 持久化
    - Conflict Resolution: USER_EXPLICIT > AGENT_INFERRED > confidence > time
  Current Phase: Memory Governance — Feature Complete, Frozen
  Constraints:
    - 禁止修改 Governor 核心逻辑
    - 禁止引入 Event Sourcing 或 Transaction Log
    - 禁止 Rewrite Ontology 或 Schema
```

---

## 5. v1.1 Progress File Template (升级版)

### 5.1 标准模板

```
# <Namespace> Progress

> **Namespace**: <name>
> **文件**: `progress/<name>.md`

---

## Current Phase

**Initialized**

---

## Active Tasks

- (无)

---

## Completed Tasks

- (无)

---

## Relevant L2 Memories

| Slot | Value |
|------|-------|
| `architecture:*@*` | ... |

## Active Decisions

- (无)

## Current Constraints

- (无)

## Working Context

- (无)

---

## Blockers

- (无)

---

## Next Steps

- 等待任务分配

---

*最后更新: <date>*
```

---

## 6. Bootstrap Summary (v1.1)

### 6.1 格式

```
Bootstrap Summary:
  Namespace: workspace / pkia_mvp / pkia_memory / mukg
  L2 Memory Reviewed: [slots count]
  Relevant Memories Extracted: [yes/no]
  Working Context Generated: [yes/no]
  Current Constraints Reviewed: [yes/no]
  L3 Progress Reviewed: [Current Phase]
  Current Phase: [phase]
  Active Tasks: [count]
  Blockers: [count]
  Governance Freeze: [Active / Not Applicable]
  Bootstrap Integrity: [PASS / FAILED]
```

### 6.2 Bootstrap Integrity 判定

| 条件 | Integrity |
|------|:---------:|
| Relevant L2 Memories 缺失 | **FAILED** |
| Working Context 缺失 | **FAILED** |
| Current Constraints 缺失 | **FAILED** |
| 全部存在 | **PASS** |

### 6.3 完整性失败处理

如果 Bootstrap Integrity = FAILED：

1. 输出警告信息
2. 记录缺失项
3. **允许继续工作**（信息缺失不阻断执行）
4. 任务完成后在 Memory Review 中注明缺失项

---

> **文档结束**  
> 本规范为 v1.0 的增强版本，不修改 v1.0 的核心生命周期。