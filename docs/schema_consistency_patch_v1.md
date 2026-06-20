# PKIA Schema Consistency Patch v1

---

## 1. Purpose

`project_data_schema_v1.md` 已成为 PKIA v0.1 的唯一数据契约（Single Source of Truth for Data Structures）。

在它创建之前，各个文档各自定义了自己的"数据结构版本"，导致以下问题：

- 同一字段在不同文档中有不同名称（`repo_name` vs `project_name`）
- 同一字段在不同文档中有不同格式（`High` vs `HIGH` vs `83%`）
- 同一类数据在不同文档中有不同边界（"项目领域"在 Stage 2 和 Stage 3 之间摇摆）
- v2 新增的输出字段（`career_goal_impact`）尚未被下游文档消费

本文件不是新体系设计文档。本文件是 **Migration Plan**——用于让现有文档体系向 `project_data_schema_v1.md` 收敛。

引用关系：

```
project_data_schema_v1.md  (已创建，数据契约)
        ↓
review_project_data_schema_consistency.md  (已创建，审查报告)
        ↓
schema_consistency_patch_v1.md  (本文件，迁移计划)
```

`review_project_data_schema_consistency.md` 回答了"有什么问题"，本文件回答"如何修复这些问题"。

---

## 2. Scope

### 2.1 审查范围

| 文档 | 是否在本次修订范围内 | 原因 |
|------|---------------------|------|
| `classification_agent_spec_v1.md` | ✅ 是 | 包含分类输出结构定义，与 Schema 的 Stage 3 定义需要对齐 |
| `prompt_scoring_agent_v2.md` | ✅ 是 | 包含 Category Input Contract 和输出格式，与 Schema 的 Stage 3/4 定义需要对齐 |
| `scoring_pipeline_schema_v1.md` | ✅ 是 | 包含所有 Stage 的输入输出定义，与 Schema 的 Stage 1~5 定义需要对齐 |
| `daily_report_spec_v1.md` | ✅ 是 | 需要评估是否新增 Career Goal Impact 展示区域 |
| `report_generation_pipeline_v1.md` | ✅ 是 | 输入字段列表需要对齐 Schema 的定义 |
| `interest_profile_v1.md` | ❌ 否 | 属于定义层（兴趣画像定义），不涉及数据结构 |
| `project_classification_taxonomy_v1.md` | ❌ 否 | 属于定义层（分类体系定义），不涉及数据结构 |
| `scoring_strategy_v1.md` | ❌ 否 | 属于定义层（评分策略定义），不涉及数据结构 |
| `scoring_examples_v1.1.md` | ❌ 否 | 属于示例层（评分案例），不涉及数据结构契约 |

### 2.2 范围排除理由

`interest_profile_v1.md`、`project_classification_taxonomy_v1.md`、`scoring_strategy_v1.md` 和 `scoring_examples_v1.1.md` 属于"定义层"文档——它们定义兴趣画像是什么、有哪些类别、评分规则是什么、案例长什么样。它们不定义数据在 pipeline 中如何流转，因此不在本次数据结构一致性修订范围内。

---

## 3. Consistency Principles

### Principle 1: Single Source of Truth

`project_data_schema_v1.md` 拥有数据结构定义的最高优先级。所有其他文档中与 Schema 冲突的数据结构定义，必须向 Schema 对齐，而不是 Schema 向它们对齐。

如果 Schema 说字段名是 `project_name`，其他文档就不能使用 `repo_name`、`repository_name` 或 `name`。

### Principle 2: No Cross-Stage Ownership

字段只能在所属阶段产生。

- `primary_category` 只能出现在 Stage 3 及之后
- `career_alignment` 只能出现在 Stage 4 及之后
- `rank` 只能出现在 Stage 5 及之后

Stage 2 的 Normalized Project 中禁止包含任何 Stage 3 的分类字段。

### Principle 3: No Silent Data Loss

所有文档中涉及项目淘汰的逻辑，必须保留 `pipeline_status` 机制。被淘汰的项目不能静默删除。

### Principle 4: Traceability First

所有涉及数据传递的文档，必须保留 `project_id` 字段作为贯穿所有阶段的唯一标识。不允许出现"从 Stage 1 传到 Stage 2 但丢失了 project_id"的情况。

---

## 4. P0 Critical Fixes

### Fix A: `project_name` 统一

**问题：** `scoring_pipeline_schema_v1.md` §3 (Stage 1 输出) 使用"Repo Name"，`classification_agent_spec_v1.md` §3 (必填输入) 使用"Project Name"。同一实体两种名称。

**Schema 决议：** `project_name`（project_data_schema_v1.md §3.2）

**受影响文档：** `scoring_pipeline_schema_v1.md`

**操作：** 将 scoring_pipeline_schema_v1.md §3 输出中的"Repo Name"改为"project_name"。

---

### Fix B: `classification_confidence` 格式统一

**问题：** 三个文档使用三种不同的 Confidence 表示方式：

| 文档 | 格式 | 示例 |
|------|------|------|
| classification_agent_spec_v1.md §7 | 首字母大写枚举 | `High`, `Medium`, `Low` |
| prompt_scoring_agent_v2.md §2 | 百分比 | `92%` |
| project_data_schema_v1.md §7.3 | 全大写枚举 | `HIGH`, `MEDIUM`, `LOW` |

**Schema 决议：** 全大写枚举 `HIGH` / `MEDIUM` / `LOW`（project_data_schema_v1.md §7.3）

**受影响文档：** `classification_agent_spec_v1.md`, `prompt_scoring_agent_v2.md`

**操作：**
1. `classification_agent_spec_v1.md` §4 和 §7：将 `High`/`Medium`/`Low` 改为 `HIGH`/`MEDIUM`/`LOW`
2. `prompt_scoring_agent_v2.md` §2：将 `Percentage (0~100%)` 改为 `Enum: HIGH/MEDIUM/LOW`，更新示例中的 `92%` 为 `HIGH`

---

### Fix C: `career_goal_impact` 定义统一

**问题：** `prompt_scoring_agent_v2.md` §12 定义了 Career Goal Impact 输出格式，但 `project_data_schema_v1.md` §8.3 将其定义为结构化对象（含 4 个子字段）。`report_generation_pipeline_v1.md` §3 和 `daily_report_spec_v1.md` §3 尚未包含此字段。

**Schema 决议：** `career_goal_impact` 是 Stage 4 Scoring Output 的必填字段（project_data_schema_v1.md §8.2）。每个子字段必须使用 `HIGH`/`MEDIUM`/`LOW` 枚举。

**受影响文档：** `report_generation_pipeline_v1.md`, `daily_report_spec_v1.md`

**操作：**
1. `report_generation_pipeline_v1.md` §3 输入字段表中新增 `career_goal_impact`
2. `daily_report_spec_v1.md` §3 评估是否新增 Career Goal Impact 展示区域

---

### Fix D: `pipeline_status` 生命周期统一

**问题：** `project_data_schema_v1.md` §11 定义了 `pipeline_status` 的完整生命周期（`PROMOTED` → `FILTERED_BY_CATEGORY`/`FILTERED_BY_SCORE` → `ARCHIVED`）。其他文档中不存在此概念。

**Schema 决议：** `pipeline_status` 是全局字段，从 Stage 1 开始存在（project_data_schema_v1.md §11）。

**受影响文档：** `scoring_pipeline_schema_v1.md`, `report_generation_pipeline_v1.md`

**操作：**
1. `scoring_pipeline_schema_v1.md` §3（Stage 1 输出）中新增 `pipeline_status` 字段
2. `scoring_pipeline_schema_v1.md` §11（Stage 9）和 §12（Stage 10）中说明 `pipeline_status` 在此阶段可更新为 `FILTERED_BY_SCORE`
3. `report_generation_pipeline_v1.md` §3 输入字段表中新增 `pipeline_status`

---

### Fix E: Stage 2/3 边界修正

**问题：** `scoring_pipeline_schema_v1.md` §4 (Stage 2 输出) 包含"项目领域"字段，但其说明为"按 Interest Tiers 映射的领域标签 — Stage 3 完成"。Stage 2 的输出中包含 Stage 3 才能产生的字段，违反 Principle 2 (No Cross-Stage Ownership)。

此外，"核心能力"字段的定义"Description 提炼"过于模糊，无法产生可重复的分类结果。

**Schema 决议：** 
- Normalized Project（Stage 2）不应包含分类字段（project_data_schema_v1.md §6.4）
- `extracted_keywords` 替代模糊的"核心能力"字段（project_data_schema_v1.md §6.3）

**受影响文档：** `scoring_pipeline_schema_v1.md`

**操作：**
1. 从 Stage 2 输出中移除"项目领域"字段（它属于 Stage 3）
2. 将"核心能力"字段替换为 `extracted_keywords`（最多 5 个关键词，结构化）
3. Stage 2 输出应与 Schema §6.2 保持一致：`normalized_description`, `primary_language`, `extracted_keywords`

---

## 5. Document-by-Document Patch Plan

### 5.1 classification_agent_spec_v1.md

#### 5.1.1 发现的问题

| # | 位置 | 问题 | 与 Schema 的差距 |
|---|------|------|-----------------|
| 1 | §4 输出结构 | `Confidence Level` 字段名 | Schema 使用 `classification_confidence` |
| 2 | §4 输出结构 | Confidence Level 使用 `High/Medium/Low` | Schema 要求 `HIGH/MEDIUM/LOW` |
| 3 | §7.1 等级定义 | 表格中显示 `High`/`Medium`/`Low` | 需要改为大写 |
| 4 | §3 输入字段 | 使用 `Project Name`（首字母大写） | Schema 使用 `project_name`（snake_case） |
| 5 | §3 输入字段 | 类型描述使用中文"字符串" | Schema 使用英文类型描述 |

#### 5.1.2 影响

这些不一致不会改变 Classification Agent 的行为，但会导致数据结构定义的混乱。实现者参考 classification_agent_spec_v1.md 时看到的字段名与 Schema 定义的不同，需要用脑内映射来转换。

#### 5.1.3 修订内容

1. §4 输出结构表：`Confidence Level` → `classification_confidence`，`High/Medium/Low` → `HIGH/MEDIUM/LOW`
2. §7.1 等级定义表：`High` → `HIGH`，`Medium` → `MEDIUM`，`Low` → `LOW`
3. §3 输入字段表：`Project Name` → `project_name`

#### 5.1.4 预期结果

classification_agent_spec_v1.md 的输出字段名与 Schema Stage 3 的字段名完全一致。实现者可以直接将 Classification Agent 的输出映射到 Schema 的 Stage 3 结构，无需任何字段名转换。

---

### 5.2 prompt_scoring_agent_v2.md

#### 5.2.1 发现的问题

| # | 位置 | 问题 | 与 Schema 的差距 |
|---|------|------|-----------------|
| 1 | §2 Input Data Structure | `Classification Confidence` 使用 `Percentage (0~100%)` | Schema 要求 `HIGH/MEDIUM/LOW` 枚举 |
| 2 | §2 Example Input | 示例中使用 `92%` | Schema 要求枚举值 |
| 3 | §2 Rules | `70%` 作为阈值 | 需要改为 `MEDIUM` 阈值 |
| 4 | §12 Output Format | 格式（非 Schema）匹配，属于 Prompt 输出格式 | 已对齐，无需修改 |

#### 5.2.2 影响

prompt_scoring_agent_v2.md 是 Scoring Agent 的 System Prompt。如果 Prompt 中说"Classification Confidence 是百分比"，但 Schema 说"只能是 HIGH/MEDIUM/LOW"，会产生以下后果：

- Scoring Agent 可能期望接收百分比值，但实际收到的是枚举值
- Prompt 中的阈值判断（`below 70%`）无法直接应用于枚举值

#### 5.2.3 修订内容

1. §2 Input Data Structure：`Percentage (0~100%)` → `Enum: HIGH / MEDIUM / LOW`，Source 列补充说明"mapped from Classification Agent's internal score"
2. §2 Example Input：`92%` → `HIGH`
3. §2 Rules：`Classification Confidence below 70%` → `Classification Confidence is LOW`

#### 5.2.4 预期结果

Scoring Agent 的 Category Input Contract 与 Schema 的 Stage 3 输出结构一致。Prompt 中的置信度阈值判断基于枚举值而非百分比。

---

### 5.3 scoring_pipeline_schema_v1.md

#### 5.3.1 发现的问题

| # | 位置 | 问题 | 与 Schema 的差距 |
|---|------|------|-----------------|
| 1 | §3 Stage 1 输出 | 使用"Repo Name" | Schema 使用 `project_name` |
| 2 | §3 Stage 1 输出 | 缺少 `project_id`、`owner`、`forks`、`pipeline_status` | Schema §5.2 定义了完整字段列表 |
| 3 | §4 Stage 2 输出 | 包含"项目领域"（属于 Stage 3） | 违反 No Cross-Stage Ownership |
| 4 | §4 Stage 2 输出 | "核心能力"定义模糊 | Schema 使用结构化的 `extracted_keywords` |
| 5 | §4 Stage 2 输出 | 使用中文字段名 | Schema §3.1 要求 snake_case 英文 |
| 6 | §6 Stage 4 输出 | 缺少 `reasoning`、`career_goal_impact` | Schema §8.2 包含这些必填字段 |
| 7 | §11/12 Stage 9/10 | 缺少 `pipeline_status` 的更新机制 | Schema §11 定义了状态生命周期 |

#### 5.3.2 影响

scoring_pipeline_schema_v1.md 是 Pipeline 的实现依据文档。它的问题是最严重的，因为：

- 它直接定义了每个 Stage 的输入输出
- 它的字段名和 Schema 不一致会导致整个实现偏离契约
- 它的 Stage 2/3 边界模糊会导致分类逻辑在错误的位置执行

#### 5.3.3 修订内容

1. **§3 Stage 1 输出重写为：** `project_id`, `project_name`, `owner`, `description`, `topics`, `stars`, `forks`, `language`, `source`, `collection_date`, `pipeline_status`——与 Schema §5.2 保持一致
2. **§4 Stage 2 输出重写为：** 继承 Stage 1 全部字段，新增 `normalized_description`, `primary_language`, `extracted_keywords`——移除"项目领域"和"核心能力"，与 Schema §6.2 保持一致
3. **§6 Stage 4 输出新增：** `reasoning` 和 `career_goal_impact`——与 Schema §8.2 保持一致
4. **§11/12 新增说明：** `pipeline_status` 在此阶段更新为 `FILTERED_BY_SCORE`（如成立）

#### 5.3.4 预期结果

scoring_pipeline_schema_v1.md 的每个 Stage 输出定义与 Schema 的对应 Stage 定义完全一致。实现者可以以 Pipeline Schema 为操作手册，以 Project Data Schema 为数据手册，两者不再冲突。

---

### 5.4 daily_report_spec_v1.md

#### 5.4.1 发现的问题

| # | 位置 | 问题 | 与 Schema 的差距 |
|---|------|------|-----------------|
| 1 | §3 Section B | `与职业目标的关系` 是文本描述 | Schema §8.3 定义了结构化的 `career_goal_impact`（4 个 HIGH/MEDIUM/LOW 子字段）|
| 2 | §3 Section B/C/D | 缺少 `project_id` 展示 | Schema §12 要求 project_id 贯穿所有阶段 |

#### 5.4.2 影响

当前日报格式中，"与职业目标的关系"以文本形式展示在 Section B 的 Reasoning 部分。而 Schema 和 prompt_scoring_agent_v2.md 都要求独立输出 `career_goal_impact` 结构。日报展示层尚未更新以利用这种结构化数据。

#### 5.4.3 修订内容

1. **§3 Section B 模板新增（可选区域，在 Reasoning 之后）：**
   ```
   职业目标影响:
   #1 Agent Application Engineer: [HIGH / MEDIUM / LOW]
   #2 AI Platform Engineer: [HIGH / MEDIUM / LOW]
   #3 LLM Inference Optimization Engineer: [HIGH / MEDIUM / LOW]
   #4 Multi-Agent System Engineer: [HIGH / MEDIUM / LOW]
   ```
2. **§3 Section B 模板新增 `project_id` 字段（隐藏或小字显示，用于追溯）**

#### 5.4.4 预期结果

Daily Report 的 Section B（Strong Recommend）展示 Career Goal Impact 的结构化信息。用户可以直接看到每个项目对其四个职业目标的贡献程度，而不再需要从 Reasoning 文本中自行推断。

---

### 5.5 report_generation_pipeline_v1.md

#### 5.5.1 发现的问题

| # | 位置 | 问题 | 与 Schema 的差距 |
|---|------|------|-----------------|
| 1 | §3 输入字段表 | 缺少 `project_id` | Schema §12 要求 project_id 贯穿所有阶段 |
| 2 | §3 输入字段表 | 缺少 `pipeline_status` | Schema §11 定义了状态生命周期 |
| 3 | §3 输入字段表 | 缺少 `career_goal_impact` | Schema §8.2 将其定义为必填字段 |
| 4 | §3 输入字段表 | 字段名使用中文 | Schema §3.1 要求 snake_case 英文 |

#### 5.5.2 影响

`report_generation_pipeline_v1.md` 的输入字段表是 Report Generation Pipeline 的数据契约。缺少 `career_goal_impact` 意味着 Report Pipeline 可能丢弃 Scoring Agent 产出的重要结构化信息。缺少 `project_id` 意味着无法从 Report Item 回溯到原始项目数据。

#### 5.5.3 修订内容

**§3 输入字段表修订为：**

| 字段 | 类型 | 来源阶段 |
|------|------|----------|
| `project_id` | string | Stage 1 |
| `project_name` | string | Stage 1 |
| `primary_category` | string | Stage 3 |
| `secondary_categories` | list[string] | Stage 3 |
| `classification_confidence` | enum | Stage 3 |
| `career_alignment` | integer (0~40) | Stage 4 |
| `interest_match` | integer (0~30) | Stage 4 |
| `trend_heat` | integer (0~20) | Stage 4 |
| `research_relevance` | integer (0~10) | Stage 4 |
| `total_score` | integer (0~100) | Stage 4 |
| `recommendation` | enum | Stage 4 |
| `reasoning` | string | Stage 4 |
| `career_goal_impact` | object | Stage 4 |
| `rank` | integer | Stage 5 |
| `ranking_group` | enum | Stage 5 |
| `pipeline_status` | enum | Stage 1 (updatable) |

#### 5.5.4 预期结果

Report Generation Pipeline 的输入字段表与 Schema 的 Stage 5（Ranking Output）定义完全一致。所有评分和分类信息都被传递到报告生成阶段，无丢失。

---

## 6. Risk Analysis

### Risk 1: 字段命名冲突导致实现错误

**概率：** 高
**影响：** 中

如果不修订，实现者可能同时看到 `repo_name`（Pipeline Schema）和 `project_name`（Data Schema），不确定哪个是正确的。如果选择了 `repo_name`，后续与 Scoring Agent 的集成会出现字段不匹配。

**缓解措施：** P0 Fix A（`project_name` 统一）必须在任何实现开始前完成。

### Risk 2: 分类结果无法正确传递

**概率：** 中
**影响：** 高

如果分类 Agent 的输出字段名（`Confidence Level`）与评分 Agent 期望的输入字段名（`Classification Confidence`）不一致，分类结果可能无法正确传递到评分阶段。

**缓解措施：** 5.1 和 5.2 的修订必须同步进行，确保分类 Agent 的输出字段名与评分 Agent 的期望输入字段名一致。

### Risk 3: Career Goal Impact 丢失

**概率：** 中
**影响：** 中

Scoring Agent v2 产生 `career_goal_impact` 数据，但 Report Generation Pipeline 的输入字段表（当前版本）不包含此字段。如果 Pipeline 实现基于文档实现，`career_goal_impact` 会被静默丢弃。

**缓解措施：** 5.5 的修订（report_generation_pipeline_v1.md 输入字段表新增 `career_goal_impact`）必须在 Scoring Agent v2 上线前完成。

### Risk 4: 日报与评分脱节

**概率：** 低
**影响：** 中

Daily Report 当前使用"与职业目标的关系"文本描述。Scoring Agent v2 产出结构化的 `career_goal_impact`。如果日报格式不更新，用户无法看到结构化信息，Scoring Agent v2 的新能力在展示层被浪费。

**缓解措施：** 5.4 的修订（daily_report_spec_v1.md 新增 Career Goal Impact 展示区域）建议在 Scoring Agent v2 上线后一个迭代内完成。

### Risk 5: Stage 2/3 边界模糊导致分类逻辑错位

**概率：** 中
**影响：** 高

如果 Pipeline Schema 的 Stage 2 输出包含"项目领域"字段（标注为"Stage 3 完成"），实现者可能会将分类逻辑部分实现在 Normalization 阶段，而不是完全交给 Classification Agent。这会导致部分项目在 Normalization 阶段就被打上了类别标签，绕过了 Classification Agent。

**缓解措施：** P0 Fix E（Stage 2/3 边界修正）必须在 Pipeline 实现前完成。

---

## 7. Recommended Execution Order

### Step 1: 修订 classification_agent_spec_v1.md

**工作量估算：** 小（3 处字段名/枚举值修改）
**依赖：** 无
**修订要点：**
- `Confidence Level` → `classification_confidence`
- `High`/`Medium`/`Low` → `HIGH`/`MEDIUM`/`LOW`
- `Project Name` → `project_name`

### Step 2: 修订 prompt_scoring_agent_v2.md

**工作量估算：** 小（3 处修改）
**依赖：** Step 1（因为评分 Agent 的输入来自分类 Agent 的输出）
**修订要点：**
- `Percentage (0~100%)` → `Enum: HIGH / MEDIUM / LOW`
- `92%` → `HIGH`
- `below 70%` → `is LOW`

### Step 3: 修订 scoring_pipeline_schema_v1.md

**工作量估算：** 大（4 个 Stage 的输出定义需要重写）
**依赖：** Step 1（因为分类 Agent 的输出字段名确定后，Pipeline 的 Stage 3 输出才能对齐）
**修订要点：**
- Stage 1 输出：对齐 Schema §5.2
- Stage 2 输出：对齐 Schema §6.2，移除"项目领域"
- Stage 4 输出：对齐 Schema §8.2，新增 `reasoning` 和 `career_goal_impact`
- Stage 9/10：新增 `pipeline_status` 更新说明

### Step 4: 修订 report_generation_pipeline_v1.md

**工作量估算：** 中
**依赖：** Step 3（因为 Report Pipeline 的输入来自 Scoring Pipeline 的输出）
**修订要点：**
- 输入字段表重写为 snake_case 英文
- 新增 `project_id`, `pipeline_status`, `career_goal_impact`

### Step 5: 修订 daily_report_spec_v1.md

**工作量估算：** 中
**依赖：** Step 4（因为日报的输入来自 Report Pipeline 的输出）
**修订要点：**
- 评估 Career Goal Impact 展示区域的设计
- 新增 project_id 字段（可选）

### Step 6: 全局一致性验证

**工作量估算：** 小
**依赖：** Step 1~5 全部完成
**操作：**
- 重新运行 `review_project_data_schema_consistency.md` 中的 7 项检查
- 确认所有字段名、格式、边界与 `project_data_schema_v1.md` 一致

---

## 8. Expected Outcome

### 完成后的文档体系状态

```
interest_profile_v1.md              [定义层]  → 用户兴趣画像
project_classification_taxonomy_v1.md [定义层] → 分类体系
scoring_strategy_v1.md               [定义层]  → 评分策略
        ↓
classification_agent_spec_v1.md     [执行层]  → 分类执行（输出与 Schema Stage 3 对齐）
        ↓
prompt_scoring_agent_v2.md          [执行层]  → 评分执行（输入与 Schema Stage 3 对齐，输出与 Stage 4 对齐）
        ↓
project_data_schema_v1.md           [数据层]  → 唯一数据契约（6 阶段定义）
        ↓
scoring_pipeline_schema_v1.md       [流程层]  → 流程编排（各阶段 I/O 与 Schema 对齐）
        ↓
report_generation_pipeline_v1.md    [流程层]  → 报告生成（输入与 Schema Stage 5 对齐）
        ↓
daily_report_spec_v1.md             [展示层]  → 日报展示（包含 Career Goal Impact 展示）
```

### 关键验收标准

| 标准 | 描述 |
|------|------|
| 字段名一致性 | 所有文档中的字段名使用 snake_case 英文，与 Schema 完全一致 |
| Confidence 一致性 | 所有文档使用 `HIGH`/`MEDIUM`/`LOW` 枚举，无百分比格式 |
| Stage 边界一致性 | Stage 2 不包含分类字段，Stage 3 包含分类字段 |
| Career Goal Impact 一致性 | Schema §8.3 → Scoring Prompt §12 → Report Pipeline §3 → Daily Report §3 完整链路 |
| pipeline_status 一致性 | Schema §11 → Pipeline §3/§11/§12 → Report Pipeline §3 完整链路 |
| project_id 贯穿性 | Schema §4 → Pipeline §3 → Report Pipeline §3 完整链路 |

### Single Source of Truth Architecture

修订完成后，PKIA 文档体系将形成"定义层 → 执行层 → 数据层 → 流程层 → 展示层"的五层架构：

- **定义层** 告诉系统"是什么"（Interest Profile、Taxonomy、Scoring Strategy）
- **执行层** 告诉系统"怎么做"（Classification Agent、Scoring Agent）
- **数据层**（Schema）告诉系统"数据长什么样"
- **流程层** 告诉系统"步骤是什么"（Scoring Pipeline、Report Pipeline）
- **展示层** 告诉系统"用户看到什么"（Daily Report）

每一层都依赖下一层，但不直接修改下一层的定义。`project_data_schema_v1.md` 作为数据层的唯一契约，是所有其他层的共同参考点。

---

## Appendix: Consistency Score Re-Estimation

修订完成后，预计一致性评分将从当前的 **15/100** 提升至：

| 检查项 | 修订前 | 修订后 | 说明 |
|--------|--------|--------|------|
| Raw Project 定义完整 | FAIL | PASS | 字段名对齐，新增 project_id 等 |
| Normalized 定义完整 | FAIL | PASS | 移除"项目领域"，替换为 extracted_keywords |
| Classification Output | FAIL | PASS | Confidence 格式统一 |
| Scoring Output | FAIL | PASS | 新增 reasoning, career_goal_impact |
| Career Goal Impact | FAIL | PASS | 定义统一，展示层新增 |
| Report Object | FAIL | PASS | 输入字段完全对齐 |
| 完整数据流 | FAIL | PASS | 所有阶段字段映射已定义 |

**预估总分：95/100**

失分（~5 分）可能来自：部分文档的中文/英文命名格式未完全统一等 minor issues。

---

*End of Patch v1. Migration plan for PKIA Schema consistency.*