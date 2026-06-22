# Agent Bootstrap Protocol v1.0

> **文档状态**: Architecture Freeze Document  
> **版本**: 1.0  
> **更新日期**: 2026-06-22  
> **用途**: 定义新 Cline Agent 如何附着到 Workspace Memory

---

## 1. Purpose

### 1.1 Problem

新 Agent 启动时不知道：

| 缺失信息 | 后果 |
|---------|------|
| 当前架构状态 | 可能做出与已冻结决策矛盾的判断 |
| 命名空间所有权 | 可能写入错误的 progress 文件 |
| 已有架构决策 | 可能重复讨论已解决的问题 |
| 当前进度状态 | 可能从错误的地方开始工作 |

### 1.2 Solution

在开始实现工作之前，Agent 必须执行 Bootstrap 流程：确定命名空间 → 加载进度 → 审查 L2 记忆 → 生成摘要。

---

## 2. Bootstrap Lifecycle

```
Agent Start
    │
    ▼
┌─────────────────────┐
│  Namespace          │── 确定当前任务属哪个命名空间
│  Resolution         │   规则见 §3
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Progress           │── 加载 progress/<namespace>.md
│  Discovery          │   如缺失则创建
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  L2 Review          │── 审查相关架构决策
│                     │   Governor.get_active()
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  L3 Review          │── 审查当前阶段/任务/阻塞
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Bootstrap Summary  │── 输出摘要（见 §6）
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Task Execution     │── 开始实现工作
└─────────────────────┘
```

**规则**: Bootstrap 完成前不得开始实现工作。

---

## 3. Namespace Resolution Rules

### 3.1 命名空间定义

| 命名空间 | 文件 | 适用任务 |
|---------|------|---------|
| `workspace` | `progress/workspace.md` | 架构决策、项目级管理、基础设施 |
| `pkia_mvp` | `progress/pkia_mvp.md` | PKIA MVP 产品开发 |
| `pkia_memory` | `progress/pkia_memory.md` | Memory 模块相关改动 |
| `mukg` | `progress/mukg.md` | MuKG 遗留项目 |

### 3.2 选择规则

1. 如果任务涉及 **Memory 架构决策** → `pkia_memory`
2. 如果任务涉及 **PKIA 产品功能** → `pkia_mvp`
3. 如果任务涉及 **MuKG 遗留代码** → `mukg`
4. 所有其他任务 → `workspace`

### 3.3 解析失败处理

如果无法确定命名空间，默认使用 `workspace` 并记录说明。

---

## 4. Progress Discovery Rules

### 4.1 加载规则

1. 读取 `progress/<namespace>.md`
2. 解析 Current Phase / Active Tasks / Completed Tasks / Blockers / Next Steps
3. 文件缺失 → 使用标准模板创建

### 4.2 创建模板

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

## Blockers

- (无)

---

## Next Steps

- 等待任务分配

---

*最后更新: <date>*
```

---

## 5. L2 Review Rules

### 5.1 必须审查的内容

| 审查项 | 方法 |
|--------|------|
| 架构决策 | `Governor.get_active("architecture:*@*")` |
| 项目阶段 | `Governor.get_active("project:*@*")` |
| 冻结规则 | 读取 `.clinerules` §5 Memory Governance + §4 Freeze Scope |

### 5.2 审查方法

```
# 通过 Governor 读取相关 ACTIVE 节点
from pkia_memory.governor import Governor

gov = Governor()
gov.startup("cline-memory.json")

# 获取所有已知 slot
gov.status()["slots"]
```

### 5.3 审查失败处理

如果 Governor 不可用或异常：

| 失败模式 | 恢复操作 |
|---------|---------|
| Governor 无法启动 | 尝试从 cline-memory.json 直接读取 |
| cline-memory.json 损坏 | 记录错误，使用空状态继续 |
| MCP Memory Server 不可用 | 不影响（Governor 直接从文件读取） |

---

## 6. Bootstrap Summary Format

每次 Bootstrap 完成后必须输出以下摘要：

```
Bootstrap Summary:
  Namespace: workspace / pkia_mvp / pkia_memory / mukg
  L2 Memory Reviewed: [slots count]
  L3 Progress Reviewed: [Current Phase]
  Current Phase: [phase]
  Active Tasks: [count]
  Blockers: [count]
  Governance Freeze: [Active / Not Applicable]
```

### 示例

```
Bootstrap Summary:
  Namespace: workspace
  L2 Memory Reviewed: 12 architecture slots
  L3 Progress Reviewed: L3 Namespace Migration — Complete
  Current Phase: Memory Governance — Feature Complete, Frozen
  Active Tasks: 0 (awaiting instruction)
  Blockers: 2 (bouncer script, MuKG remnants)
  Governance Freeze: Active
```

---

## 7. Failure Handling

| 失败场景 | 恢复动作 |
|---------|---------|
| 命名空间无法确定 | 默认使用 `workspace`，记录说明 |
| `progress/<namespace>.md` 不存在 | 使用标准模板创建 |
| Governor 不可用 | 直接从 `cline-memory.json` 读取 JSON Lines |
| `cline-memory.json` 损坏 | 记录错误，使用空索引继续 |
| `.clinerules` 不存在 | 无法发生（文件在项目根） |
| MCP 进程未运行 | 不影响（Governor 直接读文件） |