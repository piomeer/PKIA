# PKIA MVP Progress

> **Namespace**: pkia_mvp  
> **文件**: `progress/pkia_mvp.md`  
> **用途**: PKIA MVP 产品开发进度

---

## Current Phase
**Phase 0: 文档收尾 — 已完成**

P0 文档补丁全部完成，PKIA MVP v0.1 Baseline 已锁定。

---

## Active Tasks
- **Runtime 目录重构与 7 文档集合生成**: ✅ 完成
- **等待下一步**: GitHub Trending Collector 第一版实现

---

## Completed Tasks

### Phase 1: Runtime Design（2026-07）

| 任务 | 状态 | 说明 |
|------|------|------|
| Chapter 2 — Runtime Boundary 文档落库 | ✅ 完成 | `docs/runtime/Runtime Design v1.0.md` 已创建。覆盖 Collection → Normalizer → Classification → Scoring → Ranking → Report → Storage 的所有 Runtime 职责划分。引入 Dify First, Python Minimal 原则。Collector 方案待 Node Mapping 验证决定。 |
| Runtime Boundary 重构 → runtime_boundary_v1.md | ✅ 完成 | `docs/runtime/runtime_boundary_v1.md` 创建，遵循 style guide 标准结构。Collector 决策已锁定 (HTTP→Code)。Principles 合并为 P-01~P-06。Runtime Rules 引用 R-01~R-05。旧文档标记为 Superseded。大小: 467→~220 行。 |
| Runtime Architecture & Node Mapping Specification | ✅ 完成 | `docs/runtime/runtime_architecture_and_node_mapping_specification_v1.md` 创建。定义 3 域拓扑、7 节点映射矩阵、IO 契约、状态机、监控指标与日志策略。合并 runtime_architecture_overview + node_mapping 职责。添加 P-07 Fail-Fast Isolation 与 P-08 Unified Scoring 原则。 |
| Runtime 目录重构 (Directory as Architecture) | ✅ 完成 | 将单一组合文档拆分为 7 份专题文档。新建 `runtime_architecture_overview_v1.md` (拓扑总图), `node_mapping_v1.md` (MD-01/MD-02), `data_flow_v1.md` (Fat Object + State Machine), `node_io_contract_v1.md` (IO 契约), `failure_handling_v1.md` (纯故障处理), `deployment_v1.md` (部署 + Metrics)。Markdown 组合文档为 Superseded。P-07/P-08 降级为 MD-01/MD-02。更新 style guide 文档树。 |
| Runtime Document Style Guide 文档创建 | ✅ 完成 | `docs/runtime/runtime_document_style_guide_v1.md` 已创建。定义 Runtime 文档层次结构（7 份文档）、标准文档结构（7 节强制）、命名规范（snake_case）、Runtime 规则约定（R-01~R-05）、交叉引用规则和写作规范。 |
| Runtime Style Guide 追加 Lifecycle + Rule Numbering | ✅ 完成 | 新增 §6 文档生命周期（Draft→Review→Approved→Frozen）和 §7 运行时核心规则编号规范，替换规范 R-01~R-05 定义。 |

### Phase 0: 文档收尾（2026-06-24）

| 任务 | 状态 | 说明 |
|------|------|------|
| P0-1: report_generation_pipeline_v1.md Schema 补丁 | ✅ 完成 | 添加 `project_id`, `pipeline_status`, `career_goal_impact`；修复文档引用；Section B 展示添加职业目标影响字段；排序键添加 `project_id` 确定性键 |
| P0-2: daily_report_spec_v1.md Career Goal Impact 展示补丁 | ✅ 完成 | Section B 展示添加结构化职业目标影响；Section A 移除 Arxiv 统计行；移除所有 Arxiv 引用；添加 Ignore 统计行 |
| P0-3: scoring_pipeline_schema_v1.md 标记 DEPRECATED | ✅ 完成 | 添加 DEPRECATED 标志，指向 v2 作为替代 |
| P0-4: L2 图谱补充 PKIA 文档实体 | ✅ 完成 | 新增 9 个实体 + 8 条关系 |
| P0-5: L3 进度文件更新 | ✅ 完成 | 本文件 |
| **P0-6: pkia_v0.1_baseline.md 创建** | ✅ **完成** | Release Baseline，锁定实现范围（13 Frozen + 2 DEPRECATED） |

### 此前完成

- L2 Memory System 已就绪
- Governor MVP v0.1 已验证 (23/23 测试通过)
- 持久化层已部署
- Memory Sync 已部署
- PKIA 文档体系已完成（24 份文档）
- Schema 一致性审查全部通过

---

## Relevant L2 Memories

| Slot | Value |
|------|-------|
| `project:user_memory_file@global` | pkia-user-memory.json |
| `identity:verification_marker@global` | P0-B_Verification |

## Active Decisions

- **Three-Tier Memory System** (ACTIVE): L1 Constitution → L2 Knowledge Graph → L3 Progress
- **PKIA on Dify Platform** (ACTIVE): Dify Backend (Python Flask) + Dify Frontend (Next.js/React)
- **Memory Governance Frozen** (ACTIVE): Ontology, Schema, Governor, Persistence, Sync components frozen
- **Phase 1 实施路线** (ACTIVE): 1A-2B-3C-4A（先补文档 + Python 采集 + Dify Workflow 处理 + Markdown 日报 + GitHub Only）
- **Runtime Boundary v1** (ACTIVE): `runtime_boundary_v1.md`. Collector finalized (HTTP→Code). Principles P-01~P-06. Rules R-01~R-05.
- **Runtime Document Style Guide v1** (ACTIVE): snake_case 命名, 7 节强制结构, R-01~R-05 初始规则
- **Runtime Architecture & Node Mapping v1** (ACTIVE): 7-doc directory. `runtime_architecture_overview_v1.md` (topology + index), `node_mapping_v1.md` (mapping + MD-XX), `data_flow_v1.md` (data flow), `node_io_contract_v1.md` (IO contracts), `failure_handling_v1.md` (failure), `deployment_v1.md` (deployment).
- **PKIA v0.1 Baseline** (ACTIVE): 13 Frozen Documents, Success Criteria defined, Excluded Features documented

## Current Constraints

- Memory Governance Freeze
- PKIA v0.1 Baseline Frozen: 13 份核心文档禁止修改
- Dify 后端规范: Python Flask, DDD, SQLAlchemy, ruff linting
- Dify 前端规范: Next.js + TypeScript + React, pnpm
- 无用户确认禁止 git push

## Working Context

- **System State**: PKIA Phase 1 — Runtime directory restructured (7 docs), ready for Collector implementation
- **Runtime Boundary State**: `docs/runtime/runtime_boundary_v1.md` (Approved). Predecessor `Runtime Design v1.0.md` (Superseded).
- **Runtime Directory State**: 7 active docs + 2 superseded. `runtime_architecture_overview_v1.md` is the entry point. Combined spec doc is Superseded.
- **Runtime Style Guide State**: `docs/runtime/runtime_document_style_guide_v1.md` updated — tree reflects full 7-doc hierarchy.
- **Active Governance**: Memory Governance FROZEN + Baseline FROZEN
- **Key Architecture Decisions**:
  - Scoring Pipeline v2 → F4/F5
  - v0.1 实现范围: data_collection_strategy_v1.md (GitHub Only)
  - 实现载体: Python 脚本采集 + Dify Workflow 处理
  - 日报交付: Markdown (pkia/reports/YYYY-MM-DD.md)
- **Baseline 关键排除**: Arxiv, MCP Ecosystem, Memory Ecosystem, Multi-Source, Feedback Learning, Auto Prompt, Web UI, 实时推送, 多用户

## Blockers

- 等待用户指定 Phase 1 下一个实现目标（Collector 实现 / Dify Workflow 骨架搭建）

## Next Steps

Phase 1 (Runtime Design 确认后) 建议按依赖链实施：

1. **Node Mapping 设计** — 将 Runtime Boundary 映射到具体 Dify Workflow 节点配置
2. **GitHub Trending Collector** — Python 脚本 / Dify HTTP+Code（待验证），抓取 Top 30，生成 `project_id`
3. **Project Normalizer** — Dify Code Node，清洗 description、提取 keywords
4. **Dify Workflow 骨架** — Stage 1→2→3 数据流
5. **Classification Agent** — Dify LLM Node + Validation Code Node
6. **Scoring Agent v2** — Dify LLM Node + Validation Code Node
7. **Ranking Code Node** — Dify Iteration → Variable Aggregator → Code Node
8. **Template Node 报告渲染** — Jinja2 Markdown 模板
9. **Storage Adapter** — HTTP Adapter 对接 pkia/reports/

---

*最后更新: 2026-07-08 JST*