# PKIA L2 Memory Schema — 可落地规范 v1.0

> **文档状态**: Architecture Freeze Document  
> **前置依赖**: [memory_ontology_v1.1.md](./memory_ontology_v1.1.md)  
> **目标**: 将 Ontology 转换为可落地的 MCP Memory Schema，为 Governor MVP 提供实现依据  
> **版本**: 1.0  
> **更新日期**: 2026-06-20  
> **规范约束**: 本文档定义所有 MCP 实体/关系/检索/治理的精确规则，不涉及任何编程语言的具体实现。

---

## 目录

1. [Ontology → MCP Mapping](#1-ontology--mcp-mapping)
2. [Slot Schema](#2-slot-schema)
3. [Version Schema](#3-version-schema)
4. [Retrieval Schema](#4-retrieval-schema)
5. [Governor Rule Set](#5-governor-rule-set)
6. [Migration Strategy](#6-migration-strategy)

---

## 1. Ontology → MCP Mapping

本节定义 Ontology 中的抽象概念如何映射到 MCP Memory Server 的具体存储原语。

### 1.1 映射总表

| Ontology 概念 | MCP 原语 | 映射规则 |
|---------------|----------|---------|
| `Memory_Node` | Entity | 每个 Memory_Node 映射为一个 MCP Entity。entity name = `node_id`（格式 `mem_<uuid>`）。 |
| Memory_Node 字段 | Entity.observations | 每个字段映射为一条 observation。格式: `field_name: field_value`。 |
| Slot 标识 | 无直接对应 | 由 category + key + context 三个 observation 组合推导。无独立 MCP 实体。 |
| 版本链 | 无直接对应 | 由 SUPERSEDED_BY 关系串联的 Entity 集合构成隐式版本链。 |
| `HAS_MEMORY` | Relation | MCP Relation。`from` = `PKIA_Project`，`to` = `mem_<uuid>`。 |
| `SUPERSEDED_BY` | Relation | MCP Relation。`from` = 新节点，`to` = 旧节点。 |
| `HAS_DECISION` | Relation | MCP Relation。`from` = 决策结果，`to` = 决策依据。 |
| `DERIVED_FROM` | Relation | MCP Relation。`from` = 推断节点，`to` = 来源节点。 |
| `CONTRADICTS` | Relation | MCP Relation。`from` = 新证据，`to` = 旧证据。 |
| PKIA_Project | Entity | 顶层容器实体。entity name = `PKIA_Project`。是所有记忆的挂载点。 |
| Tier 分类 | 无直接对应 | 由 `category` observation 的值决定（identity / preference / project / working）。 |

### 1.2 Memory_Node → MCP Entity 编码规则

每个 Memory_Node 在 MCP 中编码为一个 Entity，其 observations 数组包含所有字段的键值对。

**编码格式**:

```
Entity {
  name: "mem_<uuid4>",
  entityType: "MemoryNode",
  observations: [
    "node_id: mem_<uuid4>",
    "category: <identity|preference|project|working>",
    "key: <snake_case_key>",
    "value: <string_value>",
    "context: <context_string>",
    "status: <ACTIVE|DRAFT|DEPRECATED|ARCHIVED>",
    "confidence: <float>",
    "source_type: <USER_EXPLICIT|AGENT_INFERRED|SYSTEM_GENERATED>",
    "created_at: <ISO_8601_UTC>",
    "updated_at: <ISO_8601_UTC>",
    "expires_at: <ISO_8601_UTC|null>",
    "version: <int>",
    "reinforcement_count: <int>"
  ]
}
```

**约束**:
- observations 中的 `node_id` 必须与 Entity 的 `name` 一致。
- 所有字段必须以 observation 形式存在，不允许遗漏必需字段。
- `expires_at` 为 `null` 时 observation 值为空字符串或省略（根据后续实现选择）。

### 1.3 PKIA_Project → MCP Entity 编码

```
Entity {
  name: "PKIA_Project",
  entityType: "Project",
  observations: [
    "name: Personal Knowledge Intelligence Agent",
    "status: active"
  ]
}
```

`PKIA_Project` 是一个**常驻实体**，在整个系统生命周期内始终存在。它是所有 `HAS_MEMORY` 关系的源端。

### 1.4 关系编码示例

```
# HAS_MEMORY: 将记忆挂载到 PKIA_Project
Relation {
  from: "PKIA_Project",
  to: "mem_a1b2c3d4",
  relationType: "HAS_MEMORY"
}

# SUPERSEDED_BY: 版本替换
Relation {
  from: "mem_v3",
  to: "mem_v2",
  relationType: "SUPERSEDED_BY"
}

# DERIVED_FROM: 推断来源
Relation {
  from: "mem_draft_001",
  to: "mem_conversation_log_042",
  relationType: "DERIVED_FROM"
}
```

### 1.5 映射规则约束

| 约束 | 说明 |
|------|------|
| entityType 统一 | 所有 Memory_Node 的 entityType 必须为 `"MemoryNode"`。不允许其他类型。 |
| 命名空间隔离 | Memory_Node 的 name 必须以 `mem_` 前缀开头。非记忆实体不得使用此前缀。 |
| PKIA_Project 单例 | `PKIA_Project` 实体在整个图谱中只能存在一个。重复创建将导致关系断裂。 |
| observation 稳定性 | 已写入的 observation 不可删除或修改（Append-only）。强化操作仅更新 `reinforcement_count` 和 `updated_at` 两条 observation。 |
| 关系单向性 | 所有关系均为有向。逆向查询由 Memory Governor 在检索层处理，不由 MCP 原生支持。 |

---

## 2. Slot Schema

Slot 是冲突检测和版本管理的核心维度。本节定义 Slot 的精确构成、查询方式和约束。

### 2.1 Slot 标识符

Slot 由三个维度组合而成：

```
slot_id = "{category}:{key}@{context}"
```

**维度定义**:

| 维度 | 来源 | 类型 | 说明 |
|------|------|------|------|
| `category` | Memory_Node.category | string | 四个固定值之一: identity / preference / project / working |
| `key` | Memory_Node.key | string | 自由定义，但必须使用 snake_case。在同一 category 内唯一。 |
| `context` | Memory_Node.context | string | 上下文限定符。空字符串等价于 "global"。大小写敏感。 |

### 2.2 Slot 字典

Slot 字典是 Memory Governor 维护的**逻辑索引**，用于快速查询 slot 状态。字典不由 MCP 原生存储，而是由 Governor 在运行时推导。

**字典结构（逻辑）**:

```json
{
  "slots": {
    "identity:research_field@global": {
      "active_node_id": "mem_a1b2c3d4",
      "version_count": 3,
      "last_updated": "2026-06-15T09:00:00Z"
    },
    "preference:response_language@global": {
      "active_node_id": "mem_x9y8z7w6",
      "version_count": 2,
      "last_updated": "2026-06-10T14:00:00Z"
    },
    "project:project_phase@PKIA_Project": {
      "active_node_id": "mem_p1p2p3p4",
      "version_count": 5,
      "last_updated": "2026-06-20T16:00:00Z"
    }
  }
}
```

### 2.3 Slot 查询操作

Governor 通过 MCP 的 `search_nodes` 工具来推导 slot 状态。查询模式如下：

**查询指定 slot 的所有节点**:

```
搜索条件:
  - observations 包含 "category: <target_category>"
  - observations 包含 "key: <target_key>"
  - observations 包含 "context: <target_context>"

等价于: search_nodes("category:<target_category> key:<target_key> context:<target_context>")
```

**查询指定 slot 的 ACTIVE 节点**:

```
搜索条件:
  - observations 包含 "category: <target_category>"
  - observations 包含 "key: <target_key>"
  - observations 包含 "context: <target_context>"
  - observations 包含 "status: ACTIVE"

返回: 至多一个节点。零个表示该 slot 无 ACTIVE 记录。
```

### 2.4 Slot 约束规则

| 规则 | 描述 | 违反后果 |
|------|------|---------|
| **唯一 ACTIVE 约束** | 同一 slot_id 下最多只能有一个 status=ACTIVE 的节点 | 重复 ACTIVE 视为数据不一致，Governor 应触发修复流程 |
| **版本号单调递增** | 同一 slot_id 下的 version 值必须严格递增 | 新节点的 version = max(现有 versions) + 1 |
| **slot 不可变** | slot_id 一旦确定，不可更改。如需变更 context，视为新 slot | — |
| **context 大小写敏感** | `@global` 与 `@Global` 是两个不同的 slot | 实践中强制小写 |

### 2.5 保留的 Key 命名空间

以下 key 名称被系统保留，Agent 层不应直接使用（由 Governor 内部管理）：

| 保留 Key | 用途 | 所属 Tier |
|----------|------|-----------|
| `_slot_metadata` | 存储 slot 级别的元数据（版本计数、创建时间戳） | system |
| `_governor_state` | 存储 Governor 内部状态（扫描时间戳、修复记录） | system |
| `_migration_log` | 存储数据迁移操作的审计记录 | system |

Agent 层使用的 key 命名空间为 `[a-z][a-z0-9_]*`，不得以 `_` 开头。

---

## 3. Version Schema

版本机制是 Append-only 架构中追踪记忆变更的核心设施。本节定义版本号的计算规则、版本链的拓扑结构和版本间的关系约束。

### 3.1 版本号规则

**版本号生成**:

```
version = max_version_of_slot + 1
```

- 初始节点的 version = 1。
- 同一 slot 的第一个节点即为 version = 1。
- 版本号不允许跳跃（例如从 v1 直接到 v3）。
- 版本号不允许重复（同一 slot 内）。

**查询版本号的方式**:

Governor 通过 `search_nodes` 查询指定 slot 的所有节点，提取 `version` observation 的最大值。

```
# 逻辑查询
nodes = search_nodes("category:preference key:response_language context:global")
max_version = max(nodes.version)
new_version = max_version + 1
```

### 3.2 版本链拓扑

版本链由 `SUPERSEDED_BY` 关系串联，形成从最新版本到最初版本的单向链表。

**版本链规则**:

```
规则的版本链:
  mem_v3 (ACTIVE, v3) ── SUPERSEDED_BY ──► mem_v2 (DEPRECATED, v2)
  mem_v2 (DEPRECATED, v2) ── SUPERSEDED_BY ──► mem_v1 (DEPRECATED, v1)

违反规则的版本链:
  ❌ 分叉: mem_v3 ── SUPERSEDED_BY ──► mem_v2a  ← 不允许两个 v2 同时存在
              └── SUPERSEDED_BY ──► mem_v2b

  ❌ 循环: mem_v3 ── SUPERSEDED_BY ──► mem_v2 ── SUPERSEDED_BY ──► mem_v1
              ▲                                              │
              └────────────────── 不允许循环关系

  ❌ 断层: mem_v3 (ACTIVE) ── SUPERSEDED_BY ──► mem_v1 (DEPRECATED)
              ↑ 缺少 v2，违反单调递增约束
```

### 3.3 版本链长度阈值

| Tier | 版本链最大长度 | 超限处理 |
|------|--------------|---------|
| Tier1 Identity | 10 | 超过 10 个版本后触发归档建议，通知用户清理 |
| Tier2 Preference | 20 | 超过 20 个版本后触发归档建议 |
| Tier3 Project | 50 | 超过 50 个版本后自动压缩（保留最近 10 个版本） |
| Tier4 Working | 100 | 超过 100 个版本后自动剪枝（删除最旧版本） |

### 3.4 版本链完整性验证

Governor 在每次写入操作后执行以下验证：

```
验证函数: validate_version_chain(slot_id)

输入: slot_id = "category:key@context"

步骤:
  1. 查询该 slot 的所有节点，按 version 升序排列
  2. 验证 version 序列连续无跳跃
  3. 验证 SUPERSEDED_BY 关系形成单向链（无分叉、无循环）
  4. 验证只有 version 最大的节点 status = ACTIVE
  5. 验证所有其他节点 status = DEPRECATED

输出: valid / invalid + 违规详情
```

---

## 4. Retrieval Schema

本节定义三个检索接口在 MCP 原语层的精确映射。每个接口给出 MCP 操作序列，而非实现代码。

### 4.1 get_active_memory

**Ontology 定义**: [Ontology 9.1 节](./memory_ontology_v1.1.md#91-get_active_memory)

**MCP 操作序列**:

```
输入: category="preference", key="response_language", context="global", confidence_threshold=0.5

Step 1: 搜索目标 slot 的 ACTIVE 节点
  └── MCP 调用: search_nodes(query="category:preference key:response_language context:global status:ACTIVE")
  └── 预期返回: 至多 1 个 Entity
  └── 如果返回 0 个 → 返回 null (no memory found)

Step 2: 置信度过滤
  └── 从返回的 Entity.observations 中提取 confidence 值
  └── 如果 confidence < 0.5 → 返回 null

Step 3: 检索版本链（可选）
  └── MCP 调用: open_nodes(names=[node_id])
  └── 递归查询: 沿 SUPERSEDED_BY 关系追溯
      └── MCP 调用: 通过 search_nodes 或关系推导找到旧版本
  └── 返回: [active_node, ...deprecated_nodes] 按 version 降序排列

输出: { node: Memory_Node, chain: Memory_Node[] }
```

**context 回退规则**:

```
如果精确 context 匹配未命中:
  1. 重新搜索 context=""（全局）：
     └── search_nodes(query="category:preference key:response_language context: status:ACTIVE")
  2. 如果仍无结果，返回 null
  3. 如果命中，使用全局 context 的 ACTIVE 节点作为返回值
```

**返回格式（逻辑）**:

```json
{
  "found": true,
  "node": {
    "node_id": "mem_001",
    "category": "preference",
    "key": "response_language",
    "value": "zh-CN",
    "context": "global",
    "status": "ACTIVE",
    "confidence": 1.0,
    "source_type": "USER_EXPLICIT",
    "version": 2,
    "reinforcement_count": 3
  },
  "chain": [
    {"version": 2, "node_id": "mem_001", "status": "ACTIVE"},
    {"version": 1, "node_id": "mem_000", "status": "DEPRECATED"}
  ]
}
```

### 4.2 get_context_memory

**Ontology 定义**: [Ontology 9.2 节](./memory_ontology_v1.1.md#92-get_context_memory)

**MCP 操作序列**:

```
输入: context="PKIA_Project", tier_filter=["project"], confidence_threshold=0.0

Step 1: 搜索指定 context 的所有 ACTIVE 节点
  └── MCP 调用: search_nodes(query="context:PKIA_Project status:ACTIVE")
  └── 预期返回: N 个 Entity

Step 2: 按 tier_filter 过滤（可选）
  └── 如果指定了 tier_filter：
      对每个返回的 Entity:
        提取 category observation
        如果 category ∉ tier_filter → 从结果集中移除

Step 3: 按 confidence_threshold 过滤（可选）
  └── 如果 threshold > 0.0：
      对每个返回的 Entity:
        提取 confidence observation
        如果 confidence < threshold → 从结果集中移除

Step 4: 排序
  └── 按 Tier 优先级排序: identity > preference > project > working
  └── 同一 Tier 内按 reinforcement_count 降序排列

输出: Memory_Node[] 按优先级排序
```

**排序优先级矩阵**:

| 排序维度 | 权重 | 说明 |
|----------|------|------|
| Tier 优先级 | 最高 | Identity=4, Preference=3, Project=2, Working=1 |
| reinforcement_count | 中 | 越大越靠前 |
| created_at | 低 | 较新的排在前面 |

### 4.3 trace_memory

**Ontology 定义**: [Ontology 9.3 节](./memory_ontology_v1.1.md#93-trace_memory)

**MCP 操作序列**:

```
输入: node_id="mem_v3", direction="backward", max_depth=10

Step 1: 获取起始节点
  └── MCP 调用: open_nodes(names=["mem_v3"])
  └── 提取起始节点的所有字段

Step 2: 沿 SUPERSEDED_BY 追溯（backward 方向）
  └── 对当前节点，查询所有以当前节点为 from 的 SUPERSEDED_BY 关系
  └── MCP 调用: 无直接「查询关系」工具，需通过已知目标推导
  └── 替代方案: 通过 slot_id 查询所有节点，按 version 降序遍历
  └── 递归执行，直到达到 max_depth 或无法继续

Step 3: 收集 DERIVED_FROM 关系
  └── 对路径上的每个节点，查询 DERIVED_FROM 关系的目标
  └── 将来源节点作为附加信息附加到对应的 TraceNode

输出: TraceNode 数组

TraceNode 逻辑结构:
[
  {
    "node": { "node_id": "mem_v3", "version": 3, "status": "ACTIVE", ... },
    "relationships": [
      { "type": "SUPERSEDED_BY", "target_id": "mem_v2" }
    ]
  },
  {
    "node": { "node_id": "mem_v2", "version": 2, "status": "DEPRECATED", ... },
    "relationships": [
      { "type": "SUPERSEDED_BY", "target_id": "mem_v1" },
      { "type": "DERIVED_FROM", "target_id": "mem_conv_001" }
    ]
  },
  {
    "node": { "node_id": "mem_v1", "version": 1, "status": "DEPRECATED", ... },
    "relationships": []
  }
]
```

**forward 方向追溯**:

```
输入: direction="forward"

Step 1: 获取起始节点（同上）
Step 2: 查询 slot_id，获取所有 version > 起始节点.version 的节点
Step 3: 沿 SUPERSEDED_BY 的反向关系向新版本追溯
Step 4: 按 version 升序排列输出
```

### 4.4 检索接口的错误处理

| 错误场景 | 处理方式 | 返回值 |
|----------|---------|--------|
| slot 不存在（无任何节点） | 返回空 | `{ found: false, node: null }` |
| slot 存在但无 ACTIVE（全是 DEPRECATED） | 返回空，但附加 `deprecated_count` 提示 | `{ found: false, node: null, deprecated_count: 3 }` |
| confidence 低于阈值 | 返回空，附加 `confidence` 和 `threshold` | `{ found: false, node: null, confidence: 0.3, threshold: 0.5 }` |
| trace_memory 节点不存在 | 返回空 | `{ timeline: [], error: "node_id not found" }` |

---

## 5. Governor Rule Set

Memory Governor 是 L2 层的治理引擎。本节以规则表的形式定义 Governor 的所有行为规则。每条规则包含触发条件、动作和副作用。

### 5.1 写入规则

| 规则 ID | 规则名称 | 触发条件 | 操作 | 副作用 |
|---------|---------|---------|------|--------|
| W01 | 重复检测 | Agent 请求写入 `(category, key, context, value)` | 查询目标 slot 的 ACTIVE 节点，比较 value 是否完全一致 | 如果一致 → 跳转到 W02；如果不一致 → 跳转到 W03 |
| W02 | 强化更新 | W01 检测到 value 一致 | 1. 递增 `reinforcement_count`<br>2. 更新 `updated_at`<br>3. 更新 `confidence` | 如果 confidence ≥ 0.9 且 status=DRAFT → 自动提升为 ACTIVE |
| W03 | Slot 冲突检测 | W01 检测到 value 不一致或 slot 无 ACTIVE | 查询目标 slot 的 ACTIVE 节点是否存在 | 如果存在 → 跳转到 W04；如果不存在 → 跳转到 W05 |
| W04 | 冲突解决 | W03 检测到 slot 已有 ACTIVE 节点 | 1. 旧节点 status → DEPRECATED<br>2. 创建新节点 status=ACTIVE<br>3. 建立 SUPERSEDED_BY 关系 | 版本号递增，旧节点退出活跃集 |
| W05 | 直接创建 | W03 检测到 slot 无 ACTIVE 节点 | 1. 创建新节点 status=ACTIVE<br>2. version=1 或 max_version+1 | 建立 HAS_MEMORY 关系 |

### 5.2 生命周期规则

| 规则 ID | 规则名称 | 触发条件 | 操作 | 执行频率 |
|---------|---------|---------|------|---------|
| L01 | 过期扫描 | 定时任务 | 查询所有 `expires_at` 非空且 `status=ACTIVE` 的节点，比较 `expires_at < now()` | 每小时 |
| L01a | 过期处理 | L01 命中 | 将匹配节点的 status → ARCHIVED | L01 触发时 |
| L02 | DRAFT 超时扫描 | 定时任务 | 查询所有 `status=DRAFT` 且 `created_at < now()-7d` 的节点 | 每天 |
| L02a | DRAFT 超时处理 | L02 命中 | 将匹配节点的 status → DEPRECATED | L02 触发时 |
| L03 | Tier4 清理 | 定时任务 | 查询所有 `category=working` 且 `expires_at < now()` 的节点 | 每小时 |
| L03a | Tier4 清理处理 | L03 命中 | 将匹配节点的 status → ARCHIVED | L03 触发时 |
| L04 | 版本链验证 | 每次写入操作后 | 对受影响的 slot 执行版本链完整性验证 | 写入触发 |

### 5.3 冲突规则

| 规则 ID | 规则名称 | 优先级 | 描述 |
|---------|---------|--------|------|
| C01 | 用户显式优先 | 最高 | `source_type=USER_EXPLICIT` 的节点优先于 `AGENT_INFERRED`。如果冲突双方一方为 USER_EXPLICIT，无条件采用 USER_EXPLICIT。 |
| C02 | 置信度决胜 | 高 | 如果双方同为 USER_EXPLICIT 或同为 AGENT_INFERRED，confidence 高的节点胜出。 |
| C03 | 时间优先 | 中 | 如果双方 confidence 相同，`created_at` 更新的节点胜出（新知识覆盖旧知识）。 |
| C04 | 强化计数辅助 | 低 | 如果以上全部相同，`reinforcement_count` 较高的节点胜出。 |

**冲突仲裁逻辑（非代码，逻辑描述）**:

```
仲裁写入 (new_node, existing_active_nodes):
  对于 existing_active_nodes 中的每个 existing_node:
    如果 existing_node.source_type == "USER_EXPLICIT"
      且 new_node.source_type == "AGENT_INFERRED":
        拒绝 new_node，返回 existing_node 仍为 ACTIVE
    如果 new_node.source_type == "USER_EXPLICIT"
      且 existing_node.source_type == "AGENT_INFERRED":
        替换 existing_node，new_node 成为 ACTIVE
    如果 source_type 相同:
      比较 confidence，高者胜出
      如果 confidence 相同，比较 created_at，新者胜出
      如果全部相同，比较 reinforcement_count，高者胜出
```

### 5.4 数据一致性规则

| 规则 ID | 规则名称 | 检查条件 | 修复动作 |
|---------|---------|---------|---------|
| D01 | 孤儿节点检测 | 存在 `entityType=MemoryNode` 但无 `HAS_MEMORY` 关系指向它 | 自动建立 HAS_MEMORY 关系（从 PKIA_Project 指向该节点） |
| D02 | 多 ACTIVE 检测 | 同一 slot 存在多个 status=ACTIVE 的节点 | 保留 version 最高的为 ACTIVE，其余 → DEPRECATED，建立 SUPERSEDED_BY 链 |
| D03 | 断层版本检测 | slot 内 version 序列不连续 | 标记为数据不一致，记录到 `_migration_log`，不自动修复 |
| D04 | 关系孤岛检测 | 存在 SUPERSEDED_BY 指向不存在的 node_id | 删除该无效关系，记录到 `_migration_log` |

### 5.5 规则执行顺序

每次写入请求的完整规则执行流水线：

```
1. W01: 重复检测
   ├── 命中 → W02: 强化更新 → 完成
   └── 未命中 → 2

2. W03: Slot 冲突检测
   ├── 有 ACTIVE → 3
   └── 无 ACTIVE → W05: 直接创建 → 5

3. C01-C04: 冲突仲裁
   ├── 新节点胜出 → 4
   └── 旧节点保留 → 拒绝写入，返回当前 ACTIVE 节点信息

4. W04: 冲突解决
   ├── 旧节点 → DEPRECATED
   ├── 创建新节点 → ACTIVE
   └── 建立 SUPERSEDED_BY

5. L04: 版本链验证
   ├── 通过 → 返回成功
   └── 不通过 → D02/D03: 修复或标记不一致
```

---

## 6. Migration Strategy

本节定义从当前图谱状态迁移到 PKIA L2 Schema 的策略。迁移仅涉及图谱数据的结构调整，不涉及代码实现。

### 6.1 当前状态分析

截至 2026-06-20，MCP Memory Server 中的图谱包含以下与 PKIA 相关的实体：

| 实体 | 类型 | 是否符合 Schema v1.0 | 需迁移 |
|------|------|---------------------|--------|
| `PKIA_Project` | Project | 部分符合 | 需要增加 status observation |
| `Dify_Platform` | Platform | 无关 | 保持不变 |
| `Dify_Backend` | Component | 无关 | 保持不变 |
| `Dify_Frontend` | Component | 无关 | 保持不变 |
| `Three_Tier_Memory_System` | Architecture | 无关 | 保持不变 |
| `Memory_Bouncer_Script` | Script | 无关 | 保持不变 |

**结论**: 当前图谱中尚无 Memory_Node 实体。迁移的主要工作是**创建首批 Memory_Node**，而非改造现有实体。

### 6.2 迁移阶段

#### Phase 0: 预检查（人工确认）

在开始迁移前，确认以下前提条件：

- [ ] MCP Memory Server 已指向 `pkia-memory.json`（而非 `mukg-memory.json`）
- [ ] `PKIA_Project` 实体在图谱中存在
- [ ] 所有非 PKIA 的孤立实体（MuKG 相关）已被清理或标记

#### Phase 1: 创建 PKIA 身份记忆（Identity Bootstrapping）

创建首批 Tier1 Identity 记忆节点，建立初始图谱拓扑。

**操作清单**:

```
1. 创建实体 (entityType=MemoryNode):
   node_id: mem_init_identity_001
   observations:
     - "node_id: mem_init_identity_001"
     - "category: identity"
     - "key: research_field"
     - "value: 知识图谱 · 自然语言处理"
     - "context: global"
     - "status: ACTIVE"
     - "confidence: 1.0"
     - "source_type: USER_EXPLICIT"
     - "created_at: 2026-06-20T00:00:00Z"
     - "updated_at: 2026-06-20T00:00:00Z"
     - "expires_at: "
     - "version: 1"
     - "reinforcement_count: 1"

2. 建立关系:
   PKIA_Project ── HAS_MEMORY ──► mem_init_identity_001
```

#### Phase 2: 创建 PKIA 偏好记忆（Preference Bootstrapping）

**操作清单**:

```
1. 创建 preference:response_language@global:
   node_id: mem_init_pref_001
   category: preference
   key: response_language
   value: "zh-CN"
   context: global
   status: ACTIVE
   confidence: 1.0
   source_type: USER_EXPLICIT
   ...

2. 创建 preference:explanation_style@global:
   node_id: mem_init_pref_002
   category: preference
   key: explanation_style
   value: "detail_first"
   context: global
   status: DRAFT
   confidence: 0.7
   source_type: AGENT_INFERRED
   ...

3. 建立 HAS_MEMORY 关系:
   PKIA_Project ── HAS_MEMORY ──► mem_init_pref_001
   PKIA_Project ── HAS_MEMORY ──► mem_init_pref_002
```

#### Phase 3: 创建 PKIA 项目记忆（Project Bootstrapping）

**操作清单**:

```
1. 创建 project:project_phase@PKIA_Project:
   node_id: mem_init_proj_001
   category: project
   key: project_phase
   value: "architecture_design"
   context: "PKIA_Project"
   status: ACTIVE
   confidence: 1.0
   source_type: USER_EXPLICIT
   ...

2. 创建 project:tech_stack@PKIA_Project:
   node_id: mem_init_proj_002
   category: project
   key: tech_stack
   value: "Dify · Python · Next.js · MCP"
   context: "PKIA_Project"
   status: ACTIVE
   confidence: 1.0
   source_type: USER_EXPLICIT
   ...

3. 建立 HAS_MEMORY 关系:
   PKIA_Project ── HAS_MEMORY ──► mem_init_proj_001
   PKIA_Project ── HAS_MEMORY ──► mem_init_proj_002
```

### 6.3 迁移验证清单

迁移完成后，通过以下查询验证迁移的正确性：

| 验证项 | 预期结果 | MCP 查询 |
|--------|---------|---------|
| PKIA_Project 存在 | 返回 1 个 Entity | `open_nodes(names=["PKIA_Project"])` |
| Memory_Node 数量 ≥ 5 | 至少 5 个 MemoryNode entity | 遍历所有 MemoryNode 实体 |
| HAS_MEMORY 关系数量 ≥ 5 | 至少 5 条从 PKIA_Project 出发的关系 | 查询所有 HAS_MEMORY 关系 |
| slot 唯一性 | 无重复 slot + ACTIVE 组合 | 按 category+key+context 分组统计 |
| 版本链完整性 | 所有 slot 的版本链无断层 | 依次验证每个 slot |

---

> **文档结束**  
> 本规范为 PKIA L2 Memory Schema v1.0，是 [memory_ontology_v1.1.md](./memory_ontology_v1.1.md) 的可落地映射规范。  
> Governor MVP 的实现必须严格遵循此文档中定义的 MCP 操作序列、规则表和迁移策略。  
> 如需偏离，必须经过架构评审并更新本文档版本号。