# Persistence Strategy Report

> **任务**: P0.5 — 确认 PKIA 长期记忆的持久化能力  
> **执行日期**: 2026-06-21 21:22 JST  
> **前提**: VS Code Reload Window 已执行

---

## 1. MCP 持久化能力验证结果

### 1.1 实验设计

```
Step 1: read_graph()                     → 基线记录（2026-06-20 23:15）
Step 2: create_entities(PERSIST_TEST_001) → 写入 MCP（2026-06-20 23:21）
Step 3: read_graph()                     → 确认存在
Step 4: grep pkia-memory.json            → 确认不在文件中
Step 5: VS Code Reload Window            → 用户执行（2026-06-21 09:22）
Step 6: read_graph()                     → 重启后检查
Step 7: grep pkia-memory.json            → 最终文件检查
```

### 1.2 实验结果

| 步骤 | 发现 | 结论 |
|------|------|------|
| Step 1: 基线 | 17 实体（6 PKIA + 10 MuKG + 1 PKIA_Verification_Node） | — |
| Step 2: 创建 | `PERSIST_TEST_001` 创建成功 | MCP `create_entities` 正常工作 |
| Step 3: 确认 | `PERSIST_TEST_001` 出现在 `read_graph()` 中 | 写入内存在当前 session 可见 |
| Step 4: 文件检查 | `pkia-memory.json` 无 `PERSIST_TEST_001` | **实体不在持久化文件中** |
| Step 5: Reload | VS Code 重启完成 | — |
| Step 6: 重启后检查 | `PERSIST_TEST_001` **仍存在**于 `read_graph()` | ⚠️ |
| Step 7: 最终文件检查 | `pkia-memory.json` 仍无 `PERSIST_TEST_001` | ✅ |

### 1.3 核心发现：MCP 进程生命周期独立于 VS Code

实验的意外结果揭示了关键架构事实：

```
VS Code Reload Window
  └── 重启了 Cline 插件进程
  └── 但未杀死 MCP 进程（PID 2665, 启动于 21:14）

MCP 进程 (PID 2665)
  └── 独立于 VS Code 窗口运行
  └── VS Code Reload 不影响它
  └── 其内存中的图谱完好无损
```

这就是为什么 Reload 后 `PERSIST_TEST_001` 仍然存在——因为 MCP 进程根本没有重启。它只是**断连后重新连接**。

### 1.4 MCP 真实持久化行为

通过分析 `pkia-memory.json` 文件内容与 `read_graph()` 返回数据的差异：

| 数据来源 | 实体数 | 内容 |
|---------|--------|------|
| `pkia-memory.json` 文件 | 6 | 仅初始 PKIA 实体（PKIA_Project, Dify_Platform 等） |
| `read_graph()` 返回 | 18 | 6 文件实体 + 10 MuKG 实体 + 2 测试实体 |

**差异原因**:
- 10 个 MuKG 实体：来自之前 MCP 进程（指向 `mukg-memory.json` 的旧实例）通过 `create_entities` 写入的残留
- 2 个测试实体：`PKIA_Verification_Node` + `PERSIST_TEST_001`——在当前 MCP 进程中通过 `create_entities` 创建的

**最终结论**: MCP Memory Server **确实不自动写回 JSON 文件**。所有通过 `create_entities` / `create_relations` / `add_observations` 写入的数据仅驻留在内存中。如果 MCP 进程被 kill 并重启，这些数据将丢失，只保留 `pkia-memory.json` 文件中初始的 6 个实体。

---

## 2. 数据生命周期分析

### 2.1 当前数据流

```
Governor/MCP Tools
  │
  ├── create_entities ──► MCP 内存 (暂存, 重启丢失)
  │                          ▲
  ├── read_graph() ◄─────────┘
  │
  └── PKIA-memory.json (启动时加载, 但从不回写)
        │
        └── 文件系统的唯一持久化点
```

### 2.2 问题

| 问题 | 严重程度 | 说明 |
|------|---------|------|
| `create_entities` 不入盘 | ❌ 严重 | MCP 进程重启后所有写入丢失 |
| MCP 进程独立于 VS Code | ⚠️ 中 | 普通 Reload 无法重启 MCP，用户可能误以为数据已持久 |
| 无原子写入保障 | ❌ 严重 | create → add_observations → create_relations 三步无事务 |
| 文件与内存不一致 | ⚠️ 中 | 文件只有 6 实体，内存有 18 实体 |

### 2.3 理想生命周期

```
写入流程:
  Agent/Cline
    → Governor.write()        # 1. 校验 + 仲裁
    → update index            # 2. 更新内存索引 (即刻生效)
    → append to pkia-memory.json  # 3. 追加到文件 (持久化)
    → MCP create_entities()   # 4. 同步到 MCP 内存 (查询接口)

读取流程:
  Agent/Cline
    → Governor.get_active()   # 1. 从内存索引读取 (O(1))
    → 无需调用 MCP             # 2. 不依赖 MCP 查询

启动流程:
  Governor.startup()
    → read pkia-memory.json   # 1. 从文件加载
    → build indexes           # 2. 重建内存索引
    → pass                    # 3. 不依赖 MCP 启动时序
```

---

## 3. Source of Truth 定义

### 3.1 最终决策：文件是唯一 Source of Truth

| 组件 | 角色 | 是否 Source of Truth |
|------|------|---------------------|
| `pkia-memory.json` | **持久化存储** | **✅ 唯一的 Source of Truth** |
| Governor 内存索引 | 读取缓存 | ❌ 派生数据，每次启动重建 |
| MCP Memory Server | 查询接口 | ❌ 纯内存副本，重启丢失 |

### 3.2 Source of Truth 切换规则

```
启动时:
  pkia-memory.json (file)
    → Governor Slot Index (memory)     # 从文件重建
    → MCP Memory Server (memory)       # 从文件加载

写入时:
  Governor 决策
    → 1. 更新内存索引 (即刻可见)
    → 2. 追加到 pkia-memory.json (持久化)  ← 这是真正的持久化步骤
    → 3. 通过 MCP create_entities 同步    ← 可降级（MCP 不可用时 Governor 仍可读）

冲突时:
  以 pkia-memory.json 为准
    → Governor 启动时从文件重建索引
    → MCP 内存状态忽略
```

---

## 4. Governor 写入流程

### 4.1 write() 的完整流程

```
write(request)
  │
  1. Slot Index 冲突检测
  │   └── read from memory (O(1))
  │
  2. 仲裁决策
  │   ├── created  → 创建新节点
  │   ├── reinforced → 强化旧节点
  │   ├── superseded → 替换旧节点
  │   └── rejected → 不操作
  │
  3. 更新内存索引 (即刻生效)
  │
  4. 追加到 pkia-memory.json ← ★ 新增的持久化步骤
  │   └── 以 JSON Lines 格式追加一行
  │
  5. 返回 MCP 命令列表
  │   └── Agent 执行这些命令同步到 MCP 内存
  │
  6. 完成
```

### 4.2 文件追加格式（JSON Lines）

每个写入操作在 `pkia-memory.json` 中追加以下行：

**创建新节点**:
```json
{"type":"entity","name":"mem_<uuid>","entityType":"MemoryNode","observations":["node_id: mem_<uuid>","category: preference","key: response_language","value: zh-CN","context: global","status: ACTIVE","confidence: 1.0","source_type: USER_EXPLICIT","created_at: 2026-06-21T12:00:00Z","updated_at: 2026-06-21T12:00:00Z","version: 1","reinforcement_count: 1"]}
{"type":"relation","from":"PKIA_Project","to":"mem_<uuid>","relationType":"HAS_MEMORY"}
```

**强化更新**（不需要追加行—仅修改内存）:
- 不追加文件行，因为 `pkia-memory.json` 只在启动时加载，reinforcement 信息是运行时状态
- 后续版本可考虑定期 snapshot

**替换节点**:
```json
{"type":"relation","from":"mem_<new>","to":"mem_<old>","relationType":"SUPERSEDED_BY"}
{"type":"entity","name":"mem_<new>","entityType":"MemoryNode","observations":[...]}
{"type":"relation","from":"PKIA_Project","to":"mem_<new>","relationType":"HAS_MEMORY"}
```

### 4.3 文件追加工具（memory_service.py 扩展）

在 `memory_service.py` 中增加：

```python
def append_entity_to_file(path: str, node: MemoryNode) -> None:
    """Append a single entity line to pkia-memory.json."""

def append_relation_to_file(path: str, record: RelationRecord) -> None:
    """Append a single relation line to pkia-memory.json."""

def append_to_file(path: str, line: dict) -> None:
    """Append any JSON Lines object to pkia-memory.json."""
```

这些函数在 Governor 的 write() 方法中被调用，在更新内存索引之后、返回 MCP 命令之前。

---

## 5. 推荐实现方案

### 5.1 方案 A（推荐）：Governor 直接写文件

| 维度 | 描述 |
|------|------|
| **架构** | Governor 是唯一写入者，MCP 是只读查询接口 |
| **持久化** | Governor 在每次 write() 后立即追加到 `pkia-memory.json` |
| **启动** | Governor 从文件加载 → 重建索引 → 不同步 MCP |
| **MCP 角色** | 仅用于 Agent 通过 `use_mcp_tool` 直接查询 |
| **优点** | 数据可靠、架构清晰、不依赖 MCP 持久化 |
| **缺点** | Governor 需要文件写入权限 |

### 5.2 方案 B（不推荐）：MCP + 定时回写

| 维度 | 描述 |
|------|------|
| **架构** | MCP 是主存储，定时 dump 到文件 |
| **持久化** | crontab 或 Governor 定时任务调用 `read_graph()` 并写文件 |
| **优点** | 不需要改 MCP 本身 |
| **缺点** | 窗口期内数据可能丢失、实现复杂、非 Append-only |

### 5.3 结论：采用方案 A

理由：

1. **一致性**: 文件是 Source of Truth，Governor 的内存索引从文件重建，保证数据一致性
2. **Append-only 兼容**: JSON Lines 格式天然支持追加，符合 Ontology 的 Append-only 要求
3. **原子性**: 一次 write() 对应一次文件追加操作，不依赖外部 MCP 的三步调用
4. **可恢复**: 文件损坏或丢失时最多丢失最后一次写入（MCP 内存模式会全部丢失）
5. **降级友好**: MCP 不可用时，Governor 仍可从文件读取完整数据

---

## 5.4 Multi-Memory Source of Truth

For future Dual-Memory support, the Source of Truth model extends to multiple files.

### Directory Layout

```
memory/
├── cline-memory.json          # Workspace Memory (current, v0.1)
└── pkia-user-memory.json      # User Memory (reserved for future)
```

### Multi-File Governance

Each file maintains its own:

- **Slot Index** (per-file, in Governor memory)
- **Relation Index** (per-file, in Governor memory)
- **Append-only JSON Lines** (per-file, on disk)

### Source of Truth Hierarchy

```
cli├──ne-memory.json          # Workspace Memory: Source of Truth for workspace/*
    └── pkia-user-memory.json      # User Memory: Source of Truth for user/*
```

Governor routes writes to the appropriate file based on domain namespace.

For detailed boundary definitions, see `memory_boundary_v1.0.md`.

---

## 6. 变更清单

需要修改的代码：

| 文件 | 变更 |
|------|------|
| `pkia_memory/memory_service.py` | 新增 `append_entity_to_file()`, `append_relation_to_file()`, `append_to_file()` |
| `pkia_memory/governor.py` | 在 `_action_create()`, `_action_reinforce()`, `_action_supersede()` 中增加文件写入步骤 |
| `pkia_memory/DESIGN.md` | 更新写入流程图，加入文件持久化步骤 |

不需要修改的代码：

| 文件 | 原因 |
|------|------|
| `pkia_memory/models.py` | 数据类不变 |
| `pkia_memory/slot_index.py` | 索引逻辑不变 |
| `pkia_memory/relation_index.py` | 索引逻辑不变 |

---

> **文档结束**  
> P0.5 验证完成。核心结论：MCP 不自动持久化，Governor 必须直接写入 `pkia-memory.json` 文件。  
> 推荐采用方案 A，在 Governor 的 write() 流程中增加文件追加步骤。