# PKIA Project Classification Taxonomy v1

---

## 1. Purpose

Scoring Agent 不应该直接根据项目名字评分。

"OpenManus"这个名字本身不携带评分信息。必须先完成：

```
Project → Classification → Scoring
```

分类是评分的前置步骤。如果分类错误，后续的 Career Alignment 评分、Interest Match 评分都会偏离正确方向。

本文件定义 PKIA 的统一项目分类体系（Project Classification Taxonomy）。该体系是 PKIA 所有 Agent 的唯一分类依据：

- **Classification Agent** 依据此 Taxonomy 对项目进行分类
- **Scoring Agent** 依据此 Taxonomy 输出的 Primary/Secondary Category 进行评分
- **Daily Report Agent** 依据此 Taxonomy 进行主题统计和 Interest Evolution 分析
- **Workflow Mapping** 依据此 Taxonomy 决定项目流向哪个评分路径

Taxonomy 只回答一个问题：**"这个项目属于哪个类别？"**

关于"这个类别值多少分"的问题，由 scoring_strategy_v1.md 回答。分类层和评分层职责不同，不应混淆。

---

## 2. Taxonomy Design Principles

### Principle 1: Single Primary Category

每个项目必须有且只有一个 **Primary Category**。

- Primary Category 是该项目最主要的身份标识
- Primary Category 决定 Career Alignment 评分的基准分（40/30/20/10/0）
- 不允许出现"无分类"或"多 Primary"的情况

选择 Primary Category 的优先级规则：
1. **S Tier > A Tier > B Tier > Ignore** — 如果项目同时属于多个 Tier 的类别，以最高 Tier 为准
2. **Agent 优先** — 如果项目同时属于 Agent 相关和非 Agent 相关类别，优先归入 Agent 类别
3. **工程优先** — 如果项目同时属于工程实现类和理论分析类，优先归入工程实现类

### Principle 2: Multiple Secondary Categories

每个项目允许有 0~3 个 Secondary Categories。

- Secondary Categories 补充描述项目的其他能力维度
- Secondary Categories 用于 Interest Match 评分的精细调整
- 超过 3 个 Secondary Categories 意味着分类粒度太粗，需要调整 Taxonomy 本身

示例：

```
LangGraph
  Primary:    Agent Framework
  Secondary:  Multi-Agent, Agent Memory  ← 2 个 Secondary
```

### Principle 3: Career Alignment First

Taxonomy 的分类逻辑服务于职业目标，而不是学术分类。

这意味着：
- **Agent Application Engineer** 关注的 Agent 相关类别值得更细的粒度（Agent Framework、Agent Runtime、Agent Platform、Agent Application 各自独立）
- **LLM Inference Optimization Engineer** 关注的 Inference 和 Serving 类别需要独立存在
- **Knowledge Graph** 虽然是一个完整的学术领域，但在 PKIA 中仅作为一个二级类别存在，因为它在职业目标中的权重较低

Taxonomy 的分类粒度与 Career Alignment 权重正相关。权重越高的方向，分类越细。

---

## 3. Level-1 Categories

PKIA 定义 11 个一级分类（Level-1 Categories），每个一级分类下包含若干二级分类（Level-2 Categories）。

### 3.1 Agent

覆盖 Agent 构建、运行、管理和应用生态。

**Level-2 Categories：**

| 二级分类 | 说明 | 典型项目 |
|----------|------|----------|
| Agent Framework | Agent 开发框架，提供 Agent 的构建基座 | LangGraph, CrewAI, AutoGen, OpenAI Agents SDK |
| Agent Runtime | Agent 运行时环境，负责 Agent 的部署和执行 | Agent Sandbox, Agent Server |
| Agent Platform | 集成化 Agent 开发/部署平台，通常包含 UI | Dify, Flowise |
| Agent Application | 面向特定场景的 Agent 产品 | Code Agent, Browser Agent |

### 3.2 Agent Memory

覆盖 Agent 记忆系统的存储、管理和检索。

**Level-2 Categories：**

| 二级分类 | 说明 | 典型项目 |
|----------|------|----------|
| Memory Framework | Agent 记忆的通用框架/库 | Mem0, LangMem |
| Memory Infrastructure | 记忆系统的底层存储和检索基础设施 | Zep, Letta, OpenMemory |

### 3.3 Multi-Agent

覆盖多 Agent 系统的协作、通信和编排。

**Level-2 Categories：**

| 二级分类 | 说明 | 典型项目 |
|----------|------|----------|
| Coordination | 多 Agent 之间的任务分配和工作流编排 | CrewAI, AutoGen |
| Communication | Agent 之间的消息传递和协议 | Agent Communication Protocol |
| Planning | 多 Agent 的联合规划和决策 | Plan-and-Solve, ReAct variants |

### 3.4 MCP

覆盖 Model Context Protocol 生态。

**Level-2 Categories：**

| 二级分类 | 说明 | 典型项目 |
|----------|------|----------|
| MCP Server | 实现 MCP Server 的工具/库 | MCP Python SDK, MCP TypeScript SDK |
| MCP Framework | 基于 MCP 的应用开发框架 | MCP Agent Framework |
| MCP Ecosystem | MCP 生态的工具链和社区项目 | MCP Marketplace, MCP Inspector |

### 3.5 RAG

覆盖检索增强生成生态。

**Level-2 Categories：**

| 二级分类 | 说明 | 典型项目 |
|----------|------|----------|
| RAG Framework | RAG 的通用框架/库 | LlamaIndex, Haystack |
| Retrieval | 检索技术，包括嵌入、索引、检索策略 | ColBERT, BM25 |
| Knowledge Ingestion | 文档解析、分块、预处理 | Unstructured, Docling |

### 3.6 AI Engineering

覆盖 AI 应用工程化的通用能力。

**Level-2 Categories：**

| 二级分类 | 说明 | 典型项目 |
|----------|------|----------|
| Workflow | AI 工作流编排 | Dify Workflow, Temporal |
| Orchestration | 多步骤任务的编排和调度 | Airflow, Prefect |
| Evaluation | AI 应用评估和测试 | LangSmith Evaluation, DeepEval |
| Observability | AI 应用的可观测性 | LangFuse, Helicone |

### 3.7 AI Infrastructure

覆盖 AI 系统的底层基础设施。

**Level-2 Categories：**

| 二级分类 | 说明 | 典型项目 |
|----------|------|----------|
| Serving | 模型服务框架 | vLLM, SGLang |
| Inference | 推理引擎和推理优化 | TensorRT-LLM, ONNX Runtime |
| Deployment | 模型部署工具 | BentoML, Ray Serve |

### 3.8 LLMOps

覆盖大模型的生产化运维。

**Level-2 Categories：**

| 二级分类 | 说明 | 典型项目 |
|----------|------|----------|
| Monitoring | 模型监控和告警 | LangSmith, Weights & Biases |
| Optimization | Prompt 优化、缓存、成本控制 | PromptPerfect, GPTCache |
| Production | 生产化工具链 | MLflow, Kubeflow |

### 3.9 Frontier AI

覆盖前沿 AI 趋势。

**Level-2 Categories：**

| 二级分类 | 说明 | 典型项目 |
|----------|------|----------|
| Model Release | 新模型发布 | Claude 新版本, GPT 新版本 |
| Research Trend | 研究趋势和技术突破 | 推理时 Scaling, Self-Play RL |

### 3.10 Knowledge Graph

覆盖知识图谱和图 ML。

**Level-2 Categories：**

| 二级分类 | 说明 | 典型项目 |
|----------|------|----------|
| KG | 知识图谱构建和查询 | Neo4j, RDFlib |
| KGE | 知识图谱嵌入 | PyTorch Geometric, DGL |
| Graph ML | 图机器学习 | Graph Neural Networks, GAT |

### 3.11 Distributed Systems

覆盖分布式系统和计算。

**Level-2 Categories：**

| 二级分类 | 说明 | 典型项目 |
|----------|------|----------|
| Distributed Training | 分布式训练框架 | DeepSpeed, Megatron |
| Graph Partitioning | 图分割和分布式图计算 | Spark GraphX, Gemini |

---

## 4. Primary Category Rules

### 4.1 选择规则

选择 Primary Category 时，按以下优先级顺序判断：

1. **匹配最高 Interest Tier** — 如果项目同时属于 Agent（S Tier）和 RAG（A Tier），以 Agent 为 Primary
2. **Agent 优先** — 如果项目同时属于 Agent 相关和非 Agent 相关，以 Agent 为 Primary
3. **具体优先于通用** — Agent Framework 优先于 AI Engineering，Memory Framework 优先于 AI Infrastructure
4. **工程优先于研究** — 如果项目同时有工程实现和理论分析属性，以工程实现为 Primary

### 4.2 示例分析

#### Dify

Dify 横跨多个类别：
- Agent Platform（Agent 类）
- Workflow（AI Engineering 类）
- RAG Platform（RAG 类）

决策过程：
1. Agent 属于 S Tier，AI Engineering 和 RAG 属于 A Tier → 以 Agent 为 Primary
2. Agent Platform 比 Agent Framework 更准确地描述 Dify 的产品定位

**结果：Primary = Agent Platform**

#### LlamaIndex

LlamaIndex 横跨：
- RAG Framework（RAG 类）
- AI Engineering 的 Evaluation 能力

决策过程：
1. RAG 是 LlamaIndex 的核心身份，Evaluation 是辅助功能
2. RAG 属于 A Tier

**结果：Primary = RAG Framework**

#### vLLM

vLLM 横跨：
- Serving（AI Infrastructure 类）
- Inference（AI Infrastructure 类）

决策过程：
1. Serving 和 Inference 同属 AI Infrastructure（A Tier）
2. vLLM 的核心能力是 Serving

**结果：Primary = Serving**

### 4.3 禁止规则

- 禁止"多 Primary" — 一个项目不能同时有两个 Primary
- 禁止"模糊 Primary" — 不能使用"其他"或"通用 AI"作为 Primary Category
- 禁止"跨 Tier Primary" — 如果项目只有 B Tier 属性（如 Knowledge Graph），不能因社区热度将其 Primary 提升到 Agent

---

## 5. Secondary Category Rules

### 5.1 允许条件

以下情况允许添加 Secondary Categories：

1. **多领域交叉** — 项目明显覆盖多个分类领域（如 Dify 覆盖 Agent + RAG + Workflow）
2. **上下游关联** — 项目是一个更大生态的组成部分（如 LangMem 是 LangChain 生态中的记忆模块）
3. **功能互补** — 项目的主功能和辅助功能分别属于不同类别（如 LlamaIndex 的 RAG 主功能 + Evaluation 辅助功能）

### 5.2 禁止条件

以下情况禁止添加 Secondary Categories：

1. **类别重复** — Secondary 与 Primary 在同一 Level-2 范围内（如 Primary 已经是 Agent Framework，Secondary 不能再加 Agent Runtime 到 Agent Framework 的同级类别）
2. **过度拆分** — 为了增加分类数量而添加无关的 Secondary
3. **推测性标注** — 项目未明确显示某种能力，但"猜测"它可能具备该能力

### 5.3 数量限制

- **最小：** 0 个（项目只属于一个分类，无需 Secondary）
- **最大：** 3 个（超过 3 个意味着分类粒度需要调整）
- **建议：** 大多数项目 1~2 个 Secondary 足够

### 5.4 示例

| 项目 | Primary | Secondary 1 | Secondary 2 | Secondary 3 |
|------|---------|-------------|-------------|-------------|
| Dify | Agent Platform | AI Engineering → Workflow | RAG → RAG Framework | — |
| LangGraph | Agent Framework | Multi-Agent → Coordination | Agent Memory → Memory Framework | — |
| LlamaIndex | RAG Framework | AI Engineering → Evaluation | — | — |

---

## 6. Classification Examples

### 6.1 OpenManus

- **Primary:** Agent Framework
- **Secondary:** Multi-Agent → Coordination, Agent Application
- **理由：** OpenManus 的核心是 Agent 构建框架，提供 Tool Use 和 Planning 能力。同时支持多 Agent 协作模式和直接构建 Agent 应用。作为社区热门开源项目，其 Framework 属性最为突出。

### 6.2 LangGraph

- **Primary:** Agent Framework
- **Secondary:** Multi-Agent → Coordination, Agent Memory → Memory Framework
- **理由：** LangGraph 是 LangChain 生态中的 Agent 工作流编排框架。其图执行模型天然支持多 Agent 协作（Coordination），且与 LangMem 深度集成提供了 Agent Memory 能力。但核心身份仍是 Agent Framework。

### 6.3 CrewAI

- **Primary:** Agent Framework
- **Secondary:** Multi-Agent → Coordination, Multi-Agent → Communication
- **理由：** CrewAI 专注于多 Agent 的角色编排和任务分配。虽然 Multi-Agent 属性很强，但其核心产品形态是 Agent Framework。Secondary 覆盖了 Coordination 和 Communication 两个 Multi-Agent 子方向。

### 6.4 AutoGen

- **Primary:** Agent Framework
- **Secondary:** Multi-Agent → Coordination, Multi-Agent → Planning
- **理由：** AutoGen（Microsoft）支持多 Agent 对话和任务分配。作为 Agent Framework，它提供了 Agent 定义、Agent 间消息传递和任务规划能力。Primary 是 Agent Framework，Secondary 覆盖 Multi-Agent 的两个子方向。

### 6.5 OpenAI Agents SDK

- **Primary:** Agent Framework
- **Secondary:** 无
- **理由：** OpenAI Agents SDK 专注于提供轻量级的 Agent 构建工具。它不涉及多 Agent 协调，也不包含记忆管理。作为一个纯粹的单 Agent SDK，不需要 Secondary Categories。

### 6.6 Dify

- **Primary:** Agent Platform
- **Secondary:** AI Engineering → Workflow, RAG → RAG Framework, MCP → MCP Ecosystem
- **理由：** Dify 是集成化 AI 应用开发平台。Agent Platform 是 Primary（Agent 类+S Tier）。Secondary 覆盖 Workflow（AI Engineering）、RAG Framework（RAG）、MCP Ecosystem（MCP）三个方向。这是 3 个 Secondary 的上限案例。

### 6.7 Flowise

- **Primary:** Agent Platform
- **Secondary:** RAG → RAG Framework, AI Engineering → Workflow
- **理由：** Flowise 是低代码 AI 工作流平台，与 Dify 定位相似但功能范围略窄。Primary 为 Agent Platform。Secondary 覆盖 RAG 和 Workflow。

### 6.8 LlamaIndex

- **Primary:** RAG Framework
- **Secondary:** AI Engineering → Evaluation
- **理由：** LlamaIndex 的核心是 RAG 数据框架，提供索引、检索和查询能力。Secondary 指向其 Evaluation 功能（AI Engineering）。不归入 Agent 类，因为 LlamaIndex 本身不是 Agent 框架。

### 6.9 Haystack

- **Primary:** RAG Framework
- **Secondary:** AI Engineering → Orchestration
- **理由：** Haystack 是 deepset 的端到端 RAG 平台。与 LlamaIndex 类似，Primary 为 RAG Framework。其 Pipeline 编排能力（Orchestration）作为 Secondary。

### 6.10 MCP Server（泛指）

- **Primary:** MCP Server
- **Secondary:** MCP → MCP Framework
- **理由：** MCP Server 项目（如 MCP Python SDK 实现的 Server）核心身份是 MCP Server。如果该项目同时提供了开发框架的能力，可加 MCP Framework 作为 Secondary。

### 6.11 Mem0

- **Primary:** Memory Framework
- **Secondary:** AI Engineering → Observability
- **理由：** Mem0 是 Agent 记忆管理框架，提供长期记忆的存储和检索。核心身份是 Memory Framework（Agent Memory 类）。其提供了记忆使用的可观测性功能作为 Secondary。

### 6.12 Letta

- **Primary:** Memory Infrastructure
- **Secondary:** Agent Framework
- **理由：** Letta（原 MemGPT）提供 Agent 记忆系统的底层基础设施，包括虚拟上下文管理和记忆分层。Primary 为 Memory Infrastructure。其与 Agent 的深度集成使 Agent Framework 成为合理的 Secondary。

### 6.13 OpenMemory

- **Primary:** Memory Infrastructure
- **Secondary:** 无
- **理由：** OpenMemory 专注于为 Agent 提供持久化记忆存储。它是一个专注的 Infrastructure 项目，不涉足 Agent 框架层面。无需 Secondary Categories。

### 6.14 LangMem

- **Primary:** Memory Framework
- **Secondary:** Agent Framework
- **理由：** LangMem 是 LangChain 生态中专门为 Agent 提供持久化状态的记忆模块。核心是 Memory Framework（Agent Memory 类），Secondary 是 Agent Framework（作为 LangChain 生态的一部分）。

### 6.15 vLLM

- **Primary:** Serving
- **Secondary:** AI Infrastructure → Inference
- **理由：** vLLM 是高性能 LLM 推理和服务引擎。Primary 为 Serving（AI Infrastructure 类），Secondary 为 Inference（同一 Level-1 下的不同 Level-2）。vLLM 的 PagedAttention 等优化技术使其在推理优化方面也有显著贡献。

### 6.16 SGLang

- **Primary:** Serving
- **Secondary:** AI Infrastructure → Inference, AI Engineering → Orchestration
- **理由：** SGLang 是 LLM 推理和服务引擎，专注于结构化生成和运行时优化。Primary 为 Serving。Secondary 覆盖 Inference（推理优化）和 Orchestration（结构化生成编排）。

### 6.17 OpenRouter

- **Primary:** AI Infrastructure
- **Secondary:** LLMOps → Monitoring
- **理由：** OpenRouter 是多模型访问网关，提供统一的 API 接口和模型路由能力。不属于 Serving（不直接部署模型），也不属于 Agent Framework。Primary 为 AI Infrastructure 的一级分类（不细分到 Level-2），Secondary 为 LLMOps 的 Monitoring。

### 6.18 PyTorch Geometric

- **Primary:** Graph ML
- **Secondary:** Knowledge Graph → KGE
- **理由：** PyTorch Geometric 是图神经网络框架。Primary 为 Graph ML（Knowledge Graph 类），Secondary 为 KGE（Knowledge Graph Embedding）。虽然在学术上 GNN 和 KGE 有区别，但在 PKIA 分类体系中，两者共同归入 Knowledge Graph 一级分类。

### 6.19 Spark GraphX

- **Primary:** Graph Partitioning
- **Secondary:** Distributed Systems → Distributed Training
- **理由：** Spark GraphX 是 Apache Spark 上的分布式图计算引擎。Primary 为 Graph Partitioning（Distributed Systems 类）。其运行在 Spark 上的分布式架构使得 Distributed Training 成为一个合理的 Secondary。

### 6.20 Anthropic Claude Release

- **Primary:** Model Release
- **Secondary:** Frontier AI → Research Trend
- **理由：** 新模型发布属于 Frontier AI 类别。Primary 为 Model Release。如果发布同时包含了重要的技术论文或架构创新，可加 Research Trend 作为 Secondary。这是一个典型的"短期事件 + 长期趋势"的混合案例。

### 6.21 Additional Examples

#### 6.21.1 LangSmith

- **Primary:** LLMOps → Monitoring
- **Secondary:** AI Engineering → Evaluation, AI Engineering → Observability
- **理由：** LangSmith 是 LLM 应用的可观测性和评估平台。Primary 为 LLMOps 的 Monitoring。Secondary 覆盖 Evaluation 和 Observability（AI Engineering 类）。

#### 6.21.2 Weights & Biases

- **Primary:** LLMOps → Monitoring
- **Secondary:** AI Engineering → Evaluation
- **理由：** W&B 是 ML 实验跟踪和模型监控平台。Primary 为 Monitoring（LLMOps）。Secondary 为 Evaluation（AI Engineering）。

#### 6.21.3 DeepSpeed

- **Primary:** Distributed Training
- **Secondary:** AI Infrastructure → Inference
- **理由：** DeepSpeed 是 Microsoft 的分布式训练优化库。Primary 为 Distributed Training（Distributed Systems 类）。其 ZeRO-Inference 技术也涉及推理优化，作为 Secondary。

#### 6.21.4 TensorRT-LLM

- **Primary:** Inference
- **Secondary:** AI Infrastructure → Serving
- **理由：** TensorRT-LLM 是 NVIDIA 的 LLM 推理优化引擎。Primary 为 Inference（AI Infrastructure 类）。Secondary 为同一 Level-1 的 Serving。

---

## 7. Mapping to Interest Profile

### 7.1 规则

Taxonomy 的 Level-1 和 Level-2 类别直接映射到 interest_profile_v1.md 的 Interest Tiers：

| Interest Tier | 对应 Level-1 类别 |
|---------------|-------------------|
| **S Tier** | Agent, Agent Memory, Multi-Agent |
| **A Tier** | MCP, RAG, AI Engineering, AI Infrastructure, LLMOps, Frontier AI |
| **B Tier** | Knowledge Graph, Distributed Systems |

### 7.2 映射说明

**S Tier 映射：**
- Agent 类的所有 Level-2（Agent Framework, Agent Runtime, Agent Platform, Agent Application）均属于 S Tier
- Agent Memory 类的所有 Level-2（Memory Framework, Memory Infrastructure）均属于 S Tier
- Multi-Agent 类的所有 Level-2（Coordination, Communication, Planning）均属于 S Tier

**A Tier 映射：**
- MCP、RAG、AI Engineering、AI Infrastructure、LLMOps 的一级分类均属于 A Tier
- Frontier AI 属于 A Tier（需要注意：Frontier AI 在 scoring_strategy_v1.md 中是 20 分，但在 Interest Profile 中属于 A Tier，两者存在细微差异——Interest Profile 认为该领域值得长期关注，Scoring Strategy 认为其直接职业价值有限）

**B Tier 映射：**
- Knowledge Graph 类（KG, KGE, Graph ML）属于 B Tier
- Distributed Systems 类（Distributed Training, Graph Partitioning）属于 B Tier

### 7.3 边界案例处理

如果一个项目跨越多个 Tier（如一个项目同时涉及 Agent Framework 和 Knowledge Graph），以最高 Tier 为准：

- Primary Category 决定基准 Career Alignment 分数
- Secondary Categories 用于 Interest Match 的精细调整
- 不会因为 Secondary 属于低 Tier 而降低总分

---

## 8. Mapping to Career Goals

### 8.1 四目标映射

| 职业目标 | 直接相关的 Level-1 类别 | 间接相关的 Level-1 类别 |
|----------|------------------------|------------------------|
| #1 Agent Application Engineer | Agent, Agent Memory, Multi-Agent | MCP, RAG, AI Engineering |
| #2 AI Platform Engineer | AI Engineering, AI Infrastructure, LLMOps | Agent, MCP, RAG |
| #3 LLM Inference Optimization Engineer | AI Infrastructure (Serving, Inference) | AI Engineering (Evaluation), LLMOps |
| #4 Multi-Agent System Engineer | Multi-Agent, Agent Memory | Agent, MCP |

### 8.2 详细说明

**Agent Application Engineer（目标 #1）：**
- 直接相关：Agent 的所有子类别（Framework、Runtime、Platform、Application）、Agent Memory、Multi-Agent
- 间接相关：MCP（Agent 需要调用工具）、RAG（Agent 需要知识注入）、AI Engineering（工程化能力）
- 重点分类：Agent Framework, Memory Framework, Coordination

**AI Platform Engineer（目标 #2）：**
- 直接相关：AI Engineering（Workflow、Orchestration、Observability）、AI Infrastructure、LLMOps
- 间接相关：Agent Platform（平台需要考虑 Agent 支持）、MCP（平台需要标准化协议）
- 重点分类：Workflow, Serving, Monitoring

**LLM Inference Optimization Engineer（目标 #3）：**
- 直接相关：AI Infrastructure 的 Serving 和 Inference 子类
- 间接相关：LLMOps 的 Optimization、AI Engineering 的 Evaluation
- 重点分类：Serving, Inference, Deployment, Optimization

**Multi-Agent System Engineer（目标 #4）：**
- 直接相关：Multi-Agent 的所有子类、Agent Memory
- 间接相关：Agent Framework（多 Agent 的框架支持）、MCP（Agent 间通信可能依赖标准化协议）
- 重点分类：Coordination, Communication, Planning, Memory Infrastructure

### 8.3 分类-职业目标决策矩阵

当分类选择存在歧义时，参考以下矩阵决定 Primary Category：

| 候选类别 A | 候选类别 B | 决策 |
|------------|------------|------|
| Agent Framework (S/#1) | RAG Framework (A/#2) | 选择 Agent Framework |
| Agent Platform (S/#1,#2) | AI Engineering (A/#2) | 选择 Agent Platform |
| Serving (A/#3) | Inference (A/#3) | 选择 Serving（更贴近 #3 核心） |
| Memory Framework (S/#1,#4) | Agent Framework (S/#1) | 选择 Memory Framework（更具体） |

---

## 9. Future Expansion

Taxonomy v1 主要覆盖 PKIA v0.1 范围内的项目类别。随着 PKIA 版本的演进，Taxonomy 也需要扩展。

### v2 待新增类别

以下类别在 PKIA v0.1 文档中已被提及但未纳入 v1 Taxonomy，预计在 v2 中加入：

| 待新增 Level-1 | 待新增 Level-2 | 预计版本 | 说明 |
|----------------|---------------|----------|------|
| Agent OS | Agent Operating System | v2 | Agent 专用操作系统层 |
| Agent Browser | Browser Agent Framework | v2 | Agent 浏览器自动化框架 |
| Computer Use Agent | GUI Agent Framework | v2 | 计算机使用 Agent 框架 |
| AI Coding Agent | Code Agent Framework | v2 | AI 编程 Agent 框架 |

### 扩展原则

1. **按需扩展** — 只有当 PKIA 的用户（项目拥有者）开始关注某个新方向的多个项目时，才新增类别。不提前创建"可能有用"的空分类。
2. **保持一级分类数量可控** — 一级分类总数建议控制在 12~15 个以内。过多的 Level-1 分类会降低分类的可用性。
3. **分类迁移** — 如果某个 B Tier 类别因为职业目标调整上升到 A Tier，对应的 Level-2 分类可能需要拆分以获得更细的粒度。
4. **向后兼容** — Taxonomy v2 不应破坏 v1 的分类规则。已有的 Primary/Secondary 分类定义保持不变，仅新增类别。

---

## 10. Relationship with Existing Documents

本文件是 PKIA v0.1 文档体系中的"分类层"，与以下文档分工协作：

```
                      ┌──────────────────────────────┐
                      │   project_data_schema_v1.md   │
                      │   "项目长什么样"                │
                      └──────────┬───────────────────┘
                                 │ 定义字段结构
                                 ▼
                      ┌──────────────────────────────┐
                      │  project_classification_     │
                      │  taxonomy_v1.md  ← 本文件      │
                      │  "项目属于哪个类别"            │
                      └──────────┬───────────────────┘
                                 │ 提供 Primary/Secondary
                                 ▼
┌─────────────────────────────────────────────────────────────┐
│                     scoring_strategy_v1.md                   │
│                     "每个类别值多少分"                        │
│  Career Alignment: S=40, A=30, B=10                        │
└──────────┬──────────────────────────────────────┬──────────┘
           │ 引用评分规则                           │ 提供示例验证
           ▼                                        ▼
┌──────────────────────────┐          ┌──────────────────────────┐
│ scoring_pipeline_       │          │ scoring_examples_       │
│ schema_v1.md            │          │ v1.1.md                  │
│ "如何评分"               │          │ "评分长什么样"           │
└──────────┬──────────────┘          └──────────────────────────┘
           │ 输出分数
           ▼
┌──────────────────────────┐
│ report_generation_      │
│ pipeline_v1.md           │
│ "如何组织日报"           │
└──────────┬──────────────┘
           │ 输出日报
           ▼
┌──────────────────────────┐
│ daily_report_spec_v1.md │
│ "日报长什么样"           │
└──────────────────────────┘
```

### 各文档关系说明

| 文档 | 与本文件的关系 |
|------|---------------|
| **interest_profile_v1.md** | Taxonomy 的分类体系和 Interest Tiers 一一对应。Interest Profile 定义"用户关注什么"，Taxonomy 将此关注转化为可操作的分类标签 |
| **scoring_strategy_v1.md** | Taxonomy 的输出（Primary Category）是 Scoring Strategy 的输入。Taxonomy 说"这是 Agent Framework"，Scoring Strategy 说"Agent Framework 值 40 分"。两者职责清晰分离 |
| **scoring_examples_v1.1.md** | 提供实际案例验证 Taxonomy 是否合理。如果一个项目的 Primary Category 与 scoring_examples 中的分类不一致，说明 Taxonomy 需要调整 |
| **project_data_schema_v1.md（规划中）** | Project Data Schema 定义"项目长什么样"（数据结构），Taxonomy 定义"项目属于哪个类别"（分类逻辑）。两者共同作用于 Stage 2（Normalization）和 Stage 3（Classification） |
| **scoring_pipeline_schema_v1.md** | Pipeline 的 Stage 3（Category Classification）直接使用本 Taxonomy。Pipeline 定义"如何执行分类"，Taxonomy 定义"分类标准是什么" |
| **daily_report_spec_v1.md** | 日报的 Section E（Interest Evolution）使用 Taxonomy 的 Level-1 类别进行主题统计。Taxonomy 的分类粒度直接影响主题统计的准确性 |

### 核心职责划分

- **Taxonomy（本文件）：** 分类层。回答"项目属于哪个类别？"
- **Scoring Strategy：** 评分层。回答"这个类别值多少分？"
- **Scoring Pipeline：** 执行层。回答"如何执行评分？"
- **Report Pipeline：** 组织层。回答"如何展示评分结果？"

---

## 附录：文档统计

### 文档结构树

```
project_classification_taxonomy_v1.md
├── 1. Purpose                      — 分类先于评分，Taxonomy 是统一分类依据
├── 2. Design Principles            — 3 条原则
│   ├── Principle 1: Single Primary Category
│   ├── Principle 2: Multiple Secondary Categories
│   └── Principle 3: Career Alignment First
├── 3. Level-1 Categories           — 11 个一级分类
│   ├── 3.1  Agent                  — 4 个二级分类
│   ├── 3.2  Agent Memory           — 2 个二级分类
│   ├── 3.3  Multi-Agent            — 3 个二级分类
│   ├── 3.4  MCP                    — 3 个二级分类
│   ├── 3.5  RAG                    — 3 个二级分类
│   ├── 3.6  AI Engineering         — 4 个二级分类
│   ├── 3.7  AI Infrastructure      — 3 个二级分类
│   ├── 3.8  LLMOps                 — 3 个二级分类
│   ├── 3.9  Frontier AI            — 2 个二级分类
│   ├── 3.10 Knowledge Graph        — 3 个二级分类
│   └── 3.11 Distributed Systems    — 2 个二级分类
├── 4. Primary Category Rules       — 选择规则 + 示例 + 禁止规则
├── 5. Secondary Category Rules     — 允许/禁止条件 + 数量限制 + 示例
├── 6. Classification Examples      — 24 个项目（含 4 个附加案例）
├── 7. Mapping to Interest Profile  — S/A/B Tier 映射规则
├── 8. Mapping to Career Goals      — 4 目标映射 + 决策矩阵
├── 9. Future Expansion             — v2 待新增类别 + 扩展原则
└── 10. Relationship with Documents — 6 文档关系 + 职责划分
```

### 一级分类总数

**11 个**：Agent、Agent Memory、Multi-Agent、MCP、RAG、AI Engineering、AI Infrastructure、LLMOps、Frontier AI、Knowledge Graph、Distributed Systems

### 二级分类总数

**32 个**，分布如下：

| 一级分类 | 二级分类数 | 具体二级分类 |
|----------|-----------|-------------|
| Agent | 4 | Framework, Runtime, Platform, Application |
| Agent Memory | 2 | Memory Framework, Memory Infrastructure |
| Multi-Agent | 3 | Coordination, Communication, Planning |
| MCP | 3 | Server, Framework, Ecosystem |
| RAG | 3 | Framework, Retrieval, Knowledge Ingestion |
| AI Engineering | 4 | Workflow, Orchestration, Evaluation, Observability |
| AI Infrastructure | 3 | Serving, Inference, Deployment |
| LLMOps | 3 | Monitoring, Optimization, Production |
| Frontier AI | 2 | Model Release, Research Trend |
| Knowledge Graph | 3 | KG, KGE, Graph ML |
| Distributed Systems | 2 | Distributed Training, Graph Partitioning |

### 20+案例统计表

| 编号 | 项目 | Primary | Secondary | S/A/B Tier |
|------|------|---------|-----------|------------|
| 1 | OpenManus | Agent Framework | Multi-Agent → Coordination, Agent Application | S |
| 2 | LangGraph | Agent Framework | Multi-Agent → Coordination, Agent Memory → Memory Framework | S |
| 3 | CrewAI | Agent Framework | Multi-Agent → Coordination, Multi-Agent → Communication | S |
| 4 | AutoGen | Agent Framework | Multi-Agent → Coordination, Multi-Agent → Planning | S |
| 5 | OpenAI Agents SDK | Agent Framework | — | S |
| 6 | Dify | Agent Platform | AI Engineering → Workflow, RAG → RAG Framework, MCP → MCP Ecosystem | S |
| 7 | Flowise | Agent Platform | RAG → RAG Framework, AI Engineering → Workflow | S |
| 8 | LlamaIndex | RAG Framework | AI Engineering → Evaluation | A |
| 9 | Haystack | RAG Framework | AI Engineering → Orchestration | A |
| 10 | MCP Server | MCP Server | MCP → MCP Framework | A |
| 11 | Mem0 | Memory Framework | AI Engineering → Observability | S |
| 12 | Letta | Memory Infrastructure | Agent Framework | S |
| 13 | OpenMemory | Memory Infrastructure | — | S |
| 14 | LangMem | Memory Framework | Agent Framework | S |
| 15 | vLLM | Serving | AI Infrastructure → Inference | A |
| 16 | SGLang | Serving | AI Infrastructure → Inference, AI Engineering → Orchestration | A |
| 17 | OpenRouter | AI Infrastructure | LLMOps → Monitoring | A |
| 18 | PyTorch Geometric | Graph ML | Knowledge Graph → KGE | B |
| 19 | Spark GraphX | Graph Partitioning | Distributed Systems → Distributed Training | B |
| 20 | Anthropic Claude Release | Model Release | Frontier AI → Research Trend | A |
| 21 | LangSmith | LLMOps → Monitoring | AI Engineering → Evaluation, AI Engineering → Observability | A |
| 22 | Weights & Biases | LLMOps → Monitoring | AI Engineering → Evaluation | A |
| 23 | DeepSpeed | Distributed Training | AI Infrastructure → Inference | B |
| 24 | TensorRT-LLM | Inference | AI Infrastructure → Serving | A |

### Tier 分布统计

| Tier | 案例数 | 占比 |
|------|--------|------|
| S Tier | 10（#1~7, #11~14） | 42% |
| A Tier | 10（#8~10, #15~17, #20~22, #24） | 42% |
| B Tier | 4（#18~19, #23） | 16% |

---

*End of Taxonomy v1. Defines canonical classification for all PKIA scoring and reporting workflows.*