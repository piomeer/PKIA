# PKIA Node Mapping v1

> **Document Type**: Design Decision
> **Status**: Approved
> **Last Updated**: 2026-07
> **Namespace**: pkia_mvp

---

## 1. Purpose

本文档定义 PKIA MVP v0.1 运行时架构的**物理节点映射**。它将 `runtime_boundary_v1.md` 中定义的每个阶段职责（Stage 1~10 + Report + Storage）映射到具体的 Dify 节点类型与子节点结构。

本文档回答：

> **哪个 Dify 节点实现哪个边界？**

边界定义（谁负责什么）由 `runtime_boundary_v1.md` 负责，本文档不重复。

---

## 2. Scope

### 2.1 In Scope

- 物理节点编号，类型，与 Pipeline Stage 的映射
- Iteration 内部子节点编排
- 节点相关的映射决策（MD-01, MD-02）
- Unified Topology 图

### 2.2 Out of Scope

- 节点输入/输出 Schema（参见 `node_io_contract_v1.md`）
- 数据流转与对象演化（参见 `data_flow_v1.md`）
- 故障处理策略（参见 `failure_handling_v1.md`）
- 部署配置（参见 `deployment_v1.md`）

---

## 3. Mapping Decisions

本文档定义以下映射决策（Mapping Decision, MD-XX），作为本地命名空间，不进入全局 P-01~P-06 原则体系。

### MD-01: Fail-Fast Isolation

Iteration 内单项目触发确定性异常时立即脱落，不影响同批次其他项目。异常项目不重试、不阻塞。

Rationale: 确保 1/30 的失败不会阻塞剩余 29 个项目的处理。遵循 R-03。

### MD-02: Unified Scoring

四维评分（Career Alignment, Interest Match, Trend Heat, Research Relevance）由单一 LLM 节点在单次调用中完成，不拆分四个独立 LLM 调用。

Rationale: 四个维度的评分共享相同的上下文（project description, classification），单次调用减少 Token 消耗和延迟。符合 R-01 要求——输出经 Code Node 统一校验。

**与冻结文档的一致性**：`scoring_pipeline_schema_v2.md` (frozen) 将四维评分定义为 Stage 4-7 四个独立子步骤。MD-02 将其合并为单一 LLM 调用，属于实现层优化。评分逻辑、权重、字段定义均未改变。

---

## 4. Main Design

### 4.1 Unified Topology (视觉 SSOT)

```
┌─────────────────────────────────────────────────────────────┐
│ [Global Ingestion]                                           │
│  HTTP (GitHub Trending) ────→ Code (Extractor & Normalizer)  │
│  Node 1                        Node 2                        │
└─────────────────────────────────┬───────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────┐
│ [Batch Iteration Sandbox]                                    │
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
│  Variable Aggregator ────→ Code (Global Ranker)              │
│  Node 4                      Node 5                          │
│                                  ↓                           │
│                         Template (Markdown Render)           │
│                         Node 6                               │
└─────────────────────────────────┬───────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────┐
│ [Storage Adapter]                                            │
│  HTTP POST (Webhook out to local FastAPI)                    │
│  Node 7                                                      │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Node Mapping Matrix

| 物理节点 | 节点类型 | 映射 Pipeline Stage | 职责 |
|----------|----------|---------------------|------|
| Node 1 | HTTP | Stage 1 (Collector) | 获取 GitHub Trending HTML |
| Node 2 | Code | Stage 1 (Extractor) + Stage 2 (Normalizer) | HTML 解析 → 字段提取 → Description 截断 → 关键词提取 |
| Node 3 | Iteration | — | Batch 控制器，最大并发度 30，沙盒隔离 |
| Node 3-1 | LLM | Stage 3 (Classification) | 语义分类：Primary/Secondary Category + Confidence |
| Node 3-2 | Code | Stage 3 (Validation I) | Classification 输出校验，异常项目脱落 (MD-01) |
| Node 3-3 | LLM | Stage 4-7 (Unified Scoring, MD-02) | 四维评分 + Reasoning + Career Goal Impact |
| Node 3-4 | Code | Stage 8-9 (Calculation + Recommendation) + Validation II | 分数求和 → 推荐等级映射 → 校验，异常项目脱落 (MD-01) |
| Node 4 | Variable Aggregator | — | 收拢存活项目 (pipeline_status = PROMOTED) 为 JSON Array |
| Node 5 | Code | Stage 10 (Global Ranker) | 全局排序 + 分组 + 排名赋值 |
| Node 6 | Template | Report Generation Pipeline | Markdown 日报渲染 (6 章节) |
| Node 7 | HTTP | Storage Adapter | 推送渲染结果至外部存储 |

### 4.3 Iteration 子节点编排

Node 3 (Iteration) 内部按固定顺序执行 4 个子节点，每项目沙盒隔离：

```
[Iteration Start]
    │
    ▼
Node 3-1: LLM (Classification)
    │ 输出: ProjectClassified
    ▼
Node 3-2: Code (Validation I)
    │ ├─ PASS → 继续
    │ └─ FAIL → Drop (SKIPPED), 不阻断
    ▼
Node 3-3: LLM (Unified Scoring)
    │ 输出: ScoredProject (含四维评分 + reasoning + career_goal_impact)
    ▼
Node 3-4: Code (Calculation + Validation II)
    │ ├─ total_score = sum of 4 dimensions
    │ ├─ recommendation = threshold mapping
    │ ├─ Validate: field completeness, enum legality
    │ ├─ PASS → pipeline_status = PROMOTED
    │ └─ FAIL → Drop (SKIPPED), 不阻断
    │
    ▼
[Iteration End → 仅 PROMOTED 项目进入 Node 4]
```

### 4.4 节点编号与命名规范

节点 ID 采用 snake_case，前缀为阶段序号：

```
s1_collector         (Node 1 — HTTP)
s2_normalizer        (Node 2 — Code)
s3_iteration         (Node 3 — Iteration)
s3_classifier        (Node 3-1 — LLM)
s3_validation_i      (Node 3-2 — Code)
s3_scorer            (Node 3-3 — LLM)
s3_aggregator_ii     (Node 3-4 — Code)
s4_aggregator        (Node 4 — Variable Aggregator)
s5_ranker            (Node 5 — Code)
s6_renderer          (Node 6 — Template)
s7_storage           (Node 7 — HTTP)
```

---

## 5. Runtime Rules

| Rule | Title | Application |
|------|-------|-------------|
| R-01 | Validation Isolation | Code Node 在每 LLM 节点后立即校验输出 (Node 3-2, Node 3-4) |
| R-03 | Fail-Fast Iteration | 异常项目立即脱落，不阻塞同批次 (Node 3-2, Node 3-4) |
| R-05 | Aggregator Anarchy | Variable Aggregator 不保证输入顺序；Node 5 始终执行全排序 |

---

## 6. Related Documents

| Document | Relationship |
|----------|--------------|
| `runtime_architecture_overview_v1.md` | 拓扑全局图与文档索引。本文档的拓扑图与其保持一致。 |
| `runtime_boundary_v1.md` | 定义每个阶段的 Runtime Owner。本文档的节点映射以此为上流输入。 |
| `data_flow_v1.md` | 描述数据在节点间的流转与状态演化。本文档的节点连接关系由此文档细化。 |
| `node_io_contract_v1.md` | 定义每个节点的输入/输出 Schema。节点映射决定了 IO 契约的范围。 |
| `project_data_schema_v1.md` | 数据契约。定义 RawProject / NormalizedProject / ClassifiedProject / ScoredProject 等对象结构。 |
| `runtime_document_style_guide_v1.md` | 定义 RW-XX 前缀命名规范与文档层次。 |

---

## 7. Version History

| Version | Date | Author | Change Summary |
|---------|------|--------|----------------|
| v1 | 2026-07 | PKIA MVP Agent | Initial release. 7-node mapping matrix, Iteration sub-node orchestration, MD-01, MD-02. Refactored from `runtime_architecture_and_node_mapping_specification_v1.md`. |

---

## 7. Implementation Status

| 组件 | 状态 |
|------|------|
| Collector | ✅ Implemented |
| Dify Workflow Trigger | ✅ Implemented |
| Storage Adapter (接收端点) | ✅ Implemented |
| Normalization (Stage 2) | ❌ Not Started |
| Classification (Stage 3) | ❌ Not Started |
| 4-Dim Scoring (Stages 4-7) | ❌ Not Started |
| Total Score/Ranking (Stages 8-10) | ❌ Not Started |
| Reporter | ❌ Not Started |
| Launcher | ❌ Not Started |
