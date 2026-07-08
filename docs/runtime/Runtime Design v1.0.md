# PKIA Runtime Design v1.0

> **Document Status**: Superseded
> **Superseded By**: `runtime_boundary_v1.md`
> **Last Updated**: 2026-07
> **Namespace**: pkia_mvp

---

## 1. Purpose

本文记录 PKIA MVP Runtime Architecture 设计阶段中关于 **Runtime Boundary（运行时边界）** 的全部设计决策。

本章节仅回答一个问题：

> **每一种职责，最终应该由谁负责执行？**

即以下执行载体之间的职责划分：

- Dify Workflow
- Dify LLM Node
- Dify Code Node
- Dify HTTP Node
- Dify Template Node
- Python Adapter（如需要）
- 外部存储

本文属于 **Implementation Design**，而非 **Business Specification**。因此不修改任何已冻结文档（`pkia_v0.1_baseline.md` 定义的 13 份 Frozen 文档）。

---

## 2. Scope

### 2.1 In Scope

- Runtime 执行载体的职责划分
- 每个 Pipeline Stage 的 Runtime Owner 定义
- Validation、Retry、Configuration 等横切关注点的 Runtime 策略
- Storage Adapter Pattern 设计

### 2.2 Out of Scope

- 业务流程定义（参见 `scoring_pipeline_schema_v2.md` / `report_generation_pipeline_v1.md`）
- 数据结构定义（参见 `project_data_schema_v1.md`）
- Prompt 内容设计（参见 `classification_agent_spec_v1.md` / `prompt_scoring_agent_v2.md`）
- 部署架构（将在后续章节确定）
- Node Mapping（将在后续章节确定）

### 2.3 与 Baseline 的关系

本文档遵循 `pkia_v0.1_baseline.md` 锁定的实现范围：

- 唯一数据源：GitHub Trending
- 线性流水线：采集 → 归一化 → 分类 → 评分 → 排序 → 输出
- 实现载体：Dify Workflow 编排，Python 仅做 Dify 无法完成的能力
- 日报交付：Markdown（`pkia/reports/YYYY-MM-DD.md`）

---

## 3. Design Principles

Runtime 边界设计遵循以下原则：

### Principle 1: LLM 做推理

LLM Node 仅负责需要语义理解的职责：

- 项目分类
- 四维评分
- 自然语言理由生成

LLM 不负责：

- 排序
- 数据处理
- 字段拼装
- JSON 修正

### Principle 2: Code Node 做确定性逻辑

Code Node 负责所有可被规则描述的运算：

- 字段计算
- 排序
- 聚合
- Validation
- 数据转换

Code Node 不负责：

- 分类
- 评分
- 自然语言生成

### Principle 3: Template Node 做文本生成

Template Node 负责展示层渲染：

- Markdown 格式
- Prompt Assembly
- Report Rendering

Template Node 不负责：

- JSON 拼装
- 业务逻辑

### Principle 4: Workflow 负责流程

Workflow 层编排执行流程：

- Iteration
- Aggregation
- Retry
- Branch
- Error Handling

Workflow 不承担业务决策。

### Principle 5: Dify First, Python Minimal

默认原则：Dify 能完成的，绝不引入 Python。

```
Dify First
Python Minimal
```

Python 仅负责 Dify 无法完成的场景：

- HTML 解析（BeautifulSoup）
- 外部服务通信

Python 不承担任何业务逻辑。

---

## 4. Main Content

### 4.1 Runtime Boundary Overview

| 模块 | Pipeline Stage | Runtime Owner | Status |
|------|---------------|---------------|--------|
| Collector | Stage 1 | HTTP Node + Code Node（待验证） / Python Adapter（备选） | Pending |
| Normalizer | Stage 2 | Code Node | ✅ |
| Classification | Stage 3 | LLM Node | ✅ |
| Classification Validation | Stage 3 | Code Node | ✅ |
| Scoring | Stage 4~9 | LLM Node | ✅ |
| Score Aggregation | Stage 8 | Code Node | ✅ |
| Recommendation | Stage 9 | Code Node | ✅ |
| Ranking | Stage 10 | Code Node（Iteration → Variable Aggregator） | ✅ |
| Markdown Rendering | Report | Template Node | ✅ |
| Storage | Post-Report | HTTP → Storage Adapter | ✅ |
| Validation | Cross-cutting | Code Node（每 LLM Node 后） | ✅ |
| Retry | Cross-cutting | Workflow | ✅ |
| Configuration | Cross-cutting | Start Variables / Environment Variables | ✅ |

---

### 4.2 Collector Boundary

**负责**：GitHub Trending 的 HTML 数据获取，转换为 Raw Project Object。

**输出**：Stage 1 Raw Project，符合 `project_data_schema_v1.md` §5。

**Runtime 候选方案**：

| 方案 | 载体 | 优势 | 劣势 |
|------|------|------|------|
| Candidate A | HTTP Node → Code Node | 全部保留在 Dify | HTML 解析能力受限 |
| Candidate B | Python Adapter → HTTP → JSON | BeautifulSoup 稳定 | 新增 Python 服务 |

**当前决策**：**Pending**。

需在 Node Mapping 阶段验证 Code Node 是否能稳定解析 GitHub Trending HTML。

- 可以 → Candidate A（HTTP → Code）
- 不可以 → Candidate B（Python Collector Adapter）

Python 仅负责 `HTML → JSON`，不承担任何业务逻辑。

---

### 4.3 Normalizer Boundary

**负责**：Stage 2 标准化处理。

- Description 清洗（≤200 字符截断）
- Language 规范化
- Keyword 提取（≤5 个，Topics 优先）

**输出**：`normalized_description`、`primary_language`、`extracted_keywords`，符合 `project_data_schema_v1.md` §6。

**决策**：**Code Node**。

理由：纯确定性转换，无需 LLM。

---

### 4.4 Classification Boundary

**负责**：Stage 3 项目分类。

**输入**：Normalized Project Object。

**输出**：

| 字段 | 类型 |
|------|------|
| `primary_category` | string（Taxonomy Level-2） |
| `secondary_categories` | list[string]（0~3） |
| `classification_confidence` | string（HIGH/MEDIUM/LOW） |
| `classification_notes` | string |

**决策**：

| 职责 | Runtime Owner |
|------|--------------|
| 分类推理 | **LLM Node** |
| 输出 Validation | **Code Node**（紧随 LLM Node 之后） |

理由：分类属于语义推理，不适合规则引擎。

Code Node 负责验证：
- JSON Parse 是否成功
- `primary_category` 是否属于 Taxonomy 定义
- `classification_confidence` 是否为有效枚举值
- 必填字段是否完整

---

### 4.5 Scoring Boundary

**负责**：Stage 4~9 四维评分。

包括：

- Career Alignment（0~40）
- Interest Match（0~30）
- Trend Heat（0~20）
- Research Relevance（0~10）
- `reasoning`（评分说明）
- `career_goal_impact`（职业目标影响）

**决策**：

| 职责 | Runtime Owner |
|------|--------------|
| 四维评分推理 | **LLM Node** |
| `total_score` 计算 | **Code Node**（严格求和） |
| `recommendation` 映射 | **Code Node**（阈值表） |
| 评分 Validation | **Code Node**（紧随 LLM Node） |

理由：四维评分属于复杂语义判断，需要 LLM 理解项目 Description、分类和用户兴趣画像的关系。确定性计算（求和、阈值映射）由 Code Node 完成。

---

### 4.6 Ranking Boundary

**负责**：Stage 10 Batch 排序。

**输入**：30 个已完成评分的项目。

**输出**：`rank`（1~30）、`ranking_group`（按 recommendation 分组）。

**决策演变**：

- 旧方案：Python 独立脚本
- **当前决策**：全部保留在 Dify

**Runtime 方案**：

```
Iteration → Variable Aggregator → Code Node
```

Code Node 接收 JSON Array，执行：

1. 一级排序：`ranking_group`（Strong Recommend > Recommend > Observe > Ignore）
2. 二级排序：`total_score`（降序）
3. 三级排序：`career_alignment`（降序）
4. 四级排序：`interest_match`（降序）

无需 Python。

---

### 4.7 Report Generation Boundary

**负责**：将排序结果渲染为 Markdown 日报。

**输出**：`pkia/reports/YYYY-MM-DD.md`，6 章节格式。

**决策演变**：

- 旧方案：Python 字符串拼接
- **当前决策**：**Template Node**

理由：Template Node 使用 Jinja2 语法，比 Python 字符串拼接更易维护。Template Node 的职责与 Principle 3（Template Node 做文本生成）完全一致。

**注意事项**：

- 模板需包含 6 个章节的完整格式定义
- 需处理空结果场景（Section B 无 Strong Recommend 等）
- 最终渲染前需验证模板变量完整性

---

### 4.8 Storage Boundary

**原则**：Workflow 永远不知道最终存储在哪里。

**架构**：**Storage Adapter Pattern**。

```
Workflow
    ↓ (HTTP POST)
Storage Adapter
    ↓
[Markdown | SQLite | Memory | OSS...]
```

**职责分离**：

| 层 | 职责 |
|----|------|
| Dify Workflow | 发送最终日报内容 |
| Storage Adapter | 决定持久化方式和存储位置 |

**优势**：

- 未来从 Markdown 切换为 SQLite，无需修改 Workflow
- Adapter 独立于 Pipeline，可独立测试
- 存储策略变更不影响业务逻辑

**当前 v0.1 选择**：Markdown 文件（`pkia/reports/`），通过 Adapter 模式封装。

---

### 4.9 Validation Boundary

LLM 不能保证 100% 输出格式合法。因此每个 LLM Node 后必须紧跟 Validation Code Node。

**执行流程**：

```
LLM Node
    ↓
Validation Code Node
    ↓
[PASS] → Next Stage
[FAIL] → Retry / Fallback / Ignore
```

**Validation 职责**：

- JSON Parse 成功性检查
- 必填字段完整性（`project_id`, `primary_category`, `total_score` 等）
- 枚举值合法性（`classification_confidence` ∈ {HIGH, MEDIUM, LOW} 等）
- 字段类型检查（`stars` 为 integer，`career_alignment` 在 0~40）
- Schema 结构性检查

**失败处理**：

| 失败等级 | 处理方式 |
|----------|----------|
| JSON Parse 失败 | Retry（最多 3 次） |
| 必填字段缺失 | Retry → 标记为 `INVALID` |
| 枚举值非法 | 修正为合理默认值（如 `LOW`） |
| 字段越界 | 截断到合法范围 |

---

### 4.10 Retry Boundary

Runtime 必须定义 Retry 策略：

| 组件 | 策略 |
|------|------|
| HTTP 调用 | Retry = 3，Interval = 5s |
| LLM Node | Timeout 设置 + Fallback |
| Validation 失败 | Retry → 单项目标记失败（不阻断 Batch） |

**核心约束**：一个项目的失败不阻断整个 Batch 的处理。

---

### 4.11 Configuration Boundary

所有 Magic Numbers 移出 Prompt 和 Code，统一管理。

| 配置项 | 类型 | 默认值 | 位置 |
|--------|------|--------|------|
| `TOP_N` | integer | 30 | Start Variables |
| `RECOMMEND_THRESHOLD_STRONG` | integer | 90 | Start Variables |
| `RECOMMEND_THRESHOLD_RECOMMEND` | integer | 70 | Start Variables |
| `RECOMMEND_THRESHOLD_OBSERVE` | integer | 40 | Start Variables |
| `COLLECTION_TIME` | string | "00:00 UTC" | Environment Variables |
| `RETRY_MAX` | integer | 3 | Workflow Variable |
| `RETRY_INTERVAL_SEC` | integer | 5 | Workflow Variable |

Workflow 读取配置，不允许硬编码。

---

## 5. Design Notes

### N-01: Collector 方案与 Baseline 的关系

`pkia_v0.1_baseline.md` §6.2 指出"数据采集: Python 独立脚本"。本文档将此作为 Candidate B 保留，同时提出 Candidate A（HTTP + Code Node）供验证。两者均兼容 Baseline，最终选择取决于 Code Node 的 HTML 解析能力验证结果。

### N-02: Ranking 实现方式的变更

此前 Phase 1 建议方案（`progress/pkia_mvp.md` Next Steps）隐含 Ranking 由 Python 脚本完成。本文档基于 Dify Variable Aggregator 的分析，将 Ranking 判定为 Dify Code Node 可独立完成。此变更属于实现层优化，不违反任何冻结文档的定义。

### N-03: Template Node 替代 Python 字符串拼接

此前 Phase 1 建议方案隐含 Report Generation 由 Python 完成。本文档改为 Dify Template Node（Jinja2）。Template Node 在 `report_generation_pipeline_v1.md` 定义的 7 阶段逻辑和 `daily_report_spec_v1.md` 定义的 6 章节格式范围内自由实现，因而不违反冻结文档。若 Template Node 能力不足以满足复杂 Markdown 排版，则回退为 Code Node Rendering。

### N-04: Storage Adapter Pattern 不属于任何冻结文档

Storage Adapter 是本文档新增的运行时架构概念，不属于 `pkia_v0.1_baseline.md` 定义的 13 份冻结文档范围。它不修改任何业务规范，仅定义实现层的持久化策略，因此不需要冻结文档更新。

---

## 6. Future Considerations

### Phase 2 可能影响 Runtime 的因素

| 因素 | 可能的影响 |
|------|-----------|
| Arxiv 数据源接入 | Collector 可能需要第二个 Adapter（Arxiv API） |
| Web UI 日报展示 | Storage Adapter 需要增加 SQLite/DB 输出 |
| User Feedback Learning | 需要 Interest Profile 的在线更新能力，可能引入 Feedback Node |
| Multi-Source 聚合 | Ranking 需要跨源统一排序，Aggregator 逻辑需要扩展 |
| Memory Ecosystem 集成 | Storage Adapter 可能需要增加 L2 写入接口 |

### Open Questions

以下问题留待 Node Mapping 章节确定：

| ID | 问题 | 影响 |
|----|------|------|
| OQ-1 | Code Node 是否足以解析 GitHub Trending HTML？ | 决定 Collector 方案（A vs B） |
| OQ-2 | Variable Aggregator 是否保证 Iteration 输出顺序？ | 若否，Ranking 需增加 Index Restore |
| OQ-3 | Template Node 是否满足复杂 Markdown 排版？ | 若否，Report 改为 Code Node Rendering |
| OQ-4 | Storage Adapter 采用 Webhook 还是 REST API？ | 待 Deployment 章节确定 |

---

## 7. Related Documents

| Document | Relationship |
|----------|-------------|
| `pkia_v0.1_baseline.md` | 锁定实现范围和载体约束。本文档在 Baseline 范围内实施。 |
| `project_data_schema_v1.md` | 定义所有 Stage 的数据结构。Runtime Boundary 的每个模块输出遵循此 Schema。 |
| `scoring_pipeline_schema_v2.md` | 定义 10 阶段 Pipeline。本文档的每个模块对应 Pipeline 的特定 Stage。 |
| `report_generation_pipeline_v1.md` | 定义 7 阶段报告生成。本文档的 Report Generation 边界遵循此定义。 |
| `daily_report_spec_v1.md` | 定义 6 章节日报格式。Template Node 的输出目标。 |
| `data_collection_strategy_v1.md` | 定义数据采集策略（GitHub Trending Top 30）。Collector 边界的设计输入。 |
| `classification_agent_spec_v1.md` | 定义分类 Agent 行为。LLM Node 的 Prompt 来源。 |
| `prompt_scoring_agent_v2.md` | 定义评分 Agent v2 Prompt。LLM Node 的评分指令来源。 |
| `workflow_v0.1_design.md` | Dify Workflow 设计草稿。本文档的 Runtime 方案以此为出发点。 |
| `classification_agent_spec_v1.md` | 定义分类 Agent 行为。LLM Node 的 Prompt 来源。 |

---

*End of Runtime Design v1.0 — Chapter 2: Runtime Boundary*
