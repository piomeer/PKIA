# PKIA Node IO Contract v1

> **Document Type**: Design Decision
> **Status**: Approved
> **Last Updated**: 2026-07
> **Namespace**: pkia_mvp

---

## 1. Purpose

本文档定义 PKIA MVP v0.1 运行时架构中每个 Dify 节点的输入/输出数据契约（IO Contract）。它规定了节点之间数据交换的 Schema 约束、类型要求与职责边界。

本文档回答：

> **每个节点的输入和输出长什么样？**

数据的流转机制（如何流动）由 `data_flow_v1.md` 负责，节点类型（用什么节点实现）由 `node_mapping_v1.md` 负责。

---

## 2. Scope

### 2.1 In Scope

- 每节点的输入类型与输出类型
- 字段级约束：必填、类型、范围
- 节点职责边界：Allowed / Forbidden 矩阵
- 契约违反的处理规则

### 2.2 Out of Scope

- 字段含义与所有权（参见 `project_data_schema_v1.md`）
- 数据流转与演化（参见 `data_flow_v1.md`）
- 节点类型与拓扑（参见 `node_mapping_v1.md`）

---

## 3. Design Principles

本文档遵循 `runtime_boundary_v1.md` 的 P-01~P-06 原则。IO 契约的核心约束来自 `project_data_schema_v1.md` (frozen) 的字段定义。

---

## 4. Main Design

### 4.1 IO Contract Matrix

| 物理节点 | 输入类型 | 输出类型 | 契约约束 |
|----------|----------|----------|----------|
| Node 1 (Collector) | None (Trigger / Timer) | string (HTML) | 必须包含有效的 HTML 结构。HTTP 状态码必须为 200。 |
| Node 2 (Normalizer) | string (HTML) | Array\<ProjectRaw\> | size ≤ 30。每项必须含 `project_id`、`project_name`、`source`、`collection_date`。 |
| Node 3-1 (Classifier) | ProjectRaw | ProjectClassified | 输出必须为合法 JSON。含 `primary_category`、`classification_confidence` ∈ {HIGH, MEDIUM, LOW}。 |
| Node 3-2 (Validation I) | ProjectClassified | ProjectClassified (pass) / Drop (fail) | 通过则透传原对象。失败则记录日志并脱落。 |
| Node 3-3 (Scorer) | ProjectClassified | ProjectScored | 输出必须含 4 维度 integer 评分、`reasoning` (非空 string)、`career_goal_impact` (4 子字段已赋值)。 |
| Node 3-4 (Calc + Valid II) | ProjectScored | ProjectScored (pass) / Drop (fail) | `total_score` 必须严格等于四维之和。`recommendation` 必须为合法枚举值。 |
| Node 4 (Aggregator) | ProjectScored (per item) | Array\<ProjectScored\> | 仅聚合 `pipeline_status = PROMOTED` 的项目。不保证输出顺序 (R-05)。 |
| Node 5 (Ranker) | Array\<ProjectScored\> | Array\<ProjectRanked\> | 每项必须带 `ranking_group` 与 `rank` (1~N)。 |
| Node 6 (Template) | Array\<ProjectRanked\> | string (Markdown) | 必须为合法 UTF-8 Markdown。6 章节结构完整。 |
| Node 7 (Storage) | string (Markdown) | HTTP Response | HTTP POST payload 为 Markdown 文本。Content-Type: text/markdown。 |

### 4.2 字段级契约 (Field-Level Contract)

以下字段在 IO 传递中必须满足的约束：

#### 4.2.1 全局标识字段 (所有阶段)

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| `project_id` | string | 是 | 生成后永不修改。格式: `{prefix}-{date}-{name}`。全局唯一。 |
| `pipeline_status` | string (enum) | 是 | 允许值: PROMOTED, FILTERED_BY_CATEGORY, FILTERED_BY_SCORE, ARCHIVED |
| `source` | string (enum) | 是 | v0.1 仅允许: `github_trending` |
| `collection_date` | date | 是 | 格式: YYYY-MM-DD |

#### 4.2.2 Classification 输出字段

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| `primary_category` | string | 是 | 必须是 Taxonomy Level-2 类别或特殊类别之一 |
| `secondary_categories` | list[string] | 否 | 0~3 个，每项必须是 Taxonomy 标准类别名 |
| `classification_confidence` | string (enum) | 是 | 仅允许: `HIGH`, `MEDIUM`, `LOW` |
| `classification_notes` | string | 否 | Confidence = LOW 时必填 |

#### 4.2.3 Scoring 输出字段

| 字段 | 类型 | 范围 | 必填 |
|------|------|------|------|
| `career_alignment` | integer | 0~40 | 是 |
| `interest_match` | integer | 0~30 | 是 |
| `trend_heat` | integer | 0~20 | 是 |
| `research_relevance` | integer | 0~10 | 是 |
| `total_score` | integer | 0~100 | 是 |
| `recommendation` | string (enum) | STRONG_RECOMMEND / RECOMMEND / OBSERVE / IGNORE | 是 |
| `reasoning` | string | — | 是，非空 |
| `career_goal_impact` | object | 4 sub-fields | 是，每子字段均为 HIGH / MEDIUM / LOW |

#### 4.2.4 Ranking 输出字段

| 字段 | 类型 | 范围 | 必填 |
|------|------|------|------|
| `rank` | integer | 1~N | 是 |
| `ranking_group` | string (enum) | STRONG_RECOMMEND / RECOMMEND / OBSERVE / IGNORE | 是 |

### 4.3 职责边界矩阵 (Responsibility Matrix)

每个节点的 Allowed / Forbidden 边界：

| 物理节点 | Allowed | Forbidden |
|----------|---------|-----------|
| Node 2 (Normalizer) | DOM 解析, 字符截断 (≤200), 语言归一化, 关键词提取 (≤5) | 过滤/丢弃项目, 发起网络请求, 修改 project_id |
| Node 3-2 (Validation I) | JSON 格式校验, 枚举值检查, 必填字段检查, 类型检查 | 篡改 LLM 原始输出文本, 重新发起 LLM 请求, 变更 primary_category |
| Node 3-4 (Calc + Valid II) | `total_score` 求和, `recommendation` 阈值映射, 格式校验 | 修改 `primary_category`, 修改 LLM 评分原始值, 重算评分 |
| Node 5 (Ranker) | 数组排序 (定义 §4.6), 数组分组, 排名序号赋值 | 重新计算得分, 修改项目属性, 过滤/丢弃项目 |
| Node 6 (Template) | 变量注入, Markdown 排版, 条件展示 (if/else) | 重新排序, 业务打分计算, 过滤丢弃项目, 发起 HTTP 请求 |

### 4.4 契约违反处理

当节点输出不符合契约时：

| 违反类型 | 处理方式 | 所属文档 |
|----------|----------|----------|
| JSON 格式错误 | Validation Gate 捕获 → Drop (SKIPPED) | `data_flow_v1.md` §4.5 |
| 必填字段缺失 | Validation Gate 捕获 → Drop (SKIPPED) | `data_flow_v1.md` §4.5 |
| 枚举值非法 | Validation Gate 修正为保守默认值（如 LOW）或 Drop | `data_flow_v1.md` §4.5 |
| 字段越界 | Validation Gate 截断到合法范围 + WARNING 日志 | `data_flow_v1.md` §4.5 |
| 网络级失败（HTTP 超时） | 重试策略 → `failure_handling_v1.md` | `failure_handling_v1.md` |

---

## 5. Runtime Rules

| Rule | Title | Application |
|------|-------|-------------|
| R-01 | Validation Isolation | 所有 LLM 输出经过 Validation Gate 后流转 (§4.1, §4.4) |
| R-05 | Aggregator Anarchy | Node 4 不保证顺序；Node 5 不依赖输入顺序 (§4.1) |

---

## 6. Related Documents

| Document | Relationship |
|----------|--------------|
| `project_data_schema_v1.md` | 定义所有字段的完整 Schema。本文档的字段级契约直接引用此文档的定义。 |
| `data_flow_v1.md` | 定义数据流转与 Validation Gate 的断言逻辑。本文档定义契约标准，data_flow 定义执行机制。 |
| `node_mapping_v1.md` | 定义节点编号与类型。本文档的 IO 契约对应其节点映射。 |
| `failure_handling_v1.md` | 定义契约违反后的重试、超时、降级策略。 |

---

## 7. Version History

| Version | Date | Author | Change Summary |
|---------|------|--------|----------------|
| v1 | 2026-07 | PKIA MVP Agent | Initial release. IO Contract matrix, field-level constraints, Responsibility matrix, contract violation handling. Refactored from `runtime_architecture_and_node_mapping_specification_v1.md`. |

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
