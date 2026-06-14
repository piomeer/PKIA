# PKIA Scoring Examples v1.1

## 文档目标

本文件用于展示典型项目如何按照 PKIA Scoring Strategy 进行评分。

评分结果用于帮助用户判断：

1. 是否值得关注
2. 是否值得投入时间
3. 与职业目标的关系
4. 与历史兴趣的关系

---

## 统一评分结构

每个案例必须严格包含：

### Project

项目名称

### Category

项目分类

### Scores

Career Alignment:
Interest Match:
Trend Heat:
Research Relevance:

Total Score:

### Recommendation

Strong Recommend
Recommend
Observe
Ignore

### Reasoning

详细说明：

- 为什么得到该 Career Alignment 分数
- 为什么与用户职业目标相关
- 为什么属于当前推荐等级

---

## 职业目标

按照以下优先级进行评分：

1. Agent Application Engineer
2. AI Platform Engineer
3. LLM Inference Optimization Engineer
4. Multi-Agent System Engineer

---

## 兴趣画像

**S Tier:**

- Agent
- Agent Application
- Agent Framework
- Agent Memory
- Multi-Agent
- AI Engineering

**A Tier:**

- MCP
- RAG
- AI Infrastructure
- Frontier AI Trends

**B Tier:**

- Knowledge Graph
- Knowledge Graph Embedding
- Distributed Training
- Graph Partitioning

**Ignore:**

- Frontend
- Mobile
- Blockchain
- Crypto

---

## 推荐等级标准

| 总分 | 等级 | 标签 |
|------|------|------|
| 90+ | 🔴 Strong Recommend | 强烈推荐 |
| 70~89 | 🟡 Recommend | 推荐 |
| 40~69 | ⚪ Observe | 观察 |
| 0~39 | ⚫ Ignore | 忽略 |

---

## 案例

---

### Case 1: OpenManus

**Category:** Agent Framework

**Scores:**

- Career Alignment: 40
- Interest Match: 30
- Trend Heat: 18
- Research Relevance: 8

**Total Score:** 96

**Recommendation:** 🔴 Strong Recommend

**Reasoning:**

OpenManus 是社区热门开源 Agent Framework。

特点：

- Tool Use
- Planning
- Autonomous Execution
- Agent Workflow

近期在 Agent 社区获得大量关注。

---

### Case 2: LangGraph

**Category:** Agent Workflow Framework

**Scores:**

- Career Alignment: 37
- Interest Match: 28
- Trend Heat: 15
- Research Relevance: 6

**Total Score:** 86

**Recommendation:** 🟡 Recommend

**Reasoning:**

LangGraph 是 LangChain 生态中的 Agent 工作流编排框架，核心能力覆盖 Stateful Agent、Multi-Agent 协作和循环控制流。Career Alignment 得 37 分，虽属 Agent Framework（40 分）子集，但其设计偏向图状工作流而非传统线性 Agent，与纯 Agent Framework 有细微偏离。对职业目标 #1（Agent Application Engineer）和 #4（Multi-Agent System Engineer）有直接价值。Interest Match 评 28 分因其属于 S Tier（Agent Framework），但 LangGraph 的图执行模型使得部分用户需要额外学习成本。综合评估后进入 Recommend 层，适合深度跟踪。

---

### Case 3: OpenAI Agents SDK

**Category:** Agent SDK

**Scores:**

- Career Alignment: 36
- Interest Match: 28
- Trend Heat: 15
- Research Relevance: 7

**Total Score:** 86

**Recommendation:** 🟡 Recommend

**Reasoning:**

OpenAI Agents SDK 是 OpenAI 官方发布的 Agent 构建工具包，定位偏向轻量级 SDK 而非 Full-Featured Framework。Career Alignment 得 36 分，因其核心属于 Agent（40 分），但 SDK 的抽象层级较低，主要解决 Agent 与 API 的交互问题，不涉及更高层次的规划与记忆管理。对职业目标 #1（Agent Application Engineer）有直接参考价值——了解 OpenAI 对 Agent 的定义和边界，有助于行业级 Agent 设计。Interest Match 得 28 分属于 S Tier。Trend Heat 适中，因 SDK 已发布一段时间，热度趋于稳定。综合评为 Recommend。

---

### Case 4: Dify

**Category:** Agent Platform

**Scores:**

- Career Alignment: 38
- Interest Match: 30
- Trend Heat: 14
- Research Relevance: 5

**Total Score:** 87

**Recommendation:** 🟡 Recommend

**Reasoning:**

Dify 是开源的 LLM 应用开发平台，核心能力覆盖 Agent Platform、Workflow Engine、RAG Platform、MCP Integration，定位为 AI Application Builder。Career Alignment 得 38 分，跨 Agent（40 分）和 AI Engineering（40 分）两大核心赛道。对于 PKIA 项目而言，Dify 不仅是工具，而是底层实现平台，因此权重提升。对职业目标 #1（Agent Application Engineer）和 #2（AI Platform Engineer）均有直接参考价值——其平台架构设计可作为构建 AI 应用的基础设施。Interest Match 得 30 分（S Tier：Agent + AI Engineering）。综合评为 Recommend，作为 PKIA 的技术底座持续跟踪。

---

### Case 5: MCP Server Framework

**Category:** MCP Ecosystem

**Scores:**

- Career Alignment: 35
- Interest Match: 25
- Trend Heat: 18
- Research Relevance: 8

**Total Score:** 86

**Recommendation:** 🟡 Recommend

**Reasoning:**

MCP（Model Context Protocol）正在成为 Agent 连接外部工具的事实标准。Agent 未来核心能力——Tool Use、External Context、System Integration——均依赖标准化的工具接口协议，而 MCP 正在成为该领域的事实标准。Career Alignment 得 35 分，对应 MCP（强相关赛道），对职业目标 #1（Agent 应用）和 #4（Multi-Agent 系统）有直接价值。Interest Match 得 25 分（A Tier）。Trend Heat 得 18 分，MCP 生态正处于快速发展期，社区活跃度高。Research Relevance 得 8 分，MCP 的定义和标准化过程本身具有一定的研究价值。综合评为 Recommend。

---

### Case 6: LlamaIndex

**Category:** RAG Framework

**Scores:**

- Career Alignment: 28
- Interest Match: 25
- Trend Heat: 12
- Research Relevance: 7

**Total Score:** 72

**Recommendation:** 🟡 Recommend

**Reasoning:**

LlamaIndex 是当前最成熟的 RAG 框架之一。Career Alignment 得 28 分，对应 RAG（30 分，强相关赛道），对职业目标 #1（Agent 应用需要 RAG 注入知识）和 #2（AI Platform Engineer 需要构建 RAG Pipeline）均有支撑。Interest Match 得 25 分（A Tier：RAG）。Trend Heat 得 12 分，RAG 已经过了爆炸性增长期，目前处于稳定成熟阶段。综合性价比较好，但已不是最前沿的探索方向。评为 Recommend。

---

### Case 7: Haystack

**Category:** RAG Platform

**Scores:**

- Career Alignment: 26
- Interest Match: 22
- Trend Heat: 10
- Research Relevance: 5

**Total Score:** 63

**Recommendation:** ⚪ Observe

**Reasoning:**

Haystack 是 deepset 推出的 RAG 平台，提供端到端的检索增强生成解决方案。Career Alignment 得 26 分，属于 RAG（30 分），但与 LlamaIndex、LangChain 等竞品相比，Haystack 的市场占有率和社区活跃度较低。对职业目标 #2（AI Platform Engineer）有一定参考价值——其 Pipeline 设计值得学习。Interest Match 得 22 分（A Tier：RAG，但非首选框架）。综合评为 Observe，值得保持关注但不作为主动跟踪的重点。

---

### Case 8: PyTorch Geometric

**Category:** Knowledge Graph / Graph ML

**Scores:**

- Career Alignment: 10
- Interest Match: 8
- Trend Heat: 12
- Research Relevance: 8

**Total Score:** 38

**Recommendation:** ⚪ Observe

**Reasoning:**

PyTorch Geometric（PyG）是图神经网络和知识图谱表示学习的核心框架。Career Alignment 得 10 分，对应 Knowledge Graph（弱相关赛道）。与当前四个职业目标交集有限——PyG 侧重图神经网络的训练，而非 Agent 应用或推理优化。Interest Match 得 8 分（B Tier）。Trend Heat 得 12 分，Graph ML 在学术界保持稳定的关注度。Research Relevance 得 8 分，图学习在 Neural-Symbolic 方向上可能与 Agent 产生交叉。综合评为 Observe，仅在 Graph RAG 或 Agent Memory 场景涉及图谱时纳入考量。

---

### Case 9: Spark GraphX

**Category:** Distributed Graph Computing

**Scores:**

- Career Alignment: 8
- Interest Match: 6
- Trend Heat: 8
- Research Relevance: 10

**Total Score:** 32

**Recommendation:** ⚫ Ignore

**Reasoning:**

Spark GraphX 是 Apache Spark 生态中的分布式图计算引擎。Career Alignment 得 8 分，靠近 Graph Partitioning（10 分，弱相关赛道）。与当前职业目标无直接交集——GraphX 专注于大规模图的分布式计算，与 Agent 应用、AI 平台工程、推理优化均不相关。Interest Match 得 6 分（B Tier），但 GraphX 作为相对成熟和老旧的技术，在 Graph ML 领域的关注度已被 PyG 和 DGL 取代。Research Relevance 得 10 分，分布式图计算仍是大规模知识图谱的底层技术，但作为独立领域投入时间性价比低。评为 Ignore。

---

### Case 10: Anthropic New Model Release

**Category:** Frontier AI Trends

**Scores:**

- Career Alignment: 20
- Interest Match: 18
- Trend Heat: 15
- Research Relevance: 4

**Total Score:** 57

**Recommendation:** ⚪ Observe

**Reasoning:**

新模型的发布（如 Claude 系列更新）属于 Frontier AI Trends。Career Alignment 得 20 分，前沿趋势虽不直接转化为工程实践，但影响技术方向判断，对所有四个职业目标都有间接价值。Interest Match 得 18 分（A Tier）。Trend Heat 得 15 分，新模型发布本身是热点事件，但热度会在发布后快速衰减。Research Relevance 得 4 分，模型发布本身是产品事件而非学术突破。评为 Observe——值得了解核心信息（能力边界、价格、可用性），但不值得投入大量时间深度研究，除非其架构带来了新的工程范式。

---

### Case 11: Agent Memory Framework

**Examples:** Mem0, Zep, Letta, OpenMemory

**Category:** Agent Memory

**Scores:**

- Career Alignment: 40
- Interest Match: 30
- Trend Heat: 18
- Research Relevance: 10

**Total Score:** 98

**Recommendation:** 🔴 Strong Recommend

**Reasoning:**

Agent Memory 框架（Mem0、Zep、Letta、OpenMemory 等）是 Agent 记忆系统的核心基础设施。Agent Memory 是 Agent → Stateful Agent → Personal Knowledge Agent 演进路径中的核心基础设施，对于 PKIA 项目价值极高。Career Alignment 得 40 分（核心赛道：Agent Memory），Agent 记忆是 Agent 从"无状态工具"进化为"有状态助手"的关键技术。对职业目标 #1（Agent Application Engineer）有极高价值——记忆系统是区分简单 Chatbot 和真正 Agent 的核心能力。对职业目标 #4（Multi-Agent System Engineer）同样重要——多 Agent 协作需要共享记忆和状态管理。Interest Match 得 30 分（S Tier）。Trend Heat 得 18 分，Agent Memory 正在成为 Agent 生态中最活跃的方向之一。Research Relevance 得 10 分，记忆机制本身是一个活跃的研究领域，且对 PKIA 的 Personal Knowledge Agent 定位有直接支撑。强烈推荐跟踪这些框架的发展和设计取舍。

---

## 案例汇总

| 编号 | 项目 | 分类 | 总分 | 推荐等级 |
|------|------|------|------|----------|
| 1 | OpenManus | Agent Framework | 96 | 🔴 Strong Recommend |
| 2 | LangGraph | Agent Workflow Framework | 86 | 🟡 Recommend |
| 3 | OpenAI Agents SDK | Agent SDK | 86 | 🟡 Recommend |
| 4 | Dify | Agent Platform | 87 | 🟡 Recommend |
| 5 | MCP Server Framework | MCP Ecosystem | 86 | 🟡 Recommend |
| 6 | LlamaIndex | RAG Framework | 72 | 🟡 Recommend |
| 7 | Haystack | RAG Platform | 63 | ⚪ Observe |
| 8 | PyTorch Geometric | Knowledge Graph / Graph ML | 38 | ⚪ Observe |
| 9 | Spark GraphX | Distributed Graph Computing | 32 | ⚫ Ignore |
| 10 | Anthropic New Model Release | Frontier AI Trends | 57 | ⚪ Observe |
| 11 | Agent Memory Framework | Agent Memory | 98 | 🔴 Strong Recommend |

---

## 分数分布检查

- **90+**（Strong Recommend）：Case 1 (96)、Case 11 (98) — 2 个
- **70~89**（Recommend）：Case 4 (87)、Case 2 (86)、Case 3 (86)、Case 5 (86)、Case 6 (72) — 5 个
- **40~69**（Observe）：Case 7 (63)、Case 10 (57)、Case 8 (38→Observe) — 3 个
- **0~39**（Ignore）：Case 9 (32) — 1 个

所有评分均严格遵守 scoring_strategy_v1.md 的 Career Alignment 分值定义。

---

# PKIA Priority Ranking

按照当前用户职业目标排序：

| 优先级 | 领域 | 代表项目 | 总分 |
|--------|------|----------|------|
| 1 | Agent Memory | Mem0, Zep, Letta, OpenMemory | 98 |
| 2 | Agent Framework | OpenManus, LangGraph, OpenAI Agents SDK | 96 / 86 |
| 3 | Dify Platform | Dify | 87 |
| 4 | MCP Ecosystem | MCP Server Framework | 86 |
| 5 | OpenAI Agents SDK | OpenAI Agents SDK | 86 |
| 6 | LangGraph | LangGraph | 86 |
| 7 | LlamaIndex | LlamaIndex | 72 |
| 8 | Frontier AI Trends | Anthropic New Model Release | 57 |
| 9 | Knowledge Graph | PyTorch Geometric | 38 |
| 10 | Distributed Graph Computing | Spark GraphX | 32 |

该排名用于未来：

- PKIA 推荐排序
- Workflow 推荐权重
- Daily Report 排序