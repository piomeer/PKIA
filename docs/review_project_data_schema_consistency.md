# Consistency Review Report

## docs/project_data_schema_v1.md 一致性审查

**审查日期：** 2026-06-19
**审查依据文档：** interest_profile_v1.md, project_classification_taxonomy_v1.md, classification_agent_spec_v1.md, prompt_scoring_agent_v2.md, scoring_pipeline_schema_v1.md, daily_report_spec_v1.md, report_generation_pipeline_v1.md
**审查对象：** docs/project_data_schema_v1.md

---

### 前置结论

`docs/project_data_schema_v1.md` **不存在**。该文件在整个 PKIA v0.1 文档体系中被多次引用（classification_agent_spec_v1.md 第 3 节、project_classification_taxonomy_v1.md 第 10 节），但均标注为"规划中"。本审查报告基于其他 6+ 文档对该文件的隐含依赖推导出一致性要求。

---

## 检查项 1: Raw Project Data 是否定义完整

**Status:** FAIL

**Reason:** 目标文件不存在。其他文档对 Raw Project Data 的字段需求散落在以下位置：

| 需求来源 | 字段 | 类型预期 |
|----------|------|----------|
| scoring_pipeline_schema_v1.md §3 (Stage 1 输出) | Repo Name | string |
| scoring_pipeline_schema_v1.md §3 (Stage 1 输出) | Description | string |
| scoring_pipeline_schema_v1.md §3 (Stage 1 输出) | Stars 数 | integer |
| scoring_pipeline_schema_v1.md §3 (Stage 1 输出) | Topics 标签 | list[string] |
| classification_agent_spec_v1.md §3 (必填输入) | Project Name | string |
| classification_agent_spec_v1.md §3 (必填输入) | Description | string |
| classification_agent_spec_v1.md §3 (必填输入) | Topics | list[string] |
| classification_agent_spec_v1.md §3 (必填输入) | Stars | integer |
| classification_agent_spec_v1.md §3 (必填输入) | Owner | string |
| classification_agent_spec_v1.md §3 (可选输入) | README Summary | string (摘要) |
| classification_agent_spec_v1.md §3 (可选输入) | Repository Language | string |
| classification_agent_spec_v1.md §3 (可选输入) | Last Updated | date |
| classification_agent_spec_v1.md §3 (可选输入) | License | string |

**字段不一致问题：** `scoring_pipeline_schema_v1.md` 使用"Repo Name"，`classification_agent_spec_v1.md` 使用"Project Name"。两者指同一字段但命名不一致。

**Impact:** HIGH — Raw Project Data 是所有下游处理的起点。缺失此文件意味着整个数据链的入口没有正式定义。字段命名不一致会导致实现时产生歧义。

**Required Fix:** 创建 `project_data_schema_v1.md`，统一命名使用 `project_name`，明确包含以下必填字段：`project_name`, `description`, `topics`, `stars`, `owner`，可选字段：`readme_summary`, `language`, `last_updated`, `license`。

---

## 检查项 2: Normalized Project Data 是否定义完整

**Status:** FAIL

**Reason:** 目标文件不存在。Normalized Project Data 的需求来自 scoring_pipeline_schema_v1.md §4 (Stage 2 输出)：

| 字段 | 说明 | 来源 |
|------|------|------|
| 项目名称 | 仓库名称 | GitHub Trending |
| 一句话描述 | Description 的第一句或核心摘要 | Description 字段 |
| 核心能力 | 该项目解决什么问题、提供什么能力 | Description 提炼 |
| 项目标签 | Topics 或自动抽取的关键词 | Topics + Description |
| 项目领域 | 按 Interest Tiers 映射的领域标签 | Stage 3 完成 |

**关键问题：** "项目领域" 字段在 Stage 2 的输出中被列为 Normalized Project 的一部分，但其说明中明确写道"按 Interest Tiers 映射的领域标签 — Stage 3 完成"。这意味着 Stage 2 的输出中包含了 Stage 3 才能产生的字段，造成阶段边界模糊。

此外，"核心能力"字段的定义过于模糊——"Description 提炼"没有任何结构化约束，不同的 Normalization 实现可能产生不同格式的输出。

**Impact:** HIGH — Normalized Project 是 Classification Agent 的直接输入。定义不清晰会导致 Classification Agent 的输入不可靠。

**Required Fix:** 
1. 将"项目领域"从 Normalized Project 中移除（它属于 Classification Result）
2. 为"核心能力"字段添加结构化约束（如限制为 3~5 个关键词或短语）
3. 统一字段命名风格（建议全英文或全中文，不要混用）

---

## 检查项 3: Classification Output 是否包含 Primary Category / Secondary Categories / Confidence / Classification Notes

**Status:** FAIL

**Reason:** 目标文件不存在。Classification Output 的需求定义在 `classification_agent_spec_v1.md` §4 和 `prompt_scoring_agent_v2.md` §2。

`classification_agent_spec_v1.md` §4 定义：

| 字段 | 类型 | 必填 |
|------|------|------|
| Primary Category | string | Yes |
| Secondary Categories | list[string] | No (0~3) |
| Confidence Level | High/Medium/Low | Yes |
| Classification Notes | string | Yes |

`prompt_scoring_agent_v2.md` §2 定义：

| 字段 | 类型 | 必填 |
|------|------|------|
| Primary Category | String (Level-2) | Yes |
| Secondary Categories | List (0~3) | No |
| Classification Confidence | Percentage (0~100%) | Yes |
| Classification Notes | Text | Yes |

**字段不一致问题：** `classification_agent_spec_v1.md` 的 Confidence Level 使用三档枚举（High/Medium/Low），而 `prompt_scoring_agent_v2.md` 的 Classification Confidence 使用百分比（0~100%）。两者语义相同但表示形式不同。如果 `project_data_schema_v1.md` 定义 Classification Output，必须选择一种表示方式。

**Impact:** MEDIUM — 两个文档对 Confidence 的表示方式不同，Schema 定义需要做一致性选择。

**Required Fix:** 
1. 在 `project_data_schema_v1.md` 中明确定义 Classification Output 结构
2. 统一 Confidence 的表示形式：建议使用百分比（0~100%）作为存储格式，High/Medium/Low 作为展示格式，两者之间建立映射规则（High=80~100%, Medium=50~79%, Low=0~49%）

---

## 检查项 4: Scoring Output 是否包含 Career Alignment / Interest Match / Trend Heat / Research Relevance / Total Score / Recommendation

**Status:** FAIL

**Reason:** 目标文件不存在。Scoring Output 的需求来自 `prompt_scoring_agent_v2.md` §12。

期望字段：

| 字段 | 类型 | 范围 |
|------|------|------|
| Career Alignment | integer | 0~40 |
| Interest Match | integer | 0~30 |
| Trend Heat | integer | 0~20 |
| Research Relevance | integer | 0~10 |
| Total Score | integer | 0~100 |
| Recommendation | enum | Strong Recommend / Recommend / Observe / Ignore |

`report_generation_pipeline_v1.md` §3 额外要求包含 Reasoning（文本）字段。

**Impact:** MEDIUM — Scoring Output 的字段定义在 prompt_scoring_agent_v2.md 中有清晰定义，但分散在两个文档中。Schema 需要整合两者。

**Required Fix:** 在 `project_data_schema_v1.md` 中定义 Scoring Output，整合 prompt_scoring_agent_v2.md 和 report_generation_pipeline_v1.md 的字段需求，确保包含 `reasoning` 字段。

---

## 检查项 5: 是否包含 Career Goal Impact

**Status:** FAIL

**Reason:** 目标文件不存在。Career Goal Impact 是 `prompt_scoring_agent_v2.md` §12 新增的输出字段，v1 中不存在。

期望字段：

| 字段 | 类型 | 可能值 |
|------|------|--------|
| #1 Agent Application Engineer | enum | High / Medium / Low |
| #2 AI Platform Engineer | enum | High / Medium / Low |
| #3 LLM Inference Optimization Engineer | enum | High / Medium / Low |
| #4 Multi-Agent System Engineer | enum | High / Medium / Low |

**Impact:** MEDIUM — Career Goal Impact 是 v2 新增的独立输出部分。如果 `project_data_schema_v1.md` 定义完整数据流，必须包含此结构。其他文档（report_generation_pipeline_v1.md, daily_report_spec_v1.md）尚未更新以展示 Career Goal Impact，存在展示层的缺口。

**Required Fix:** 
1. 在 `project_data_schema_v1.md` 的定义中包含 Career Goal Impact 结构
2. 检查 daily_report_spec_v1.md 是否需要新增 Career Goal Impact 展示区域（当前版本仅在 Reasoning 中提及职业目标，未独立展示）

---

## 检查项 6: 是否包含 Report Object

**Status:** FAIL

**Reason:** 目标文件不存在。Report Object 的需求来自 `daily_report_spec_v1.md` §3 和 `report_generation_pipeline_v1.md` §8。

`daily_report_spec_v1.md` 定义的 Daily Report 包含 6 个 Sections：
- Section A: 今日概览（统计数据）
- Section B: Strong Recommend（项目列表）
- Section C: Recommend（项目列表）
- Section D: Observe（项目列表）
- Section E: Interest Evolution（主题分布）
- Section F: What To Read Today（3 项推荐）

`report_generation_pipeline_v1.md` §8 定义了每节的展示格式。

**Impact:** LOW — Report Object 的消费者主要是 Report Generation Pipeline 和前端展示，项目数据 Schema 可能不需要完整定义日报结构（日报结构已由 daily_report_spec_v1.md 定义）。但如果 Schema 定义完整数据流（Raw → Normalized → Classified → Scored → Report），则需要包含 Ranked Project 列表作为 report 的组成部分。

**Required Fix:** 评估是否需要将 Report Object 纳入 `project_data_schema_v1.md`。建议在 Schema 中至少定义一个轻量级的 Report Header 结构（日期、数据源、统计信息），而非完整的 Report Body。

---

## 检查项 7: 是否包含完整数据流

**Status:** FAIL

**Reason:** 目标文件不存在。但完整的数据流散落在多个文档中：

```
GitHub Trending                          [data_collection_strategy_v1.md]
  ↓
Raw Project Data                         [预期在 project_data_schema_v1.md 中定义]
  ↓ (Stage 1: Data Collection)
Project Normalization                    [scoring_pipeline_schema_v1.md §4]
  ↓ (Stage 2: Normalization)
Normalized Project Data                  [预期在 project_data_schema_v1.md 中定义]
  ↓
Classification Agent                     [classification_agent_spec_v1.md]
  ↓ (Stage 3: Classification)
Classification Result                    [classification_agent_spec_v1.md §4, prompt_scoring_agent_v2.md §2]
  ↓
Scoring Agent                            [prompt_scoring_agent_v2.md]
  ↓ (Stage 4~8: Scoring)
Scoring Result                           [prompt_scoring_agent_v2.md §12, report_generation_pipeline_v1.md §3]
  ↓
Recommendation Assignment                [scoring_pipeline_schema_v1.md §11]
  ↓ (Stage 9: Recommendation)
Ranked Project                           [scoring_pipeline_schema_v1.md §12]
  ↓ (Stage 10: Daily Report Ranking)
Report Generation Pipeline               [report_generation_pipeline_v1.md]
  ↓
Daily Report                             [daily_report_spec_v1.md]
```

**数据流中的缺口：** 虽然数据流的逻辑在各文档中均有描述，但没有任何一个文档对**数据流的边界和数据结构的转换规则**进行统一定义。`project_data_schema_v1.md` 的缺失意味着从 Raw Project 到 Normalized Project 的字段映射规则、从 Normalized 到 Classification Result 的字段追加规则、从 Classification Result 到 Scoring Result 的字段追加规则都没有被正式定义。

**Impact:** HIGH — 数据流中各阶段的字段转换规则缺失。实现者需要自行推导以下映射：
- Raw Project 的 Repo Name → Normalized Project 的项目名称 (1:1)
- Raw Project 的 Description → Normalized Project 的一句话描述 (需截断)
- Raw Project 的 Description → Normalized Project 的核心能力 (需提炼)
- Normalized Project → Classification Result (追加 Primary Category 等)
- Classification Result → Scoring Result (追加 4 维度分数等)

**Required Fix:** 在 `project_data_schema_v1.md` 中使用统一的字段命名规范，定义每个数据阶段的结构，并明确标注字段在各阶段之间的转换关系（新增、保留、修改或删除）。

---

## Overall Consistency Score

**得分：15 / 100**

评分依据：文件不存在（0 分基础），但现有 6+ 文档对其隐含需求基本一致（+15 分）。主要失分点：

| 失分项 | 扣分 | 说明 |
|--------|------|------|
| 文件不存在 | -50 | 文件完全缺失 |
| Raw Project 字段命名不一致 | -10 | "Repo Name" vs "Project Name" |
| Normalized 包含 Stage 3 字段 | -5 | "项目领域"字段跨越阶段边界 |
| Confidence 表示不统一 | -5 | 枚举 vs 百分比 |
| 核心能力字段无结构化约束 | -5 | "Description 提炼"定义模糊 |
| 数据流转换规则缺失 | -10 | 无字段映射形式化定义 |

---

## 修改建议

### 必须修改项

| 优先级 | 修改项 | 说明 |
|--------|--------|------|
| P0 | **创建 docs/project_data_schema_v1.md** | 文件完全缺失，是所有下游处理的入口依赖 |
| P0 | **统一字段命名规范** | 在 "Repo Name" 和 "Project Name" 之间选择其一，建议全小写 snake_case 英文 |
| P0 | **将"项目领域"移出 Normalized Project** | 该字段产生于 Stage 3，不应出现在 Stage 2 的输出中 |
| P0 | **定义 5 阶段数据结构的完整字段列表** | Raw → Normalized → Classification Result → Scoring Result → Ranked Project |

### 建议修改项

| 优先级 | 修改项 | 说明 |
|--------|--------|------|
| P1 | **统一 Confidence 表示方式** | 建议百分比（0~100%）为存储格式，三档枚举为展示格式 |
| P1 | **为"核心能力"添加结构化约束** | 如限制为 3~5 个关键词，或固定格式的短语列表 |
| P1 | **Career Goal Impact 纳入字段定义** | v2 新增输出，需成为 Scoring Result 的组成部分 |
| P1 | **检查 daily_report_spec_v1.md 的 Career Goal Impact 展示** | 当前日报格式未体现 Career Goal Impact，v2 输出中包含但展示层未准备 |

### 可以忽略项

| 优先级 | 修改项 | 说明 |
|--------|--------|------|
| P2 | **Report Object 的完整定义** | 日报结构已在 daily_report_spec_v1.md 中完整定义，Schema 只需轻量级引用 |
| P2 | **可选输入字段（README Summary 等）** | 属于 v0.2 及以后扩展，当前版本标记为可选即可 |
| P2 | **Owner 字段的来源确认** | GitHub Trending 数据中 Owner 的获取方式属于实现细节，Schema 仅定义字段存在性 |

---

## 结论

`project_data_schema_v1.md` 是 PKIA v0.1 文档体系中唯一的缺失文件。其他 6 个核心文档均已存在并相互引用，但均依赖此文件定义的数据结构。

创建此文件时，需要：
1. 统一字段命名（解决 Repo Name vs Project Name 冲突）
2. 定义 5 个数据阶段的完整字段列表（Raw → Normalized → Classified → Scored → Ranked）
3. 规范 Confidence 表示方式（解决枚举 vs 百分比冲突）
4. 整合 Career Goal Impact（v2 新增需求）
5. 确保阶段边界清晰（解决"项目领域"跨越 Stage 2/3 的问题）
6. 提供字段映射表（定义各阶段之间字段的转换关系）