# Agent Memory Integration v1.0

> **文档状态**: Operational Specification  
> **版本**: 1.0  
> **更新日期**: 2026-06-22  
> **用途**: 定义 Agent 必须执行的 Memory Governance 流程

---

## 1. Agent 生命周期

```
Task Start
    │
    ▼
┌──────────────────┐
│  Task Execution  │── 执行用户分配的任务
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Memory Review   │── 必须执行（见 §2）
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  L2 Update       │── 如果需要（见 §2.1）
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  L3 Update       │── 始终需要（见 §2.2）
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Receipt Gen     │── 必须生成（见 §3）
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Completion Gate │── Gate 1-3 全部通过？
│       ┌─────┐   │
│       │ YES │   ├── attempt_completion
│       └─────┘   │
│       ┌─────┐   │
│       │ NO  │   ├── ❌ 阻断，返回修复
│       └─────┘   │
└──────────────────┘
```

---

## 2. Mandatory Memory Review

### 2.1 L2 Review — 必须执行的 4 项检查

```
□ 1. 架构决策变更？
  示例: 技术栈变更、架构模式变更、约束变更
  → 需要 → Governor.write() → architecture:*@*
  → 不需要 → 跳过

□ 2. 长期事实变更？
  示例: 项目阶段、里程碑、性能基线
  → 需要 → Governor.write() → project:*@*
  → 不需要 → 跳过

□ 3. 规范变更？
  示例: Schema 版本变更、Protocol 变更
  → 需要 → Governor.write() → project:*@*
  → 不需要 → 跳过

□ 4. 系统行为变更？
  示例: Governor 行为变更、持久化策略变更
  → 需要 → Governor.write() → architecture:*@*
  → 不需要 → 跳过
```

### 2.2 L3 Review — 必须执行的 4 项检查

```
□ 1. 任务是否完成？
  → 更新 PROGRESS.md「✅ 已完成」

□ 2. 阶段是否完成？
  → 更新 PROGRESS.md「🎯 当前活动目标」

□ 3. 阻塞是否解除？
  → 更新 PROGRESS.md「⛔ 已知卡点」

□ 4. 是否有新阶段启动？
  → 更新 PROGRESS.md「🚀 下一步计划」
```

### 2.3 快速判定表

| 任务类型 | L2 同步 | L3 同步 |
|---------|:-------:|:-------:|
| Bug 修复 | ❌ | ✅ |
| 功能实现 | ⚠️ 仅架构影响时 | ✅ |
| 文档编写 | ✅ 规范变更 | ✅ |
| 测试编写 | ❌ | ✅ |
| 架构评审 | ✅ 决策冻结 | ✅ |
| 性能优化 | ✅ 基线数据 | ✅ |
| 重构 | ✅ 架构变更 | ✅ |
| 流程定义 | ✅ 系统行为 | ✅ |
| 配置变更 | ✅ 长期事实 | ✅ |

---

## 3. Receipt Generation

每次同步后必须在 `docs/memory_sync_receipts/` 生成 Receipt。

**文件名格式**: `YYYY-MM-DD_taskname_receipt.md`

**必须包含**:
- Timestamp
- Task Name
- L2 Updates（slot_id + value + action）
- L3 Updates（section + change）
- Checklist（4 项通过/跳过）
- Verification（Governor Write / File Persistence / PROGRESS Update / MCP Sync）
- Gate Summary（OPEN / CLOSED）
- Result（PASS / FAIL）

模板参见 `docs/memory_sync_receipt_template.md`。

---

## 4. Completion Gate

attempt_completion **之前**必须确认：

```
Gate 1: L2 Review Complete    → ✅ or ❌
Gate 2: L3 Review Complete    → ✅ or ❌
Gate 3: Receipt Generated     → ✅ or ❌

Gate Status: CLOSED → attempt_completion 允许
Gate Status: OPEN   → ❌ 阻断
```

**attempt_completion 的 result 中必须包含**:
```
Memory Sync:
  L2: [updated|skipped] — [slots]
  L3: [updated|skipped] — [sections]
  Receipt: [generated|skipped]
  Gate: [CLOSED|OPEN]