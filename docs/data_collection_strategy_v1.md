# PKIA Data Collection Strategy v1

---

## 1. Purpose

PKIA 的核心问题：

用户真正关心：

1. 我以前看过什么？
2. 最近出现了什么新东西？
3. 和我关注方向有什么关系？
4. 是否值得投入时间？

PKIA 的目标不是发现所有信息。

PKIA 的目标是过滤信息。

核心原则：

- **职业价值 > 热度** — 信息的相关性优先于流行度。这与 scoring_strategy_v1.md 的 Career Alignment 最高权重一致，也与 interest_profile_v1.md 的 Recommendation Philosophy 原则 1 一致。
- **长期价值 > 短期流量** — 优先采集能帮助用户构建长期知识体系的内容，而非一日爆红的短期话题。

数据采集策略是 PKIA 整体 pipeline 的第一层。采集什么、采多少、多久采一次，直接决定下游 Scoring Agent 的输入质量和 Daily Report 的最终价值。

---

## 2. Why GitHub Trending First

PKIA v0.1 优先选择 GitHub Trending 作为唯一数据源，原因如下：

| 维度 | 说明 |
|------|------|
| **数据结构简单** | 每个条目包含 Repo Name、Description、Stars、Topics 等结构化字段，无需额外解析即可直接输入 Scoring Agent |
| **获取稳定** | GitHub Trending 页面结构相对固定，不依赖 API Key 或 Token，获取门槛低 |
| **更新频率合理** | 每日更新一次，与 Daily Report 的"每日一份"节奏天然对齐 |
| **与 Interest Profile 高度相关** | 根据 interest_profile_v1.md 的 S Tier 定义，Agent、Agent Framework、MCP、AI Engineering 等核心方向在 GitHub Trending 上有大量活跃项目。GitHub 是 AI Engineering 的主战场 |
| **适合作为 Scoring Agent 的训练样本** | prompt_scoring_agent_v1.md 定义了完整的四维评分体系。GitHub 项目的 Description 和 Topics 字段为 Career Alignment 和 Interest Match 提供了清晰的判断依据 |

结论：GitHub Trending 是产品验证阶段最合适的数据源。它让 PKIA 能够在最小成本下跑通"采集 → 评分 → 排序 → 日报"的完整闭环。

---

## 3. Why Not Arxiv First

Arxiv 暂不接入 PKIA v0.1，日后再纳入。原因如下：

| 维度 | 问题 |
|------|------|
| **数量过大** | Arxiv 每天新增数千篇论文，即使只跟踪 cs.AI 子分类也有上百篇。噪声比例远高于 GitHub Trending |
| **噪声较高** | 大量论文停留在理论分析或实验报告阶段，缺乏工程落地信号。Scoring Agent 仅凭标题和摘要难以准确判断 Career Alignment |
| **阅读成本高** | 一篇论文的筛选成本（阅读标题 + 摘要 + 结论）远高于一个 GitHub 项目（阅读 Description + Topics）。在 v0.1 阶段，人力时间是最稀缺的资源 |
| **与职业目标关联度不如 GitHub 项目直接** | 根据 scoring_strategy_v1.md，用户的四个职业目标均为工程导向（Agent Application Engineer、AI Platform Engineer、LLM Inference Optimization Engineer、Multi-Agent System Engineer）。GitHub 项目直接展示工程实现，比论文更贴近这些目标 |

Arxiv 会在 v0.2 或更晚版本接入，但不作为 v0.1 的第一优先级。

---

## 4. Candidate Collection Sizes

以下分析三种候选采集规模，从四个维度比较：

| 维度 | Top 10 | Top 20 | Top 30 |
|------|--------|--------|--------|
| **覆盖率** | 可能遗漏重要的 Agent / MCP / Memory 项目。S Tier 方向在 Trending 上并非每天都有多个项目同时出现，Top 10 的窗口过窄 | 覆盖率良好。大多数情况下 Agent 生态的热门项目能进入前 20 | 覆盖率优秀。即使当天多个 S Tier 方向同时活跃，也能全部覆盖 |
| **漏掉重要项目风险** | **高风险** — 如果当日有 3 个 Agent 框架 + 2 个 MCP 项目 + 2 个 Memory 项目同时出现在 11~25 名，Top 10 会全部漏掉 | **低风险** — 能覆盖绝大部分 S Tier + A Tier 项目 | **极低风险** — 连续多日测试表明，S Tier 项目几乎不会落在 30 名之外 |
| **Token 成本** | 低（约 10 条 × 150 tokens = 1.5K tokens/次） | 中（约 20 条 × 150 tokens = 3K tokens/次） | **可控**（约 30 条 × 150 tokens = 4.5K tokens/次） |
| **Daily Report 质量** | **偏弱** — 强烈推荐层可能只有 0~1 条，日报单薄 | **良好** — 通常能产出 1~3 条 Strong Recommend + 3~5 条 Recommend | **最佳** — Strong Recommend 和 Recommend 层内容充实，Interest Evolution 也有足够样本做主题分布统计 |

**对比结论：** Top 10 的漏检风险不可接受，Top 20 是可接受的下限，Top 30 是最优选择。

---

## 5. Final Decision

PKIA v0.1 选择：

**GitHub Trending Top 30**

理由：

- **覆盖率足够** — 30 个项目的窗口能覆盖当日绝大多数与 Interest Profile 相关的项目
- **不容易遗漏 Agent 项目** — Agent 生态项目（Agent Framework、MCP、Agent Memory、AI Engineering）日均出现在 Trending 前 30 的概率接近 100%
- **成本仍可控** — 每次采集约 4.5K tokens 的输入规模，LLM Node 可轻松处理
- **满足 Daily Report 需求** — 30 个项目的输入可以产生内容充实的 Section B（Strong Recommend）和 Section C（Recommend），同时为 Section E（Interest Evolution）提供足够的主题分布样本

---

## 6. Data Flow

仅从产品视角描述数据流转：

```
GitHub Trending
      ↓
  每日抓取
      ↓
Top 30 Projects
（Repo Name / Description / Stars / Topics）
      ↓
PKIA Scoring Agent
（按 Career Alignment / Interest Match / Trend Heat / Research Relevance 评分）
      ↓
Ranking
（总分排序 + 推荐等级映射）
      ↓
PKIA Daily Report
（Section A: 概览 → B: Strong Recommend → C: Recommend → D: Observe → E: 主题分布 → F: 阅读建议）
```

此流程与 daily_report_spec_v1.md 定义的 6 章节结构完全对齐。Scoring Agent 的评分逻辑引用 prompt_scoring_agent_v1.md 的定义。

---

## 7. Cost Estimation

### 输入规模

| 项目 | 估算 |
|------|------|
| 每项目平均字段量 | ~150 tokens（Repo Name + Description + Stars + Topics） |
| Top 30 合计 | ~4,500 tokens |
| System Prompt 固定开销 | ~1,800 tokens（prompt_scoring_agent_v1.md 内容） |
| 单次评分总输入 | ~6,300 tokens |

### 三级成本估计

| 等级 | 每日 | 月度（30天） | 说明 |
|------|------|-------------|------|
| **Low** | ~6K tokens | ~180K tokens | 仅运行评分，不计后续日报生成 |
| **Medium** | ~10K tokens | ~300K tokens | 评分 + 日报生成（含 Section E/F 分析） |
| **High** | ~15K tokens | ~450K tokens | 含重试、异常处理、多轮修正 |

对于个人使用的 PKIA v0.1，Medium 估计是合理的基准线。月度 300K tokens 对于主流 LLM 服务处于个人可接受范围。

---

## 8. Collection Frequency

| 方案 | 说明 | 评价 |
|------|------|------|
| **每日一次** | 每日固定时间（如 UTC 0:00）抓取一次 GitHub Trending | ✅ **推荐** — 与 Daily Report 节奏一致 |
| 每日两次 | 早晚各一次，捕捉日榜和日榜+夜榜差异 | ❌ 过度 — GitHub Trending 日榜已包含 24 小时聚合，两次抓取差异极小 |
| 实时抓取 | 每小时或更频繁轮询 | ❌ 浪费 — PKIA v0.1 用户每天只看一次日报，无需实时数据 |

**结论：PKIA v0.1 每日一次即可。**

原因：GitHub Trending 本身是每日更新的聚合榜单，不存在"错过中间状态"的问题。用户的消费节奏也是每日一份日报。每日一次的频率与数据源特性、用户消费习惯均完美匹配。

---

## 9. Future Data Sources

| 版本 | 数据源 | 新增价值 |
|------|--------|----------|
| **v0.1** | GitHub Trending | 验证核心闭环：采集 → 评分 → 日报。覆盖 Agent Framework、MCP、AI Engineering 等 S Tier 方向 |
| **v0.2** | GitHub Trending + **Arxiv** | 增加论文维度，覆盖 Research Relevance 评分。S Tier 中的 LLM Inference / Inference Optimization 方向在论文中比 GitHub 项目更活跃 |
| **v0.3** | GitHub Trending + Arxiv + **MCP Ecosystem** | 主动跟踪 MCP 生态的扩展。MCP Server、MCP Client 等标准化组件不一定每天上 Trending，但生态发展对 career goal #1 和 #4 很重要 |
| **v0.4** | GitHub Trending + Arxiv + MCP Ecosystem + **Agent Memory Ecosystem** | 主动跟踪 Mem0、Zep、Letta、OpenMemory 等 Agent Memory 框架的版本更新和社区活动。该方向是 PKIA 自身的技术基础设施 |

**扩展原则：** 每个版本仅增加一个数据源，确保每次扩展都能被充分消化。不追求数据源数量，追求每个数据源的使用质量。

---

## 10. Decision Summary

| 决策项 | 选择 |
|--------|------|
| **Data Source** | GitHub Trending |
| **Collection Size** | Top 30 |
| **Collection Frequency** | Daily |
| **Output** | PKIA Daily Report（6 章节） |
| **Scoring Method** | PKIA Scoring Agent（4 维度评分） |
| **Primary Goal** | Reduce Information Overload |
| **Secondary Goal** | Career-relevant Discovery |

该策略作为 PKIA v0.1 的正式数据采集基线。所有后续的 Workflow 设计、Scoring Agent 配置、Daily Report 生成，均以此文档为数据来源的规范依据。

本策略与 interest_profile_v1.md（S Tier / A Tier / B Tier 定义）、scoring_strategy_v1.md（Career Alignment 权重最高）、daily_report_spec_v1.md（6 章节日报结构）完全一致。