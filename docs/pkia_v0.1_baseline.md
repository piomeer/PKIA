# PKIA MVP v0.1 Release Baseline

> **生成时间**: 2026-06-24 22:30 JST  
> **生成者**: PKIA MVP Development Agent (Namespace: `pkia_mvp`)  
> **文档状态**: ✅ Frozen — 锁定实现范围，作为后续开发依据

---

## 1. Purpose

本文件锁定 PKIA MVP v0.1 的实现范围，作为所有后续开发的单一依据。它不是设计文档、Schema 文档、Workflow 文档或 Patch Plan。

**本文件回答以下 8 个核心问题：**

1. PKIA v0.1 的目标是什么
2. PKIA v0.1 包含哪些能力
3. PKIA v0.1 不包含哪些能力
4. PKIA v0.1 的唯一数据源是什么
5. PKIA v0.1 的完整处理链路是什么
6. PKIA v0.1 的最终输出是什么
7. 哪些文档属于 Frozen State
8. 未来 v0.2 的扩展方向是什么

---

## 2. Scope

### 2.1 目标

每日自动采集 GitHub Trending Top 30 项目，经过分类、评分、排序后，生成一份结构化日报，帮助用户发现与职业目标和兴趣方向最匹配的开源项目。

### 2.2 核心原则

| 原则 | 说明 |
|------|------|
| **单一数据源** | v0.1 仅处理 GitHub Trending 数据 |
| **线性流水线** | 采集 → 归一化 → 分类 → 评分 → 排序 → 输出，不可跳跃 |
| **确定性评分** | 所有评分规则预定义，不存在在线学习或反馈循环 |
| **职业价值优先** | Career Alignment（0~40）权重是 Trend Heat（0~20）的两倍 |
| **Focus Over Completeness** | 日报每天只推荐 3 项必读内容 |

### 2.3 非目标

- 不是通用信息聚合平台
- 不是 Arxiv 论文推荐系统
- 不是社交/协作平台
- 不是实时通知系统
- 不是 Auto Prompt 优化系统

---

## 3. Included Features

PKIA v0.1 包含以下能力，对应 PKIA v0.1 PRD 的 F1~F6 的子集：

### 3.1 F2: GitHub Trending 每日采集

| 项目 | 规格 |
|------|------|
| 数据源 | GitHub Trending（https://github.com/trending） |
| 采集规模 | Top 30 项目/天 |
| 采集频率 | 每日 1 次（建议 UTC 00:00 触发） |
| 采集字段 | `project_id`, `project_name`, `owner`, `description`, `topics`, `stars`, `forks`, `language`, `source`, `collection_date` |
| 失败降级 | 保留上次成功数据 |

### 3.2 F2: Project Normalization

| 项目 | 规格 |
|------|------|
| 输入 | Stage 1 Raw Object |
| 输出 | Stage 2 Normalized Object |
| 处理能力 | Description 截断（≤200 字符）、标签标准化、关键词提取（≤5 个） |
| 新增字段 | `normalized_description`, `primary_language`, `extracted_keywords` |

### 3.3 F2: Category Classification

| 项目 | 规格 |
|------|------|
| 分类体系 | 11 个 Level-1, 32 个 Level-2（`project_classification_taxonomy_v1.md`） |
| 输出字段 | `primary_category`, `secondary_categories`, `classification_confidence` (HIGH/MEDIUM/LOW), `classification_notes` |
| 生命周期 | 有效类别 → `PROMOTED`；Ignore 列表 → `FILTERED_BY_CATEGORY` |
| Ignore 类别 | Frontend, Mobile, Blockchain, Crypto, NFT, Web3 |

### 3.4 F4 + F5: Scoring Pipeline（Stage 4~9）

| 维度 | 分值范围 | 来源文档 |
|------|----------|----------|
| Career Alignment | 0~40 | `scoring_strategy_v1.md` |
| Interest Match | 0~30 | `interest_profile_v1.md` |
| Trend Heat | 0~20 | `scoring_strategy_v1.md` |
| Research Relevance | 0~10 | `scoring_strategy_v1.md` |
| Total Score | 0~100 | 四维之和 |
| `career_goal_impact` | HIGH/MEDIUM/LOW × 4 目标 | `prompt_scoring_agent_v2.md` |
| Recommendation | STRONG_RECOMMEND / RECOMMEND / OBSERVE / IGNORE | 阈值: 90+/70~89/40~69/0~39 |

### 3.5 F4: Daily Report Ranking（Stage 10）

| 项目 | 规格 |
|------|------|
| 排序依据 | ranking_group → total_score → career_alignment → interest_match |
| 输出字段 | `rank`, `ranking_group` |
| 生命周期 | 全部项目 → `ARCHIVED` |

### 3.6 F4: Daily Report 生成

| 项目 | 规格 |
|------|------|
| 输出格式 | Markdown 文件 |
| 存储位置 | `pkia/reports/YYYY-MM-DD.md` |
| 章节结构 | Section A: 今日概览 / B: Strong Recommend / C: Recommend / D: Observe / E: Interest Evolution / F: 今日阅读建议 |
| Section B 展示 | 含职业目标影响（4 个目标 × HIGH/MEDIUM/LOW） |
| Section F 限制 | 每天仅选 3 项 |

### 3.7 F3: 兴趣标注（基础版）

| 项目 | 规格 |
|------|------|
| 标注操作 | 兴趣 / 待深度阅读 / 已读 / 不感兴趣 |
| 存储 | Session 级或本地文件（v0.1 不需要 DB） |
| 影响范围 | 影响 Interest Match 评分权重 |

### 3.8 F6: 历史回顾（基础版）

| 项目 | 规格 |
|------|------|
| 查询维度 | 按日期 / 按分类 / 按来源 |
| 数据源 | 历史 Markdown 日报文件 |

---

## 4. Excluded Features

以下能力**明确不属于** PKIA v0.1 范围：

| 能力 | 说明 | 计划版本 |
|------|------|----------|
| **Arxiv 论文采集** | v0.1 仅 GitHub Trending，不包含 Arxiv | v0.2 |
| **MCP Ecosystem 集成** | 不集成 MCP Server 作为数据源或工具 | v0.2+ |
| **Memory Ecosystem 集成** | 不将 L2 Memory 作为评分输入或输出存储 | v0.2+ |
| **Multi-Source Aggregation** | 不聚合多个数据源（如 Hacker News, Reddit） | v0.2 |
| **User Feedback Learning** | 不根据用户反馈自动调整评分权重 | v0.3 |
| **Auto Prompt Optimization** | 不自动优化 Scoring Agent Prompt | v0.3 |
| **Web UI** | 日报通过 Markdown 文件交付，不开发 Web 界面 | v0.2 |
| **实时推送** | 不提供 WebSocket/Webhook 推送 | v0.2 |
| **用户登录/鉴权** | 单机本地使用，不实现多用户系统 | v0.2+ |
| **数据分析/可视化仪表盘** | 不提供历史趋势图表 | v0.2 |

---

## 5. Data Sources

### 5.1 唯一数据源

```
GitHub Trending
  └── URL: https://github.com/trending
  └── 规模: Top 30 / 天
  └── 频率: 每日 1 次
  └── 首字段: project_id
```

### 5.2 数据源约束

| 约束 | 说明 |
|------|------|
| 不可配置 | v0.1 不支持用户自定义数据源 |
| 不可扩展 | v0.1 不支持在 GitHub 之外增加额外来源 |
| 降级策略 | 采集失败时展示"数据采集失败，展示昨日数据"并复用缓存 |

### 5.3 数据标识规则

`project_id` 生成规则：`collection_date + source + project_name` 的确定性哈希。

示例：
```
输入: 2026-06-14 + github_trending + openmanus
输出: gt-20260614-openmanus (确定性哈希前缀 + 可读标识)
```

---

## 6. Processing Pipeline

### 6.1 完整链路

```
GitHub Trending (Top 30)
    │
    ▼
Stage 1: Data Collection     [Python 脚本]
    │                         输出: Raw Object (含 project_id)
    ▼
Stage 2: Project Normalization [Python 脚本 / Dify Code Node]
    │                         输出: Normalized Object
    ▼
Stage 3: Classification       [Dify LLM Node]
    │                         输出: Classified Object
    ▼
Stage 4-7: 四维评分           [Dify LLM Node — Scoring Agent v2 Prompt]
    │                         输出: Career Alignment / Interest Match / Trend Heat / Research Relevance
    ▼
Stage 8: Total Score          [Dify Code Node]
    │                         输出: Total Score + reasoning + career_goal_impact
    ▼
Stage 9: Recommendation       [Dify Code Node]
    │                         输出: STRONG_RECOMMEND / RECOMMEND / OBSERVE / IGNORE
    ▼
Stage 10: Ranking             [Dify Code Node]
    │                         输出: rank + ranking_group
    ▼
Report Generation Pipeline    [Dify Code Node / Python 脚本]
    │                         7 阶段: 分组 → 排序 → 兴趣演化 → 阅读选择 → 组装 → 最终检查
    ▼
Daily Report (Markdown)       [输出]
    存储: pkia/reports/YYYY-MM-DD.md
```

### 6.2 实现载体

| 层级 | 载体 | 说明 |
|------|------|------|
| 数据采集 | Python 独立脚本 | 抓取 GitHub Trending，生成 `project_id` |
| 数据处理 | Dify Workflow | Code Node + LLM Node 编排 |
| Agent 调用 | Dify LLM Node | Classification Agent + Scoring Agent v2 Prompt |
| 日报输出 | Python 脚本 / Dify Code Node | 生成结构化 Markdown |

### 6.3 关键约束

- `project_id` 必须在 Stage 1 生成，贯穿全链路，不可修改
- `pipeline_status` 生命周期：`PROMOTED` → `FILTERED_BY_CATEGORY` / `FILTERED_BY_SCORE` → `ARCHIVED`
- Stage 3 分类完成后才允许进入评分
- 被淘汰的项目（`FILTERED_BY_CATEGORY` / `FILTERED_BY_SCORE`）不删除，保留在历史数据中

---

## 7. Final Outputs

### 7.1 每日产出

```
pkia/reports/YYYY-MM-DD.md
  ├── Section A: 今日概览（统计数据）
  ├── Section B: Strong Recommend（完整展示 + 职业目标影响）
  ├── Section C: Recommend（简洁展示）
  ├── Section D: Observe（最小展示）
  ├── Section E: Interest Evolution（主题分布 + 条形图）
  └── Section F: 今日阅读建议（3 项）
```

### 7.2 每项目最终携带字段

| 类别 | 字段 | 来源 |
|------|------|------|
| 全局标识 | `project_id`, `project_name`, `source`, `collection_date` | Stage 1 |
| 原始数据 | `owner`, `description`, `topics`, `stars`, `forks`, `language` | Stage 1 |
| 标准化 | `normalized_description`, `primary_language`, `extracted_keywords` | Stage 2 |
| 分类 | `primary_category`, `secondary_categories`, `classification_confidence`, `classification_notes` | Stage 3 |
| 评分 | `career_alignment`, `interest_match`, `trend_heat`, `research_relevance`, `total_score`, `reasoning`, `career_goal_impact` | Stage 4~8 |
| 推荐 | `recommendation` | Stage 9 |
| 排名 | `rank`, `ranking_group` | Stage 10 |
| 状态 | `pipeline_status` | 贯穿 |

### 7.3 输出规格

| 规格项 | 值 |
|--------|-----|
| 文件格式 | Markdown (.md) |
| 文件命名 | `YYYY-MM-DD.md` |
| 存储路径 | `pkia/reports/` |
| 编码 | UTF-8 |
| 每日数量 | 1 份（包含当日所有 30 个项目） |

---

## 8. Frozen Documents

以下文档在 v0.1 范围内处于 **Frozen State**：

### 8.1 核心冻结文档（8 份）

| # | 文档 | 状态 | 作用域 |
|---|------|------|--------|
| 1 | `interest_profile_v1.md` | ✅ Frozen | 定义 S/A/B Tier 兴趣画像 |
| 2 | `project_classification_taxonomy_v1.md` | ✅ Frozen | 定义 11 Level-1 / 32 Level-2 分类体系 |
| 3 | `classification_agent_spec_v1.md` | ✅ Frozen | 定义 Classification Agent 行为（已 Schema 补丁） |
| 4 | `prompt_scoring_agent_v2.md` | ✅ Frozen | 定义 Scoring Agent v2 Prompt（已 Schema 补丁） |
| 5 | `project_data_schema_v1.md` | ✅ Frozen | 唯一数据契约，6 阶段数据结构 |
| 6 | `scoring_pipeline_schema_v2.md` | ✅ Frozen | 10 阶段评分流水线编排 |
| 7 | `report_generation_pipeline_v1.md` | ✅ Frozen | 7 阶段报告生成流水线（已 Schema 补丁） |
| 8 | `daily_report_spec_v1.md` | ✅ Frozen | 日报 6 章节展示规范（已 Career Goal Impact 补丁） |

### 8.2 辅助冻结文档（5 份）

| # | 文档 | 状态 | 说明 |
|---|------|------|------|
| 9 | `scoring_strategy_v1.md` | ✅ Frozen | 评分策略（基准分、阈值） |
| 10 | `scoring_examples_v1.1.md` | ✅ Frozen | 11 个 Few-shot 评分案例 |
| 11 | `data_collection_strategy_v1.md` | ✅ Frozen | 数据采集策略（Top 30, GitHub Only） |
| 12 | `workflow_v0.1_design.md` | ✅ Frozen | Dify Workflow 设计草稿 |
| 13 | `pkia-v01-prd.md` | ✅ Frozen | 原始 PRD（实现范围以本 Baseline 为准） |

### 8.3 已弃用文档（1 份）

| # | 文档 | 状态 | 说明 |
|---|------|------|------|
| — | `scoring_pipeline_schema_v1.md` | ⛔ DEPRECATED | 被 v2 取代，保留为历史参考 |
| — | `prompt_scoring_agent_v1.md` | ⛔ DEPRECATED | 被 v2 取代 |

### 8.4 冻结规则

- 冻结文档在 v0.1 生命周期内**禁止修改**
- 所有实现必须严格遵循冻结文档的定义
- 如需修改，必须发布 v0.2 Baseline 并升版对应文档

---

## 9. Success Criteria

### 9.1 MVP 成功定义

成功运行一次以下完整链路即视为 **PKIA MVP v0.1 成功**：

```
GitHub Trending Top 30
    ↓ (采集成功)
Stage 1: Data Collection       → 30 个 Raw Object（含 project_id）
    ↓
Stage 2: Normalization         → 30 个 Normalized Object
    ↓
Stage 3: Classification        → 30 个 Classified Object（含 primary_category + confidence）
    ↓
Stage 4~7: 四维评分            → 30 组评分（career_alignment + interest_match + trend_heat + research_relevance）
    ↓
Stage 8: Total Score           → 30 个 total_score + reasoning + career_goal_impact
    ↓
Stage 9: Recommendation        → 30 个 recommendation（含至少 1 个 STRONG_RECOMMEND 或 RECOMMEND）
    ↓
Stage 10: Ranking              → 30 组 rank + ranking_group
    ↓
Report Generation Pipeline     → 完整日报（6 章节，Markdown 格式）
```

### 9.2 验证检查清单

| 检查项 | 标准 |
|--------|------|
| 采集完整性 | 30 个项目，均含 `project_id` |
| 数据血缘 | 所有阶段 `project_id` 一致，可回溯到原始数据 |
| 分类覆盖率 | 所有项目的 `primary_category` 属于分类体系定义 |
| 评分一致性 | 4 维度分数之和 = `total_score` |
| `career_goal_impact` 完整性 | 每项 4 个子字段均已赋值，无空值 |
| Reasoning 完整性 | 每项均有 Reasoning 说明 |
| 推荐分布 | 30 个项目至少覆盖 3 个推荐等级中的 2 个（STRONG_RECOMMEND / RECOMMEND / OBSERVE） |
| 日报结构 | 6 章节完整，Section A 统计数据求和正确，Section F 恰好 3 项 |
| 章节互斥 | 同一项目不出现在不同章节（Section A 的统计数据除外） |
| 输出路径 | `pkia/reports/YYYY-MM-DD.md` 文件生成并格式正确 |

### 9.3 失败标准

| 失败场景 | 严重级别 | 处理方式 |
|----------|----------|----------|
| GitHub Trending 不可达 | BLOCKER | 保留上次成功数据，日报显示"采集失败，展示昨日数据" |
| 全部 30 个项目均为 Ignore | WARNING | 日报仅含 Section A + "今日所有项目均不符合兴趣画像" |
| Classification 覆盖率 < 80% | ERROR | 标记未分类项目，人工复核 |
| 评分维度缺失 | ERROR | 缺失维度按 0 分处理，在 Reasoning 中注明 |
| 日报章节缺失 | BLOCKER | 不输出无效日报，保留上一份日报 |
| `project_id` 冲突 | BLOCKER | 失败并记录冲突原始数据，不可静默覆盖 |

---

## 10. Future Roadmap

### v0.2（计划中）

| 能力 | 优先级 | 说明 |
|------|--------|------|
| Arxiv 论文采集 | P0 | 增加 cs.AI / cs.CL / cs.LG 分类论文 |
| Web UI 日报展示 | P0 | 替代 Markdown 文件，提供浏览器查看 |
| 多数据源聚合 | P1 | GitHub + Arxiv 统一评分与排序 |
| 实时推送 | P1 | Webhook / 邮件推送日报 |
| 历史数据可视化 | P2 | 趋势图表、兴趣演化时间线 |

### v0.3（远期）

| 能力 | 说明 |
|------|------|
| User Feedback Learning | 根据标注行为自动调整 Interest Match 权重 |
| Auto Prompt Optimization | 根据评分结果自动优化 Agent Prompt |
| MCP 工具集成 | 将 PKIA 暴露为 MCP Server |
| Multi-Agent 协作 | 多 Agent 并行评分与交叉验证 |

---

## 附录 A: 文档结构树

```
docs/
├── pkia_v0.1_baseline.md              ← 📌 本文件（Release Baseline）
│
├── pkia-v01-prd.md                     [Frozen] 产品需求文档
├── workflow_v0.1_design.md             [Frozen] Workflow 设计
│
├── interest_profile_v1.md              [Frozen] 兴趣画像
├── scoring_strategy_v1.md              [Frozen] 评分策略
├── scoring_examples_v1.1.md            [Frozen] 评分案例
├── project_classification_taxonomy_v1.md [Frozen] 分类体系
│
├── classification_agent_spec_v1.md     [Frozen] 分类 Agent ✅
├── prompt_scoring_agent_v2.md          [Frozen] 评分 Prompt v2 ✅
│
├── project_data_schema_v1.md           [Frozen] 数据契约
├── scoring_pipeline_schema_v2.md       [Frozen] 评分流水线 v2
├── report_generation_pipeline_v1.md    [Frozen] 报告生成流水线 ✅
├── daily_report_spec_v1.md             [Frozen] 日报规范 ✅
│
├── data_collection_strategy_v1.md      [Frozen] 数据采集策略
│
├── scoring_pipeline_schema_v1.md       [⛔ DEPRECATED]
├── prompt_scoring_agent_v1.md          [⛔ DEPRECATED]
│
├── schema_consistency_patch_v1.md      [历史] 一致性补丁计划
├── review_*.md                         [历史] 审查文档（5 份）
├── scoring_pipeline_patch_plan_v1.md   [历史] 补丁计划
│
└── migration_pkia_agent.md             [历史] 迁移上下文
```

## 附录 B: 缩写对照

| 缩写 | 全称 |
|------|------|
| PKIA | Personal Knowledge Intelligence Agent |
| PRD | Product Requirements Document |
| MVP | Minimum Viable Product |
| SSOT | Single Source of Truth |
| L2 | Layer 2 — Knowledge Graph Memory |
| L3 | Layer 3 — Progress Memory |
| F1~F6 | PKIA v0.1 PRD 定义的 6 个功能 |

---

*End of Baseline. Implementation scope locked for PKIA MVP v0.1.*