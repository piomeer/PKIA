# Memory Governance Rule Block — 可直接插入

> **用途**: 插入 `.clinerules` 或其他 Agent 入口文件  
> **行数**: ~120 行  
> **版本**: v1.0

---

将以下内容完整复制到 `.clinerules` 文件中：

```
## 7. Memory Governance (强制流程)

### 7.1 Agent 生命周期

每次任务必须按以下顺序执行:

   Task → Memory Review → L2 Update(如需) → L3 Update → Receipt → Completion Gate → attempt_completion

### 7.2 任务结束前强制检查清单

#### L2 Review (长期记忆检查)

   □ 架构决策变更?(技术栈/架构模式/约束)
     → 需要: Governor.write() → architecture:*@*
   □ 长期事实变更?(项目阶段/里程碑/基线)
     → 需要: Governor.write() → project:*@*
   □ 规范变更?(Schema/Protocol/API)
     → 需要: Governor.write() → project:*@*
   □ 系统行为变更?(Governor/持久化)
     → 需要: Governor.write() → architecture:*@*

#### L3 Review (进度同步检查)

   □ 任务完成? → 更新 PROGRESS.md「✅ 已完成」
   □ 阶段完成? → 更新 PROGRESS.md「🎯 当前活动目标」
   □ 阻塞解除? → 更新 PROGRESS.md「⛔ 已知卡点」
   □ 新阶段启动? → 更新 PROGRESS.md「🚀 下一步计划」

### 7.3 快速判定表

   任务类型       L2同步  L3同步
   ───────────    ─────  ─────
   Bug修复        ❌     ✅
   功能实现        ⚠️     ✅
   文档编写        ✅     ✅
   测试编写        ❌     ✅
   架构评审        ✅     ✅
   性能优化        ✅     ✅
   重构            ✅     ✅
   流程定义        ✅     ✅
   配置变更        ✅     ✅

### 7.4 Completion Gate

   attempt_completion 前必须确认:

   Gate 1: L2 Review Complete    ✅/❌
   Gate 2: L3 Review Complete    ✅/❌
   Gate 3: Receipt Generated     ✅/❌

   全部通过 → 允许 attempt_completion
   任一未通过 → 阻断,返回修复

### 7.5 attempt_completion result 格式

   每次 attempt_completion 的 result 必须包含:

   Memory Sync:
     L2: [updated|skipped] — [slots]
     L3: [updated|skipped] — [sections]
     Receipt: [generated|skipped]
     Gate: [CLOSED|OPEN]

### 7.6 Memory Operations

   L2 写入: Governor.write() → 自动持久化到 cline-memory.json
   L2 查询: Governor.get_active(slot_id)
   L3 更新: 直接编辑 PROGRESS.md
   MCP 同步: 执行 Governor.write() 返回的 commands

### 7.7 参考文档

   - docs/agent_memory_integration_v1.0.md (完整流程)
   - docs/memory_sync_receipt_template.md (Receipt模板)
   - docs/memory_sync_protocol_v1.0.md (同步协议)
   - docs/memory_governance_freeze_v1.0.md (冻结范围)