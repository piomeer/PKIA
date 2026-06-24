# PKIA Report Generation Pipeline v1

---

## 1. Purpose

本文件定义：

Score Results → Daily Report 的转换过程。

评分流水线（Scoring Pipeline）负责产生分数，而报告生成流水线（Report Generation Pipeline）负责将这些分数组织成用户每天早上看到的那份日报。

目标：

确保用户每天看到的信息：

- **有价值** — 每一条内容都通过了 Career Alignment 和 Interest Match 的筛选
- **有优先级** — Strong Recommend 在最前面，Ignore 不出现，用户不需要自己排序
- **不造成信息焦虑** — 日报的目标是帮用户知道"哪些可以放心跳过"，而不是"你错过了什么"

两份流水线的关系：

- **Scoring Pipeline**：项目 → 分数（告诉系统"这个项目值多少分"）
- **Report Generation Pipeline**：分数 → 日报（告诉用户"今天你应该看什么"）

---

## 2. Pipeline Overview

报告生成流水线包含 7 个阶段：

```
Scored Projects
      ↓
Stage 1: Recommendation Grouping
      ↓
Stage 2: Priority Ranking
      ↓
Stage 3: Interest Evolution Analysis
      ↓
Stage 4: Daily Reading Selection
      ↓
Stage 5: Daily Report Assembly
      ↓
Stage 6: Final Report
```

每个阶段均以 Daily Report Spec 定义的 6 章节结构（Section A~F）为最终输出目标。

---

## 3. Input

### 输入来源

Scoring Pipeline（scoring_pipeline_schema_v2.md）的输出。

### 每项目的输入字段

| 字段 | 类型 | 来源阶段 |
|------|------|----------|
| `project_id` | string | Stage 1（Data Collection） |
| `pipeline_status` | string (enum) | 贯穿所有 Stage |
| Project Name | 字符串 | Stage 2（Normalization） |
| Category | 字符串（Primary Category） | Stage 3（Classification） |
| Career Alignment | 0~40 | Stage 4 |
| Interest Match | 0~30 | Stage 5 |
| Trend Heat | 0~20 | Stage 6 |
| Research Relevance | 0~10 | Stage 7 |
| Total Score | 0~100 | Stage 8 |
| `career_goal_impact` | object | Stage 8 — 包含 4 个职业目标影响评估（Agent Application Engineer, AI Platform Engineer, LLM Inference Optimization Engineer, Multi-Agent System Engineer，各值为 HIGH / MEDIUM / LOW）|
| Recommendation | Strong Recommend / Recommend / Observe / Ignore | Stage 9 |
| Reasoning | 文本 | Scoring Agent 输出 |

### 输入规模

- 每日 30 个项目（由 data_collection_strategy_v1.md 固定）
- 全部带有完整的评分和 Reasoning

---

## 4. Stage 1: Recommendation Grouping

### 目的

将评分完成的项目按推荐等级分组，为日报的 Section B/C/D 准备内容。

### 输入

- 30 个 Scored Projects（每个包含 Total Score 和 Recommendation）

### 输出

- **Group A（Strong Recommend）**：Total Score ≥ 90
- **Group B（Recommend）**：Total Score 70~89
- **Group C（Observe）**：Total Score 40~69
- **Group D（Ignore）**：Total Score 0~39

### 规则

- 分组是纯规则驱动，不存在主观判断。所有评分判断在 Scoring Pipeline 中已完成。
- 分组完成后，Group D（Ignore）不再参与后续的日报主体内容生成。但在 Section A（概览）中需要统计其数量。

### 与 Daily Report Spec 的关系

此阶段的 4 个分组直接对应 daily_report_spec_v1.md 中 Section B、C、D 的展示层级。Group A → Section B（Strong Recommend），Group B → Section C（Recommend），Group C → Section D（Observe）。

---

## 5. Stage 2: Priority Ranking

### 目的

在每个分组内部按优先级排序，确保同一层级内最重要的内容排在最前面。

### 输入

- Stage 1 输出的 4 个分组

### 输出

- 每个分组内排序后的项目列表

### 排序优先级

1. **Total Score（降序）** — 总分最高的排最前面
2. **Career Alignment（降序）** — 同分时职业相关性高的优先
3. **Interest Match（降序）** — 仍同分时兴趣匹配度高的优先
4. **Trend Heat（降序）** — 仍同分时热度高的优先
5. **`project_id`（字典序升序）** — 所有排序字段均相同时作为确定性排序键

### 规则

- 排序仅在分组内部进行。Strong Recommend 组内的最后一名仍然排在 Recommend 组的第一名之前。
- 总分相同时，Career Alignment 作为第二排序字段，体现了"职业价值 > 热度"的设计原则。即使一个项目的 Trend Heat 很高，如果 Career Alignment 较低，在排序中也会被 Career Alignment 高但热度略低的项目反超。

### 与 Design Principles 的关系

此阶段是 pipeline 设计原则 2（Career Value First）的具体执行点。排序算法写死了"职业价值优先"的规则，确保日报的阅读顺序天然反映职业目标优先级。

---

## 6. Stage 3: Interest Evolution Analysis

### 目的

分析当日所有项目（包含 Group A/B/C）的主题分布，生成 Section E（Interest Evolution）。

### 输入

- 30 个项目的 Category 和 Secondary Tags

### 输出

- 主题热度排名（按出现频次降序）
- 每个主题对应的 Interest Tier 标注
- 趋势说明文本

### 分析维度

按 interest_profile_v1.md 的 Interest Tiers 统计当日出现频次：

**S Tier 统计：**
Agent、Agent Application、Agent Framework、Agent Memory、Multi-Agent、AI Engineering、LLM Inference、LLM Serving、Inference Optimization

**A Tier 统计：**
MCP、RAG、AI Infrastructure、LLMOps、Frontier AI Trends

**B Tier 统计：**
Knowledge Graph、Knowledge Graph Embedding、Distributed Training、Graph Partitioning

### 输出格式

热度排名（按出现频次），附带条形图（ASCII 风格）和 Interest Tier 标注，以及一段说明文本解释今日主题趋势。

### 规则

- 此阶段不重新评分，仅做统计。
- 如果一个项目有多个标签，计入每个匹配主题的频次。
- 说明文本需要与 Interest Profile 建立关联，例如"Agent 方向持续活跃，与 S Tier 核心定位一致"或"Knowledge Graph 今日未见显著活动"。

### 与 Interest Profile 的关系

此阶段的统计分类和 Tier 标注完全引用 interest_profile_v1.md 的第 3 节。Interest Profile 定义"我们关注什么主题"，Interest Evolution 告诉用户"今天这些主题的活跃度如何"。

---

## 7. Stage 4: Daily Reading Selection

### 目的

从所有项目中选出当天最值得投入时间的 **3 项**，生成 Section F（What To Read Today）。

### 输入

- Stage 2 排序后的 Group A + Group B

### 输出

- 3 个 Priority 条目，每个包含：项目名、分类、推荐原因、预计阅读时间、预期收益

### 选择规则

1. **第一优先：Group A（Strong Recommend）中的第一名** — 除非 Group A 为空（极少数情况），否则 Priority #1 必须是 Strong Recommend 层的最高分项目。
2. **第二优先：**
   - 如果 Group A 有 ≥ 2 个项目，取 Group A 的第二名。
   - 如果 Group A 只有 1 个项目，取 Group B 的第一名。
3. **第三优先：**
   - 从剩余项目中选出与 Priority #1 和 #2 **不重复领域**的最高分项目。
   - 目的是提供领域多样性，避免三个推荐全都属于 Agent Framework。

### 规则

- **每天仅选 3 项**，不多不少。这是强制限制，不是建议。
- 即使当日有 6 个 Strong Recommend 项目，也只会进入日报的 Section B 完整展示，但 Section F 仍然只选 3 项。
- 阅读时间估算标准：阅读项目 README + 快速了解核心能力 = 10~20 分钟；深入了解技术架构 = 20~30 分钟；深入阅读源码 = 30~60 分钟。

### 与 Design Principles 的关系

此阶段直接体现了设计原则 4（Focus Over Completeness）。每天只选 3 项的强制限制，确保用户不会被"必须看完所有 Strong Recommend"的压力压垮。选 3 项意味着"今天看完这三项，你就完成了今天的核心功课"。

---

## 8. Stage 5: Daily Report Assembly

### 目的

将所有内容组装为 daily_report_spec_v1.md 定义的 6 章节格式。

### 输入

- Stage 1：分组结果
- Stage 2：排序结果
- Stage 3：Interest Evolution 分析
- Stage 4：Daily Reading Selection（3 项）

### 输出

- 完整的 Daily Report 正文

### 组装顺序

```
Section A: 今日概览
← 从 Stage 1 + Stage 5 统计数据

Section B: 🔴 Strong Recommend
← Stage 1 Group A + Stage 2 排序

Section C: 🟡 Recommend
← Stage 1 Group B + Stage 2 排序

Section D: ⚪ Observe
← Stage 1 Group C + Stage 2 排序

Section E: 📈 Interest Evolution
← Stage 3 分析结果

Section F: 📋 What To Read Today
← Stage 4 选择结果
```

### 各章节详细展示格式

**Section A（今日概览）：**
```
📊 今日概览
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 新项目（GitHub Trending）:  30 个
• 🔴 Strong Recommend:         N 项
• 🟡 Recommend:                 N 项
• ⚪ Observe:                   N 项
• ⚫ Ignore:                    N 项
```

**Section B（Strong Recommend）— 每项完整展示：**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔴 Strong Recommend
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
项目名:     [name]
分类:       [category]
总分:       [score]
职业目标影响:
  Agent Application Engineer:        [HIGH / MEDIUM / LOW]
  AI Platform Engineer:              [HIGH / MEDIUM / LOW]
  LLM Inference Optimization Engineer: [HIGH / MEDIUM / LOW]
  Multi-Agent System Engineer:       [HIGH / MEDIUM / LOW]
推荐理由:
[detailed reasoning]
与职业目标的关系:
[career goal connection]
预计阅读时间: [X] 分钟
```

**Section C（Recommend）— 每项简洁展示：**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🟡 Recommend
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
项目名:     [name]
分类:       [category]
总分:       [score]
推荐理由: [one sentence]
```

**Section D（Observe）— 每项最小展示：**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚪ Observe
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
项目名:     [name]
分类:       [category]
总分:       [score]
说明: [one sentence]
```

**Section E（Interest Evolution）：**
```
📈 今日主题分布
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[热度排名 + 条形图 + Tier 标注 + 趋势说明]
```

**Section F（What To Read Today）：**
```
📋 今日阅读建议
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Priority #1: [name] — [reason] — [time] min
Priority #2: [name] — [reason] — [time] min
Priority #3: [name] — [reason] — [time] min
```

---

## 9. Stage 6: Final Report

### 目的

输出最终日报，准备交付给用户。

### 输入

- Stage 5 组装的完整日报

### 输出

- 一份结构完整、可读性强的 PKIA Daily Report

### 最终检查清单

生成最终报告前，需验证以下条件：

- [ ] 所有项目均包含 `project_id`（作为数据血缘回溯键）
- [ ] `pipeline_status` 已更新为 `ARCHIVED`（所有完成评分的项目）
- [ ] Section A 统计数据准确（Strong Recommend + Recommend + Observe + Ignore = 30）
- [ ] Section B 不包含总分 < 90 的项目
- [ ] Section C 不包含总分 > 89 或 < 70 的项目
- [ ] Section D 不包含总分 > 69 的项目
- [ ] Section F 恰好包含 3 项
- [ ] 每项 Score 均附带 Reasoning（Section B 必须有详细 Reasoning，Section C/D 至少有一句话说明）
- [ ] 没有重复项目出现在不同章节

---

## 10. 空结果处理

### 场景 1：当日无 Strong Recommend 项目

- Section B 展示："今日无强烈推荐项目。"
- Section F 的 Priority #1 从 Recommend 组第一名选取。

### 场景 2：当日所有 30 个项目均为 Ignore

- 日报仅包含 Section A + 一条说明："今日所有项目均不符合兴趣画像。"
- 此情况在 v0.1 中极为罕见（GitHub Trending Top 30 通常至少包含 2~5 个 Agent 相关项目）。

### 场景 3：采集失败

- 日报展示："数据采集失败，展示昨日数据。"
- 展示上一次成功采集的日报（缓存版本）。

### 场景 4：当日项目少于 30 个

- Section A 按实际数量统计。
- 不影响其他章节，评分和分组逻辑不变。

---

## 11. 日报质量检查

每份日报生成后，需满足以下质量标准：

| 检查项 | 标准 |
|--------|------|
| Strong Recommend 合理性 | 所有 Strong Recommend 项目的 Career Alignment ≥ 35 |
| Recommend 合理性 | 所有 Recommend 项目的 Career Alignment ≥ 25 |
| 分数一致性 | 每个项目的 4 项分数之和等于 Total Score |
| `career_goal_impact` 完整性 | 每项的 4 个职业目标影响均已赋值，无空值 |
| Reasoning 完整性 | 每项均有 Reasoning，无纯分数输出 |
| 主题分布准确性 | Section E 的统计与实际项目标签一致 |
| 阅读建议多样性 | Section F 的 3 项覆盖至少 2 个不同领域 |

---

## 12. Design Principles

### 原则 1：Reduce Information Anxiety

日报的核心目标不是展示更多信息，而是让用户有信心跳过大量信息。Section D（Observe）和 Ignore 的"不展示但统计数量"设计，共同服务于这个目标。用户不需要担心"我错过了什么"，因为日报已经替他们做出了过滤决策。

### 原则 2：Career Value First

从 Stage 2 的排序规则到 Section B 的展示优先级，职业价值始终是最高排序依据。一个 Career Alignment 40 但 Trend Heat 8 的项目，排序一定高于 Career Alignment 30 但 Trend Heat 18 的项目。

### 原则 3：Actionable Recommendations

Section F 的"每天只选 3 项"将推荐转化为可执行的动作。用户不需要面对"我应该先看哪个"的选择困难。日报已经替他们选好了今天最重要的 3 件事。

### 原则 4：Focus Over Completeness

日报不追求展示所有信息。Ignore 等级不展示、Observe 等级最小化展示、Strong Recommend 完整展示——三级展示策略确保用户的注意力集中在最重要的内容上。日报的设计目标是"看完 3 项就算完成"，而不是"看完所有条目"。

### 原则 5：Explain Every Recommendation

日报中的每一项推荐都必须附带 Reasoning。Section B 需要详细解释"为什么推荐"和"与职业目标的关系"。Section C 和 D 至少需要一句话说明。这既是 prompt_scoring_agent_v2.md 的强制要求，也是用户信任评分系统的前提。

---

## 13. Error Handling

### 评分异常

如果某个项目的 Total Score 明显异常（如 Career Alignment 为 0 但 Category 属于 S Tier），日报应在该条目的 Reasoning 中注明"分数异常，建议人工复核"。

### 重复项目

如果同一项目在同一份日报中出现两次（理论上不应发生，但作为 Pipeline 防御性设计），保留评分更高的那次，移除重复项。

### 格式错误

如果某个字段为空（如 Reasoning 缺失），日报在对应位置输出"暂无说明"，不允许跳过整个条目。

---

## 14. Relationship With Other Documents

本文件是 PKIA v0.1 文档体系中负责"输出端"的核心架构文档，与以下文档的关系如下：

| 文档 | 关系 |
|------|------|
| **data_collection_strategy_v1.md** | 提供输入规模约束（Top 30）。报告生成管线的数据源质量取决于采集策略的入口选择。如果采集策略改为 Top 20，日报的 Section B/C/D 的内容密度会相应变化 |
| **project_data_schema_v1.md** | PKIA 唯一数据契约，定义每个项目的 6 阶段数据结构。报告生成管线的 Stage 5（Assembly）依赖 Schema 定义的数据字段进行格式化输出 |
| **scoring_pipeline_schema_v2.md** | 本文件的上游。Scoring Pipeline 负责"项目 → 分数"，Report Generation Pipeline 负责"分数 → 日报"。Score Pipeline 的输出（`project_id`、`pipeline_status`、Project Name、Category、4 维度分数、Total Score、`career_goal_impact`、Recommendation、Reasoning）是本文件的全部输入 |
| **prompt_scoring_agent_v2.md** | 提供 Scoring Agent v2 的推理能力和 Reasoning 风格约束。报告生成管线不对 Reasoning 做重新生成，而是直接使用 Scoring Agent 输出的 Reasoning 原文。因此 prompt_scoring_agent_v2.md 中"禁止只输出分数"的要求间接影响了日报 Section B 的 Reasoning 质量 |
| **daily_report_spec_v1.md** | 本文件的最终输出目标。daily_report_spec_v1.md 定义了"日报长什么样"（6 章节结构、展示格式、设计原则），而本文件定义了"如何生成日报"（7 阶段流水线、分组规则、排序规则、选择逻辑）。两份文档的关系是：Spec 定义 What，Pipeline 定义 How |

---

**强调：**

- **Scoring Pipeline** 负责产生分数
- **Report Generation Pipeline** 负责组织日报

两者共同构成 PKIA 的完整数据处理管线：从原始 GitHub Trending 数据开始，到用户每天看到的最终日报结束。

---

*End of Report Generation Pipeline. Compliant with PKIA v0.1 document architecture.*