# 评分策略 v1 — Career Alignment

## 职业目标（优先级排序）

1. **Agent Application Engineer** — 构建 Agent 应用的核心执行者
2. **AI Platform Engineer** — 搭建 AI 基础设施与平台
3. **LLM Inference Optimization Engineer** — 推理性能优化
4. **Multi-Agent System Engineer** — 多智能体系统协调

---

## 评分规则

### 40 分 — 核心赛道

| 领域 | 评分理由 | 与职业目标的关系 |
|------|----------|------------------|
| **Agent** | Agent 是当前 AI 应用层的核心范式，直接对应职业目标 #1 Agent Application Engineer 的核心能力。 | 构建、调试、优化 Agent 是首要职责，必须持续跟踪。 |
| **Agent Memory** | Agent 记忆系统是 Agent 从"无状态工具"进化为"有状态助手"的关键基础设施。 | 直接影响 Agent 应用的用户体验和实用性，是区别于简单 Chatbot 的核心差异点。 |
| **Agent Framework** | LangChain、CrewAI、AutoGen 等框架是 Agent 开发的脚手架，决定开发效率和架构选择。 | 框架生态走向直接影响技术选型和工程实践。 |
| **Multi-Agent** | 多 Agent 协作是 Agent 从单兵作战到系统化解决问题的进阶方向，对应职业目标 #4。 | 直接对齐职业目标 #4，且是 #1 的自然演进。 |
| **AI Engineering** | 贯穿所有目标的基础能力——如何将模型能力工程化、产品化、可观测化。 | 所有四个职业目标的底层通用技能，覆盖测试、部署、监控、迭代全链路。 |

### 30 分 — 强相关

| 领域 | 评分理由 | 与职业目标的关系 |
|------|----------|------------------|
| **MCP** | Model Context Protocol 是 Agent 连接外部工具和数据的标准化接口，正在成为行业趋势。 | 对 #1（Agent 应用）和 #4（Multi-Agent）有直接价值，标准化协议决定 Agent 生态互操作性。 |
| **RAG** | 检索增强生成是 Agent 获取外部知识的主要手段，也是企业落地的核心场景。 | 职业目标 #2 AI Platform Engineer 需要构建 RAG Pipeline；#1 Agent 应用也需要 RAG 能力注入。 |
| **AI Infrastructure** | GPU 调度、模型部署、推理集群管理是 AI Platform Engineer 的日常。 | 直接对齐职业目标 #2。 |
| **LLMOps** | 模型生命周期管理、Prompt 管理、评估、监控。 | 对齐 #2 AI Platform Engineer 和 #3 LLM Inference Optimization Engineer。 |

### 20 分 — 值得关注

| 领域 | 评分理由 | 与职业目标的关系 |
|------|----------|------------------|
| **Frontier AI Trends** | 前沿趋势（如推理时 Scaling、合成数据、Self-Play）虽不直接落工程，但影响技术方向判断。 | 保持对前沿的感知有助于所有四个职业目标的技术判断力，但优先级低于可直接转化为工程实践的内容。 |

### 10 分 — 弱相关

| 领域 | 评分理由 | 与职业目标的关系 |
|------|----------|------------------|
| **Knowledge Graph** | 知识图谱在特定场景（企业知识管理、可解释推理）有价值，但与当前职业路径交集有限。 | 在 RAG 和 Agent Memory 场景中可能作为辅助技术出现，但不作为主攻方向。 |
| **Knowledge Graph Embedding** | 图嵌入技术主要用于 KG 的表示学习，偏研究侧，与工程落地距离较远。 | 与当前四个职业目标无直接交集，仅在涉及 Graph RAG 时可能间接相关。 |
| **Distributed Training** | 分布式训练是大模型训练的核心，但职业目标偏推理和应用侧而非训练侧。 | 对 #3 推理优化有一定参考价值（了解训练才能做推理优化），但非核心。 |
| **Graph Partitioning** | 图分割是分布式图计算/存储的系统问题，偏底层基础设施。 | 与当前职业路径交集极少，仅在超大规模知识图谱场景下可能涉及。 |

### 0 分 — 不相关

| 领域 | 评分理由 | 与职业目标的关系 |
|------|----------|------------------|
| **Frontend** | 前端开发属于传统 Web 工程，与 AI 系统工程无直接关联。 | 无。 |
| **Mobile** | 移动端开发与 AI 工程几乎没有交集。 | 无。 |
| **Blockchain** | 区块链与 AI Agent/平台工程属于完全不同的技术领域。 | 无。 |
| **Crypto** | 加密货币/Web3 与当前职业目标无任何关联。 | 无。 |

---

## 评分总览

| 分值 | 标签 | 领域 |
|------|------|------|
| **40** | 核心赛道 | Agent, Agent Memory, Agent Framework, Multi-Agent, AI Engineering |
| **30** | 强相关 | MCP, RAG, AI Infrastructure, LLMOps |
| **20** | 值得关注 | Frontier AI Trends |
| **10** | 弱相关 | Knowledge Graph, KG Embedding, Distributed Training, Graph Partitioning |
| **0** | 不相关 | Frontend, Mobile, Blockchain, Crypto |

此评分策略用于 PKIA v0.1 推荐系统的优先级排序：评分越高的领域，新条目更可能进入 🔴 强烈推荐层。