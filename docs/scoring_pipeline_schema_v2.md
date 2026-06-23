# PKIA Scoring Pipeline Schema v2

---

## 1. Purpose

本文件定义 PKIA v0.1 评分流水线的完整架构。它替代 `scoring_pipeline_schema_v1.md`，修复了审查发现的所有 10 个 P0 一致性问题。

### Design Principles

1. **Schema First** — 所有 Stage 输出字段的定义必须引用 `project_data_schema_v1.md`，不得重新定义字段
2. **Data Lineage First** — `project_id` 必须贯穿全部 10 个 Stage，每个 Stage 输出必须包含此字段
3. **No Silent Data Loss** — 通过 `pipeline_status` 跟踪所有项目状态，被淘汰的项目不会静默删除
4. **Classification First** — Stage 3 分类完成后才允许进入评分阶段；Stage 2 不包含任何分类字段
5. **Batch-Aware Design** — Stage 1~9 为 Item Processing，Stage 10 为 Batch Processing

### 与 v1 的关系

本文件吸收 `scoring_pipeline_patch_plan_v1.md` 的全部补丁，并基于 `project_data_schema_v1.md` 重新组织了 Stage 输出定义。10 个 Pipeline Stage 的结构保持不变，但每个 Stage 的输出字段、生命周期规则和所有权边界已与 Schema 对齐。

---

## 2. Pipeline Overview

PKIA 评分流水线包含 10 个阶段：

```
┌─────────────────────────────────────────────────────┐
│               Item Processing Flow                   │
│  Stage  1: Data Collection                           │
│  Stage  2: Project Normalization                     │
│  Stage  3: Category Classification                   │
│  Stage  4: Career Alignment Scoring                  │
│  Stage  5: Interest Match Scoring                    │
│  Stage  6: Trend Heat Scoring                        │
│  Stage  7: Research Relevance Scoring                │
│  Stage  8: Total Score Calculation                   │
│  Stage  9: Recommendation Assignment                 │
├─────────────────────────────────────────────────────┤
│               Batch Processing Flow                  │
│  Stage 10: Daily Report Ranking                      │
└─────────────────────────────────────────────────────┘
```

每个阶段均为独立步骤。前一个阶段的输出是下一个阶段的标准输入。不允许跨阶段跳跃。所有阶段共享 `project_id` 和 `pipeline_status` 作为全局标识字段。

---

## 3. Stage Mapping: Pipeline ↔ Schema

| Pipeline Stage | Pipeline Output | Schema Stage | Schema Fields | Relationship |
|---------------|----------------|--------------|---------------|-------------|
| 1. Data Collection | Raw project list | Stage 1 (Raw) | `project_id`, `project_name`, `owner`, `description`, `topics`, `stars`, `forks`, `language`, `source`, `collection_date`, `pipeline_status` | 1:1 Direct |
| 2. Normalization | Normalized project | Stage 2 (Normalized) | Inherits Stage 1 + `normalized_description`, `primary_language`, `extracted_keywords` | 1:1 Direct |
| 3. Classification | Classification result | Stage 3 (Classified) | Inherits Stage 2 + `primary_category`, `secondary_categories`, `classification_confidence`, `classification_notes` | 1:1 Direct |
| 4. Career Alignment | 0~40 score | Stage 4 (Scored) | `career_alignment` | 4:N Composite |
| 5. Interest Match | 0~30 score | Stage 4 (Scored) | `interest_match` | 4:N Composite |
| 6. Trend Heat | 0~20 score | Stage 4 (Scored) | `trend_heat` | 4:N Composite |
| 7. Research Relevance | 0~10 score | Stage 4 (Scored) | `research_relevance` | 4:N Composite |
| 8. Total Score | 0~100 + metadata | Stage 4 (Scored) | `total_score`, `reasoning`, `career_goal_impact` | 1:N Enriched |
| 9. Recommendation | STRONG_RECOMMEND... | Stage 4 (Scored) | `recommendation` | 1:1 Direct |
| 10. Ranking | Ranked list | Stage 5 (Ranked) | `rank`, `ranking_group` | 1:1 Direct |

**关键说明：** Pipeline Stage 4~9 是评分子步骤，它们共同产生 Schema 的 Stage 4 (Scoring Output Object)。这是一种 4:N Composite 映射关系——Pipeline 提供更细粒度的过程文档，Schema 定义统一的数据结构。两者不是冲突，而是不同粒度的表达。

---

## 4. Stage 1: Data Collection

### 目的

从数据源获取原始项目信息。此阶段不做任何判断、过滤或结构化处理。

### 输入

GitHub Trending Top 30（由 `data_collection_strategy_v1.md` 定义）

### 输出

每个项目输出以下标准化字段，与 `project_data_schema_v1.md` §5.2 完全一致：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `project_id` | string | 是 | 全局唯一标识，进入 PKIA 时立即生成 |
| `project_name` | string | 是 | GitHub 仓库名称（如 "LangGraph"） |
| `owner` | string | 是 | 项目所属组织或作者 |
| `description` | string | 是 | GitHub 项目的描述文本 |
| `topics` | list[string] | 否 | GitHub Topics 标签列表 |
| `stars` | integer | 是 | GitHub Stars 数量 |
| `forks` | integer | 否 | GitHub Forks 数量 |
| `language` | string | 否 | GitHub 检测到的主编程语言 |
| `source` | string (enum) | 是 | 数据来源：`github_trending` |
| `collection_date` | date | 是 | 采集日期 |
| `pipeline_status` | string (enum) | 是 | 初始值为 `PROMOTED` |

### 规则

- **仅负责收集，不做判断。** 此阶段不进行任何过滤、分类或评分
- `project_id` 在此阶段生成后不得再修改
- 以下字段在此阶段**禁止**出现：`primary_category`, `secondary_categories`, `classification_confidence`, `career_alignment`, `interest_match`, `trend_heat`, `research_relevance`, `total_score`, `recommendation`, `rank`, `ranking_group`, `normalized_description`, `extracted_keywords`
- 采集失败时，保留上一次成功采集的数据作为降级方案

### Schema 引用

`project_data_schema_v1.md` §5 (Stage 1 — Raw Project Object)

---

## 5. Stage 2: Project Normalization

### 目的

将原始项目数据标准化为统一格式，为分类阶段做准备。此阶段消除不同数据源之间的格式差异。

### 输入

Stage 1 输出的原始项目列表

### 输出

继承 Stage 1 的全部字段，并新增以下字段（与 `project_data_schema_v1.md` §6.2 一致）：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `normalized_description` | string | 是 | Description 的截断/摘要版本，不超过 200 字符 |
| `primary_language` | string | 否 | 标准化后的主编程语言 |
| `extracted_keywords` | list[string] | 否 | 从 Description 和 Topics 中提取的核心关键词，最多 5 个 |

### 规则

- `description` 超过 200 字符时截断为 `normalized_description`
- `extracted_keywords` 的提取规则：优先使用 Topics，Topics 不足时从 Description 中提取
- **Stage 2 不产生任何与分类相关的字段。** `primary_category`、`secondary_categories`、`classification_confidence` 等分类字段属于 Stage 3
- 禁止出现：`primary_category`, `secondary_categories`, `classification_confidence`, `classification_notes`, `项目领域`

### 对比：v1 的变更

| v1 (问题) | v2 (修复) |
|-----------|----------|
| 使用中文字段名（项目名称、一句话描述等） | 使用 snake_case 英文（`project_name`, `normalized_description`） |
| 包含"项目领域"（属于 Stage 3） | 已移除 |
| 包含"核心能力"（非 Schema 字段） | 替换为 `extracted_keywords` |

### Schema 引用

`project_data_schema_v1.md` §6 (Stage 2 — Normalized Project Object)

---

## 6. Stage 3: Category Classification

### 目的

将项目归类到 Interest Profile 定义的领域类别。此阶段是项目获得"身份"的阶段。

### 输入

Stage 2 输出的标准化项目对象

### 输出

继承 Stage 2 的全部字段，并新增以下字段（与 `project_data_schema_v1.md` §7.2 一致，与 `classification_agent_spec_v1.md` §4 一致）：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `primary_category` | string | 是 | 项目的主要类别，必须是 Taxonomy 定义的 Level-2 类别或特殊类别之一 |
| `secondary_categories` | list[string] | 否 (0~3) | 项目的次要类别，用于 Interest Match 精细调整 |
| `classification_confidence` | string (enum) | 是 | `HIGH` / `MEDIUM` / `LOW`。不是百分比，不是概率分数 |
| `classification_notes` | string | 否 | 分类依据说明 |

`classification_confidence` 使用三档枚举（与 `project_data_schema_v1.md` §7.3 一致）：

| 枚举值 | 含义 |
|--------|------|
| `HIGH` | 分类明确，无歧义 |
| `MEDIUM` | 存在一定模糊性，但可做出合理判断 |
| `LOW` | 推测性分类，需要下游谨慎处理 |

### Pipeline Status 更新

此阶段可根据分类结果更新 `pipeline_status`：

| 分类结果 | pipeline_status | 后续处理 |
|----------|----------------|----------|
| 属于 Interest Profile 的有效类别 | `PROMOTED` | 进入评分阶段 |
| 属于 Ignore 列表（Frontend, Mobile, Blockchain, Crypto, NFT, Web3） | `FILTERED_BY_CATEGORY` | 终止评分，进入 ARCHIVED |

### 规则

- **每个项目必须且只能有一个 Primary Category**
- 分类逻辑由 `classification_agent_spec_v1.md` 定义，Pipeline 不重复定义分类规则
- 此阶段不进行任何评分。评分从 Stage 4 开始

### Schema 引用

- `project_data_schema_v1.md` §7 (Stage 3 — Classification Output Object)
- `classification_agent_spec_v1.md` §4, §7

---

## 7. Stage 4: Career Alignment Scoring

### 目的

评估项目与用户四个职业目标的直接相关性。

### 输入

- Stage 3 输出的 `primary_category`
- Stage 3 输出的 `secondary_categories`

### 输出

| 字段 | 类型 | 范围 | 说明 |
|------|------|------|------|
| `career_alignment` | integer | 0~40 | 与职业目标的匹配程度 |

### 评分基准

由 `scoring_strategy_v1.md` 定义：

| Primary Category 所在层级 | 基准分 |
|---------------------------|--------|
| S Tier（核心赛道） | 40 |
| A Tier（强相关） | 30 |
| Frontier AI Trends | 20 |
| B Tier（弱相关） | 10 |
| Ignore | 0 |

### 调整规则

在基准分基础上，Scoring Agent 可根据以下因素在 ±3 范围内调整：
- **正向调整（+1~3）：** 是否直接支持构建生产级 Agent 产品？是否作为 PKIA 的底层实现平台？
- **负向调整（-1~3）：** 与职业目标的关系是否间接？是否重复已有工具生态？

### 规则

- `pipeline_status` 保持为 `PROMOTED`（已由 Stage 3 决定）
- 此阶段不修改 `primary_category` 或 `classification_confidence`

### Schema 引用

`project_data_schema_v1.md` §8 (Stage 4 — Scoring Output Object)

---

## 8. Stage 5: Interest Match Scoring

### 目的

评估项目与用户兴趣画像的匹配程度。

### 输入

Stage 3 输出的 `secondary_categories`

### 输出

| 字段 | 类型 | 范围 | 说明 |
|------|------|------|------|
| `interest_match` | integer | 0~30 | 与兴趣画像的匹配程度 |

### 评分规则

| 匹配层级 | 分数范围 | 条件 |
|----------|----------|------|
| S Tier | 25~30 | 匹配 S Tier 领域 |
| A Tier | 20~25 | 匹配 A Tier 领域 |
| B Tier | 8~15 | 匹配 B Tier 领域 |
| Ignore | 0~5 | 匹配 Ignore 列表 |

### Schema 引用

`project_data_schema_v1.md` §8 (Stage 4 — Scoring Output Object)

---

## 9. Stage 6: Trend Heat Scoring

### 目的

评估项目的当前社区热度。

### 输入

Stage 2 输出的 `stars` 数和活跃度信号

### 输出

| 字段 | 类型 | 范围 | 说明 |
|------|------|------|------|
| `trend_heat` | integer | 0~20 | 社区热度和关注度 |

### 评分规则

| 热度水平 | 分数范围 | 典型信号 |
|----------|----------|----------|
| 爆炸增长 | 16~20 | 千级以上 Stars，高频 Releases |
| 稳定增长 | 10~15 | 持续多日 Trend，中等活跃度 |
| 小众稳定 | 5~10 | 小社区但持续维护 |
| 下降/停滞 | 0~5 | 长期无更新 |

### Schema 引用

`project_data_schema_v1.md` §8 (Stage 4 — Scoring Output Object)

---

## 10. Stage 7: Research Relevance Scoring

### 目的

评估项目的长期研究价值和技术创新性。

### 输入

Stage 2 输出的 `normalized_description` 和 `extracted_keywords`

### 输出

| 字段 | 类型 | 范围 | 说明 |
|------|------|------|------|
| `research_relevance` | integer | 0~10 | 长期研究价值 |

### 评分规则

| 研究价值 | 分数范围 | 典型信号 |
|----------|----------|----------|
| 高 | 8~10 | 新范式、新架构、活跃的研究领域 |
| 中 | 5~7 | 扎实的增量工作，有工程落地价值 |
| 低 | 2~4 | 实现导向，已有成熟方案 |
| 无 | 0~2 | 纯产品发布、新闻事件 |

### Schema 引用

`project_data_schema_v1.md` §8 (Stage 4 — Scoring Output Object)

---

## 11. Stage 8: Total Score Calculation

### 目的

汇总四个维度的评分，生成总分和补充信息。

### 输入

- Stage 4: `career_alignment` (0~40)
- Stage 5: `interest_match` (0~30)
- Stage 6: `trend_heat` (0~20)
- Stage 7: `research_relevance` (0~10)

### 输出

继承 Stage 3 全部字段 + Stage 4~7 的评分字段，并新增（与 `project_data_schema_v1.md` §8.2 一致）：

| 字段 | 类型 | 范围 | 必填 | 说明 |
|------|------|------|------|------|
| `total_score` | integer | 0~100 | 是 | 四维分数之和 |
| `reasoning` | string | — | 是 | 评分理由的详细说明 |
| `career_goal_impact` | object | — | 是 | 对四个职业目标的影响评估 |

### 公式

```
total_score = career_alignment + interest_match + trend_heat + research_relevance
```

### `career_goal_impact` 子字段

与 `project_data_schema_v1.md` §8.3 和 `prompt_scoring_agent_v2.md` §12 一致：

| 子字段 | 类型 | 允许值 |
|--------|------|--------|
| `agent_application_engineer` | string (enum) | `HIGH`, `MEDIUM`, `LOW` |
| `ai_platform_engineer` | string (enum) | `HIGH`, `MEDIUM`, `LOW` |
| `llm_inference_optimization_engineer` | string (enum) | `HIGH`, `MEDIUM`, `LOW` |
| `multi_agent_system_engineer` | string (enum) | `HIGH`, `MEDIUM`, `LOW` |

### Pipeline Status 更新

| 总分 | pipeline_status | 后续处理 |
|------|----------------|----------|
| ≥ 40 | `PROMOTED` | 进入 Ranking |
| < 40 (IGNORE) | `FILTERED_BY_SCORE` | 进入 ARCHIVED，不进入 Daily Report 主体 |

### 规则

- `total_score` 必须严格等于四维分数之和，不允许额外调整
- `reasoning` 必须解释每个分数的依据，禁止仅输出分数
- `career_goal_impact` 的每个子字段都必须赋值，不允许空值
- 任何维度缺失时，该维度按 0 分处理并在 `reasoning` 中注明

### Schema 引用

- `project_data_schema_v1.md` §8 (Stage 4 — Scoring Output Object)
- `prompt_scoring_agent_v2.md` §12

---

## 12. Stage 9: Recommendation Assignment

### 目的

将总分映射到推荐等级。

### 输入

Stage 8 输出的 `total_score`

### 输出

| 字段 | 类型 | 说明 |
|------|------|------|
| `recommendation` | string (enum) | `STRONG_RECOMMEND`, `RECOMMEND`, `OBSERVE`, `IGNORE` |

### 映射规则

由 `scoring_strategy_v1.md` 定义：

| 总分范围 | 等级 |
|----------|------|
| 90+ | 🔴 `STRONG_RECOMMEND` |
| 70~89 | 🟡 `RECOMMEND` |
| 40~69 | ⚪ `OBSERVE` |
| 0~39 | ⚫ `IGNORE` |

### 规则

- 此阶段是纯规则映射，不存在主观判断
- 边界值统一向上取整（70 分 → `RECOMMEND`，90 分 → `STRONG_RECOMMEND`）

### Schema 引用

`project_data_schema_v1.md` §8.4 (推荐等级枚举)

---

## 13. Stage 10: Daily Report Ranking

### 目的

将所有评分完成的项目排序，生成 Daily Report 的内容顺序。此阶段是 **Batch Processing**——排序依赖同批次其他项目的信息。

### 输入

- Stage 8 的 `total_score`
- Stage 9 的 `recommendation`

### 输出

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `rank` | integer | 是 | 在当日所有项目中的排名（1~30） |
| `ranking_group` | string (enum) | 是 | `STRONG_RECOMMEND`, `RECOMMEND`, `OBSERVE`, `IGNORE` |

### 排序规则

1. **一级排序：** `ranking_group` — Strong Recommend > Recommend > Observe > Ignore
2. **二级排序：** `total_score` — 同等级内按总分降序
3. **三级排序：** `career_alignment` — 同分时职业相关性高的优先
4. **四级排序：** `interest_match` — 仍相同时兴趣匹配度高的优先

### Pipeline Status 更新

所有项目在 Stage 10 完成后设置 `pipeline_status: ARCHIVED`。

### 与 Daily Report 的关系

输出直接对应 `daily_report_spec_v1.md` 的 Section B (Strong Recommend)、Section C (Recommend)、Section D (Observe)。Ignore 等级的项目不出现在日报主体中，但统计数据出现在 Section A。

### Schema 引用

- `project_data_schema_v1.md` §9 (Stage 5 — Ranking Output Object)
- `project_data_schema_v1.md` §13 (Batch vs Item Processing)

---

## 14. Pipeline Status Lifecycle

### 生命周期图

```
Stage 1: pipeline_status = PROMOTED (初始值)
  │
  ▼
Stage 3 (Classification):
  ├── 有效类别 (S/A/B Tier) → PROMOTED (进入评分)
  └── Ignore 列表 → FILTERED_BY_CATEGORY
          │
          ▼
        ARCHIVED（保留在历史数据中）
  │
  ▼
Stage 8 (Total Score):
  ├── total_score ≥ 40 → PROMOTED (进入 Ranking)
  └── total_score < 40 (IGNORE) → FILTERED_BY_SCORE
          │
          ▼
        ARCHIVED
  │
  ▼
Stage 10 (Ranking):
  └── 全部项目 → ARCHIVED
```

### 各 Stage 的 pipeline_status 权限

| Stage | 可设置 | 可读取 | 状态值 |
|-------|--------|--------|--------|
| 1 | ✅ 初始化 | — | `PROMOTED` |
| 2 | ❌ | ✅ | 继承自 Stage 1 |
| 3 | ✅ 更新 | ✅ | `PROMOTED` 或 `FILTERED_BY_CATEGORY` |
| 4~7 | ❌ | ✅ | 继承自 Stage 3 |
| 8 | ✅ 更新 | ✅ | `PROMOTED` 或 `FILTERED_BY_SCORE` |
| 9 | ❌ | ✅ | 继承自 Stage 8 |
| 10 | ✅ 更新 | ✅ | 设置 `ARCHIVED` |

### 无静默数据丢失

被淘汰的项目（`FILTERED_BY_CATEGORY` 或 `FILTERED_BY_SCORE`）不会删除。它们存在于历史数据中，可供审计、统计和调试。

### Schema 引用

`project_data_schema_v1.md` §11 (Pipeline Status Rules)

---

## 15. Data Lineage

### `project_id` 贯穿路径

```
Stage 1 (Data Collection)
  └── project_id: "gt-20260614-openmanus" (生成)
        ↓
Stage 2 (Normalization)
  └── project_id: 相同 (继承)
        ↓
Stage 3 (Classification)
  └── project_id: 相同 (继承)
        ↓
Stage 4-9 (Scoring + Recommendation)
  └── project_id: 相同 (继承)
        ↓
Stage 10 (Ranking)
  └── project_id: 相同 (继承)
        ↓
Report Generation (report_generation_pipeline_v1.md)
  └── project_id: 相同 (继承)
```

### 回溯查询路径

从日报中的某条推荐可反向追溯：
```
Daily Report Item
  → project_id
  → Stage 10 data (ranking_group, rank)
  → Stage 8 data (total_score, reasoning, career_goal_impact)
  → Stage 3 data (primary_category, classification_confidence)
  → Stage 2 data (normalized_description, extracted_keywords)
  → Stage 1 data (project_name, owner, stars, description)
```

### 数据血缘规则

1. `project_id` 在 Stage 1 中生成，必须永不修改
2. 每个 Stage 的输出必须包含 `project_id` 作为必填字段
3. 如果某个 Stage 遇到没有 `project_id` 的项目，必须失败（而非生成新的）
4. 同一项目的 `project_id` 在所有 10 个 Stage 中必须完全相同

### Schema 引用

`project_data_schema_v1.md` §12 (Data Lineage Rules)

---

## 16. Item vs Batch Processing

### 核心区分

| 维度 | Item Processing | Batch Processing |
|------|----------------|------------------|
| 适用 Stage | Stage 1~9 | Stage 10 |
| 处理单元 | 单个项目 | 项目集合（当日所有项目） |
| 是否依赖其他项目 | 否 | 是 |
| 产生的字段 | category, score 等 | `rank`, `ranking_group` |

### 为什么 `rank` 只能在 Batch 阶段出现

Rank 是一个相对值。一个项目的 rank 不是由自身决定的，而是由它与其他项目比较的结果决定的。在 Item Processing 阶段（Stage 1~9），系统不知道其他项目的情况，因此无法产生 rank。

### Schema 引用

`project_data_schema_v1.md` §13 (Batch vs Item Processing Rules)

---

## 17. Document Relationships

本文件是 PKIA v0.1 文档体系中的"流程编排层"，与其他文档的关系如下：

### 职责边界总览

```
interest_profile_v1.md              [定义层]  用户兴趣画像
project_classification_taxonomy_v1.md [定义层] 分类体系
scoring_strategy_v1.md              [定义层]  评分策略
        ↓
classification_agent_spec_v1.md    [执行层]  分类执行
prompt_scoring_agent_v2.md         [执行层]  评分执行
        ↓
project_data_schema_v1.md          [数据层]  唯一数据契约
        ↓
scoring_pipeline_schema_v2.md (本文件) [流程层] 评分编排
        ↓
report_generation_pipeline_v1.md   [流程层]  报告生成
        ↓
daily_report_spec_v1.md            [展示层]  日报展示
```

### 各文档引用关系

| 文档 | 本文件的引用方式 |
|------|-----------------|
| `project_data_schema_v1.md` | 每个 Stage 的输出字段定义直接引用 Schema 的对应章节 |
| `classification_agent_spec_v1.md` | Stage 3 的分类逻辑由此文档定义；Pipeline 仅传递分类结果 |
| `prompt_scoring_agent_v2.md` | Stage 4~9 的评分逻辑由此 Prompt 定义；Pipeline 编排流程 |
| `scoring_strategy_v1.md` | Stage 4 的 Career Alignment 基准分和 Stage 9 的推荐阈值由此文档定义 |
| `report_generation_pipeline_v1.md` | Pipeline Stage 10 的输出由此文档消费 |
| `daily_report_spec_v1.md` | Pipeline 的最终输出对应 Daily Report 的 6 章节结构 |
| `scoring_pipeline_patch_plan_v1.md` | 本文件吸收此补丁计划的所有修正 |

---

## 18. Migration Notes: v1 → v2

### 变更摘要

| 类别 | v1 (问题) | v2 (修复) | 对应 P0 |
|------|-----------|-----------|---------|
| 字段命名 | "Repo Name" | `project_name` | P0-7 |
| 字段命名 | 中文字段名（5 个） | snake_case 英文 | P0-6 |
| 字段命名 | "Secondary Tags" | `secondary_categories` | P0-8 |
| 缺少字段 | `project_id` 完全不存在 | 所有 Stage 均包含 | P0-2 |
| 缺少字段 | `pipeline_status` 完全不存在 | 完整生命周期定义 | P0-1 |
| 缺少字段 | `classification_confidence` | Stage 3 输出新增 | P0-8 |
| 缺少字段 | `classification_notes` | Stage 3 输出新增 | P0-8 |
| 缺少字段 | `reasoning` | Stage 8 输出新增 | P0-9 |
| 缺少字段 | `career_goal_impact` | Stage 8 输出新增 | P0-10 |
| 缺少字段 | `rank`, `ranking_group` | Stage 10 输出新增 | P1 |
| Stage 边界 | Stage 2 包含"项目领域" | 已移除 | P0-3 |
| Stage 边界 | Stage 2 包含"核心能力" | 替换为 `extracted_keywords` | P0-4 |
| Stage 1 输出 | 4 个字段 | 11 个字段（与 Schema 一致） | P0-5 |
| 数据结构 | 未引用 Schema | 每个 Stage 均引用 Schema 对应章节 | Schema First |
| 数据血缘 | 无 | 完整 `project_id` 贯穿路径 | P0-2 |
| 生命周期 | 无 | `pipeline_status` 4 值生命周期 | P0-1 |
| 处理模式 | 隐式 | 明确区分 Item vs Batch Processing | P1 |
| Pipeline ↔ Schema | 未定义 | 完整映射表（§3） | — |

### 向后兼容性

- 10 个 Pipeline Stage 的结构和顺序未变更
- 评分逻辑（Career Alignment / Interest Match / Trend Heat / Research Relevance）未变更
- 推荐阈值（90+/70~89/40~69/0~39）未变更
- Stage 4~7 的独立评分阶段保留（它们与 Schema 的 4:N 复合映射关系已在 §3 中说明）

---

## 19. Expected Outputs

### 每项目最终输出

经过全部 10 个 Stage 处理后，每个项目携带以下字段进入 Report Generation Pipeline：

| 类别 | 字段 | 来源 Stage |
|------|------|-----------|
| 全局标识 | `project_id`, `project_name`, `source`, `collection_date` | Stage 1 |
| 原始数据 | `owner`, `description`, `topics`, `stars`, `forks`, `language` | Stage 1 |
| 标准化数据 | `normalized_description`, `primary_language`, `extracted_keywords` | Stage 2 |
| 分类结果 | `primary_category`, `secondary_categories`, `classification_confidence`, `classification_notes` | Stage 3 |
| 评分结果 | `career_alignment`, `interest_match`, `trend_heat`, `research_relevance`, `total_score`, `reasoning`, `career_goal_impact` | Stage 4~8 |
| 推荐等级 | `recommendation` | Stage 9 |
| 排名 | `rank`, `ranking_group` | Stage 10 |
| **状态** | **`pipeline_status`** | **贯穿所有 Stage** |

### 完整字段表

共约 26 个字段（含 `career_goal_impact` 的 4 个子字段），严格遵循 `project_data_schema_v1.md` 的 Stage 1~5 定义。

---

## 20. Success Criteria

| 条件 | 标准 |
|------|------|
| Schema 合规性 | 100% — 所有 Stage 输出字段与 project_data_schema_v1.md 完全一致 |
| 字段命名 | 全部 snake_case 英文，无中文 |
| project_id | 出现在所有 10 个 Stage |
| pipeline_status | 完整 4 值生命周期（PROMOTED → FILTERED_BY_CATEGORY / FILTERED_BY_SCORE → ARCHIVED） |
| Stage 边界 | Stage 2 不含分类字段，Stage 1 不含评分字段 |
| 分类输出 | 包含 primary_category, secondary_categories, classification_confidence, classification_notes |
| 评分输出 | 包含 career_alignment, interest_match, trend_heat, research_relevance, total_score, reasoning, recommendation, career_goal_impact |
| Batch/Item | Stage 1~9 = Item Processing, Stage 10 = Batch Processing, 明确说明 |
| 数据血缘 | 完整 project_id 贯穿路径，支持从报表回溯到原始数据 |
| 文档引用 | Schema 非"规划中"、引用 prompt v2 而非 v1、引用 classification_agent_spec、引用 report_generation_pipeline |

---

*End of Schema v2. Fully compliant with project_data_schema_v1.md. Replaces scoring_pipeline_schema_v1.md.*