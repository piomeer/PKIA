# Memory Sync Enforcement v1.0

> **文档状态**: Process Mandate — 必须遵守  
> **版本**: 1.0  
> **更新日期**: 2026-06-22  
> **用途**: 定义 Memory Sync Protocol 的强制执行机制  
> **前置协议**: `memory_sync_protocol_v1.0.md`

---

## 1. Memory Review Checklist

任何任务在调用 `attempt_completion` **之前**，必须逐项执行以下检查。

### 1.1 L2 Review — 长期事实

```
□ 有架构决策变更？
  例如: 技术栈变更、架构模式变更、约束变更
  → 需要 Governor.write() → architecture:*@*

□ 有规范变更？
  例如: Schema 版本变更、Protocol 变更、API Contract 变更
  → 需要 Governor.write() → project:*@*

□ 有长期事实变更？
  例如: 项目阶段、里程碑、性能基线
  → 需要 Governor.write() → project:*@*

□ 有系统行为变更？
  例如: Governor 行为变更、持久化策略变更
  → 需要 Governor.write() → architecture:*@*
```

### 1.2 L3 Review — 进度同步

```
□ 任务完成？
  当前 Active Task 是否完成？
  → 更新 PROGRESS.md「✅ 已完成」板块

□ 阶段完成？
  是否完成了一个 Phase 或里程碑？
  → 更新「🎯 当前活动目标」+「✅ 已完成」

□ 阻塞解除？
  已知卡点是否已解决？
  → 从「⛔ 已知卡点」移除或更新

□ 新阶段启动？
  是否有新的 Active Task？
  → 更新「🎯 当前活动目标」+「🚀 下一步计划」
```

### 1.3 快速判定表

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

## 2. 强制执行规则

### 2.1 规则链

```
Rule 1: 每次 attempt_completion 前必须加载 Checklist
Rule 2: 根据任务类型判定 L2/L3 是否需要更新
Rule 3: 如果需要更新但未执行 → 不得 attempt_completion
Rule 4: L2 Update 必须通过 Governor.write()
Rule 5: L3 Update 必须写入 PROGRESS.md
Rule 6: attempt_completion 的 result 中必须包含同步摘要
```

### 2.2 阻断条件

以下情况下 `attempt_completion` **必须被阻断**：

| 阻断条件 | 检查方式 |
|---------|---------|
| L2 需要更新但未执行 | L2 Review 清单未全部通过 |
| L3 需要更新但未执行 | L3 Review 清单未全部通过 |
| Governor.write() 返回 rejected | 冲突未被解决 |
| PROGRESS.md 未实际更新 | 文件内容与任务状态不一致 |

### 2.3 豁免条件

以下情况下上述检查可以跳过：

| 豁免 | 条件 |
|------|------|
| 纯调试任务 | 用户明确要求「只调试不记录」 |
| 临时分析 | 用户明确要求「临时查看，不需要持久化」 |
| 废弃任务 | 用户明确取消当前任务，不需要记录 |

---

## 3. 违规后果

| 违规 | 后果 |
|------|------|
| L2 漏同步 | 架构决策在 session 结束后不可恢复 |
| L3 漏同步 | PROGRESS.md 漂移，新 Agent 上下文缺失 |
| 连续 3 次漏同步 | Sync Protocol 信誉降级，后续任务每次启动时自动加载 Checklist |

---

## 4. 执行摘要格式

每次 `attempt_completion` 的 `result` 中必须包含以下同步摘要：

```
Memory Sync:
  L2: [updated|skipped] — [slots updated, if any]
  L3: [updated|skipped] — [sections updated]
  Checklist: [PASS|FAIL]
```

### 示例

```
Memory Sync:
  L2: updated — architecture:memory_timestamp_extension@global = Enabled_v1.0
  L3: updated — Active Task, Completed Items
  Checklist: PASS
```

---

> **文档结束**  
> 本规范为强制流程规范。任何 attempt_completion 前必须执行 Memory Review Checklist。  
> 违反规则的 attempt_completion 将被视为流程违规。