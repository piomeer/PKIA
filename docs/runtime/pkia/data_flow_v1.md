# PKIA Data Flow v1

> **Document Type**: Design Decision
> **Status**: Approved
> **Last Updated**: 2026-07
> **Namespace**: pkia_mvp

---

## 1. Purpose

本文档定义 PKIA MVP v0.1 运行时中的数据流转规则。它描述一个项目从原始 HTML 到最终日报的完整演化路径，以及数据在 Dify Workflow 各节点间的传递机制。

本文档回答：

> **数据如何流动、如何演化、如何在节点间传递？**

---

## 2. Scope

### 2.1 In Scope

- Fat Object 演化模型：各阶段的对象结构与字段追加规则
- 业务状态机：pipeline_status 生命周期
- Batch Flow 展开与聚合机制
- Variable Flow：运行时变量定义与传递
- Validation Gate：断言拦截逻辑

### 2.2 Out of Scope

- 节点类型与职责（参见 `node_mapping_v1.md`）
- 节点输入/输出 Schema 的字段级定义（参见 `node_io_contract_v1.md`）
- 故障处理策略（参见 `failure_handling_v1.md`）

---

## 3. Design Principles

本文档继承 `runtime_boundary_v1.md` 的 P-01~P-06 原则。以下原则在 Data Flow 层面有直接体现：

| Principle | Data Flow 体现 |
|-----------|----------------|
| P-05 (Fat Object) | 单一 Canonical Object 贯穿全流程，逐阶段追加字段 |
| P-06 (Append-Only Mutation) | 每阶段仅追加自有字段，不回溯修改上游字段 |
| R-02 (Append-Only Object) | 禁止重新实例化对象，禁止静默覆盖已有字段 |

---

## 4. Main Design

### 4.1 Fat Object 演化模型

PKIA 使用单一 Canonical Project Object 贯穿全部 6 个 Schema Stage。每个阶段仅追加字段，不修改上游字段。

```
Stage 1: RawProject
┌─────────────────────────────────────────────────┐
│ project_id, project_name, owner, description,   │
│ topics, stars, forks, language, source,         │
│ collection_date, pipeline_status                │
└─────────────────────────────────────────────────┘
        │ 追加
        ▼
Stage 2: NormalizedProject (继承 Stage 1 全部字段 +)
┌─────────────────────────────────────────────────┐
│ normalized_description, primary_language,        │
│ extracted_keywords                               │
└─────────────────────────────────────────────────┘
        │ 追加
        ▼
Stage 3: ClassifiedProject (继承 Stage 2 全部字段 +)
┌─────────────────────────────────────────────────┐
│ primary_category, secondary_categories,          │
│ classification_confidence, classification_notes  │
└─────────────────────────────────────────────────┘
        │ 追加
        ▼
Stage 4: ScoredProject (继承 Stage 3 全部字段 +)
┌─────────────────────────────────────────────────┐
│ career_alignment, interest_match, trend_heat,   │
│ research_relevance, total_score, reasoning,      │
│ career_goal_impact, recommendation,              │
│ pipeline_status (可能更新)                       │
└─────────────────────────────────────────────────┘
        │ 追加
        ▼
Stage 5: RankedProject (继承 Stage 4 全部字段 +)
┌─────────────────────────────────────────────────┐
│ rank, ranking_group,                             │
│ pipeline_status → ARCHIVED                      │
└─────────────────────────────────────────────────┘
        │ 追加
        ▼
Stage 6: ReportItem (继承 Stage 5 全部字段 +)
┌─────────────────────────────────────────────────┐
│ summary, recommended_read_time, daily_priority   │
└─────────────────────────────────────────────────┘
```

**核心约束**：
- 每阶段产生的字段由该阶段的 Runtime Owner 写入（见 `runtime_boundary_v1.md` §4.1）
- `project_id` 在 Stage 1 生成后永不修改
- `pipeline_status` 是唯一可被多个阶段修改的字段（仅允许枚举值转换）

### 4.2 业务状态机 (Business State Machine)

`pipeline_status` 描述了项目在业务层面的生命周期。此状态机仅反映正常业务流程中的状态迁移，不包含异常状态（异常状态见 `failure_handling_v1.md`）。

```
                ┌──────────────────────────────┐
                │        PROMOTED               │
                │  (Stage 1: 初始状态)           │
                └──────────────┬───────────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                 │
              ▼                ▼                 │
   FILTERED_BY_CATEGORY   PROMOTED              │
   (Stage 3: Ignore 类别)  (通过分类,进入评分)    │
              │                │                 │
              ▼                ▼                 │
          ARCHIVED       FILTERED_BY_SCORE       │
                        (Stage 8: 分数 < 40)     │
                              │                  │
                              ▼                  │
                          PROMOTED               │
                          (分数 ≥ 40,进入排序)    │
                              │                  │
                              ▼                  │
                          ARCHIVED               │
                          (Stage 10: 完成处理)    │
                              │                  │
                              ▼                  │
                     ┌────────────────┐          │
                     │    ARCHIVED    │◄─────────┘
                     │  (所有路径终点)  │
                     └────────────────┘
```

| 状态 | 说明 | 设置时机 | 后续处理 |
|------|------|----------|----------|
| PROMOTED | 项目正常通过当前阶段 | Stage 1 初始值，Stage 3/8 确认通过 | 进入下一阶段 |
| FILTERED_BY_CATEGORY | 分类为 Ignore 类别 | Stage 3 分类后 | 不进入评分，直接归档 |
| FILTERED_BY_SCORE | 总分低于 40 | Stage 8 计算后 | 不进入排序，直接归档 |
| ARCHIVED | 完成全部处理 | Stage 10 或任意 FILTERED 状态后 | 保留在历史数据中 |

被淘汰的项目不会静默删除。`pipeline_status` 确保数据血缘可追溯。

### 4.3 Batch Flow 展开与聚合

Node 3 (Iteration) 将 30 个项目的批处理展开为独立沙盒实例：

```
Node 2 输出: Array<NormalizedProject> [30 items]
    │
    ▼
Node 3: Iteration
    │
    ├── [Sandbox 1]  Project A  →  4 子节点  →  PROMOTED
    ├── [Sandbox 2]  Project B  →  4 子节点  →  PROMOTED
    ├── [Sandbox 3]  Project C  →  4 子节点  →  SKIPPED (Validation Fail)
    │                                    │
    │                         Dropped — 不影响其他项目 (MD-01)
    ├── ...
    │
    ▼
Node 4: Variable Aggregator
    │
    ├── 仅收拢 pipeline_status = PROMOTED 的项目
    ├── 输出: Array<ScoredProject> [N items, N ≤ 30]
    │    (N = 30 - dropped count)
    ▼
Node 5: Global Ranker (接收完整 Array)
```

**关键机制**：
- Iteration 最大并发度 = 30（与 TOP_N 一致）
- 每项目沙盒隔离：一个项目的异常（超时、校验失败）不影响其他 29 个
- Variable Aggregator 仅收拢 `pipeline_status = PROMOTED` 的项目
- Aggregator 不保证输出顺序（R-05），排序由 Node 5 重新计算

### 4.4 Variable Flow (运行时变量流转)

#### 4.4.1 Configuration Variables (Start Variables)

以下变量在 Workflow 启动时注入，贯穿全流程：

| 变量名 | 类型 | 默认值 | 注入位置 | 消费节点 |
|--------|------|--------|----------|----------|
| `TOP_N` | integer | 30 | Start Variable | Node 2 (提取上限) |
| `RECOMMEND_THRESHOLD_STRONG` | integer | 90 | Start Variable | Node 3-4, Node 5 |
| `RECOMMEND_THRESHOLD_RECOMMEND` | integer | 70 | Start Variable | Node 3-4, Node 5 |
| `RECOMMEND_THRESHOLD_OBSERVE` | integer | 40 | Start Variable | Node 3-4, Node 5 |
| `RETRY_MAX` | integer | 3 | Start Variable | Workflow (HTTP retry) |

#### 4.4.2 运行时中间变量 (Runtime Variables)

以下变量在 Workflow 执行过程中产生，不在节点间持久化：

| 变量名 | 产生节点 | 消费节点 | 生命周期 |
|--------|----------|----------|----------|
| `raw_html` | Node 1 | Node 2 | Node 2 消费后结束 |
| `project_array` | Node 2 | Node 3 (Iteration) | 展开为 30 沙盒实例后结束 |
| `scored_array` | Node 3 (via Aggregator) | Node 5 | Node 5 消费后结束 |
| `ranked_array` | Node 5 | Node 6 | Node 6 消费后结束 |
| `report_markdown` | Node 6 | Node 7 | Node 7 推送后结束 |

#### 4.4.3 Iteration 内部变量 (Sandbox Variables)

Iteration 内部每项目沙盒独立维护：

| 变量名 | 产生节点 | 类型 | 说明 |
|--------|----------|------|------|
| `current_project` | Node 3 (Iteration input) | NormalizedProject | 当前正在处理的项目 |
| `classified` | Node 3-1 | ClassifiedProject | 分类结果 |
| `validation_i_passed` | Node 3-2 | boolean | Validation I 是否通过 |
| `scored` | Node 3-3 | ScoredProject | 评分结果 |
| `validation_ii_passed` | Node 3-4 | boolean | Validation II 是否通过 (决定进入 aggregator) |

### 4.5 Validation Gate 断言拦截逻辑

#### 4.5.1 架构

每 LLM 节点后串联一个 Code Node 作为 Validation Gate：

```
LLM Node 输出
    │
    ▼
Validation Gate (Code Node)
    │
    ├── 断言 1: JSON Parse 合法？
    ├── 断言 2: 必填字段完整？
    ├── 断言 3: 枚举值合法？
    ├── 断言 4: 字段类型正确？
    ├── 断言 5: 字段范围有效？
    │
    ├── ALL PASS → 设 pipeline_status = PROMOTED, 继续
    └── ANY FAIL → 设 pipeline_status = SKIPPED, 脱落 (MD-01)
```

#### 4.5.2 断言清单

| Gate | 位置 | 断言列表 |
|------|------|----------|
| Validation I | Node 3-2 (紧跟 Node 3-1 LLM) | `primary_category` 属于 Taxonomy 定义；`classification_confidence` ∈ {HIGH, MEDIUM, LOW}；`secondary_categories` ≤ 3；JSON 结构完整 |
| Validation II | Node 3-4 (紧跟 Node 3-3 LLM) | 4 维分数均存在且 ∈ [0, MAX]；`total_score` = 四维之和；`reasoning` 非空；`career_goal_impact` 4 子字段均已赋值 |

#### 4.5.3 脱落语义

当断言失败时：

```
1. 记录失败原因（结构化日志，WARNING 级别）
2. 项目标记为 pipeline_status = SKIPPED
3. 项目不进入 Variable Aggregator
4. 同批次其他项目不受影响
```

失败处理的具体策略（重试、Fallback 等）参见 `failure_handling_v1.md`。

---

## 5. Runtime Rules

| Rule | Title | Application |
|------|-------|-------------|
| R-01 | Validation Isolation | Validation Gate 在每 LLM 节点后强制执行 (§4.5) |
| R-02 | Append-Only Object | Fat Object 逐阶段追加字段，不修改上游 (§4.1) |
| R-03 | Fail-Fast Iteration | 断言失败的项目立即脱落，不阻塞批次 (§4.5.3) |
| R-05 | Aggregator Anarchy | Variable Aggregator 不保证顺序；排序由 Node 5 重算 (§4.3) |

---

## 6. Related Documents

| Document | Relationship |
|----------|--------------|
| `node_mapping_v1.md` | 定义本文档描述的节点类型与编排结构。 |
| `node_io_contract_v1.md` | 定义每个节点的输入/输出 Schema。Fat Object 的字段结构由此文档定义。 |
| `failure_handling_v1.md` | 定义断言失败后的重试、超时、Fallback 策略。本文档仅定义"脱落"动作，不定义"如何恢复"。 |
| `runtime_boundary_v1.md` | 定义每阶段由谁负责。本文档描述数据在该阶段如何变换。 |
| `project_data_schema_v1.md` | 数据契约。定义所有 Stage 的字段结构与所有权。本文档的 Fat Object 模型直接对应其 Stage 1~6。 |

---

## 7. Version History

| Version | Date | Author | Change Summary |
|---------|------|--------|----------------|
| v1 | 2026-07 | PKIA MVP Agent | Initial release. Fat Object evolution, Business State Machine, Batch Flow, Variable Flow, Validation Gate assertions. Refactored from `runtime_architecture_and_node_mapping_specification_v1.md`. |

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
