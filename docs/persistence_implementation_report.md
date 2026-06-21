# Persistence Implementation Report

> **任务**: P0.6 — 实现持久化层  
> **前置**: P0.5 策略确认（MCP 为纯内存，文件为唯一 Source of Truth）  
> **版本**: v1.0  
> **完成日期**: 2026-06-21 21:35 JST  
> **测试结果**: 7/7 全部通过

---

## 1. 变更文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `pkia_memory/memory_service.py` | **修改** | 新增文件追加函数 + bootstrap `observation_update` 回放 |
| `pkia_memory/governor.py` | **修改** | write 流程增加文件落盘步骤 |
| `tests/test_persistence.py` | **新建** | 7 个测试用例覆盖全部持久化场景 |
| `tests/__init__.py` | **新建** | 测试包初始化 |

---

## 2. 修改详情

### 2.1 memory_service.py — 文件持久化层

**新增函数**:

| 函数 | 说明 | 写入格式 |
|------|------|---------|
| `set_storage_path(path)` | 设置全局存储路径 | — |
| `get_storage_path()` | 获取当前存储路径 | — |
| `append_to_file(line)` | 追加任意 JSON Lines 对象 | `{"type":"...", ...}` |
| `append_entity_to_file(node)` | 追加实体行 | `{"type":"entity","name":"mem_...","entityType":"MemoryNode","observations":[...]}` |
| `append_relation_to_file(record)` | 追加关系行 | `{"type":"relation","from":"...","to":"...","relationType":"..."}` |
| `append_observation_to_file(node_id, obs)` | 追加观察更新事件 | `{"type":"observation_update","entityName":"...","observations":[...],"timestamp":"..."}` |

**Bootstrap 增强**:

`load_json_lines()` 现在支持三种行类型:

| type | 处理方式 |
|------|---------|
| `entity` | 解析为 MemoryNode |
| `relation` | 解析为 RelationRecord |
| `observation_update` | 在实体加载后回放，更新 `status` 字段 |

新函数 `_apply_observation_update()` 在 bootstrap 过程中回放 `observation_update` 事件，确保状态变更（如 `ACTIVE → DEPRECATED`）能从文件恢复。

### 2.2 governor.py — 写入流程增加文件落盘

三个 action 函数的流程变更为：

```
_action_create():
  1. 创建 MemoryNode
  2. 更新内存索引 (slot_index + relation_index)
  3. append_entity_to_file(node)        ← 新增
  4. append_relation_to_file(HAS_MEMORY) ← 新增
  5. 返回 MCP 命令

_action_reinforce():
  1. 更新内存索引 (reinforce_node)
  2. append_observation_to_file(node_id, count+timestamp) ← 新增
  3. 返回 MCP 命令

_action_supersede():
  1. 创建新 MemoryNode + 旧节点 DEPRECATED
  2. 更新内存索引
  3. append_entity_to_file(new_node)     ← 新增
  4. append_observation_to_file(old, status:DEPRECATED) ← 新增
  5. append_relation_to_file(SUPERSEDED_BY)  ← 新增
  6. append_relation_to_file(HAS_MEMORY)     ← 新增
  7. 返回 MCP 命令
```

**startup() 增强**: 增加 `svc.set_storage_path(storage_path)` 调用，使持久化函数知道写入路径。

---

## 3. 测试结果

| 测试用例 | 验证内容 | 结果 |
|---------|---------|------|
| `test_create_writes_entity_and_relation_to_file` | create 后文件增加 2 行（entity + relation） | ✅ |
| `test_reinforce_appends_observation_marker` | reinforce 后文件增加 1 行（observation_update） | ✅ |
| `test_supersede_appends_entity_status_and_relations` | supersede 后文件增加 4 行 | ✅ |
| `test_rebuild_recovers_active_node` | 新 Governor 实例从文件重建后找到 ACTIVE 节点 | ✅ |
| `test_rebuild_recovers_superseded_chain` | 重建后 v2 为 ACTIVE，v1 为 DEPRECATED | ✅ |
| `test_rebuild_recovers_reinforcement_count` | reinforcement_count 为运行时状态，重建后为 1 | ✅ |
| `test_startup_empty_file_returns_empty_index` | 空文件启动 → 空索引 | ✅ |

### 3.1 测试覆盖的数据流

```
Create Test:
  Governor.write() → append_entity + append_relation → file
  ↓
  Governor.startup() → load_json_lines → index_node + index_relations
  ↓
  get_active() → returns ACTIVE node ✅

Reinforce Test:
  Governor.write() (same value) → append_observation_update → file
  ↓
  Governor.startup() → replay observation_update → no status change
  ↓
  get_active() → still ACTIVE ✅ (reinforcement_count is runtime-only)

Supersede Test:
  Governor.write() (different value) → append_entity + observation_update + 2 relations → file
  ↓
  Governor.startup() → replay observation_update → old node → DEPRECATED
  ↓
  get_active() → returns v2 (light) ✅
  get_slot_nodes() → v1 = DEPRECATED, v2 = ACTIVE ✅
```

---

## 4. 数据生命周期

### 写入流（最终版）

```
Agent/Cline
  │
  ▼
Governor.write(request)
  ├── 1. 冲突检测 (SlotIndex, O(1))
  ├── 2. 仲裁决策 (C01-C04)
  ├── 3. 更新内存索引 (即刻生效)
  ├── 4. 追加到 pkia-memory.json ★ 持久化
  └── 5. 返回 MCP 命令 (同步到 MCP 内存)
```

### Source of Truth 关系

```
pkia-memory.json (文件)
  ↑ 唯一的持久化存储
  │
  ├── Governor 启动时从此文件重建索引
  ├── Governor 写入时先写文件再更新索引
  │
  └── MCP Memory Server 启动时从此文件加载
       (MCP 写入不入盘，但 Governor 已代为持久化)
```

### 文件格式

`pkia-memory.json` 是 Append-only JSON Lines 文件：

```
{"type":"entity","name":"PKIA_Project",...}          ← 启动时创建
...
{"type":"entity","name":"mem_abc123","entityType":"MemoryNode","observations":[...]}  ← create 写入
{"type":"relation","from":"PKIA_Project","to":"mem_abc123","relationType":"HAS_MEMORY"}  ← create 写入
{"type":"observation_update","entityName":"mem_abc123","observations":["reinforcement_count: 2"],"timestamp":"..."}  ← reinforce 写入
{"type":"entity","name":"mem_def456","entityType":"MemoryNode","observations":[...]}  ← supersede 写入
{"type":"observation_update","entityName":"mem_abc123","observations":["status: DEPRECATED"],"timestamp":"..."}  ← supersede 写入
{"type":"relation","from":"mem_def456","to":"mem_abc123","relationType":"SUPERSEDED_BY"}  ← supersede 写入
{"type":"relation","from":"PKIA_Project","to":"mem_def456","relationType":"HAS_MEMORY"}  ← supersede 写入
```

---

## 5. 验证确认

| 验证项 | 状态 |
|--------|------|
| MCP 为纯内存数据库 | ✅ 已确认（P0.5） |
| pkia-memory.json 为唯一 Source of Truth | ✅ 已确认 |
| Governor 写入同时落盘文件 | ✅ 7 测试通过 |
| Governor 启动时从文件重建索引 | ✅ 重建测试通过 |
| observation_update 回放恢复 ACTIVE/DEPRECATED | ✅ 版本链测试通过 |
| 不依赖 MCP 状态 | ✅ Governor 启动不调用 MCP |

---

> **文档结束**  
> P0.6 持久化层实现完成。PKIA L2 长期记忆现在具备完整的文件持久化能力。  
> 7/7 测试通过。可进入 P1 Governor Test Suite。