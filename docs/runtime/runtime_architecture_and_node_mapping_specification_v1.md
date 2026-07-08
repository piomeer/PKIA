# PKIA Runtime Architecture & Node Mapping Specification v1

> **Document Type**: Design Decision
> **Status**: Superseded
> **Superseded By**: `runtime_architecture_overview_v1.md`, `node_mapping_v1.md`, `data_flow_v1.md`, `node_io_contract_v1.md`, `failure_handling_v1.md`, `deployment_v1.md`
> **Last Updated**: 2026-07
> **Namespace**: pkia_mvp

---

## 1. Purpose

本规范定义了 PKIA MVP 从业务逻辑向 Dify 原生运行时架构的物理映射。本规范不仅规定了节点拓扑，还严格界定了数据契约、职责边界与可观测性指标，确保系统的确定性与高可用性。

本文档在 Runtime 文档层次中同时承担两个角色：

- **Runtime Architecture Overview** — 描述运行时架构的物理域划分与拓扑结构
- **Node Mapping** — 将每个 Pipeline Stage 映射到具体的 Dify 节点类型与职责边界

职责划分（谁负责什么）的完整定义参见 `runtime_boundary_v1.md`。

---

## 2. Scope

### 2.1 In Scope

- 运行时拓扑结构：三个物理执行域
- 物理节点映射：业务 Pipeline Stage 到 Dify 节点的对应关系
- 节点 IO 契约：输入/输出的 Schema 约束
- 职责边界：各节点的 Allowed / Forbidden 矩阵
- 运行时状态机：全局工作流与单项目生命周期
- 可观测性指标与日志规范

### 2.2 Out of Scope

- 业务流程定义（参见 `scoring_pipeline_schema_v2.md`, `report_generation_pipeline_v1.md`）
- 数据结构定义（参见 `project_data_schema_v1.md`）
- Prompt 内容设计（参见 `classification_agent_spec_v1.md`, `prompt_scoring_agent_v2.md`）
- 部署架构与定时调度（参见 `deployment_v1.md`）
- 失败处理与降级策略（参见 `failure_handling_v1.md`）

---

## 3. Design Principles

本架构遵循 `runtime_boundary_v1.md` §3 定义的 6 项原则：

| ID | Principle | Application |
|----|-----------|-------------|
| P-01 | Dify First | 全部 7 个物理节点均为 Dify 内置节点类型 |
| P-02 | Python Minimal | 无 Python 运行时依赖。HTML 解析由 Code Node 完成 |
| P-03 | Workflow SSOT | 拓扑结构与节点配置以 Dify 导出 `.yml` 为准 |
| P-04 | Storage Adapter | Node 7 通过 HTTP 解耦，不感知存储后端 |
| P-05 | Fat Object | 单 Canonical Object 贯穿全流程，逐阶段追加字段 |
| P-06 | Append-Only Mutation | 各节点仅追加自有字段，不回溯修改上游字段 |

**新增架构原则：**

### P-07: Fail-Fast Isolation (R-03)

Iteration 内单项目触发确定性异常时立即脱落，不影响同批次其他项目。异常项目不重试、不阻塞。

### P-08: Unified Scoring

四维评分（Career Alignment, Interest Match, Trend Heat, Research Relevance）由单一 LLM 节点在单次调用中完成，不拆分四个独立 LLM 调用。

---

## 4. Main Content

### 4.1 Runtime Topology (运行时拓扑)

系统拓扑分为三个物理执行域：

```
┌──────────────────────────────────────────────────┐
│ 1. Global Ingestion (全局摄入)                     │
│    单实例执行，负责数据采集与初始化                  │
│    Node 1 (HTTP) → Node 2 (Code)                  │
└──────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────┐
│ 2. Batch Processing (并发迭代)                     │
│    Iteration 节点，最大并发度 30                    │
│    Node 3-1 (LLM) → Node 3-2 (Code)               │
│    → Node 3-3 (LLM) → Node 3-4 (Code)             │
│    沙盒隔离，异常自动脱落 (Fail-fast)               │
└──────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────┐
│ 3. Global Output (全局收拢)                        │
│    单实例执行，重组、排序、渲染、推送                │
│    Node 4 (Variable Aggregator) → Node 5 (Code)    │
│    → Node 6 (Template) → Node 7 (HTTP)            │
└──────────────────────────────────────────────────┘
```

### 4.2 Node Mapping (节点映射矩阵)

业务 Pipeline Stage 到物理 Dify 节点的映射：

| 物理节点 | 节点类型 | 映射 Pipeline Stage | 职责简述 |
|----------|----------|---------------------|----------|
| Node 1 | HTTP | Stage 1 (Collector) | 获取 GitHub Trending HTML |
| Node 2 | Code | Stage 1 (Extractor) + Stage 2 (Normalizer) | HTML 解析 → 字段提取 → Description 截断 → 关键词提取 |
| Node 3 | Iteration | — | Batch 控制器，最大并发 30 |
| Node 3-1 | LLM | Stage 3 (Classification) | 语义分类：Primary/Secondary Category + Confidence |
| Node 3-2 | Code | Stage 3 (Validation I) | Classification 输出校验 |
| Node 3-3 | LLM | Stage 4-7 (Unified Scoring) | 四维评分 + Reasoning + Career Goal Impact |
| Node 3-4 | Code | Stage 8-9 (Total Score + Recommendation) + Validation II | 分数求和 → 推荐等级映射 → 输出校验 |
| Node 4 | Variable Aggregator | — | 收拢存活项目为 JSON Array |
| Node 5 | Code | Stage 10 (Global Ranker) | 全局排序 + 分组 + 排名赋值 |
| Node 6 | Template | Report Generation Pipeline | Markdown 日报渲染 |
| Node 7 | HTTP | Storage Adapter | 推送渲染结果至外部存储 |

### 4.3 Node IO Contract (数据契约)

所有节点之间的数据流转必须严格遵守以下 Schema 契约。不符合契约的输入或输出应在当前节点直接触发异常。

| 物理节点 | 输入类型 | 输出类型 | 契约约束 |
|----------|----------|----------|----------|
| Node 1 (Collector) | None (Trigger) | string (HTML) | 必须包含有效的 HTML 结构 |
| Node 2 (Normalizer) | string (HTML) | Array\<ProjectRaw\> | size ≤ 30，每项必须含 `project_id` |
| Node 3-1 (Classifier) | ProjectRaw | ProjectClassified | 输出必须为合法 JSON，含 `primary_category`, `classification_confidence` |
| Node 3-3 (Scorer) | ProjectClassified | ProjectScored | 输出必须含 4 维度评分 + `reasoning` + `career_goal_impact` |
| Node 4 (Aggregator) | ProjectScored | Array\<ProjectScored\> | 仅聚合 pipeline_status = PROMOTED 的项目 |
| Node 5 (Ranker) | Array\<ProjectScored\> | Array\<ProjectRanked\> | 每项必须带 `ranking_group` 与 `rank` |
| Node 6 (Template) | Array\<ProjectRanked\> | string (Markdown) | 纯文本渲染，6 章节格式 |

### 4.4 Node Responsibility (职责边界)

为防止业务逻辑逃逸，各节点必须严格遵守 Allowed / Forbidden 边界。

| 物理节点 | Allowed (允许) | Forbidden (禁止) |
|----------|----------------|------------------|
| Node 2 (Normalizer) | DOM 解析, 字符截断, 语言归一化, 关键词提取 | 过滤/丢弃项目, 发起网络请求 |
| Node 3-2 (Validation I) | JSON 格式校验, 枚举值检查, 必填字段检查, 类型检查 | 篡改 LLM 原始输出文本, 重新发起 LLM 请求 |
| Node 3-4 (Validation II + Aggregation) | `total_score` 求和, `recommendation` 阈值映射, 格式校验 | 修改 `primary_category`, 修改 LLM 评分原始值 |
| Node 5 (Ranker) | 数组排序, 数组分组, 排名序号赋值 | 重新计算得分, 修改项目属性, 过滤项目 |
| Node 6 (Template) | 变量注入, Markdown 排版, 条件展示 | 重新排序, 业务打分计算, 过滤丢弃 |

### 4.5 Runtime State Machine (运行时状态)

工作流及单个 Project 的生命周期遵循严格的状态转移机制。

**全局工作流状态：**

```
TRIGGERED → RUNNING → SUCCESS | FAILED
```

**Iteration 内部单项目状态 (Project Lifecycle)：**

| 状态 | 说明 | 转移条件 |
|------|------|----------|
| PENDING | 进入 Iteration 队列等待执行 | Iteration 启动 |
| RUNNING | 正在被 LLM 或 Code 节点处理 | 节点开始执行 |
| SUCCESS | 顺利通过 Node 3-4 校验，等待聚合 | Validation 通过 |
| FAILED | 网络超时或节点内部崩溃，触发 R-03 | 确定性异常 |
| SKIPPED | 未通过 Validation（如 JSON 彻底损坏），触发 Fail-fast 丢弃 | Validation 失败且不可修复 |

仅状态为 `SUCCESS` 的项目进入 Node 4 (Variable Aggregator)。`FAILED` 和 `SKIPPED` 项目自动脱落，不影响同批次其他项目。

### 4.6 Runtime Metrics (监控指标)

各节点需向系统日志抛出关键运行时指标。

| 观测域 | 核心指标 | 采集节点 |
|--------|----------|----------|
| 采集健康度 | `projects_collected` (0-30), `github_latency_ms` | Node 1, Node 2 |
| 大模型消耗 | `classification_token_usage`, `scoring_token_usage`, `llm_latency_ms` | Node 3-1, Node 3-3 |
| 数据质量 | `validation_failed_count`, `projects_dropped_count` | Node 3-2, Node 3-4 |
| 产出统计 | `strong_recommend_count`, `total_ranked_items` | Node 5 |

### 4.7 Logging Strategy (日志边界)

系统需在关键边界实施结构化日志打印，禁止输出无意义调试信息。

**INFO (正常流程节点)：**

| 节点 | 日志内容 |
|------|----------|
| Node 2 结束 | `Top N projects extracted successfully.` |
| Node 5 结束 | `Ranking completed. N items ranked into A/B/C/D groups.` |
| Node 7 结束 | `Markdown output pushed to Storage Adapter.` |

**WARNING (非致命异常)：**

| 场景 | 日志内容 |
|------|----------|
| Node 3-2 / 3-4 项目丢弃 | `Project dropped. reason=<reason>. project_id=<id>.` |
| Node 1 重试 | `GitHub fetch retry triggered. attempt=N.` |

**ERROR (致命异常 — 阻断流程)：**

| 场景 | 日志内容 |
|------|----------|
| Node 1 源不可达 | `GitHub source unavailable (HTTP <code>). Workflow aborted.` |
| Node 7 存储不可达 | `Storage Adapter unreachable. Output rendering failed.` |

### 4.8 Runtime Sequence (执行时序)

1. 每日定时触发 **Node 1 (HTTP)** 获取 GitHub Trending HTML
2. **Node 2 (Code)** 执行 HTML 解析与字段规整，产出 30 个 `RawProject` 对象
3. **Node 3 (Iteration)** 展开 Batch，并发执行：
   - Node 3-1 (LLM): 项目分类
   - Node 3-2 (Code): Classification 校验（R-01）
   - Node 3-3 (LLM): 四维统一评分
   - Node 3-4 (Code): `total_score` 计算 + `recommendation` 映射 + 校验
   - 单项目失败时自动脱落（R-03），不影响其他项目
4. **Node 4 (Variable Aggregator)** 自动聚合所有 `SUCCESS` 项目
5. **Node 5 (Code)** 实施全局权重排序与分组（R-05）
6. **Node 6 (Template)** 渲染 6 章节 Markdown 日报
7. **Node 7 (HTTP)** 推送渲染结果至 Storage Adapter，生命周期结束

---

## 5. Design Notes

### N-01: 文档合并说明

本文档合并了 `runtime_document_style_guide_v1.md` §2.2 中规划的 `runtime_architecture_overview_v1.md` 和 `node_mapping_v1.md` 两个文档的职责。作为 Phase 1 的初始 Runtime 设计，合并有利于保持拓扑与节点映射的一致性。后续如有需要可拆分为独立文档。

### N-02: Runtime Config 状态

本文档 §10 将 Runtime Config 列为"未来扩展"，但 `runtime_boundary_v1.md` §4.10 已将 Configuration 作为已决策的运行时层纳入。`TOP_N`、`RECOMMEND_THRESHOLD_*` 等参数已通过 Workflow Start Variables 实现，不属于未来工作。本文档保留原文表述，实际实现以 `runtime_boundary_v1.md` 的已决决策为准。

### N-03: Python Minimal 原则的落地

本文档与 `runtime_boundary_v1.md` 保持一致：HTML 解析由 Code Node 完成（P-02），无 Python 运行时依赖。Collector 的 HTML 解析方案已在 `runtime_boundary_v1.md` 中标记为 Code Node 优先，仅解析稳定性待验证。

### N-04: Unified Scoring 与 Scoring Pipeline 的一致性

`scoring_pipeline_schema_v2.md` (frozen) 将四维评分定义为 Stage 4-7（四个独立子步骤），本文档将其合并为单一 LLM 调用（Node 3-3）。此合并属于实现层优化——四个评分维度在一次 LLM 推理中完成，不改变评分逻辑、权重或字段定义。冻结文档的业务定义不受影响。

### N-05: 拓扑与 Baseline 实现载体的一致性

`pkia_v0.1_baseline.md` §6.2 (frozen) 指出实现载体为 "Python 脚本采集 + Dify Workflow 处理"。本文档的拓扑结构已将 Collector 纳入 Dify Workflow（HTTP Node + Code Node），仅在 HTML 解析方案待验证时保留 Python Adapter 备选。此演进方向与 Baseline "Dify Workflow 处理" 的总体方针一致。

---

## 6. Future Considerations

### Runtime Config (配置下发)

未来 `TOP_N`、`MIN_SCORE_THRESHOLD` 等运行时参数可通过环境变量 (ENV) 统一注入，而非硬编码在 Code Node 逻辑中。

> **NOTE**: `runtime_boundary_v1.md` §4.10 已将 Configuration 作为已决设计纳入。此处的"未来"指参数来源的集中化管理（如外部配置中心），而非配置能力本身。

### Storage Adapter (存储适配)

目前 Node 7 指向 Markdown 文件接收器。未来如需接入 SQLite 或 VectorDB，只需修改外部 Python 接收器的路由逻辑，Dify Workflow 本体无需任何改动（P-04: Storage Adapter Pattern）。

### Memory Gateway

未来 Memory Governor 接入时，将作为独立的 API 提供方，在 Iteration 内部由额外的 HTTP Node 实施非阻塞调用。此扩展点不改变现有节点拓扑，仅新增可选节点。

---

## 7. Related Documents

| Document | Relationship |
|----------|--------------|
| `runtime_document_style_guide_v1.md` | 定义本文档的写作标准与 Runtime 文档层次 |
| `runtime_boundary_v1.md` | 定义每个 Pipeline Stage 的 Runtime Owner。本文档的节点映射以此为上游输入。 |
| `pkia_v0.1_baseline.md` | Frozen baseline。锁定实现范围与载体约束。 |
| `project_data_schema_v1.md` | 数据契约。本文档 Node IO Contract 的字段定义来源。 |
| `scoring_pipeline_schema_v2.md` | 定义 10 阶段 Pipeline。本文档的节点映射覆盖全部 Stage。 |
| `report_generation_pipeline_v1.md` | 定义 7 阶段报告生成。Node 6 (Template) 的输出逻辑遵循此文档。 |
| `daily_report_spec_v1.md` | 定义 6 章节日报格式。Template Node 的输出格式目标。 |
| `data_collection_strategy_v1.md` | 定义数据采集策略。Node 1 / Node 2 的设计输入。 |
| `classification_agent_spec_v1.md` | 分类 Prompt。Node 3-1 的 LLM 指令来源。 |
| `prompt_scoring_agent_v2.md` | 评分 Prompt。Node 3-3 的 LLM 指令来源。 |
| `failure_handling_v1.md` | 失败处理策略。Node 3-2 / 3-4 的 Validation 逻辑遵守此文档。 |

---

## 8. Version History

| Version | Date | Author | Change Summary |
|---------|------|--------|----------------|
| v1 | 2026-07 | PKIA MVP Agent | Initial release. Defines 3-domain topology, 7-node mapping matrix, IO contracts, state machine, metrics, and logging strategy. |
