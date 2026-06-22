# Memory Synchronization Protocol v1.0

> **文档状态**: Architecture Freeze Document  
> **版本**: 1.0  
> **更新日期**: 2026-06-21  
> **用途**: 定义 L2 (cline-memory.json) 与 L3 (progress/<namespace>.md) 之间的同步机制

---

## 目录

1. [核心原则](#1-核心原则)
2. [L2 更新触发条件](#2-l2-更新触发条件)
3. [L3 更新触发条件](#3-l3-更新触发条件)
4. [Task Completion Checklist](#4-task-completion-checklist)
5. [Memory Update Workflow](#5-memory-update-workflow)
6. [未来自动化方向](#6-未来自动化方向)
7. [同步优先级矩阵](#7-同步优先级矩阵)
8. [附录：同步示例](#8-附录同步示例)

---

## 1. 核心原则

### 1.1 同步方向

```
L1 宪法层 (.clinerules)
    │ 永久不变，仅手动修改
    │
    ▼
L2 图谱层 (cline-memory.json)
    │ 长期语义记忆，确定性拓扑
    │ 更新需要 Governor 或 MCP 操作
    │
    ▼
L3 进度层 (PROGRESS.md)
    │ 短期工作记忆，自由文本
    │ 可直接编辑
```

### 1.2 同步纪律

| 原则 | 说明 |
|------|------|
| **L3 必须先更新** | 进度变化先行记录在 L3，再由 Agent 判断是否沉淀到 L2 |
| **L2 不可逆** | L2 写入是 Append-only，删除/修改必须通过 DEPRECATED 机制 |
| **L3 可覆盖** | L3 是草稿本，旧进度直接覆盖，无需保留历史 |
| **不同步则丢失** | 未写入 L2 的架构决策在 session 结束后不可恢复 |
| **禁止自动同步** | 所有从 L3 → L2 的同步必须基于 Agent 的判断，不可自动化 |

### 1.3 数据流模型

```
Task Execution
    │
    ▼
┌────────────────────────────────┐
│ L3 更新（实时）                │
│ - 进度记录                     │
│ - 阻塞登记                     │
│ - 下一步计划                   │
└────────────┬───────────────────┘
             │ Agent 判断是否需要沉淀
             ▼
┌────────────────────────────────┐
│ L2 更新（按需）                │
│ - 架构决策                     │
│ - 规范变更                     │
│ - 长期事实                     │
└────────────────────────────────┘
```

---

## 2. L2 更新触发条件

L2 是**长期语义记忆**，只存储确定性的、跨 session 可复用的知识。以下情况必须触发 L2 更新。

### 2.1 架构决策变化

| 决策类型 | 示例 | L2 写入格式 |
|---------|------|------------|
| 技术栈变更 | 新增框架/语言/工具 | `workspace:project:tech_stack@current` |
| 架构模式变更 | 从方案 A 改为方案 B | `workspace:architecture:pattern@<domain>`，旧节点 → DEPRECATED |
| 约束变更 | 新增显存限制/性能红线 | `workspace:project:constraint@<domain>` |
| 命名规则变更 | 文件命名/代码风格 | `workspace:project:naming_convention@global` |

**触发条件判断**: 当决策被「冻结」为 Architecture Decision Record (ADR) 时。

**禁止同步**: 方案讨论阶段或未确定的技术调研不写入 L2。

### 2.2 规范变化

| 规范类型 | 示例 | L2 写入格式 |
|---------|------|------------|
| Schema 版本变更 | v1.0 → v1.1 | `workspace:project:schema_version@memory` |
| Protocol 变更 | 新协议定义 | `workspace:project:protocol@<name>` |
| API Contract 变更 | 接口签名/行为 | `workspace:project:api_contract@<service>` |

**触发条件判断**: 规范文档进入 Architecture Freeze 状态时。

### 2.3 长期事实变化

| 事实类型 | 示例 | L2 写入格式 |
|---------|------|------------|
| 项目阶段变更 | 设计 → 开发 → 测试 | `workspace:project:phase@global` |
| 里程碑完成 | Phase 1 completed | `workspace:project:milestone@<name>` |
| 性能基线 | 实测指标 | `workspace:project:benchmark@<module>` |

**触发条件判断**: 事实经过至少 2 次独立验证或测量。

### 2.4 不需要 L2 更新的情况

| 情况 | 原因 |
|------|------|
| 单次调试结论 | 不需要跨 session 记忆 |
| 未确认的设计方案 | 不是确定性知识 |
| 临时工作笔记 | 属于 Tier4 Working，自动过期 |
| Agent session 日志 | 属于 Workspace Memory 但非架构知识 |
| 用户日常对话 | 属于 User Memory（预留域） |

---

## 3. L3 更新触发条件

L3 是**短期工作记忆**，需要实时反映当前状态。以下情况必须触发 L3 更新。

### 3.1 阶段完成

| 事件 | L3 更新动作 |
|------|------------|
| 当前 Active Task 完成 | 将状态从「进行中」移到「已完成」 |
| 新阶段开始 | 添加到「当前活动目标」 |
| 多个子任务完成 | 批量更新 L3 清单 |

**触发条件**: Agent 完成 `attempt_completion` 时。

### 3.2 任务完成

| 粒度 | 示例 | L3 更新 |
|------|------|---------|
| 文件级任务 | 实现一个模块 | ✅ 更新清单 |
| 功能级任务 | 实现一个功能 | ✅ 更新清单 |
| 里程碑级 | 完成一个 Phase | ✅ 更新清单 + 可能需要 L2 更新 |

**触发条件**: 任务通过用户确认的 `attempt_completion` 时。

### 3.3 阻塞解除

| 阻塞类型 | L3 更新动作 |
|---------|------------|
| 已知阻塞解除 | 从「已知卡点」移除 |
| 新阻塞出现 | 添加到「已知卡点」 |
| 阻塞降级 | 从「高影响」降为「低影响」 |

**触发条件**: 用户提供解决方案 / Agent 发现 workaround / 外部依赖满足。

### 3.4 下一阶段启动

| 事件 | L3 更新动作 |
|------|------------|
| 用户下达新指令 | 更新「当前活动目标」和「下一步计划」 |
| 当前任务被终止 | 记录终止原因到「已知卡点」 |
| 优先级变更 | 重新排序「下一步计划」 |

---

## 4. Task Completion Checklist

任何任务完成后，Agent 必须在 `attempt_completion` **之前**执行此检查。

### 4.1 检查清单

```
□ 1. 检查 L2 是否需要更新
    □ 是否有架构决策变化？
    □ 是否有规范变化？
    □ 是否有长期事实变化？
    ↓ 需要 → 执行 L2 Update
    ↓ 不需要 → 跳过

□ 2. 检查 L3 是否需要更新
    □ 当前 Active Task 是否完成？
    □ 是否有阻塞解除？
    □ 是否有新阶段启动？
    ↓ 需要 → 执行 L3 Update
    ↓ 不需要 → 跳过

□ 3. 验证同步一致性
    □ L2 中记录的 ACTIVE 决策与当前项目状态一致？
    □ L3 中的进度标记已更新？
    □ 如果 L2 被更新，对应的事件是否在 L3 中可见？

□ 4. 确认完整性
    □ 当前任务的所有架构决策已被记录？
    □ 所有发现的阻塞已登记？
    □ 没有未被记录的确定性事实？
```

### 4.2 快速判定表

| 任务类型 | 是否需要 L2 更新 | 是否需要 L3 更新 |
|---------|:---------------:|:----------------:|
| Bug 修复 | ❌ | ✅ |
| 功能实现 | ⚠️ 仅架构影响时 | ✅ |
| 文档编写 | ✅ 规范变更 | ✅ |
| 测试编写 | ❌ | ✅ |
| 架构评审 | ✅ 决策冻结 | ✅ |
| 性能优化 | ✅ 基线数据 | ✅ |
| 重构 | ✅ 架构变更 | ✅ |
| 调试/分析 | ❌ | ✅ |

---

## 5. Memory Update Workflow

### 5.1 完整流程

```
Task → Review → L2 Update → L3 Update → Report → attempt_completion

Step 1: Task
  └── 执行任务（可能是多轮对话）

Step 2: Review (Task Completion Checklist)
  └── 执行第 4 章的 4 项检查

Step 3: L2 Update (如果需要)
  └── 通过 Governor.write() 写入 cline-memory.json
  └── 格式: WriteRequest(category, key, value, context)
  └── 确保: source_type="SYSTEM_GENERATED" 或 "USER_EXPLICIT"

Step 4: L3 Update
  └── 更新 PROGRESS.md
  └── 板块: Active Task / Constraints / Progress & Blockers / Next Steps

Step 5: Report
  └── 在 attempt_completion 的 result 中汇报同步摘要

Step 6: attempt_completion
  └── 提交结果给用户确认
```

### 5.2 L2 写入操作指南

| 操作 | Governor 调用 | 说明 |
|------|-------------|------|
| 创建新记录 | `write(WriteRequest(category, key, value, context))` | 新事实或新决策 |
| 覆盖旧记录 | `write(WriteRequest(..., same_slot_id))` | 自动触发 SUPERSEDED |
| 强化记录 | `write(WriteRequest(..., same_value))` | 增加 reinforcement_count |

**注意事项**:
- Governor 的 `write()` 自动处理重复检测和冲突仲裁
- 写入后 Governor 返回 MCP 命令列表，Agent 需要执行这些命令
- 如果 MCP 不可用，L2 数据已通过 Governor 持久化到文件，不依赖 MCP 执行

### 5.3 L3 编辑模板

```
## 🎯 当前活动目标 (Active Task)
[当前主要任务描述]

---

## ⚠️ 活跃约束提醒 (Active Constraints)
- [约束 1]
- [约束 2]

---

## 📌 当前进度与卡点 (Current Progress & Blockers)

### ✅ 已完成
- [x] [已完成项 1]
- [x] [已完成项 2]

### 🔄 进行中
- [进行中项]

### ⛔ 已知卡点
- [卡点 1]

---

## 🚀 下一步计划 (Next Steps)
1. [步骤 1]
2. [步骤 2]

---

*最后更新: [时间]*
```

---

## 6. 未来自动化方向

以下自动化方向为未来版本规划，不在 v1.0 规范范围之内。

### 6.1 Git Commit Hook

**方向**: 在 `git commit` 时自动触发 L2 更新。

**设想**:
- `pre-commit` hook 检测 `docs/` 下新增的 Architecture Freeze Document
- `post-commit` hook 解析 commit message，提取 `feat:` / `docs:` 等类型
- 根据 commit 类型自动追加 `workspace:project:milestone@git` 节点

**技术方案**:
- `.git/hooks/pre-commit` 或 `.husky/pre-commit`
- 通过 Python 脚本调用 Governor API

**风险**: 可能产生过多噪声节点，需要阈值控制（仅 major 类型触发）。

### 6.2 Change Detection

**方向**: 自动检测项目中关键文件的变化并同步到 L2。

**检测目标**:

| 文件模式 | 变化含义 | L2 同步动作 |
|---------|---------|------------|
| `docs/*_v*.md` | 新规范版本 | 创建 `workspace:project:schema_version@<name>` |
| `pkia_memory/*.py` | Governor 变更 | 更新 `workspace:architecture:component@governor` |
| `.clinerules` | 宪法变更 | 更新 `workspace:project:constraint@constitution` |
| `cline-memory.json` | L2 自身变化 | 检测一致性（可选） |

**技术方案**:
- `inotify` 或 `watchdog` 监听文件变化
- 变化延迟 30 秒后触发 Governor 写入（防抖）

**风险**: 自动检测可能导致频繁写入。建议仅对 `docs/*_v*.md` 这类低频率文件启用自动检测。

### 6.3 Governor Integration

**方向**: 将 Sync Protocol 内建到 Governor 中。

**设想**:

```
Agent
  │
  ├── Governor.write()          # 当前：写入 L2
  ├── Governor.sync()           # 未来：写入 L2 + 生成 L3 增量
  └── Governor.checklist()      # 未来：输出 Task Completion Checklist
```

**新增 Governor 接口**（未来）:

| 接口 | 功能 |
|------|------|
| `Governor.sync(task_result)` | 接受任务结果，自动判定 L2/L3 更新需求 |
| `Governor.detect_changes(paths)` | 扫描文件变更，推荐 L2 更新 |
| `Governor.summarize_session()` | 生成当前 session 的同步摘要 |

**约束**: Governor 不直接编辑 PROGRESS.md（那是 L3 的职责），但可以输出结构化的同步建议。

---

## 7. 同步优先级矩阵

当多项同步需求同时出现时，按以下优先级排序：

| 优先级 | 同步内容 | 原因 |
|:------:|---------|------|
| P0 | L3 进度更新 | 影响下次任务启动 |
| P1 | L2 架构决策 | 影响长期记忆一致性 |
| P2 | L2 约束变更 | 影响后续开发行为 |
| P3 | L2 里程碑记录 | 项目阶段性总结 |
| P4 | L2 性能基线 | 可延迟到 session 结束 |
| P5 | L2 技术日志 | 非关键确定性事实 |

---

## 8. 附录：同步示例

---

## 9. Memory Sync Audit

### 9.1 审计层定义

Memory Sync Audit 是独立的**审计层**，不属于记忆层（L2）、Governor 或 Persistence。

| 属性 | 值 |
|------|-----|
| 层定位 | Audit Layer |
| 依赖 | 无代码依赖 |
| 存储 | Markdown Receipt 文件 |
| 数据流 | Task → Review → L2 Update → L3 Update → **Receipt Generation** → Completion |

### 9.2 完整流程

```
Task
  ↓
Review (L2 + L3 Checklist)
  ↓
L2 Update (Governor.write() → cline-memory.json)
  ↓
L3 Update (PROGRESS.md)
  ↓
Receipt Generation (docs/memory_sync_receipts/YYYY-MM-DD_task_receipt.md)
  ↓
Completion (attempt_completion with sync summary)
```

### 9.3 Receipt 文件

Receipt 存储在 `docs/memory_sync_receipts/` 目录中，每个任务一个文件。

命名格式: `YYYY-MM-DD_taskname_receipt.md`

Receipt 模板参见 `docs/memory_sync_receipt_template.md`。

### 9.4 审计规则

| 规则 | 说明 |
|------|------|
| 每个任务至多一个 Receipt | 多个子任务可合并 |
| Receipt 必须在 attempt_completion 前生成 | 保证凭证完整性 |
| Receipt 一经生成不得修改 | Append-only |
| 缺失 Receipt = 同步未完成 | 审计断点 |

### 9.5 不审计范围

- Governor 内部算法
- MCP 内部实现
- Git 操作
- Conflict Resolution 结果

完整定义参见 `docs/memory_sync_audit_v1.0.md`。

### 示例 1: 实现一个规范文档

```
Task: 创建 memory_schema_v1.0.md

Review Checklist:
  □ L2 需要更新? ✅ 规范变化（新 Schema 版本）
  □ L3 需要更新? ✅ 任务完成

L2 Update:
  write(category="project", key="schema_version",
        value="v1.0", context="memory_schema")

L3 Update:
  ✅ 已完成 添加 "- [x] 创建 memory_schema_v1.0.md"
  🔄 进行中 更新为当前任务

Report:
  "文档已创建。L2: workspace:project:schema_version@memory_schema = v1.0. L3: 已更新进度清单。"
```

### 示例 2: 实现 Governor 核心功能

```
Task: 实现 Governor.write() 方法

Review Checklist:
  □ L2 需要更新? ✅ 架构决策（Governor 核心流程确认）
  □ L3 需要更新? ✅ 任务完成

L2 Update:
  write(category="architecture", key="component",
        value="Governor_MVP_v0.1", context="governor")
  write(category="project", key="implementation_phase",
        value="Writing decision tree", context="governor")

L3 Update:
  ✅ 已完成 添加 "- [x] 实现 Governor.write() 决策树"
  ⛔ 已知卡点 更新（如有）

Report:
  "Governor.write() 已完成。L2: architecture:component@governor 已记录。L3: 进度已更新。"
```

### 示例 3: Bug 修复

```
Task: 修复 Supersede 后 ACTIVE 状态显示错误

Review Checklist:
  □ L2 需要更新? ❌ Bug fix，无架构变更
  □ L3 需要更新? ✅ 任务完成

L2 Update: 跳过

L3 Update:
  ✅ 已完成 添加 "- [x] 修复 Supersede 后 ACTIVE 状态错误"

Report:
  "Bug 已修复。L2 无更新（非架构变更）。L3 进度已更新。"
```

---

> **文档结束**  
> 本规范定义了 L2 与 L3 之间的同步机制，包括触发条件、检查清单、工作流程和自动化方向。  
> 所有任务完成前必须执行 Task Completion Checklist。