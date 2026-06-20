# PKIA MCP Memory Server 能力审计报告

> **文档状态**: Capability Audit  
> **审计目标**: 验证 MCP Memory Server 是否满足 memory_schema_v1.0.md 的落地需求  
> **审计日期**: 2026-06-20  
> **审计方法**: 通过 MCP 工具真实调用，逐项验证能力  
> **审计结论**: 底部给出 Governor MVP 调整建议

---

## 1. 当前 MCP Memory Server 类型

| 属性 | 值 |
|------|-----|
| 服务器名称 | `memory` |
| 启动命令 | `npx -y @modelcontextprotocol/server-memory /home/mahe/muKG_LB/mukg-memory.json` |
| 存储文件 | `/home/mahe/muKG_LB/mukg-memory.json` |
| 底层格式 | JSON Lines（每行一个 JSON 对象，无外层 `[]` 或 `{}`） |
| 是否指向 PKIA | **否** — 仍指向 MuKG 项目的 `mukg-memory.json`，非 `pkia-memory.json` |

**影响**: Schema v1.0 中引用的 `pkia-memory.json` 尚未创建。当前所有操作均在 MuKG 的存储文件上执行。迁移前需要先切换存储目标。

---

## 2. 支持的 Tool 列表

通过 MCP 协议暴露的可用工具如下：

| 工具名称 | 功能 | 是否可用于 Governor |
|---------|------|--------------------|
| `create_entities` | 批量创建实体 | ✅ 可用于创建 Memory_Node |
| `create_relations` | 批量创建关系 | ✅ 可用于创建 HAS_MEMORY / SUPERSEDED_BY 等 |
| `add_observations` | 向已有实体追加 observation | ✅ 可用于强化更新（更新 reinforcement_count / updated_at） |
| `delete_entities` | 批量删除实体 | ⚠️ 权限保留但不应在 Append-only 架构中使用 |
| `delete_relations` | 批量删除关系 | ⚠️ 同上 |
| `delete_observations` | 删除指定 observation | ⚠️ 违反 Append-only 原则，不应使用 |
| `read_graph` | 读取完整图谱 | ✅ 可用于 Governor 冷启动时重建 Slot 字典 |
| `search_nodes` | 全文搜索实体和关系 | ✅ 核心检索工具 |
| `open_nodes` | 按 name 打开指定实体 | ✅ 可用于获取具体 Memory_Node 的完整数据 |

**不支持的缺失工具**:
- ❌ 无 `update_entity` — 不能直接修改实体的 entityType 或 name
- ❌ 无 `query_relations_by_type` — 不能按 relationType 查询关系
- ❌ 无 `batch_read` — 不能批量按条件读取，只能全量 read_graph 或逐个 open_nodes

---

## 3. Entity 能力

### 3.1 Entity 结构

```
Entity {
  name: string          // 全局唯一，等同于 node_id
  entityType: string    // 分类标签，如 "Project", "MemoryNode"
  observations: string[]  // 字符串数组，自由格式
}
```

### 3.2 能力评估

| 能力 | 状态 | 说明 |
|------|------|------|
| 创建 Entity | ✅ | `create_entities` 支持批量创建，每次最多不限 |
| 读取 Entity | ✅ | `open_nodes(names)` 按 name 读取，`read_graph()` 全量读取 |
| 删除 Entity | ✅ | `delete_entities` 支持批量删除 |
| 修改 Entity 名称 | ❌ | 不支持。违反 Append-only，不应使用 |
| 修改 entityType | ❌ | 不支持 |
| entityType 过滤 | ❌ | `search_nodes` 不支持按 entityType 精确过滤 |

### 3.3 entityType 的实际用途

`entityType` 在 MCP Memory Server 中**参与全文搜索索引**。测试验证：

```
search_nodes("entityType:Project") → 返回空
search_nodes("Project") → 返回所有 entityType=Project 的实体
```

即 `entityType` 的值被当作全文索引的一部分，但不支持字段级过滤。Schema v1.0 中要求所有 Memory_Node 的 entityType = "MemoryNode"，这个约束可以在 Governor 层校验，但 MCP 层无法强制。

---

## 4. Relation 能力

### 4.1 Relation 结构

```
Relation {
  from: string        // 源实体 name
  to: string          // 目标实体 name
  relationType: string // 关系类型，如 "HAS_MEMORY"
}
```

### 4.2 能力评估

| 能力 | 状态 | 说明 |
|------|------|------|
| 创建 Relation | ✅ | `create_relations` 支持批量创建 |
| 读取所有 Relations | ✅ | 通过 `read_graph()` 全量读取 |
| 按类型查询 Relation | ❌ | 无 `query_relations_by_type` 工具 |
| 按源/目标查询 Relation | ❌ | 无定向查询工具 |
| 删除 Relation | ✅ | `delete_relations` 支持批量删除 |

### 4.3 关键限制

**关系无法单独查询。** 这是 Schema v1.0 落地的一个核心障碍。

Schema v1.0 中定义的检索操作依赖于以下查询模式：

```
# 查询某个节点的 SUPERSEDED_BY 关系
> 需要: 查询所有 from=mem_v3, relationType=SUPERSEDED_BY 的关系
> 实际: 只能通过 read_graph() 全量读取后内存过滤

# 查询某个 slot 的所有节点
> 需要: search_nodes 按 category+key+context 精确定位
> 实际: 只能通过全文搜索近似匹配
```

这意味着 Governor 的检索层必须在**本地内存中维护一个关系索引**，而不能依赖 MCP 运行时查询。

---

## 5. Observation 能力

### 5.1 Observation 结构

Observation 是 Entity 上的字符串数组，每条是一个自由文本字符串。

### 5.2 能力评估

| 能力 | 状态 | 说明 |
|------|------|------|
| 创建 Observation | ✅ | 通过 `create_entities` 初始写入 |
| 追加 Observation | ✅ | `add_observations` 支持追加新字符串到已有实体 |
| 删除 Observation | ✅ | `delete_observations` 支持精确字符串匹配删除 |
| 修改 Observation | ❌ | 不支持原地修改。必须删除后重新追加 |
| 按字段名搜索 | ❌ | 不支持 `category:identity` 格式的精确字段查询 |

### 5.3 全文搜索实际表现

测试矩阵：

| 查询词 | 搜索结果 | 分析 |
|--------|---------|------|
| `"category"` | 空 | Observation 内容不包含裸露的字段名 "category" |
| `"entityType:Project"` | 空 | 全文搜索不识别 `entityType:` 前缀 |
| `"standard"` (英文) | 空 | 可能是大小写敏感或索引问题 |
| `"FB15k"` | ✅ 命中 FB15k-237 | Entity name 匹配 |
| `"多源知识图谱"` | ✅ 命中 MuKG_Project | Observation 内容匹配（中文正常） |
| `"PKIA"` | ✅ 命中 5 个实体 | 跨实体匹配 |

**结论**: search_nodes 是**全文搜索**，匹配范围包括 entity name、entityType、observations。它不支持结构化查询，不能用来精确查找 `category=identity AND key=research_field` 的组合条件。

### 5.4 对 Schema v1.0 的影响

Schema v1.0 中定义的 Slot 查询方式：

```
search_nodes("category:preference key:response_language context:global status:ACTIVE")
```

**在实际 MCP 上无法工作**，因为：
1. `search_nodes` 不支持多字段 AND 查询
2. Observation 中存储的是 `"category: preference"` 而非 `"category:preference"`
3. 无法区分字段名和字段值

---

## 6. Search 能力总结

| 搜索维度 | 支持情况 | 实际行为 |
|---------|---------|---------|
| Entity name 精确匹配 | ✅ | `search_nodes("PKIA_Project")` 直接命中 |
| Entity name 部分匹配 | ✅ | `search_nodes("PKIA")` 模糊命中 |
| Observation 内容匹配 | ✅ | `search_nodes("多源")` 命中 observation 包含该词的实体 |
| 多字段组合查询 | ❌ | 无法在同一次搜索中指定多个 AND 条件 |
| 字段级精确过滤 | ❌ | 无法按 `category=identity` 精确过滤 |
| entityType 过滤 | ❌ | `search_nodes("Dataset")` 可匹配但为全文模糊，非精确过滤 |
| Relation 搜索 | ❌ | 关系仅能从 `read_graph()` 全量读取后自行过滤 |
| 分页/偏移 | ❌ | 无分页支持。大量实体时需要全量读取 |

---

## 7. 与 memory_schema_v1.0 的兼容性分析

### 7.1 兼容项（✅）

| Schema v1.0 要求 | 兼容性 | 说明 |
|------------------|--------|------|
| 创建 Memory_Node 实体 | ✅ | `create_entities` 可直接创建 |
| 编写字段到 observations | ✅ | 作为字符串数组写入 |
| 创建 HAS_MEMORY 关系 | ✅ | `create_relations` 支持 |
| 创建 SUPERSEDED_BY 关系 | ✅ | 同上 |
| 创建 DERIVED_FROM 关系 | ✅ | 同上 |
| 强化更新（reinforcement_count） | ✅ | `add_observations` 追加更新 |
| 读取特定节点 | ✅ | `open_nodes(names)` |
| 读取完整图谱（冷启动） | ✅ | `read_graph()` |

### 7.2 不兼容项（❌）

| Schema v1.0 要求 | 实际能力 | 差距 |
|------------------|---------|------|
| `search_nodes("category:preference key:response_language context:global status:ACTIVE")` | 仅支持单字符串全文搜索 | **无法实现** slot 级精确查询 |
| 查询特定 slot 的所有版本节点 | 需要全量读取后内存过滤 | 性能差，数据量大后不可行 |
| 按 relationType 查询关系 | 无定向关系查询工具 | **必须**在 Governor 内存中维护关系索引 |
| 对 ACTIVE 唯一的强制约束 | MCP 层无约束机制 | **必须**在 Governor 层校验 |
| 版本号单调递增的强制约束 | MCP 层无约束机制 | **必须**在 Governor 层校验 |
| 写入时原子性（创建节点 + 更新旧节点 + 建立关系） | 三次独立 API 调用，无事务 | **无原子性**，部分失败可能导致数据不一致 |

---

## 8. 不兼容项详细说明

### 8.1 无结构化查询

**根本问题**: MCP Memory Server 的 `search_nodes` 是纯文本全文搜索，不支持 JSON 或字段级过滤。

**影响范围**:
- 无法实现 `get_active_memory()` 的精确 slot 查询
- 无法实现版本链的自动发现
- 无法实现 Slot 字典的增量更新

**应对方案**: Governor 必须在冷启动时通过 `read_graph()` 全量加载图谱，在本地内存中建立 Slot 字典和关系索引。

### 8.2 无原子写入

**根本问题**: 一次 Conflict Resolution 操作需要 3 次 MCP 调用：
1. `create_entities` — 创建新节点
2. `add_observations` — 旧节点 status → DEPRECATED
3. `create_relations` — 建立 SUPERSEDED_BY 关系

如果步骤 2 或 3 失败，系统处于不一致状态（新节点 ACTIVE，旧节点也是 ACTIVE）。

**应对方案**: Governor 需要实现补偿逻辑，在检测到部分失败时回滚已执行的步骤。Governor 启动时还应运行一致性检查（D01-D04 规则），修复上次运行遗留的不一致。

### 8.3 无关系查询

**根本问题**: 无法按条件查询关系，只能全量读取。

**影响范围**: `trace_memory()` 接口无法按需查询 SUPERSEDED_BY 链。

**应对方案**: Governor 在内存中维护关系索引（二维 Map: `from → relationType → [to]`）。冷启动时全量加载，写入时增量更新。

### 8.4 Observation 更新非原子

**根本问题**: `add_observations` 只能追加，不能修改。强化更新需要「删除旧 observation + 追加新 observation」两步操作，不是原子的。

**应对方案**: 强化更新仅追加 `reinforcement_count` 和 `updated_at` 的新 observation，保留旧值作为历史。读取时取最新值。

---

## 9. Governor MVP 需要调整的部分

### 9.1 架构调整

```
原架构（Schema v1.0）:
Agent → Governor → MCP Memory Server

实际可行架构（Audit v1.0）:
Agent → Governor
            ├── 内存: Slot 字典 + 关系索引（由 Governor 维护）
            └── MCP Memory Server（作为持久化后端）
```

Governor 不再仅仅是「校验层」，还必须承担**内存索引层**的职责。

### 9.2 具体调整项

| 调整项 | Schema v1.0 设计 | Audit 修正 |
|--------|-----------------|-----------|
| **Slot 查询** | 依赖 search_nodes 精确匹配 | **改为本地内存查询**。Governor 启动时全量加载，构建 `slot_id → active_node_id` 字典 |
| **关系查询** | 通过 MCP 原生关系查询 | **改为本地内存索引**。Governor 维护 `from → relationType → [to]` 和 `to → relationType → [from]` 双向索引 |
| **写入原子性** | 未处理 | **引入补偿机制**。每次写入三步骤前先记录操作日志，失败时回滚 |
| **搜索** | search_nodes 字段级精确搜索 | **改为 Governor 本地过滤**。全量加载后在内存中按条件过滤 |
| **version 管理** | 由 Governor 查询 MCP 获取 max_version | **改为内存维护**。Governor 在 Slot 字典中缓存 version_count |
| **冷启动策略** | 未定义 | **需要全量加载**。Governor 启动时调用 read_graph()，重建全部内存索引 |
| **增量同步** | 未定义 | 写入操作后同时更新 MCP 和本地内存索引，保持两者一致 |

### 9.3 Governor MVP v0.1 的最小可行范围

基于审计结果，MVP 的核心职责调整为：

1. **内存索引层**
   - 启动时通过 `read_graph()` 全量加载图谱
   - 构建 Slot 字典（`slot_id → active_node_id + version_count`）
   - 构建关系索引（`from → relationType → [to]` 双向）

2. **写入校验**
   - 重复检测（W01）：通过 Slot 字典快速定位，无需查询 MCP
   - 冲突仲裁（C01-C04）：内存比较，无需查询 MCP
   - 版本号管理：从 Slot 字典获取 max_version

3. **持久化写入**
   - 直接调用 MCP 工具执行实际的创建/更新操作
   - 写入成功后同步更新内存索引
   - 失败时执行补偿

4. **检索接口**
   - `get_active_memory`: 从 Slot 字典直接返回，无需查询 MCP
   - `get_context_memory`: 从内存索引按 context 过滤
   - `trace_memory`: 从关系索引沿 SUPERSEDED_BY 链遍历

5. **不包含**
   - 生命周期定时任务（L01-L03）— 需要在独立进程中运行，MVP 阶段暂不实现
   - 数据一致性修复（D01-D04）— 作为启动时的一次性检查
   - 版本链长度超限处理（裁剪/压缩）— 简化处理

### 9.4 启动流程

```
Governor.startup():
  1. read_graph() → 全量加载 entities + relations
  2. 遍历所有 entityType=MemoryNode 的实体：
     a. 从 observations 解析所有字段
     b. 构建 slot_id = category:key@context
     c. 更新 Slot 字典（记录 ACTIVE 节点和最新 version）
  3. 遍历所有 relations：
     a. 构建正向索引: from → relationType → [to]
     b. 构建反向索引: to → relationType → [from]
  4. 验证一致性（D01-D04），记录不一致但不自动修复
  5. 进入就绪状态
```

---

## 10. 审计结论

| 维度 | 结论 |
|------|------|
| 核心架构可行性 | ✅ 可行，但需要调整架构 |
| Schema v1.0 准确度 | ⚠️ 检索部分需要修正（search_nodes 达不到预期精度） |
| 主要风险 | 无原子写入、无关系查询、无结构化搜索 |
| 关键修正 | Governor 必须维护本地内存索引，不能依赖 MCP 运行时查询 |
| MVP 可否启动 | ✅ 可以，按 9.3 节调整范围后即可实现 |
| 存储文件切换 | ⚠️ MCP 仍指向 `mukg-memory.json`，需先切换至 `pkia-memory.json` |

---

> **文档结束**  
> 本审计报告为 Governor MVP v0.1 的实现依据。所有实现决策应以本报告的实际测试结果为准，  
> 而非 Schema v1.0 的理论假设。建议在实现前更新 Schema v1.0 的检索章节以反映 MCP 的实际能力。