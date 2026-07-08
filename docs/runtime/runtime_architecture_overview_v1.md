# PKIA Runtime Architecture Overview v1

> **Document Type**: Design Decision
> **Status**: Approved
> **Last Updated**: 2026-07
> **Namespace**: pkia_mvp

---

## 1. Purpose

本文档是 PKIA MVP v0.1 Runtime Architecture 的核心概览与索引入口。它定义了：

- 运行时拓扑结构（视觉 SSOT）
- 文档目录与各文档职责
- 推荐的阅读顺序

本文档不深入任何技术细节。每项能力的完整定义由其对应的专题文档负责。

---

## 2. Runtime Topology (视觉 SSOT)

以下是全系 Runtime 架构文档唯一依赖的核心拓扑图。所有 data flow、IO contract、failure handling 均以此结构为基准。

```
┌─────────────────────────────────────────────────────────────┐
│ [Global Ingestion]                                           │
│                                                              │
│  HTTP (GitHub Trending) ────→ Code (Extractor & Normalizer)  │
│  Node 1                        Node 2                        │
└─────────────────────────────────┬───────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────┐
│ [Batch Iteration Sandbox]                                    │
│                                                              │
│  Iteration (Top 30 Projects, max concurrency = 30)           │
│    │                                                         │
│    ├─ LLM (Classification)          Node 3-1                 │
│    ├─ Code (Validation I)           Node 3-2  ← Drop on Fail │
│    ├─ LLM (Unified Scoring)         Node 3-3                 │
│    └─ Code (Calculation & Valid II) Node 3-4  ← Drop on Fail │
└─────────────────────────────────┬───────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────┐
│ [Global Output]                                              │
│                                                              │
│  Variable Aggregator ────→ Code (Global Ranker)              │
│  Node 4                      Node 5                          │
│                                  ↓                           │
│                         Template (Markdown Render)           │
│                         Node 6                               │
└─────────────────────────────────┬───────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────┐
│ [Storage Adapter]                                            │
│                                                              │
│  HTTP POST (Webhook out to local FastAPI)                    │
│  Node 7                                                      │
└─────────────────────────────────────────────────────────────┘
```

### 物理执行域说明

| 域 | 执行模式 | 包含节点 | 职责 |
|----|----------|----------|------|
| Global Ingestion | 单实例串行 | Node 1, Node 2 | 数据采集与初始化，不涉及业务判断 |
| Batch Iteration Sandbox | 并发迭代，最大 30 | Node 3-1~3-4 | 业务智能处理，每项目沙盒隔离，异常自动脱落 |
| Global Output | 单实例串行 | Node 4, Node 5, Node 6 | 收拢存活项目，全局排序，渲染输出 |
| Storage Adapter | 外部进程 | Node 7 | 持久化，Workflow 不感知存储后端 |

---

## 3. Document Index

| 文档 | 职责 | 状态 | 前置阅读 |
|------|------|------|----------|
| `runtime_document_style_guide_v1.md` | 写作标准：文档结构、命名规范、规则体系 | Active | 1st |
| `runtime_boundary_v1.md` | 运行时边界：每阶段由哪个组件负责，P-01~P-06 | Active | 2nd |
| `runtime_architecture_overview_v1.md` | （本文档）拓扑概览与索引 | Active | 3rd |
| `node_mapping_v1.md` | 物理节点映射：Dify 节点类型、子节点决策 (MD-XX) | Active | 4th |
| `data_flow_v1.md` | 数据流：Fat Object 演化、State Machine、Variable Flow、Validation Gates | Active | 5th |
| `node_io_contract_v1.md` | IO 契约：节点输入/输出 Schema、职责边界矩阵 | Active | 6th |
| `failure_handling_v1.md` | 故障处理：Retry、Timeout、Drop、Abort、异常日志 | Active | 7th |
| `deployment_v1.md` | 部署：触发器、环境配置、Storage Adapter、Metrics | Active | 8th |
| `runtime_glossary_v1.md` | 全局术语表：统一 Data States、Flow Concepts、Architecture 概念 | Active | 参考

### 已废弃文档

| 文档 | 替代 |
|------|------|
| `Runtime Design v1.0.md` | `runtime_boundary_v1.md` |
| `runtime_architecture_and_node_mapping_specification_v1.md` | 本文档 + `node_mapping_v1.md` + 其余 5 份专题文档 |

---

## 4. Reading Order

首次阅读 Runtime Architecture 的推荐路径：

```
runtime_document_style_guide_v1.md   (先读懂写作规范)
        ↓
runtime_boundary_v1.md               (理解谁负责什么)
        ↓
runtime_architecture_overview_v1.md  (建立拓扑全局图——即本文档)
        ↓
node_mapping_v1.md                   (看具体映射到哪些 Dify 节点)
        ↓
data_flow_v1.md                      (理解数据如何流转)
        ↓
node_io_contract_v1.md               (理解每个节点的契约)
        ↓
failure_handling_v1.md               (理解异常发生时怎么办)
        ↓
deployment_v1.md                     (理解如何部署运行)
        ↓
runtime_glossary_v1.md               (遇到术语疑问时查阅)
```

---

## 5. Related Documents

| Document | Relationship |
|----------|--------------|
| `runtime_document_style_guide_v1.md` | 定义本文档的写作规范与文档层次结构。 |
| `runtime_boundary_v1.md` | 定义 P-01~P-06 全局原则与阶段职责。拓扑图的每个节点对应 Boundary 中的一个模块。 |
| `node_mapping_v1.md` | 详细描述拓扑中每个物理节点的类型、子节点结构与映射决策。 |
| `data_flow_v1.md` | 描述拓扑中数据如何在节点间流转与演化。 |
| `pkia_v0.1_baseline.md` | Frozen baseline。锁定实现范围与载体约束。 |

---

## 6. Version History

| Version | Date | Author | Change Summary |
|---------|------|--------|----------------|
| v1 | 2026-07 | PKIA MVP Agent | Initial release. Topology diagram, document index, and reading order for the refactored Runtime Architecture directory. |
