# PKIA Runtime Glossary v1

> **Document Type**: Reference
> **Status**: Active
> **Last Updated**: 2026-07
> **Namespace**: pkia_mvp

---

## 1. Purpose

本术语表统一 PKIA MVP v0.1 运行时架构中的核心术语定义。所有后续的 Dify Workflow 搭建、Prompt 编写、Code Node 实现和团队讨论，均须严格使用本表中的标准名词。

定义来源为现有 Runtime 文档集。本表不发明新概念。

---

## 2. Data States (数据状态)

每阶段产生的数据结构，遵循 `project_data_schema_v1.md` (frozen) 定义的字段契约。

| 术语 | 定义 | 产生阶段 | 关键约束 |
|------|------|----------|----------|
| **ProjectRaw** | 从 GitHub Trending 获取的初始项目对象。包含 `project_id`, `project_name`, `owner`, `description`, `topics`, `stars`, `forks`, `language`, `source`, `collection_date`, `pipeline_status`。 | Node 2 (Code) 输出 | `project_id` 在此阶段生成后永不修改。`pipeline_status` 初始值为 `PROMOTED`。 |
| **ProjectNormalized** | 经过清洗和标准化的项目对象。继承 ProjectRaw 全部字段，追加 `normalized_description` (≤200 chars), `primary_language`, `extracted_keywords` (≤5)。 | Node 2 (Code) 输出 | 不含任何分类字段。关键词 Topics 优先、Description 次之。 |
| **ProjectClassified** | 完成语义分类的项目对象。继承 ProjectNormalized 全部字段，追加 `primary_category`, `secondary_categories` (0~3), `classification_confidence` (HIGH/MEDIUM/LOW), `classification_notes`。 | Node 3-1 (LLM) 输出 | `primary_category` 必须属于 Taxonomy 定义或特殊类别。Ignore 类别项目在此阶段 `pipeline_status` 变为 `FILTERED_BY_CATEGORY`。 |
| **ProjectScored** | 完成四维评分的项目对象。继承 ProjectClassified 全部字段，追加 `career_alignment` (0~40), `interest_match` (0~30), `trend_heat` (0~20), `research_relevance` (0~10), `total_score`, `reasoning`, `career_goal_impact`, `recommendation`。 | Node 3-3 (LLM) + Node 3-4 (Code) 输出 | `total_score` 必须严格等于四维之和。总分 < 40 时 `pipeline_status` 变为 `FILTERED_BY_SCORE`。 |
| **ProjectRanked** | 完成全局排序的日报就绪对象。继承 ProjectScored 全部字段，追加 `rank` (1~N), `ranking_group` (STRONG_RECOMMEND / RECOMMEND / OBSERVE / IGNORE)。 | Node 5 (Code) 输出 | `pipeline_status` 变为 `ARCHIVED`。排序键优先级: ranking_group → total_score → career_alignment → interest_match → project_id。 |

---

## 3. Data Flow Concepts (数据流概念)

描述数据如何在工作流中流转、演化和组织。

| 术语 | 定义 | 涉及文档 |
|------|------|----------|
| **Fat Object** | 工作流中始终流转的单一 Canonical Object。每个阶段仅追加字段，从不重新实例化。确保 `project_id` 贯穿全管线的数据血缘可追溯。 | `runtime_boundary_v1.md` P-05, `data_flow_v1.md` §4.1 |
| **Append Only** | 每阶段仅追加自有字段，不修改、不覆盖上游字段的变异规则。违反此规则将导致数据血缘断裂。由 R-02 强制执行。 | `runtime_boundary_v1.md` P-06, `data_flow_v1.md` §4.1 |
| **Batch Flow** | Node 3 (Iteration) 将 30 个项目展开为独立沙盒实例并行处理。异常项目自动脱落 (Drop)，存活项目经 Node 4 (Variable Aggregator) 收拢为 JSON Array 后进入全局处理。 | `data_flow_v1.md` §4.3, `node_mapping_v1.md` §4.3 |
| **Item Flow** | 单个项目在 Iteration 沙盒内依次经过 4 个子节点 (Classification → Validation I → Scoring → Validation II) 的串行处理路径。每项目独立，沙盒隔离。 | `node_mapping_v1.md` §4.3 |
| **Global Ingestion** | 运行时拓扑中的第一物理执行域。Node 1 (HTTP) + Node 2 (Code) 以单实例串行模式执行数据采集与初始化。 | `runtime_architecture_overview_v1.md` §2 |
| **Global Output** | 运行时拓扑中的第三物理执行域。Node 4 (Variable Aggregator) + Node 5 (Code) + Node 6 (Template) 以单实例串行模式执行收拢、排序、渲染。 | `runtime_architecture_overview_v1.md` §2 |
| **Iteration Sandbox** | Node 3 (Iteration) 为每项目分配的隔离执行环境。沙盒内异常不影响其他沙盒。最大并发度 = 30。 | `node_mapping_v1.md` §4.3 |

---

## 4. Architecture & Control (架构与控制)

描述运行时架构中的控制机制、边界概念和策略。

| 术语 | 定义 | 涉及节点 / 文档 |
|------|------|-----------------|
| **Runtime Boundary** | 每一 Pipeline Stage 与运行时组件 (HTTP / LLM / Code / Template / Adapter) 之间的职责划分决策。定义"谁负责什么"。 | `runtime_boundary_v1.md` |
| **Node Mapping** | 业务 Pipeline Stage 到具体 Dify 物理节点类型的映射关系。定义"用哪个 Dify 节点实现"。 | `node_mapping_v1.md` |
| **Validation Gate** | 每 LLM 节点后串联的 Code Node，负责断言 LLM 输出符合 IO Contract。断言失败时项目标记为 SKIPPED 并脱落。遵循 R-01 (Validation Isolation)。 | `data_flow_v1.md` §4.5, Node 3-2 / 3-4 |
| **Storage Adapter** | 接收 Workflow 最终 Markdown 输出并决定持久化方式的外部 Python 服务。Workflow 通过 HTTP POST 推送，不感知存储后端。遵循 P-04。 | `runtime_boundary_v1.md` §4.8, `deployment_v1.md` §4.4 |
| **Drop** | 项目级故障处理动作。单项目在 Iteration 沙盒内触发确定性异常时立即脱落，标记为 SKIPPED 或 FAILED，不影响同批次其他项目。遵循 MD-01 / R-03。 | `failure_handling_v1.md` §4.2, Node 3-2 / 3-4 |
| **Abort** | 工作流级故障处理动作。致命异常 (数据源不可达、存储不可达) 时终止整个 Workflow，保留上次成功数据作为 Fallback。 | `failure_handling_v1.md` §4.3 |
| **Fallback** | 工作流级故障后的降级策略。GitHub 不可达时使用上次成功数据生成日报；存储不可达时保留内容在 Workflow 变量中人工恢复。 | `failure_handling_v1.md` §4.3.3 |
| **Retry** | 可恢复故障的自动重试机制。HTTP 请求最多重试 3 次 (间隔 5s)。LLM 超时不重试 (直接 Drop)。 | `failure_handling_v1.md` §4.4 |
| **pipeline_status** | 贯穿全管线的生命周期字段。允许转换路径: PROMOTED (初始) → FILTERED_BY_CATEGORY (分类淘汰) / FILTERED_BY_SCORE (评分淘汰) → ARCHIVED (终态)。 | `data_flow_v1.md` §4.2 |

---

## 5. Related Documents

| Document | Relationship |
|----------|--------------|
| `data_flow_v1.md` | Data States 定义来源。Fat Object, Append Only, Batch Flow 在此文档中完整描述。 |
| `node_mapping_v1.md` | Node Mapping, Iteration Sandbox 定义来源。 |
| `failure_handling_v1.md` | Drop, Abort, Fallback, Retry 的完整策略定义来源。 |
| `runtime_boundary_v1.md` | Runtime Boundary, Storage Adapter, P-05/P-06 原则来源。 |
| `runtime_architecture_overview_v1.md` | Global Ingestion, Global Output 拓扑域定义来源。 |
| `node_io_contract_v1.md` | IO Contract, Validation Gate 的字段级约束来源。 |

---

## 6. Version History

| Version | Date | Author | Change Summary |
|---------|------|--------|----------------|
| v1 | 2026-07 | PKIA MVP Agent | Initial release. 17 terms across 3 categories: Data States (5), Data Flow Concepts (7), Architecture & Control (8). All definitions sourced from existing Runtime documents. |
