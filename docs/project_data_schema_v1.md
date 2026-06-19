# PKIA Project Data Schema v1

---

## 1. Purpose

本文件定义了一个项目从进入 PKIA 到最终进入日报，在每一个阶段的数据结构、字段定义、生命周期和转换规则。

在 PKIA 文档体系中，职责分离如下：

| 文档 | 职责 |
|------|------|
| **Project Data Schema（本文件）** | **定义数据长什么样** |
| Project Classification Taxonomy | 定义有哪些类别 |
| Classification Agent Spec | 定义如何执行分类 |
| Prompt Scoring Agent | 定义如何执行评分 |
| Scoring Pipeline Schema | 定义如何编排流程 |
| Report Generation Pipeline | 定义如何生成日报 |
| Daily Report Spec | 定义日报长什么样 |

Classification Agent、Scoring Agent、Report Agent 都不是数据结构定义者。它们消费和产生数据，但不定义数据。本文件是唯一的数据定义来源。

本文件不包含代码、Workflow 配置、数据库设计、SQL、JSON Schema 或任何编程语言实现细节。它只描述数据结构及其行为规则。

---

## 2. Design Principles

### Principle 1: Single Source of Truth

所有 Agent 和 Pipeline 阶段的数据结构定义，必须且只能来自本文件。不允许任何一个 Agent 私自定义"自己的数据格式"。如果 Agent 需要新增字段，必须先更新本文件，再更新 Agent。

### Principle 2: Classification First

数据产生顺序严格遵循：Raw → Normalized → Classified → Scored → Ranked → Report。禁止跳过分类阶段直接评分。禁止在 Normalized Project 中预置分类字段。

### Principle 3: Traceability First

每个项目通过 `project_id` 在其整个生命周期中可追溯。任何人在任何时候都可以回答："这个项目现在在哪个阶段？它经历了什么变化？"

### Principle 4: No Silent Data Loss

当项目在某个阶段被淘汰（如分类后确定为 Ignore 类别），其数据不会静默消失。`pipeline_status` 字段明确记录项目的淘汰原因和淘汰阶段。未被选入日报的项目仍然存在于历史数据中，可供审查。

### Principle 5: Batch-Aware Design

Rank 只能在 Batch 处理阶段产生。Item 处理（Stage 1~4）中的项目不携带排名信息。设计上明确区分 Item Processing 和 Batch Processing 的边界。

### Principle 6: Forward Compatibility

Schema 版本从 v1 开始，允许未来新增字段，但不允许删除或修改核心字段（`project_id`, `project_name`, `pipeline_status`）。新增字段必须有明确的"预期使用版本"标记。

---

## 3. Global Rules

### 3.1 命名规范

- 所有字段名使用小写字母加下划线（`snake_case`）
- 所有字段名使用英文，禁止中文字段名
- 同一字段在所有 Stage 中必须使用相同的名称

### 3.2 正式名称

`project_name` 是项目的正式名称字段。禁止使用以下变体：

- ❌ `repo_name`
- ❌ `repository_name`
- ❌ `name`
- ❌ `projectName`

### 3.3 字段生命周期

每个字段在其定义 Stage 中产生，在后续 Stage 中要么保留、要么修改、要么废弃。没有 Stage 可以"提前"产生一个属于后续 Stage 的字段。

### 3.4 空值规则

允许为空的字段必须标注"可选"。必填字段在任何 Stage 中都不得为空。如果必填字段在某个 Stage 中无法获取，该 Stage 的处理应失败（不产生输出），而非生成空值。

---

## 4. Global Identity Fields

以下字段在所有 Stage 中均存在，永不修改，永不删除。

### 4.1 `project_id`

| 属性 | 值 |
|------|-----|
| 类型 | string |
| 产生时机 | Stage 1 — 项目首次进入 PKIA 时 |
| 修改权限 | 禁止修改 |
| 删除权限 | 禁止删除 |
| 唯一性 | 全局唯一 |
| 生成规则 | 基于 collection_date + source + 项目名称的确定性哈希 |

`project_id` 是整个 PKIA 数据管线的脊梁。它使得以下操作成为可能：

- **Data Lineage** — 追踪一个项目从原始数据到日报的全路径
- **Debug** — 当某个项目的评分异常时，通过 `project_id` 可以回溯其所有阶段的中间数据
- **Audit** — 验证任意阶段的处理是否正确
- **Traceback** — 从日报中的某条推荐反向追溯到其原始 GitHub 数据

### 4.2 `source`

| 属性 | 值 |
|------|-----|
| 类型 | string (enum) |
| 允许值 | `github_trending`, `arxiv` (预留) |
| 修改权限 | 禁止修改 |

标识数据来源。v0.1 仅支持 `github_trending`。

### 4.3 `collection_date`

| 属性 | 值 |
|------|-----|
| 类型 | date (YYYY-MM-DD) |
| 产生时机 | Stage 1 |
| 修改权限 | 禁止修改 |

标识项目被采集的日期。用于 Daily Report 的日期匹配和数据回溯。

---

## 5. Stage 1 — Raw Project Object

### 5.1 目的

表示从数据源获取的原始项目数据。此阶段不做任何判断、过滤或结构化处理。

### 5.2 字段定义

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `project_id` | string | 是 | 全局唯一标识，进入 PKIA 时立即生成 |
| `project_name` | string | 是 | GitHub 仓库名称（如 "LangGraph"） |
| `owner` | string | 是 | 项目所属组织或作者（如 "langchain-ai"） |
| `description` | string | 是 | GitHub 项目的描述文本 |
| `topics` | list[string] | 否 | GitHub Topics 标签列表 |
| `stars` | integer | 是 | GitHub Stars 数量 |
| `forks` | integer | 否 | GitHub Forks 数量 |
| `language` | string | 否 | GitHub 检测到的主编程语言 |
| `source` | string (enum) | 是 | 数据来源：`github_trending` |
| `collection_date` | date | 是 | 采集日期 |
| `pipeline_status` | string (enum) | 是 | 初始值为 `PROMOTED` |

### 5.3 禁止字段

以下字段在 Stage 1 中**禁止**出现：

- ❌ `primary_category`（未分类）
- ❌ `secondary_categories`（未分类）
- ❌ `classification_confidence`（未分类）
- ❌ `career_alignment`（未评分）
- ❌ `interest_match`（未评分）
- ❌ `trend_heat`（未评分）
- ❌ `research_relevance`（未评分）
- ❌ `total_score`（未评分）
- ❌ `recommendation`（未评分）
- ❌ `rank`（未进入 Batch 处理）
- ❌ `ranking_group`（未进入 Batch 处理）
- ❌ `normalized_description`（未归化）
- ❌ `extracted_keywords`（未归化）

### 5.4 规则

- 此阶段不修改原始数据。即使某个项目明显与 Interest Profile 无关（如一个前端框架），也完整保留。
- `project_id` 在此阶段生成后不得再修改。

---

## 6. Stage 2 — Normalized Project Object

### 6.1 目的

将原始项目数据标准化为统一格式，为分类阶段做准备。此阶段消除不同数据源之间的格式差异。

### 6.2 字段定义

Stage 2 **继承** Stage 1 的所有字段，并新增以下字段：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `normalized_description` | string | 是 | Description 的截断/摘要版本，不超过 200 字符 |
| `primary_language` | string | 否 | 标准化后的主编程语言（如果 `language` 存在则归一化） |
| `extracted_keywords` | list[string] | 否 | 从 Description 和 Topics 中提取的核心关键词，最多 5 个 |

### 6.3 `extracted_keywords` 的用途

该字段为 Classification Agent 预留。即使当前 Workflow 不单独部署 Classification Agent，该字段也必须保留，因为：

- 未来可被分类器直接使用，无需重新解析 Description
- 避免重复调用 LLM 解析相同的文本内容
- 作为 Classification Agent 的辅助输入信号

### 6.4 规则

- `description` 超过 200 字符时，截断为 `normalized_description`（保留前 200 字符）；不超过 200 字符时，`normalized_description` 与 `description` 一致
- `extracted_keywords` 的提取规则：优先使用 Topics，Topics 不足时从 Description 中提取
- Stage 2 不产生任何与分类相关的字段

### 6.5 对比：Stage 1 vs Stage 2

| 维度 | Stage 1 | Stage 2 |
|------|---------|---------|
| 数据来源 | GitHub 原始数据 | Stage 1 输出 |
| 核心操作 | 采集 | 标准化 |
| 新增字段 | project_id, source, collection_date | normalized_description, primary_language, extracted_keywords |
| 是否可过滤 | 否 | 否（所有项目进入 Normalization） |

---

## 7. Stage 3 — Classification Output Object

### 7.1 目的

表示 Classification Agent 的分类结果。此阶段是项目获得"身份"的阶段——它首次被赋予类别标签。

### 7.2 字段定义

Stage 3 **继承** Stage 2 的所有字段，并新增以下字段：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `primary_category` | string | 是 | 项目的主要类别，必须是 Taxonomy 定义的 Level-2 类别或特殊类别 |
| `secondary_categories` | list[string] | 否 | 项目的次要类别，0~3 个 |
| `classification_confidence` | string (enum) | 是 | 分类置信度，仅允许 `HIGH`, `MEDIUM`, `LOW` |
| `classification_notes` | string | 否 | 分类依据说明 |

### 7.3 Confidence 统一规则

`classification_confidence` 使用三档枚举，禁止使用百分比或分数：

| 枚举值 | 含义 | 对应百分比范围（内部参考） |
|--------|------|---------------------------|
| `HIGH` | 分类明确，无歧义 | 80~100% |
| `MEDIUM` | 存在一定模糊性，但可做出合理判断 | 50~79% |
| `LOW` | 推测性分类，需要下游谨慎处理 | 0~49% |

**禁止形式**（违反 Global Rules）：

- ❌ `83%` — 百分比格式不允许出现在 Schema 中
- ❌ `0.83` — 小数格式不允许
- ❌ `87/100` — 分数格式不允许
- ❌ `high` — 必须使用大写枚举值：`HIGH`

### 7.4 特殊类别值

`primary_category` 允许以下三个特殊值：

| 特殊值 | 含义 | 使用场景 |
|--------|------|----------|
| `EMERGING_CATEGORY` | 新方向，Taxonomy 尚未覆盖 | 见 classification_agent_spec_v1.md §8 |
| `UNCLASSIFIED_AI_PROJECT` | AI 项目但无法分类 | 见 classification_agent_spec_v1.md §10 |
| `TREND_OVERRIDE` | 极度热门项目的覆盖机制 | 见 classification_agent_spec_v1.md §9 |

### 7.5 规则

- `primary_category` 必须来自 project_classification_taxonomy_v1.md 的 Level-2 类别或三个特殊类别之一
- `secondary_categories` 最多 3 个，每个必须是 Taxonomy 定义的标准类别名
- `classification_confidence` 为 `LOW` 时，`classification_notes` 为必填

---

## 8. Stage 4 — Scoring Output Object

### 8.1 目的

表示 Scoring Agent 的评分结果。此阶段是项目获得"价值"的阶段——它被赋予反映职业相关性的分数。

### 8.2 字段定义

Stage 4 **继承** Stage 3 的所有字段，并新增以下字段：

| 字段 | 类型 | 范围 | 必填 | 说明 |
|------|------|------|------|------|
| `career_alignment` | integer | 0~40 | 是 | 与职业目标的匹配程度 |
| `interest_match` | integer | 0~30 | 是 | 与兴趣画像的匹配程度 |
| `trend_heat` | integer | 0~20 | 是 | 社区热度和关注度 |
| `research_relevance` | integer | 0~10 | 是 | 长期研究价值 |
| `total_score` | integer | 0~100 | 是 | 四维分数之和 |
| `recommendation` | string (enum) | — | 是 | `STRONG_RECOMMEND`, `RECOMMEND`, `OBSERVE`, `IGNORE` |
| `reasoning` | string | — | 是 | 评分理由的详细说明 |
| `career_goal_impact` | object | — | 是 | 对四个职业目标的影响评估 |

### 8.3 `career_goal_impact` 子字段

| 子字段 | 类型 | 允许值 |
|--------|------|--------|
| `agent_application_engineer` | string (enum) | `HIGH`, `MEDIUM`, `LOW` |
| `ai_platform_engineer` | string (enum) | `HIGH`, `MEDIUM`, `LOW` |
| `llm_inference_optimization_engineer` | string (enum) | `HIGH`, `MEDIUM`, `LOW` |
| `multi_agent_system_engineer` | string (enum) | `HIGH`, `MEDIUM`, `LOW` |

此字段与 `prompt_scoring_agent_v2.md` §12 的 Career Goal Impact 定义保持一致。

### 8.4 推荐等级枚举

| 枚举值 | 对应总分范围 |
|--------|-------------|
| `STRONG_RECOMMEND` | 90~100 |
| `RECOMMEND` | 70~89 |
| `OBSERVE` | 40~69 |
| `IGNORE` | 0~39 |

### 8.5 规则

- `total_score` 必须严格等于四个分数之和，不允许额外调整
- `reasoning` 必须解释每个分数的依据，禁止仅输出分数
- `career_goal_impact` 的每个子字段都必须赋值，不允许空值

---

## 9. Stage 5 — Ranking Output Object

### 9.1 目的

表示项目在 Batch 排序后的排名结果。此阶段是项目获得"位置"的阶段——它被放入一个推荐层级并赋予排名。Rank 只能在 Batch 处理中产生，因为排名是相对位置，需要知道同批次其他项目的信息。

### 9.2 字段定义

Stage 5 **继承** Stage 4 的所有字段，并新增以下字段：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `rank` | integer | 是 | 在当日所有项目中的排名（1~30） |
| `ranking_group` | string (enum) | 是 | `STRONG_RECOMMEND`, `RECOMMEND`, `OBSERVE`, `IGNORE` |

### 9.3 排序规则

1. 一级排序：`ranking_group`（Strong Recommend > Recommend > Observe > Ignore）
2. 二级排序：`total_score`（降序）
3. 三级排序：`career_alignment`（降序）
4. 四级排序：`interest_match`（降序）

### 9.4 规则

- `rank` 只能在 Batch 处理阶段产生。Item 处理（Stage 1~4）中禁止生成 `rank`
- `ranking_group` 在 Stage 5 中的值与 Stage 4 的 `recommendation` 值严格一致
- `ranking_group` 的存在是为了让 Report Generation Pipeline 可以直接按组别读取项目，无需重新计算推荐等级

---

## 10. Stage 6 — Report Item Object

### 10.1 目的

表示项目在 Daily Report 中的最终展示形态。Report Item 是展示层对象，包含了展示所需的额外信息，但**不替代** Scoring Object。

### 10.2 原则：Report Item ≠ Scoring Object

Report Item 允许新增展示层字段，但这些字段不能修改或覆盖来自 Scoring Object 的数据。Scoring Object 是"真实数据"，Report Item 是"展示数据"。

### 10.3 字段定义

Stage 6 **继承** Stage 5 的所有字段，并新增以下字段：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `summary` | string | 是 | 适合日报展示的简短摘要，不超过 100 字符 |
| `recommended_read_time` | integer | 是 | 预计阅读时间，单位：分钟 |
| `daily_priority` | integer | 否 | 当日优先级（1~3），仅在 What To Read Today 中存在 |

### 10.4 规则

- `recommended_read_time` 根据项目复杂度估算：
  - README 快速了解：10~15 分钟
  - 技术架构了解：15~25 分钟
  - 深度源码学习：25~40 分钟
- `daily_priority` 仅在 Section F（What To Read Today）中出现的 3 个项目上有值
- Report Item 不允许修改从上游继承的字段（如 `total_score`, `career_alignment` 等）

---

## 11. Pipeline Status Rules

### 11.1 `pipeline_status` 字段

该字段在 Stage 1 中产生（初始值 `PROMOTED`），在所有后续 Stage 中存在，允许修改。

### 11.2 枚举值

| 值 | 含义 | 设置时机 |
|-----|------|----------|
| `PROMOTED` | 项目正常通过当前阶段，进入下一阶段 | 每次 Stage 成功处理后 |
| `FILTERED_BY_CATEGORY` | 项目在分类阶段被淘汰 | Stage 3 之后 |
| `FILTERED_BY_SCORE` | 项目在评分阶段被淘汰 | Stage 4 之后 |
| `ARCHIVED` | 项目完成全部处理，已进入历史数据 | Stage 6 之后 |

### 11.3 为什么需要保留被淘汰项目

Pipeline Status 存在的核心原因是 Design Principle 4：No Silent Data Loss。

即使一个项目在某个阶段被淘汰（例如分类后确定为 `IGNORE`），以下原因决定它不能被静默删除：

1. **Audit 需求** — 需要确认系统没有错误地淘汰了本应保留的项目
2. **统计需求** — Daily Report 的 Section A（今日概览）需要统计 Ignore 项目的数量
3. **调试需求** — 当用户发现"某个应该出现的项目没有出现在日报中"时，可以通过 `FILTERED_BY_*` 状态快速定位原因

被淘汰的项目将 `pipeline_status` 设置为对应值，然后进入 ARCHIVED 状态。它们不进入 Daily Report 主体，但存在于历史数据中。

---

## 12. Data Lineage Rules

### 12.1 `project_id` 的贯穿路径

```
Stage 1 (Raw)
├── project_id: "gt-20260614-openmanus"
├── project_name: "OpenManus"
├── stars: 8500
├── pipeline_status: "PROMOTED"
│
↓ Stage 2 (Normalized)
├── project_id: "gt-20260614-openmanus"  ← 相同
├── normalized_description: "..."        ← 新增
├── extracted_keywords: ["agent", ...]   ← 新增
│
↓ Stage 3 (Classified)
├── project_id: "gt-20260614-openmanus"  ← 相同
├── primary_category: "Agent Framework"  ← 新增
├── classification_confidence: "HIGH"    ← 新增
│
↓ Stage 4 (Scored)
├── project_id: "gt-20260614-openmanus"  ← 相同
├── career_alignment: 40                 ← 新增
├── total_score: 96                      ← 新增
├── recommendation: "STRONG_RECOMMEND"   ← 新增
│
↓ Stage 5 (Ranked)
├── project_id: "gt-20260614-openmanus"  ← 相同
├── rank: 1                              ← 新增
├── ranking_group: "STRONG_RECOMMEND"    ← 新增
│
↓ Stage 6 (Report)
├── project_id: "gt-20260614-openmanus"  ← 相同
├── summary: "..."                       ← 新增
├── recommended_read_time: 15            ← 新增
```

在每个阶段，`project_id` 的值保持不变。通过 `project_id` 可以从 Report Item 一直回溯到 Raw Project。

### 12.2 回溯查询路径

```
从日报中的某条推荐：
  project_id: "gt-20260614-openmanus"
    → 查询 Stage 6 数据（展示层）
    → 查询 Stage 5 数据（排名信息）
    → 查询 Stage 4 数据（评分信息）
    → 查询 Stage 3 数据（分类信息）
    → 查询 Stage 2 数据（归化信息）
    → 查询 Stage 1 数据（原始数据）
```

---

## 13. Batch vs Item Rules

### 13.1 核心区分

| 维度 | Item Processing | Batch Processing |
|------|----------------|------------------|
| 适用 Stage | Stage 1~4 | Stage 5~6 |
| 处理单元 | 单个项目 | 项目集合（当日所有项目） |
| 是否依赖其他项目 | 否 | 是（排名依赖于其他项目的分数） |
| 产生字段 | category, score 等 | rank, ranking_group |

### 13.2 为什么 `rank` 只能在 Batch 阶段出现

Rank 是一个相对值。一个项目的 rank 不是由它自身决定的，而是由它与其他项目比较的结果决定的。例如，如果当天有 30 个项目，Score 最高的项目 rank=1，最低的 rank=30。在 Item Processing 阶段，系统不知道其他项目的情况，因此无法产生 rank。

### 13.3 混合处理

- Stage 5（Ranking）是 Batch 处理的第一个阶段
- Stage 6（Report）也是 Batch 处理（需要依赖整组数据生成 Section E 的主题分布和 Section F 的每日阅读建议）

---

## 14. Field Ownership Rules

### 14.1 所有权矩阵

每个字段由产生它的阶段或 Agent "拥有"。只有拥有者可以修改该字段。

| 字段 | 拥有者 | 产生 Stage | 修改权限 |
|------|--------|-----------|----------|
| `project_id` | Stage 1 | Stage 1 | 禁止修改 |
| `project_name` | Stage 1 | Stage 1 | 禁止修改 |
| `owner` | Stage 1 | Stage 1 | 禁止修改 |
| `description` | Stage 1 | Stage 1 | 禁止修改 |
| `topics` | Stage 1 | Stage 1 | 禁止修改 |
| `stars` | Stage 1 | Stage 1 | 可更新（Stage 6 中可能更新为最新值） |
| `source` | Stage 1 | Stage 1 | 禁止修改 |
| `collection_date` | Stage 1 | Stage 1 | 禁止修改 |
| `normalized_description` | Stage 2 | Stage 2 | 禁止修改（如需要调整，回退到 Stage 1 重新处理） |
| `primary_language` | Stage 2 | Stage 2 | 禁止修改 |
| `extracted_keywords` | Stage 2 | Stage 2 | 禁止修改 |
| `primary_category` | Classification Agent | Stage 3 | 仅 Classification Agent 可修改 |
| `secondary_categories` | Classification Agent | Stage 3 | 仅 Classification Agent 可修改 |
| `classification_confidence` | Classification Agent | Stage 3 | 仅 Classification Agent 可修改 |
| `classification_notes` | Classification Agent | Stage 3 | 仅 Classification Agent 可修改 |
| `career_alignment` | Scoring Agent | Stage 4 | 仅 Scoring Agent 可修改 |
| `interest_match` | Scoring Agent | Stage 4 | 仅 Scoring Agent 可修改 |
| `trend_heat` | Scoring Agent | Stage 4 | 仅 Scoring Agent 可修改 |
| `research_relevance` | Scoring Agent | Stage 4 | 仅 Scoring Agent 可修改 |
| `total_score` | Scoring Agent | Stage 4 | 仅 Scoring Agent 可修改（必须为四维之和） |
| `recommendation` | Scoring Agent | Stage 4 | 仅 Scoring Agent 可修改 |
| `reasoning` | Scoring Agent | Stage 4 | 仅 Scoring Agent 可修改 |
| `career_goal_impact` | Scoring Agent | Stage 4 | 仅 Scoring Agent 可修改 |
| `rank` | Ranking Stage | Stage 5 | 仅 Ranking Stage 可修改 |
| `ranking_group` | Ranking Stage | Stage 5 | 仅 Ranking Stage 可修改（必须与 recommendation 一致） |
| `summary` | Report Stage | Stage 6 | 仅 Report Stage 可修改 |
| `recommended_read_time` | Report Stage | Stage 6 | 仅 Report Stage 可修改 |
| `daily_priority` | Report Stage | Stage 6 | 仅 Report Stage 可修改 |
| `pipeline_status` | Pipeline | Stage 1 | 任何 Stage 可修改（但仅允许设置为枚举值之一） |

### 14.2 禁止跨阶段修改

**核心原则：任何阶段都不能修改不属于它的字段。**

示例：

- Scoring Agent 不能修改 `primary_category`（属于 Classification Agent）
- Ranking Stage 不能修改 `total_score`（属于 Scoring Agent）
- Report Stage 不能修改 `career_alignment`（属于 Scoring Agent）

违反此规则将导致数据不可追溯。如果发现某个字段需要跨阶段修改，说明 Pipeline 设计有误，应该调整数据流结构而不是允许跨阶段修改。

---

## 15. Relationship with PKIA Documents

本文件是 PKIA v0.1 文档体系中的"数据层"，与其他文档的关系如下：

### 15.1 职责边界总览

```
interest_profile_v1.md
  职责：定义用户兴趣画像
  输出：S/A/B Tier 定义 + Career Goals
  关系：Schema 的评分字段（career_alignment, interest_match）在此文档中定义评分依据

project_classification_taxonomy_v1.md
  职责：定义分类体系
  输出：11 个 Level-1 类别，32 个 Level-2 类别
  关系：Schema 的 primary_category 字段的值必须来自 Taxonomy

classification_agent_spec_v1.md
  职责：定义如何执行分类
  输出：分类结果（Primary + Secondary + Confidence）
  关系：Schema 的 Stage 3 结构定义与此文档 §4 的输出定义保持一致

prompt_scoring_agent_v2.md
  职责：定义如何执行评分
  输出：4 维度分数 + Career Goal Impact
  关系：Schema 的 Stage 4 结构定义与此文档 §12 的输出格式保持一致

scoring_pipeline_schema_v1.md
  职责：定义评分流程
  输出：10 阶段 Pipeline
  关系：Schema 的 Stage 1~5 对应 Pipeline 的 Stage 1~10

report_generation_pipeline_v1.md
  职责：定义报告生成流程
  输出：Report Item → Daily Report
  关系：Schema 的 Stage 6 定义在此文档中消费

daily_report_spec_v1.md
  职责：定义日报格式
  输出：6 章节日报
  关系：Schema 的 Stage 6（Report Item）是日报的组成单元
```

### 15.2 职责分离总结

| 文档 | 核心问题 | 定位 |
|------|----------|------|
| interest_profile_v1.md | 用户关注什么？ | 兴趣定义层 |
| project_classification_taxonomy_v1.md | 有哪些类别？ | 分类定义层 |
| classification_agent_spec_v1.md | 如何分类？ | 分类执行层 |
| prompt_scoring_agent_v2.md | 如何评分？ | 评分执行层 |
| **project_data_schema_v1.md（本文件）** | **数据长什么样？** | **数据定义层** |
| scoring_pipeline_schema_v1.md | 如何编排？ | 流程编排层 |
| report_generation_pipeline_v1.md | 如何生日报？ | 报告执行层 |
| daily_report_spec_v1.md | 日报长什么样？ | 展示定义层 |

---

## Appendix A — End-to-End Data Flow Example: MarkItDown

此示例展示 MarkItDown（一个文档转换工具）在 PKIA 数据管线中的完整生命周期。

### Stage 1: Raw Project

```
project_id: "gt-20260619-markitdown"
project_name: "MarkItDown"
owner: "microsoft"
description: "Python tool for converting files and office documents to Markdown."
topics: ["python", "markdown", "converter", "documents"]
stars: 25000
forks: 1200
language: "Python"
source: "github_trending"
collection_date: "2026-06-19"
pipeline_status: "PROMOTED"
```

### Stage 2: Normalized Project

继承 Stage 1 所有字段，新增：

```
normalized_description: "Python tool for converting files and office documents to Markdown."
primary_language: "Python"
extracted_keywords: ["python", "markdown", "converter", "documents"]
```

### Stage 3: Classification Output

继承 Stage 2 所有字段，新增：

```
primary_category: "UNCLASSIFIED_AI_PROJECT"
secondary_categories: ["RAG → Knowledge Ingestion"]
classification_confidence: "LOW"
classification_notes: "MarkItDown converts file formats to Markdown. Functionally close to RAG Knowledge Ingestion but strictly speaking not part of RAG ecosystem. No existing Taxonomy category fits precisely."
```

### Stage 4: Scoring Output

继承 Stage 3 所有字段，新增：

```
career_alignment: 12
interest_match: 8
trend_heat: 10
research_relevance: 3
total_score: 33
recommendation: "IGNORE"
reasoning: "MarkItDown is classified as UNCLASSIFIED_AI_PROJECT. Document conversion is tangentially relevant to RAG pipeline preprocessing (career goal #2) but does not directly serve any primary career goal. Trend Heat is moderate. Research value is low."
career_goal_impact: {
  agent_application_engineer: "LOW",
  ai_platform_engineer: "MEDIUM",
  llm_inference_optimization_engineer: "LOW",
  multi_agent_system_engineer: "LOW"
}
```

### Stage 5: Ranking Output

继承 Stage 4 所有字段，新增：

```
rank: 28
ranking_group: "IGNORE"
```

`pipeline_status` 更新为：

```
pipeline_status: "FILTERED_BY_SCORE"
```

### Stage 6: Report Item

MarkItDown 的总分 33 属于 IGNORE 等级，因此不会出现在 Daily Report 的 Section B/C/D 主体中。但其统计数据出现在 Section A。

```
summary: "Microsoft 出品的文档转 Markdown 工具，与 RAG 预处理流程间接相关。"
recommended_read_time: 10
daily_priority: null
pipeline_status: "ARCHIVED"
```

---

## Appendix B — Schema Evolution Rules

### B.1 版本标识

Schema 版本号遵循 `v{major}` 格式（如 `v1`, `v2`）。每次更新递增主版本号。

### B.2 v1 → v2 规则

| 操作 | 允许 | 说明 |
|------|------|------|
| 新增字段 | ✅ 允许 | 必须有"预期使用版本"标记，如 `expected_version: "v2"` |
| 删除字段 | ❌ 禁止 | 只能弃用（标记为 `deprecated`），不能物理删除 |
| 修改字段类型 | ❌ 禁止 | 如必须修改，新增字段替换旧字段，旧字段标记为 `deprecated` |
| 修改 project_id 语义 | ❌ 禁止 | `project_id` 的生成规则一旦确定，永远不得修改 |
| 修改枚举值的含义 | ❌ 禁止 | 新的枚举值只能新增不能修改已有值 |
| 新增枚举值 | ✅ 允许 | 如新增 recommendation 枚举值 |

### B.3 弃用字段的标记

弃用字段必须：

1. 在字段定义中添加 `deprecated: true` 标记
2. 在字段定义中添加 `deprecated_in_version: "v2"` 标记
3. 在字段定义中添加 `replaced_by: "new_field_name"` 标记（如适用）
4. 弃用的字段在实际数据中至少保留一个版本周期（`v2` 弃用的字段在 `v3` 中才能移除）

### B.4 向后兼容保证

- Schema vN 的消费者必须能正确处理 Schema vN-1 产生的数据
- 新增字段不能改变已有字段的语义
- 字段的默认值策略必须在新旧版本之间一致

### B.5 更新流程

1. 更新 `project_data_schema_v1.md`（或创建 `project_data_schema_v2.md`）
2. 更新受影响的 Agent Spec 文档
3. 更新 Pipeline Schema
4. 更新 Daily Report Spec
5. 所有更新完成后，记录版本变更日期和变更摘要

所有文档的更新必须在 Schema 更新后的一个工作日内同步完成。

---

*End of Schema v1. Defines canonical data structures for all PKIA pipeline stages.*