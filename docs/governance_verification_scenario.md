# Governance Verification Scenarios v1.0

> **任务**: Memory Governance Deployment v1.0 — Task 5  
> **日期**: 2026-06-22

---

## Scenario A: 文档编写（规范变更）

**Task**: 创建 `docs/test.md`

**预期 Memory Sync**:

```
L2: updated — project:test_document@global
L3: updated — ✅ 已完成
Receipt: generated
Gate: CLOSED
```

**Expected Result Matrix**:

| Check | Expected | Rationale |
|-------|:--------:|-----------|
| L2 架构决策? | ❌ | 非架构变更 |
| L2 规范变更? | ✅ | 新规范文档 |
| L2 长期事实? | ❌ | 文档不改变项目阶段 |
| L2 系统行为? | ❌ | 非系统变更 |
| L3 任务完成? | ✅ | Task done |
| L3 阶段完成? | ❌ | 单文件不构成阶段 |
| L3 阻塞解除? | ❌ | 无阻塞 |
| L3 新阶段? | ❌ | 不启动新阶段 |
| Receipt 生成? | ✅ | 必须生成 |
| Gate? | CLOSED | 全部通过 |

---

## Scenario B: 架构决策变更

**Task**: 决定从 API A 迁移到 API B

**Expected Memory Sync**:

```
L2: updated — architecture:api_provider@global = API_B
L3: updated — ✅ 已完成
Receipt: generated
Gate: CLOSED
```

**Expected Result Matrix**:

| Check | Expected | Rationale |
|-------|:--------:|-----------|
| L2 架构决策? | ✅ | 架构模式变更 |
| L2 规范变更? | ❌ | 决策未沉淀为规范文档 |
| L2 长期事实? | ✅ | API 选择是长期事实 |
| L2 系统行为? | ❌ | 非 Governor 变更 |
| L3 任务完成? | ✅ | Task done |
| L3 阶段完成? | ❌ | 单决策不构成阶段 |
| L3 阻塞解除? | ❌ | 无阻塞 |
| L3 新阶段? | ❌ | 不启动新阶段 |
| Receipt 生成? | ✅ | 必须生成 |
| Gate? | CLOSED | 全部通过 |

---

## Scenario C: 纯代码重构（无行为变化）

**Task**: 重命名变量，提取函数，不改变逻辑

**Expected Memory Sync**:

```
L2: skipped — 无架构/规范/事实变更
L3: updated — ✅ 已完成
Receipt: generated
Gate: CLOSED
```

**Expected Result Matrix**:

| Check | Expected | Rationale |
|-------|:--------:|-----------|
| L2 架构决策? | ❌ | 重构不改变架构 |
| L2 规范变更? | ❌ | 非规范变更 |
| L2 长期事实? | ❌ | 重构不改变项目阶段 |
| L2 系统行为? | ❌ | 非 Governor 变更 |
| L3 任务完成? | ✅ | Task done |
| L3 阶段完成? | ❌ | 重构不构成阶段 |
| L3 阻塞解除? | ❌ | 无阻塞 |
| L3 新阶段? | ❌ | 不启动新阶段 |
| Receipt 生成? | ✅ | 必须生成 |
| Gate? | CLOSED | L2 skipped, L3 done, Receipt done |

---

## Expected Result Matrix Summary

| Scenario | L2 | L3 | Receipt | Gate |
|----------|:--:|:--:|:-------:|:----:|
| A: 文档编写 | project:test_document@global | ✅ 已完成 | ✅ | CLOSED |
| B: 架构决策 | architecture:api_provider@global | ✅ 已完成 | ✅ | CLOSED |
| C: 纯重构 | skipped | ✅ 已完成 | ✅ | CLOSED |