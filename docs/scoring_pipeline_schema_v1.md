# PKIA Scoring Pipeline Schema v1

> **⚠️ DEPRECATED — 此文档已被 `scoring_pipeline_schema_v2.md` 取代**
>
> 本文件保留为历史参考。v2 修复了审查发现的所有 10 个 P0 一致性问题，包括：
> - 缺少 `project_id` 和 `pipeline_status` 字段
> - 中文字段名（5 处）
> - Stage 2 包含分类字段（Stage 边界违规）
> - 缺少 `classification_confidence`、`reasoning`、`career_goal_impact` 等字段
> - 未引用 `project_data_schema_v1.md` 作为数据契约
>
> **所有新实现请引用 `docs/scoring_pipeline_schema_v2.md`。**
>
> 迁移说明参见 `docs/scoring_pipeline_patch_plan_v1.md`。

---

## 1. Purpose

本文件定义：

Project Data → Scoring Agent → Score Result → Daily Report 之间的数据流。

PKIA v0.1 的评分不是一次性事件，而是一个包含 10 个阶段的流水线。每个阶段有明确的输入、处理和输出责任。

目标：

让任何实现方式（Dify Workflow、Python 脚本、LangGraph Agent、MCP Server）都遵守同一套评分流程。

本文件只描述"项目如何被评分"。关于"项目长什么样"的定义，属于 Project Data Schema 的范畴。

---

## 2. Pipeline Overview

总分 10 个阶段：

```
Stage  1: Data Collection
            ↓
Stage  2: Project Normalization
            ↓
Stage  3: Category Classification
            ↓
Stage  4: Career Alignment Scoring
            ↓
Stage  5: Interest Match Scoring
            ↓
Stage  6: Trend Heat Scoring
            ↓
Stage  7: Research Relevance Scoring
            ↓
Stage  8: Total Score Calculation
            ↓
Stage  9: Recommendation Assignment
            ↓
Stage 10: Daily Report Ranking
```

每个阶段均为独立步骤。前一个阶段的输出是下一个阶段的标准输入。不允许跨阶段跳跃。

---

## 3. Stage 1: Data Collection

### 目的

从数据源获取原始项目信息。

### 输入

- GitHub Trending Top 30（由 data_collection_strategy_v1.md 定义）

### 输出

- 原始项目列表（30 条）
- 每个条目包含：Repo Name、Description、Stars 数、Topics 标签

### 规则

- **仅负责收集，不做判断。** 此阶段不进行任何过滤、分类或评分。
- 不修改原始数据。即使某个项目明显与 Interest Profile 无关（如一个前端框架），也完整保留。
- 采集失败时（如 GitHub Trending 不可达），保留上一次成功采集的数据作为降级方案。

### 与 Data Collection Strategy 的关系

此阶段的输入规模（Top 30）和频率（Daily）完全由 data_collection_strategy_v1.md 的第 5 节和第 8 节固定。该文档是此阶段的唯一决策依据。

---

## 4. Stage 2: Project Normalization

### 目的

将原始项目数据结构化为统一格式，消除不同数据源之间的格式差异。

### 输入

- Stage 1 输出的原始项目列表

### 输出

- 标准化项目对象，每个对象包含：

| 字段 | 说明 | 来源 |
|------|------|------|
| 项目名称 | 仓库名称 | GitHub Trending |
| 一句话描述 | Description 的第一句或核心摘要 | Description 字段 |
| 核心能力 | 该项目解决什么问题、提供什么能力 | Description 提炼 |
| 项目标签 | Topics 或自动抽取的关键词 | Topics + Description |
| 项目领域 | 按 Interest Tiers 映射的领域标签 | Stage 3 完成 |

### 规则

- 描述截断：超过 200 字符的描述需做摘要压缩，避免后续 Scoring Agent 的 Token 浪费。
- 标签标准化：将 GitHub Topics 映射到 Interest Profile 定义的标准领域名（如 agent-framework → Agent Framework）。

### 与 Project Data Schema 的关系

Project Data Schema 定义"项目长什么样"——即标准化项目对象的结构约束。此阶段是 Project Data Schema 的第一个消费者：将原始数据转换为符合 Schema 定义的格式。

---

## 5. Stage 3: Category Classification

### 目的

将项目归类到 Interest Profile 定义的领域类别。

### 输入

- Stage 2 输出的标准化项目对象

### 输出

- Primary Category：主要类别（用于 Career Alignment 评分）
- Secondary Tags：次要标签（用于 Interest Match 评分）

### 分类体系

映射到 interest_profile_v1.md 的 Interest Tiers：

**S Tier（核心赛道）：**
Agent、Agent Application、Agent Framework、Agent Memory、Multi-Agent、AI Engineering、LLM Inference、LLM Serving、Inference Optimization

**A Tier（强相关）：**
MCP、RAG、AI Infrastructure、LLMOps、Frontier AI Trends

**B Tier（研究背景）：**
Knowledge Graph、Knowledge Graph Embedding、Distributed Training、Graph Partitioning

**Ignore：**
Frontend、Mobile、Blockchain、Crypto、NFT、Web3

### 规则

- **一个项目允许有多个标签。** 例如 Dify 同时属于 Agent Platform、AI Engineering、RAG Platform。
- **必须选出 Primary Category。** 同一个项目即使横跨多个领域，也必须选出一个主要类别用于 Career Alignment 评分基准分。
- 如果项目同时属于 S Tier 和 A Tier，以 S Tier 为 Primary Category。

### 与 Interest Profile 的关系

此阶段的分类体系完全引用 interest_profile_v1.md 的第 3 节（Interest Tiers）。任何分类体系调整都应在 Interest Profile 中先行修改。

---

## 6. Stage 4: Career Alignment Scoring

### 目的

评估项目与用户四个职业目标的直接相关性。

### 输入

- Stage 3 输出的 Primary Category

### 输出

- Career Alignment 分数：0~40

### 评分基准

由 scoring_strategy_v1.md 定义的 Career Alignment 分值映射：

| Primary Category 所在层级 | 基准分 |
|---------------------------|--------|
| S Tier（核心赛道） | 40 |
| A Tier（强相关） | 30 |
| Frontier AI Trends | 20 |
| B Tier（弱相关） | 10 |
| Ignore | 0 |

### 调整规则

在基准分基础上，Scoring Agent 可根据以下因素在 ±3 范围内调整：

- **正向调整（+1~3）：** 该项目是否直接支持用户构建生产级 Agent 产品？是否作为 PKIA 的底层实现平台？
- **负向调整（-1~3）：** 该项目与职业目标的关系是否间接？是否重复已有的工具生态而无创新？

### 与 Career Goals 的关系

四个职业目标的优先级（Agent Application Engineer > AI Platform Engineer > LLM Inference Optimization Engineer > Multi-Agent System Engineer）决定了调整方向：如果项目同时服务于多个目标，优先按最高目标评分。

---

## 7. Stage 5: Interest Match Scoring

### 目的

评估项目与用户兴趣画像的匹配程度。

### 输入

- Stage 3 输出的 Secondary Tags

### 输出

- Interest Match 分数：0~30

### 评分规则

| 匹配层级 | 分数范围 | 条件 |
|----------|----------|------|
| S Tier | 25~30 | 匹配 S Tier 领域 |
| A Tier | 20~25 | 匹配 A Tier 领域 |
| B Tier | 8~15 | 匹配 B Tier 领域 |
| Ignore | 0~5 | 匹配 Ignore 列表 |

### 规则

- 如果项目同时匹配多个 Tier 的标签，取最高 Tier 的分数。
- Interest Match 反映的是"用户对这类话题的天然兴趣"，不考虑职业价值。例如一个有趣的 B Tier 知识图谱工具，即使 Career Alignment 低，Interest Match 仍可给出 B Tier 范围的分数。

### 与 Interest Profile 的关系

此阶段的 Tier 定义和匹配规则完全引用 interest_profile_v1.md 的第 3 节。

---

## 8. Stage 6: Trend Heat Scoring

### 目的

评估项目的当前社区热度。

### 输入

- Stage 2 输出的 Stars 数、活跃度信号

### 输出

- Trend Heat 分数：0~20

### 评分规则

| 热度水平 | 分数范围 | 典型信号 |
|----------|----------|----------|
| 爆炸增长 | 16~20 | 千级以上 Stars，高频 Releases，活跃 Discord/GitHub Discussions |
| 稳定增长 | 10~15 | 持续多日 Trend，中等活跃度 |
| 小众稳定 | 5~10 | 小社区但持续维护 |
| 下降/停滞 | 0~5 | 长期无更新，Star 增长停滞 |

### 规则

- **Trend Heat 不单独决定推荐等级。** 一个高热度但 Career Alignment 低的项目（如一个爆火的前端框架），总分仍会落入低推荐区间。
- 避免"刷榜"效应：连续多日占据 Trending 的项目，热度评分不应逐日递增，而是保持稳定。

### 与 Scoring Strategy 的关系

此阶段确认 scoring_strategy_v1.md 中"职业价值 > 热度"的核心原则。Trend Heat 的权重上限（20/100）低于 Career Alignment（40/100），确保热度不会掩盖职业相关性。

---

## 9. Stage 7: Research Relevance Scoring

### 目的

评估项目的长期研究价值和技术创新性。

### 输入

- Stage 2 输出的项目描述和核心能力

### 输出

- Research Relevance 分数：0~10

### 评分规则

| 研究价值 | 分数范围 | 典型信号 |
|----------|----------|----------|
| 高 | 8~10 | 新范式、新架构、活跃的研究领域、可能改变工程实践 |
| 中 | 5~7 | 扎实的增量工作，有工程落地价值 |
| 低 | 2~4 | 实现导向，已有成熟方案，创新点有限 |
| 无 | 0~2 | 纯产品发布、新闻事件，无研究内容 |

### 规则

- 此维度权重最低（10/100），仅作为参考信号。
- 对于 PKIA v0.1，大多数 GitHub 项目属于"低"到"中"范围。"高"分仅保留给引入了新架构范式的项目（如首次提出 Agent Memory 分层设计的框架）。

---

## 10. Stage 8: Total Score Calculation

### 目的

将四个维度的分数合并为总分。

### 输入

- Stage 4：Career Alignment（0~40）
- Stage 5：Interest Match（0~30）
- Stage 6：Trend Heat（0~20）
- Stage 7：Research Relevance（0~10）

### 输出

- Total Score：0~100

### 公式

```
Total Score = Career Alignment + Interest Match + Trend Heat + Research Relevance
```

### 规则

- 四个分数独立计算，不存在乘数或加权系数。Career Alignment 的天然权重（最高 40）已经体现了"职业价值优先"原则。
- 总分保留整数，不作四舍五入外的额外处理。
- 任何维度缺失时（如某个项目无法评估 Trend Heat），该维度按 0 分处理并在 Reasoning 中注明。

### 与 Scoring Examples 的关系

scoring_examples_v1.1.md 的 11 个案例均按此公式计算总分。例如 Case 1（OpenManus）：40 + 30 + 18 + 8 = 96。

---

## 11. Stage 9: Recommendation Assignment

### 目的

将总分映射到推荐等级。

### 输入

- Stage 8 输出的 Total Score

### 输出

- Recommendation 等级

### 映射规则

由 scoring_strategy_v1.md 定义：

| 总分范围 | 等级 | 说明 |
|----------|------|------|
| 90+ | 🔴 Strong Recommend | 必须仔细阅读 |
| 70~89 | 🟡 Recommend | 值得投入时间 |
| 40~69 | ⚪ Observe | 保持关注，不必深读 |
| 0~39 | ⚫ Ignore | 跳过 |

### 规则

- 此阶段是纯规则映射，不存在主观判断。所有判断在 Stage 4~7 已完成。
- 如果项目总分刚好在边界（如 70 分、90 分），推荐统一向上取整（70 分 → Recommend，90 分 → Strong Recommend）。

---

## 12. Stage 10: Daily Report Ranking

### 目的

将所有评分完成的项目排序，生成 Daily Report 的内容顺序。

### 输入

- Stage 8 的 Total Score
- Stage 9 的 Recommendation

### 输出

- 排序后的项目列表，按推荐等级分组

### 排序规则

1. **一级排序：Recommendation 等级** — Strong Recommend > Recommend > Observe > Ignore
2. **二级排序：Total Score** — 同等级内按总分降序排列
3. **三级排序：Career Alignment** — 同分情况下 Career Alignment 高的优先
4. **四级排序：Interest Match** — 仍相同时 Interest Match 高的优先

### 与 Daily Report 的关系

此阶段的输出直接对应 daily_report_spec_v1.md 的 Section B（Strong Recommend）、Section C（Recommend）、Section D（Observe）。Ignore 等级的项目不出现在日报中，仅在原始数据中可查。

---

## 13. Pipeline Design Principles

### 原则 1：Career Value > Trend

职业价值是评分体系中权重最高的维度。Career Alignment（0~40）的天然权重是 Trend Heat（0~20）的两倍。这意味着一个中等热度但高 Career Alignment 的项目，得分一定超过一个火爆但低 Career Alignment 的项目。

### 原则 2：Long-term Value > Short-term Hype

Trend Heat 仅反映当下的热度信号。Research Relevance 和 Career Alignment 共同捕捉长期价值。Pipeline 的设计确保短期爆红项目不会因热度而冲入 Strong Recommend 层，除非它们也具备职业相关性。

### 原则 3：Agent First

当项目同时属于 Agent 和非 Agent 类别时，分类系统优先将其归入 Agent 相关类别。这确保 Agent 项目在 Stage 3 就能进入 S Tier，从而在 Stage 4 获得最高的 Career Alignment 基准分。

### 原则 4：Reduce Information Anxiety

Pipeline 的最终输出不是"给你更多信息"，而是"告诉你哪些可以跳过"。Stage 9 的 Ignore 等级和 Stage 10 的 Daily Report 分组设计，共同服务于这个目标。Observe 和 Ignore 两个等级的存在，是为了让用户能放心地跳过大量内容，而不产生"可能错过了什么"的焦虑。

### 原则 5：Explainability Required

Pipeline 不允许"黑盒评分"。Stage 8 计算出总分后，必须有对应的 Reasoning 解释每个维度的得分原因。这是 prompt_scoring_agent_v1.md 第 7 节（Reasoning Requirements）的强制规定。没有 Reasoning 的分数不可输出到 Daily Report。

---

## 14. Relationship With Other Documents

本文件是 PKIA v0.1 文档体系的核心架构文档之一，与以下文档的关系如下：

| 文档 | 关系 |
|------|------|
| **interest_profile_v1.md** | 提供 Stage 3（Category Classification）的分类体系和 Stage 5（Interest Match）的评分依据。Interest Profile 定义"用户关注什么"，Pipeline 将此定义转化为可执行的分类和评分规则 |
| **scoring_strategy_v1.md** | 提供 Stage 4（Career Alignment）的基准分数线、Stage 9（Recommendation Assignment）的推荐阈值。Scoring Strategy 是 Pipeline 的评分规则总纲 |
| **scoring_examples_v1.1.md** | 验证 Pipeline 的 10 个阶段是否能够产生预期输出。11 个案例分别覆盖了 S Tier（OpenManus、Agent Memory）、A Tier（MCP）、B Tier（PyTorch Geometric）、Ignore（Spark GraphX）等各类情况 |
| **Project Data Schema（规划中）** | 定义"项目长什么样"——即 Stage 2（Project Normalization）输出的数据结构约束。本文件与 Project Data Schema 共同构成 PKIA 评分系统的一体两面：Schema 定义数据格式，Pipeline 定义数据处理流程 |
| **prompt_scoring_agent_v1.md** | 提供 Stage 4~7 的具体评分执行逻辑。当 Pipeline 通过 Dify LLM Node 实现时，prompt_scoring_agent_v1.md 作为 System Prompt 注入评分节点 |
| **daily_report_spec_v1.md** | 消费 Stage 10 的输出。Daily Report 定义的 6 章节结构中的 Section B/C/D 直接使用 Pipeline 的 Recommendation 分组结果 |
| **data_collection_strategy_v1.md** | 提供 Stage 1 的输入。采集策略决定 Pipeline 的入口规模（Top 30）和频率（Daily） |

---

*End of Schema. Defines the canonical scoring pipeline for PKIA v0.1.*