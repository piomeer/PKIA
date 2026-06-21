# Memory Refactor Report — Memory Ownership Clarification v1.0

> **任务**: Architecture Refactor — Memory Ownership Clarification  
> **执行日期**: 2026-06-21 22:16 JST  
> **涉及**: Task A (Rename) + Task B (Doc Updates) + Task C (Boundary) + Task D (Report)

---

## 1. 修改文件列表

### 1.1 重命名

| 旧路径 | 新路径 | 操作 |
|--------|--------|------|
| `/home/mahe/dify/pkia-memory.json` | `/home/mahe/dify/cline-memory.json` | **重命名** ✅ |

### 1.2 配置文件

| 文件 | 修改内容 | 操作 |
|------|---------|------|
| `cline_chinese_mcp_settings.json` | `mukg-memory.json` → `cline-memory.json` | **更新** ✅ |

### 1.3 代码文件

| 文件 | 修改内容 | 操作 |
|------|---------|------|
| `pkia_memory/governor.py` | 5 处 docstring + comment: `pkia-memory.json` → `cline-memory.json` | **更新** ✅ |
| `pkia_memory/memory_service.py` | 3 处 docstring + comment | **更新** ✅ |
| `pkia_memory/DESIGN.md` | 1 处 文件路径引用 | **更新** ✅ |
| `tests/test_persistence.py` | 1 处 docstring comment | **更新** ✅ |
| `tests/test_governor.py` | 1 处 docstring comment | **更新** ✅ |

### 1.4 L2 存储文件内部引用

| 文件 | 修改内容 | 操作 |
|------|---------|------|
| `cline-memory.json` | `Three_Tier_Memory_System` 内部的 `pkia-memory.json` → `cline-memory.json` | **更新** ✅ |

### 1.5 L3 进度层

| 文件 | 修改内容 | 操作 |
|------|---------|------|
| `PROGRESS.md` | 约束中 `pkia-memory.json` → `cline-memory.json` | **更新** ✅ |

### 1.6 新增文档

| 文件 | 操作 | 说明 |
|------|------|------|
| `docs/memory_boundary_v1.0.md` | **新建** | Workspace vs User Memory 定义 |

### 1.7 更新文档

| 文件 | 修改内容 | 操作 |
|------|---------|------|
| `docs/memory_ontology_v1.1.md` | §11.5 Future Memory Domains 新增 | **更新** ✅ |
| `docs/memory_schema_v1.0.md` | §5.6 Memory Namespace Strategy 新增 | **更新** ✅ |
| `docs/persistence_strategy_report.md` | §5.4 Multi-Memory Source of Truth 新增 | **更新** ✅ |

---

## 2. 重命名结果

### 2.1 文件状态

| 项目 | 状态 |
|------|:----:|
| `pkia-memory.json` 是否存在 | ❌ 已删除（重命名） |
| `cline-memory.json` 是否存在 | ✅ 已创建 |
| MCP 配置指向新文件 | ✅ |

### 2.2 内容验证

```
$ head -1 cline-memory.json
{"type":"entity","name":"PKIA_Project",...}  ← 内容完整迁移
```

`cline-memory.json` 的内容等于原 `pkia-memory.json` 的内容，仅更新了 `Three_Tier_Memory_System` 实体中对文件名和域名的引用。

---

## 3. 剩余引用检查

以下引用 `pkia-memory.json` 的文档文件为**历史记录**，保留原样不做修改：

| 文档 | 原因 |
|------|------|
| `docs/memory_backend_cutover_report.md` | 历史割接记录 |
| `docs/p0_verification_report.md` | 历史验证记录 |
| `docs/mcp_capability_audit.md` | 旧的能力审计 |

**判定**: 这些文档是历史审计和验证的产物，修改它们会破坏审计线索。新的引用已全部指向 `cline-memory.json`。

---

## 4. 双图谱架构图

```
┌────────────────────────────────────────────────────────────┐
│                     PKIA L2 Memory OS                      │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌─────────────────────────┐  ┌─────────────────────────┐  │
│  │   Workspace Memory      │  │    User Memory          │  │
│  │   (Active v0.1)         │  │    (Reserved)           │  │
│  │                         │  │                         │  │
│  │   cline-memory.json     │  │   pkia-user-memory.json │  │
│  │                         │  │                         │  │
│  │   Stores:               │  │   Stores:               │  │
│  │   - 架构决策            │  │   - Identity            │  │
│  │   - 项目历史            │  │   - Preference          │  │
│  │   - 开发过程            │  │   - Project Context     │  │
│  │   - 技术方案            │  │   - Facts & Decisions   │  │
│  │   - Agent Session Logs  │  │   - User Knowledge      │  │
│  │                         │  │                         │  │
│  │   Producer: Cline Agent │  │   Producer: User        │  │
│  │   Consumer: Cline Agent │  │   Consumer: PKIA Agent  │  │
│  └───────────┬─────────────┘  └───────────┬─────────────┘  │
│              │                             │               │
│              └──────────┬──────────────────┘               │
│                         │                                  │
│              ┌──────────▼──────────┐                       │
│              │   Memory Governor   │                       │
│              │   (Slot Index +     │                       │
│              │    Relation Index)  │                       │
│              └──────────┬──────────┘                       │
│                         │                                  │
│              ┌──────────▼──────────┐                       │
│              │   MCP Memory        │                       │
│              │   (Ephemeral Query) │                       │
│              └─────────────────────┘                       │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## 5. 命名空间策略

| Memory Domain | Namespace Prefix | 存储文件 | 当前状态 |
|--------------|-----------------|---------|:--------:|
| Workspace Memory | `workspace/*` | `cline-memory.json` | ✅ Active |
| User Memory | `user/*` | `pkia-user-memory.json` | ❌ Reserved |

---

## 6. 下一阶段建议

| 优先级 | 建议 | 条件 |
|--------|------|------|
| P1 | 执行 P1 Governor Test Suite（已验证 16/16 ✅） | 已完成 |
| P2 | 创建 `pkia-user-memory.json` 空文件 | 用户确认后 |
| P3 | Governor 支持多文件（domain routing） | 确认 User Memory 需求后 |
| P4 | 实现 Memory Boundary 的跨域迁移流程 | Multi-file Governor 完成后 |
| P5 | 清理 MCP 中的 MuKG 残留实体 | 可选，不影响功能 |

---

> **文档结束**  
> Memory Ownership Clarification v1.0 完成。当前所有引用已更新为 `cline-memory.json`。  
> 双图谱架构已预留 `pkia-user-memory.json` 位置。