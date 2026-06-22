# L3 Namespace Architecture v1.0

> **文档状态**: Architecture Freeze Document  
> **版本**: 1.0  
> **更新日期**: 2026-06-22  
> **用途**: 定义基于命名空间的多文件 L3 模型

---

## 1. 为什么单文件 PROGRESS.md 不足

### 1.1 当前问题

| 问题 | 影响 |
|------|------|
| **单文件冲突** | 多 Agent/多任务同时写入同一文件，产生编辑冲突 |
| **注意力稀释** | 单个文件包含所有命名空间的内容，Agent 难以聚焦 |
| **上下文污染** | PKIA Memory 的进度出现在 Workspace 的上下文中 |
| **迁移困难** | 单文件无法分拆到不同 Agent 的工作流 |

### 1.2 Multi-Agent 冲突

```
Agent A (Workspace): 更新 PROGRESS.md 第 1 节
Agent B (PKIA MVP): 同时更新 PROGRESS.md 第 3 节
→ 冲突: 后写入者覆盖先写入者的内容
→ 丢失: A 的更新可能被 B 覆盖
```

## 2. Namespace 设计

### 2.1 结构

```
progress/
├── workspace.md          # Workspace 级项目进度
├── pkia_mvp.md           # PKIA MVP 开发进度
├── pkia_memory.md        # PKIA Memory 模块进度
└── mukg.md               # MuKG 项目进度（遗留）
```

### 2.2 原则

| 原则 | 说明 |
|------|------|
| **一个任务 → 一个文件** | 每个逻辑任务组使用独立的 L3 文件 |
| **按命名空间隔离** | 不同命名空间的操作永不交叉 |
| **文件名 = 命名空间** | `progress/<namespace>.md` |
| **无跨文件引用** | L3 文件之间不互相依赖 |

### 2.3 命名空间定义

| 命名空间 | 文件 | 用途 |
|---------|------|------|
| `workspace` | `progress/workspace.md` | Workspace 级开发管理，架构决策跟踪 |
| `pkia_mvp` | `progress/pkia_mvp.md` | PKIA MVP 产品开发进度 |
| `pkia_memory` | `progress/pkia_memory.md` | Memory 模块（Ontology/Governor/Governor/测试） |
| `mukg` | `progress/mukg.md` | MuKG 遗留项目（只读，不活跃） |

## 3. 所有权规则

| 规则 | 说明 |
|------|------|
| 每个 Agent 必须知道自己当前操作的命名空间 | 通过 `.clinerules` 或任务上下文确定 |
| 每个 Agent 只能写入自己的命名空间文件 | 禁止跨命名空间写入 |
| 命名空间文件不存在时自动创建 | 使用标准模板初始化 |
| 命名空间文件保留历史记录 | 不删除旧内容，Append-style 追加 |

## 4. 向后兼容

`PROGRESS.md` 作为根级汇总文件保留，但内容改为：

```
# L3 Progress — Namespace Index

当前系统使用基于命名空间的 L3 模型。
单文件 PROGRESS.md 已退役。

请参见:
- progress/workspace.md
- progress/pkia_mvp.md
- progress/pkia_memory.md
- progress/mukg.md
```

## 5. 未来可扩展性

| 扩展方向 | 操作 |
|---------|------|
| 新命名空间 | 新增 `progress/<name>.md` 即可 |
| 子命名空间 | 支持 `progress/<parent>/<child>.md`（v2.0） |
| 跨命名空间视图 | 自动聚合工具（v3.0） |