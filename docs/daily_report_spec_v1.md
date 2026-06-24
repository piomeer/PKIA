# PKIA Daily Report Specification v1

---

## 1. Purpose

Daily Report 是 PKIA 的核心输出。

它帮助用户回答四个问题：

1. 我以前看过什么？
2. 最近出现了什么新东西？
3. 和我关注方向有什么关系？
4. 是否值得投入时间？

---

## 2. Input Sources

v0.1 包含：

- **GitHub Trending** — 每日热门开源项目（Top 30）

---

## 3. Report Structure

每份日报包含以下 6 个章节。

---

### Section A: 今日概览

统计当日数据快照。

格式：

```
📊 今日概览
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• 新项目（GitHub Trending）:  N 个
• 🔴 Strong Recommend:        N 项
• 🟡 Recommend:                N 项
• ⚪ Observe:                  N 项
• ⚫ Ignore:                   N 项
```

---

### Section B: 🔴 Strong Recommend

强烈推荐层。展示评分 90+ 的项目。

每项包含：

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔴 Strong Recommend
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

项目名:     [name]
分类:       [category]
来源:       GitHub Trending
总分:       [score]

职业目标影响:
  Agent Application Engineer:        [HIGH / MEDIUM / LOW]
  AI Platform Engineer:              [HIGH / MEDIUM / LOW]
  LLM Inference Optimization Engineer: [HIGH / MEDIUM / LOW]
  Multi-Agent System Engineer:       [HIGH / MEDIUM / LOW]

推荐理由:
[why this project matters to the user]

与职业目标的关系:
[which career goal it serves and how]

预计阅读时间: [X] 分钟
```

---

### Section C: 🟡 Recommend

推荐层。展示评分 70–89 的项目。

每项包含：

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🟡 Recommend
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

项目名:     [name]
分类:       [category]
来源:       GitHub Trending
总分:       [score]

推荐理由:
[one-sentence reason]
```

---

### Section D: ⚪ Observe

观察层。展示评分 40–69 的项目。

每项包含：

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚪ Observe
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

项目名:     [name]
分类:       [category]
来源:       GitHub Trending
总分:       [score]

说明:
[one-sentence note on why it's on radar]
```

---

### Section E: Interest Evolution

今日主题分布分析。统计当日项目/论文中 Interest Profile 各主题的出现频次，并说明与用户兴趣方向的关系。

格式：

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 今日主题分布
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

热度排名（按出现频次）:

1. Agent            ████████████  N 次  ← S Tier
2. Memory           █████████      N 次  ← S Tier
3. MCP              ██████         N 次  ← A Tier
4. RAG              █████          N 次  ← A Tier
5. Multi-Agent      ████           N 次  ← S Tier
6. Inference        ███            N 次  ← S Tier
7. Knowledge Graph  ██             N 次  ← B Tier

说明:
[commentary on today's theme trends and how they relate to Interest Profile]
```

---

### Section F: What To Read Today

今日阅读优先级建议。从所有项目中选出 **3 项**最值得投入时间的内容，排序并解释原因。

格式：

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 今日阅读建议
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Priority #1: [项目名]
原因: [为什么今天最值得读]
预计阅读时间: [X] 分钟

Priority #2: [项目名]
原因: [为什么值得排第二]
预计阅读时间: [X] 分钟

Priority #3: [项目名]
原因: [为什么值得排第三]
预计阅读时间: [X] 分钟
```

---

## 4. Design Principles

日报遵循以下原则：

1. **职业价值 > 热度** — 不因项目热门而提高推荐等级，只因其与用户职业目标的相关性。
2. **长期价值 > 短期热点** — 优先推荐具有持续学习价值的项目，而非一日爆红后快速沉寂的内容。
3. **Agent 优先** — Agent 相关项目在同等条件下优先级更高。
4. **帮助用户减少信息焦虑** — 日报的目标不是展示所有信息，而是告诉用户哪些值得看、哪些可以放心跳过。

---

## 5. Example Report

以下是一份基于示例数据的完整日报。

---

```
╔══════════════════════════════════════════════╗
║         PKIA Daily Report — 2026-06-14      ║
╚══════════════════════════════════════════════╝


📊 今日概览
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• 新项目（GitHub Trending）:  24 个
• 🔴 Strong Recommend:         3 项
• 🟡 Recommend:                 4 项
• ⚪ Observe:                   6 项
• ⚫ Ignore:                   11 项


━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔴 Strong Recommend
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

项目名:     OpenManus
分类:       Agent Framework
来源:       GitHub Trending
总分:       96

职业目标影响:
  Agent Application Engineer:        HIGH
  AI Platform Engineer:              MEDIUM
  LLM Inference Optimization Engineer: LOW
  Multi-Agent System Engineer:       MEDIUM

推荐理由:
社区最受关注的 Agent 框架之一，深度集成了 Tool Use、
Planning 和 Autonomous Execution 能力，代表了 Agent
框架的前沿设计方向。

与职业目标的关系:
直接支撑职业目标 #1（Agent Application Engineer）。
框架的技术架构和设计取舍将影响 Agent 产品的开发方式。

预计阅读时间: 15 分钟


━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔴 Strong Recommend
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

项目名:     Mem0 / Zep / Letta
分类:       Agent Memory
来源:       GitHub Trending
总分:       98

职业目标影响:
  Agent Application Engineer:        HIGH
  AI Platform Engineer:              MEDIUM
  LLM Inference Optimization Engineer: LOW
  Multi-Agent System Engineer:       HIGH

推荐理由:
Agent Memory 是 Agent 从无状态工具进化为有状态助手的
核心基础设施，且直接关系到 PKIA 自身的 Personal
Knowledge Agent 定位。

与职业目标的关系:
支撑职业目标 #1（Agent Application Engineer）和 #4
（Multi-Agent System Engineer）。记忆系统是区分简单
Chatbot 和真正 Agent 的核心差异点。

预计阅读时间: 20 分钟


━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🟡 Recommend
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

项目名:     LangGraph
分类:       Agent Workflow Framework
来源:       GitHub Trending
总分:       86

推荐理由:
LangChain 生态的 Agent 工作流编排框架，支持 Stateful
Agent 和 Multi-Agent 协作，值得作为 Agent Framework
的重要参考持续跟踪。


━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🟡 Recommend
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

项目名:     MCP Server Framework
分类:       MCP Ecosystem
来源:       GitHub Trending
总分:       86

推荐理由:
MCP 正在成为 Agent 连接外部工具的事实标准协议，对
Agent Tool Use 能力的实现有直接影响。


━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚪ Observe
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

项目名:     LlamaIndex
分类:       RAG Framework
来源:       GitHub Trending
总分:       72

说明:
RAG 成熟框架，功能稳定但已过快速创新期，按需查阅即可。


━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚪ Observe
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

项目名:     PyTorch Geometric
分类:       Knowledge Graph / Graph ML
来源:       GitHub Trending
总分:       38

说明:
图神经网络框架，与当前职业路径交集有限。仅在涉及
Graph RAG 或 Agent Memory + KG 场景时纳入考量。


━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 今日主题分布
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

热度排名（按出现频次）:

1. Agent            ████████████  12 次  ← S Tier
2. Memory           █████████      8 次  ← S Tier
3. MCP              ██████         5 次  ← A Tier
4. RAG              █████          4 次  ← A Tier
5. Multi-Agent      ████           3 次  ← S Tier
6. Inference        ███            2 次  ← S Tier
7. Knowledge Graph  ██             1 次  ← B Tier

说明:
今日 Agent 和 Memory 方向热度突出，与 Interest Profile
的 S Tier 高度吻合。MCP 持续增长，值得关注标准化进展。
Knowledge Graph 仅零星出现，不影响当前注意力分配。


━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 今日阅读建议
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Priority #1: Mem0 / Zep / Letta (Agent Memory)
原因: Agent Memory 是 PKIA 的底层技术基础，也是
职业目标 #1 和 #4 的核心能力。今日多个记忆框架同时
出现在 Trending 上，值得集中对比它们的设计取舍。
预计阅读时间: 20 分钟

Priority #2: OpenManus (Agent Framework)
原因: 社区热度最高，代表了 Agent 框架的最新发展方向。
理解其 Tool Use 和 Planning 设计有助于 Agent 产品开发。
预计阅读时间: 15 分钟

Priority #3: MCP Server Framework (MCP Ecosystem)
原因: MCP 标准化将直接影响 Agent Tool Use 的实现方式。
协议层的设计选择具有长期影响，值得花时间建立认知。
预计阅读时间: 10 分钟
```

---

*End of Specification. Compliant with PKIA Daily Report v0.1.*