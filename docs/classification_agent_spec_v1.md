# PKIA Classification Agent Specification v1

---

## 1. Purpose

Classification Agent 是 PKIA 的第一层智能模块。

它的职责是回答一个核心问题：

**"这个项目属于什么类别？"**

而不是：

**"这个项目值得关注吗？"**

后者是 Scoring Agent 的工作。分类必须发生在评分之前。

### 核心原则

```
Classification First
Scoring Second
```

违反这条原则的后果：如果分类错误，Scoring Agent 的 Career Alignment 评分和 Interest Match 评分都会建立在错误的基础上。一个实际属于 Agent Framework 的项目如果被错误地分类为 Knowledge Graph，其 Career Alignment 分数会从 40 分降为 10 分，直接导致该项目被错误地置入 Observe 甚至 Ignore 等级。

Classification Agent 的定位是"守门员"——它决定了哪些项目以什么身份进入评分管线。

---

## 2. Position In PKIA

Classification Agent 位于整个 PKIA 数据管线的第二层，紧接在 Project Normalization 之后。

```
Data Collection (GitHub Trending Top 30)
        ↓
Project Normalization (统一数据结构)
        ↓
  ┌─ Classification Agent ──┐
  │  分类层：项目→类别      │
  └─────────┬───────────────┘
            ↓
  ┌─ Scoring Agent ─────────┐
  │  评分层：类别→分数       │
  └─────────┬───────────────┘
            ↓
  ┌─ Report Generation ─────┐
  │  输出层：分数→日报       │
  └─────────────────────────┘
```

### 与上下游模块的关系

**上游：** 接收 Project Normalization 输出的标准化项目数据（Project Name、Description、Topics、Stars、Owner）。Classification Agent 不直接接触原始采集数据，只处理经过 Normalization 的结构化数据。

**下游：** 将分类结果（Primary Category + Secondary Categories）传递给 Scoring Agent。Scoring Agent 依赖 Classification Agent 的输出进行 Career Alignment 评分。

**独立性：** Classification Agent 的运行不依赖 Scoring Agent 的结果。它可以在 Scoring Agent 不可用的情况下独立运行并产生分类结果。

---

## 3. Inputs

Classification Agent 的输入来自 Project Normalization 阶段（基于 project_data_schema_v1.md 定义的数据结构）。

### 必填输入

| 字段 | 类型 | 说明 |
|------|------|------|
| Project Name | 字符串 | GitHub 仓库名称或项目名称 |
| Description | 字符串 | 项目的核心描述，通常来自 GitHub README 或 Topics 描述 |
| Topics | 字符串列表 | 项目的 GitHub Topics 标签 |
| Stars | 整数 | 项目的 GitHub Stars 数量（作为辅助信号） |
| Owner | 字符串 | 项目所属的组织或作者 |

### 可选输入（未来扩展）

| 字段 | 类型 | 预计接入版本 |
|------|------|-------------|
| README Summary | 字符串（摘要） | v0.3 |
| Repository Language | 字符串 | v0.2 |
| Last Updated | 日期 | v0.2 |
| License | 字符串 | v0.2 |

### 关键约束

- Classification Agent **不依赖评分结果**。它不需要知道 Career Alignment 分数或 Total Score 就能完成分类。
- 输入缺失处理：如果 Description 为空，Classification Agent 应仅基于 Topics 和 Project Name 进行分类，并在 Classification Notes 中注明"Description 缺失，分类基于 Topics 推断"。
- 项目名称不能作为唯一的分类依据。例如"OpenManus"这个名称本身不提供分类信息，必须结合 Description 和 Topics。

---

## 4. Outputs

Classification Agent 的输出是 Scoring Agent 的输入。

### 输出结构

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| Primary Category | 字符串 | 是 | 项目的主要类别，必须是 Taxonomy 定义的 Level-2 类别、Emerging Category、Unclassified AI Project 之一 |
| Secondary Categories | 字符串列表 | 否（0~3个） | 项目的次要类别，用于 Interest Match 精细调整 |
| Confidence Level | High/Medium/Low | 是 | Classification Agent 对自己分类结果的信心程度 |
| Classification Notes | 字符串 | 是 | 分类依据的简短说明，必须解释为什么选择该 Primary Category |

### 字段说明

**Primary Category：** 
项目的核心身份标识。它必须来自 project_classification_taxonomy_v1.md 定义的 Level-2 类别（如 Agent Framework、Serving、Memory Framework 等），或者是三个特殊类别之一：Emerging Category、Unclassified AI Project。

**Secondary Categories：**
补充描述项目的其他能力维度。每个 Secondary Category 必须引用 Taxonomy 定义的标准类别名（如"Multi-Agent → Coordination"而非自定义标签）。最多 3 个，0 个也是合法的。

**Confidence Level：**
Classification Agent 对自己判断的信心程度。High 表示分类明确，Medium 表示存在一些模糊性，Low 表示推测性分类。

**Classification Notes：**
分类的理由说明。必须包含：为什么选择这个 Primary Category、是否考虑了多个候选类别、最终决策的依据。格式为自然语言段落，不少于 1 句话。

### 输出示例

```
Project: LangGraph
Primary Category: Agent Framework
Secondary Categories: Multi-Agent → Coordination, Agent Memory → Memory Framework
Confidence Level: High
Classification Notes: LangGraph 是 LangChain 生态中的 Agent 工作流编排框架，
核心能力是图状执行流程。Primary 归为 Agent Framework（S Tier）。
其多 Agent 协作能力和 LangMem 集成使其同时具备 Multi-Agent 和 Agent Memory 属性。
```

---

## 5. Primary Category Rules

### 5.1 硬性规则

1. **每个项目必须且只能有一个 Primary Category。**
   - 不允许出现"无分类"的情况
   - 不允许出现"多个 Primary"的情况
   - 如果不确定，使用 Confidence 为 Low 的 Emerging Category 或 Unclassified AI Project

2. **Primary Category 必须来自 project_classification_taxonomy_v1.md 定义的 Level-2 类别，或三个特殊类别之一。**
   - 有效 Level-2 类别：Agent Framework、Agent Platform、Memory Framework、MCP Server、RAG Framework、Serving、Inference 等 32 个
   - 有效特殊类别：Emerging Category、Unclassified AI Project、Trend Override

3. **Agent 优先原则。**
   - 如果项目同时属于 Agent 相关和非 Agent 相关类别，优先归入 Agent 类别
   - 如果项目同时属于 Agent Framework 和 Multi-Agent，选择 Agent Framework（更具体）

### 5.2 选择优先级

当存在多个候选类别时，按以下顺序决策：

1. **匹配最高 Interest Tier** — S Tier（Agent、Agent Memory、Multi-Agent）> A Tier > B Tier
2. **Agent 优先** — Agent 相关 > 非 Agent 相关
3. **具体优先于通用** — Agent Framework > AI Engineering，Memory Framework > AI Infrastructure
4. **工程优先于研究** — 工程实现 > 理论分析

### 5.3 禁止行为

- 禁止使用"其他"或"通用 AI"作为 Primary Category（应使用 Unclassified AI Project）
- 禁止因为项目热门而将其 Primary Category 提升到不应属的层级（如将 B Tier 项目标记为 Agent）
- 禁止在 Confidence Level 为 Low 时不加 Notes 说明

### 5.4 为什么不能有多个 Primary Category

Scoring Agent 的 Career Alignment 评分机制决定了每个项目只能有一个 Primary Category。Career Alignment 的基准分（40/30/20/10/0）直接映射到 Primary Category 所属的 Interest Tier。如果允许两个 Primary，Scoring Agent 将无法确定使用哪个基准分。

示例：如果一个项目同时被标记为 Agent Framework（S Tier，基准 40 分）和 RAG Framework（A Tier，基准 30 分），Scoring Agent 无法决定使用 40 还是 30。正确的做法是选择一个 Primary（如 Agent Framework），将另一个作为 Secondary（RAG Framework），Scoring Agent 在 Interest Match 维度中使用 Secondary 做精细调整。

---

## 6. Secondary Category Rules

### 6.1 为什么需要 Secondary Categories

Secondary Categories 解决了"项目横跨多个领域"的实际问题。现代 AI 项目很少只属于一个纯粹的分类。例如：

- Dify 既是 Agent Platform（Primary），也具备 Workflow Engine 和 RAG Platform 能力
- LangGraph 既是 Agent Framework（Primary），也支持 Multi-Agent 协作和 Agent Memory

如果没有 Secondary Categories，这些项目的多维能力会在 Interest Match 评分中被忽略，导致推荐不够精准。

### 6.2 允许条件

以下情况允许添加 Secondary Categories：

1. **多领域交叉** — 项目明显覆盖多个分类领域
   - 示例：Dify 覆盖 Agent + Workflow + RAG → Secondary 为 Workflow 和 RAG Framework
2. **上下游关联** — 项目是一个更大生态的组成部分
   - 示例：LangMem 是 LangChain 生态的记忆模块 → Secondary 为 Agent Framework
3. **功能互补** — 项目的主功能和辅助功能分别属于不同类别
   - 示例：vLLM 的核心是 Serving，但其 PagedAttention 技术也是 Inference 优化 → Secondary 为 Inference

### 6.3 数量限制

- **最小：** 0 个（项目只属于一个分类，无需 Secondary）
- **最大：** 3 个（超过 3 个意味着 Taxonomy 的分类粒度需要调整）
- **建议：** 大多数项目 1~2 个 Secondary 足够

### 6.4 禁止条件

1. **类别重复** — Secondary 与 Primary 在同一 Level-2 范围内
   - 错误示例：Primary = Agent Framework, Secondary = Agent Platform（两个不同的 Agent 子类可以，但不能一样）
2. **过度拆分** — 为了增加分类数量而添加无关的 Secondary
3. **推测性标注** — 项目未明确显示某种能力，但"猜测"它可能具备

### 6.5 示例

```
Mem0
  Primary:     Memory Framework
  Secondary:   Agent, AI Engineering → Observability
  说明：Mem0 的核心身份是记忆框架（Memory Framework）。
  它服务于 Agent 生态，并提供了记忆使用的可观测性。
```

---

## 7. Confidence System

### 7.1 等级定义

| 等级 | 含义 | 典型场景 |
|------|------|----------|
| **High** | 分类明确，无歧义 | 项目 Description 和 Topics 清晰指向某个 Level-2 类别；Classification Agent 对判断有 90% 以上把握 |
| **Medium** | 存在一定模糊性，但可以做出合理判断 | 项目横跨多个分类但能选出 Primary；Topics 和 Description 不完全一致但总体可判断 |
| **Low** | 推测性分类，需要下游谨慎处理 | 项目属于新兴方向尚无 Taxonomy 覆盖；Description 过少或不清晰；Confidence 不足 50% |

### 7.2 High 条件

满足以下 **所有** 条件时，Confidence 为 High：

1. Primary Category 在 Taxonomy 中有明确的 Level-2 对应
2. Project Description 和 Topics 至少有两个来源指向该类别
3. 没有交叉类别的严重冲突（候选类别之间的差距在一个 Tier 以内）
4. Secondary Categories 不超过 2 个

### 7.3 Medium 条件

满足以下 **任一** 条件时，Confidence 为 Medium：

1. Primary Category 明确，但存在一个以上的强候选类别（候选类别属于不同 Tier）
2. Description 和 Topics 指向不一致（如 Description 暗示 Agent Framework，Topics 全是 RAG）
3. 项目横跨 3 个以上分类领域
4. 需要 3 个 Secondary Categories 才能完整描述

### 7.4 Low 条件

满足以下 **任一** 条件时，Confidence 为 Low：

1. 项目属于 Emerging Category（尚未被 Taxonomy 覆盖的新方向）
2. Description 过短（少于 50 字符）或信息量不足
3. Topics 为空且 Description 模糊
4. 无法在现有 Taxonomy 中找到直接对应的 Level-2 类别

### 7.5 下游处理

- **High Confidence** → Scoring Agent 直接使用分类结果，无需额外校验
- **Medium Confidence** → Scoring Agent 在 Reasoning 中注明"分类置信度为 Medium"
- **Low Confidence** → 报告生成管线在 Daily Report 中该条目的 Reasoning 部分注明"分类基于推测，建议人工复核"

---

## 8. Emerging Category Mechanism

### 8.1 为什么需要这个机制

Taxonomy 不是封闭系统。PKIA v0.1 的 Taxonomy 覆盖了当前已知的 AI 项目类别，但 Agent 生态正在快速演进。未来可能出现：

- Agent Browser（浏览器 Agent 框架）
- Agent Computer Use（计算机使用 Agent）
- Agent OS（Agent 操作系统）
- Agent Runtime（Agent 运行时）
- AI Coding Agent（AI 编程 Agent）

这些新方向可能没有任何 Level-2 类别可以容纳。Emerging Category 机制就是为了处理这种情况而设计的。

### 8.2 触发条件

当 Classification Agent 遇到一个项目，满足以下 **所有** 条件时，应使用 Emerging Category：

1. 无法匹配现有 Taxonomy 的任何 Level-2 类别
2. 项目明显属于 AI/Agent 领域（不是前端、移动端、区块链等 Ignore 类别）
3. 项目的技术方向和能力有明确的定义和边界

### 8.3 输出格式

```
Primary Category: Emerging Category
Secondary Categories: [建议的分类标签]
Confidence Level: Low
Classification Notes: [解释为什么现有 Taxonomy 无法覆盖]
Candidate Category: [建议在下一版 Taxonomy 中新增的类别名称]
```

### 8.4 示例

**场景：** 一个名为 "AgentBrowser" 的项目在 GitHub Trending 上出现，提供 Agent 端的浏览器自动化能力。它不完全属于 Agent Framework（不提供 Agent 构建基座），也不属于 Agent Application（不是面向终端用户的产品）。Taxonomy 中没有"Browser Agent"这个类别。

```
Project: AgentBrowser
Primary Category: Emerging Category
Secondary Categories: Agent → Agent Application
Confidence Level: Low
Classification Notes: AgentBrowser 提供 Agent 端的浏览器自动化能力，
不属于现有 Taxonomy 的任何 Level-2 类别。它介于 Agent Framework
和 Agent Application 之间，建议在下一版 Taxonomy 中新增
"Agent Browser" 类别。
Candidate Category: Agent Browser
```

### 8.5 生命周期

Emerging Category 不是一个永久分类。当同一方向的第 3 个项目出现时，应该触发 Taxonomy 更新流程——将 Candidate Category 正式纳入下一版 Taxonomy。Classification Agent 的设计者应定期审查所有标记为 Emerging Category 的项目，决定是否需要更新 Taxonomy。

---

## 9. Trend Override Rule

### 9.1 为什么需要这个规则

在极少数情况下，一个项目可能无法被清晰分类，甚至不属于明确的 AI 领域，但因为其极高的社区关注度，完全忽略它会造成信息盲区。

Trend Override 是为这种情况设计的"安全阀"。

### 9.2 触发条件

当项目满足以下 **任一** 指标时，Classification Agent 应启动 Trend Override：

1. **Stars 阈值** — 项目在 24 小时内 Stars 增长超过 1000（基于 GitHub Trending 数据）
2. **Trending Rank 阈值** — 项目进入 GitHub Trending 前 3 名
3. **社区信号** — 在多个独立渠道（Hacker News、Twitter、Reddit）同时出现

### 9.3 行为

当 Trend Override 触发时：

1. 项目仍然进入评分管线，不会被丢弃
2. 如果项目可以被分类，使用正常分类；如果无法分类，使用 Emerging Category
3. 在 Classification Notes 中注明"Trend Override 触发"及触发原因

### 9.4 示例

**场景：** 一个名为 "Cursor" 的 AI 编程工具突然在 GitHub Trending 上排名第 1。它不属于 PKIA 关注的 Agent Framework、MCP、RAG 等核心方向，属于 AI Coding Agent（Taxonomy v1 未覆盖）。

```
Project: Cursor
Primary Category: Emerging Category
Secondary Categories: Agent → Agent Application
Confidence Level: Medium
Classification Notes: Trend Override triggered — ranked #1 on GitHub Trending.
Cursor 属于 AI 编程 Agent 方向，Taxonomy v1 尚未覆盖此类别。
建议关注并评估是否在下一版中新增 "AI Coding Agent" 类别。
Candidate Category: AI Coding Agent
```

### 9.5 限制

- Trend Override 只决定项目"是否进入管线"，不改变评分结果。进入管线后，Scoring Agent 仍然按正常规则评分。一个热门但 Career Alignment 低下的项目（如一个爆火的前端工具），即使在 Trend Override 下进入系统，最终仍然会落入 Ignore 或 Observe 等级。
- Trend Override 每天的触发次数限制为 3 次，防止 Trending Top 3 全部被自动纳入。

---

## 10. Unclassified AI Project

### 10.1 为什么需要这个机制

Emerging Category 适用于"有明确方向但 Taxonomy 尚未覆盖"的情况。但有些项目确实属于 AI 领域，却难以归入任何明确的类别——它们可能太新、太模糊、或者跨界太多。

Unclassified AI Project 是为这类项目设计的兜底分类。

### 10.2 触发条件

当项目满足以下 **所有** 条件时，使用 Unclassified AI Project：

1. 无法匹配现有 Taxonomy 的任何 Level-2 类别
2. 也不适合使用 Emerging Category（没有明确的 Candidate Category）
3. 但项目明显属于 AI 领域（涉及 LLM、Agent、ML、Deep Learning 等技术关键词）
4. 不属于 Ignore 列表中的类别（Frontend、Mobile、Blockchain、Crypto、NFT、Web3）

### 10.3 与 Emerging Category 的区别

| 维度 | Emerging Category | Unclassified AI Project |
|------|-------------------|------------------------|
| 方向明确性 | 有明确的 Candidate Category | 无法确定候选类别 |
| Taxonomy 更新预期 | 下一个版本可能新增类别 | 需要更多观察才能判断 |
| Confidence Level | Low | Low |
| 使用频率 | 每月 1~3 次（新版 Tax 更新前） | 极少使用（每月 < 1 次） |

### 10.4 输出格式

```
Primary Category: Unclassified AI Project
Secondary Categories: [最接近的现有类别标签，可以为空]
Confidence Level: Low
Classification Notes: [解释为什么无法分类]
```

### 10.5 示例

**场景：** 一个名为 "AI Deconstructor" 的工具出现在 GitHub Trending 上。它能分析任何 AI 项目的架构并生成可视化架构图。它不属于 Agent Framework（不构建 Agent），不属于 AI Engineering（不是工程化工具），也不属于 MCP 或 RAG。它是一个全新的工具类型。

```
Project: AI Deconstructor
Primary Category: Unclassified AI Project
Secondary Categories: AI Engineering → Observability
Confidence Level: Low
Classification Notes: AI Deconstructor 提供 AI 项目架构分析能力，
不属于现有 Taxonomy 的任何 Level-2 类别，也没有明确的
Candidate Category。暂归入 Unclassified AI Project，Secondary
指向 AI Engineering 的 Observability 作为最接近的现有类别。
```

### 10.6 生命周期

Unclassified AI Project 的项目应每月回顾一次。如果同一方向出现 2 个以上项目，应启动 Taxonomy 更新讨论。

---

## 11. Classification Examples

以下 10 个案例展示 Classification Agent 在不同场景下的分类决策。

### 11.1 OpenManus

```
Primary Category: Agent Framework
Secondary Categories: Multi-Agent → Coordination, Agent Application
Confidence Level: High
Classification Notes: OpenManus 的核心是 Agent 构建框架，
提供 Tool Use 和 Planning 能力。Description 和 Topics 均指向
Agent Framework。支持多 Agent 协作和直接构建 Agent 应用，
作为 Secondary Categories。
```

### 11.2 LangGraph

```
Primary Category: Agent Framework
Secondary Categories: Multi-Agent → Coordination, Agent Memory → Memory Framework
Confidence Level: High
Classification Notes: LangGraph 是 LangChain 生态的 Agent 工作流
编排框架。其图执行模型天然支持多 Agent 协作。与 LangMem 深度集成
提供 Agent Memory 能力。核心身份是 Agent Framework。
```

### 11.3 Dify

```
Primary Category: Agent Platform
Secondary Categories: AI Engineering → Workflow, RAG → RAG Framework, MCP → MCP Ecosystem
Confidence Level: High
Classification Notes: Dify 是集成化 AI 应用开发平台。
Agent Platform 是 Primary（Agent 类 + S Tier）。同时具备
Workflow 编排、RAG Pipeline 和 MCP 集成能力。3 个 Secondary
Categories 完整覆盖其多面性，已达 Secondary 数量上限。
```

### 11.4 Mem0

```
Primary Category: Memory Framework
Secondary Categories: Agent, AI Engineering → Observability
Confidence Level: High
Classification Notes: Mem0 的核心身份是 Agent 记忆管理框架
（Memory Framework）。它服务于 Agent 生态（Secondary: Agent），
提供了记忆使用的可观测性（Secondary: AI Engineering → Observability）。
分类明确，无歧义。
```

### 11.5 Letta

```
Primary Category: Memory Infrastructure
Secondary Categories: Agent Framework
Confidence Level: High
Classification Notes: Letta（原 MemGPT）提供 Agent 记忆系统的
底层基础设施，包括虚拟上下文管理和记忆分层。Primary 为
Memory Infrastructure。其与 Agent 的深度集成使 Agent Framework
成为合理的 Secondary。注意与 Mem0 的区别：Mem0 是 Framework，
Letta 是 Infrastructure。
```

### 11.6 OpenMemory

```
Primary Category: Memory Infrastructure
Secondary Categories: 无
Confidence Level: High
Classification Notes: OpenMemory 专注于为 Agent 提供持久化记忆存储。
作为一个专注的 Infrastructure 项目，不涉足 Agent 框架层面。
无需 Secondary Categories。分类明确。
```

### 11.7 LlamaIndex

```
Primary Category: RAG Framework
Secondary Categories: AI Engineering → Evaluation
Confidence Level: High
Classification Notes: LlamaIndex 的核心是 RAG 数据框架，
提供索引、检索和查询能力。不归入 Agent 类（LlamaIndex 本身
不是 Agent 框架）。Secondary 指向其 Evaluation 功能。
```

### 11.8 MCP Server (MCP Python SDK)

```
Primary Category: MCP Server
Secondary Categories: MCP → MCP Framework
Confidence Level: High
Classification Notes: MCP Python SDK 提供了实现 MCP Server 的
核心工具。Primary 为 MCP Server。该 SDK 同时也提供了开发框架
的能力，因此 MCP Framework 作为 Secondary。
```

### 11.9 PyTorch Geometric

```
Primary Category: Graph ML
Secondary Categories: Knowledge Graph → KGE
Confidence Level: High
Classification Notes: PyTorch Geometric 是图神经网络框架。
Primary 为 Graph ML（Knowledge Graph 类）。其图嵌入能力
（KGE）作为 Secondary。虽然学术上 GNN 和 KGE 有区别，
但在 PKIA Taxonomy 中统一归入 Knowledge Graph 一级分类。
```

### 11.10 MarkItDown

```
Primary Category: Unclassified AI Project
Secondary Categories: RAG → Knowledge Ingestion
Confidence Level: Low
Classification Notes: MarkItDown 是一个将各种格式文件转换为
Markdown 的工具。它不属于 Taxonomy 的现有 Level-2 类别。
其功能与 RAG 的 Knowledge Ingestion（文档预处理）较为接近，
但严格来说不属于 RAG 生态。作为 Unclassified AI Project 处理，
Secondary 指向最接近的现有类别。建议观察是否有更多类似的
文档预处理工具出现，考虑在下一版 Taxonomy 中新增
"Document Processing" 类别。
```

---

## 12. Relationship With Existing Documents

### 12.1 职责边界

```
┌──────────────────────────────────────────────────────────┐
│  project_classification_taxonomy_v1.md                   │
│  职责：定义"有哪些类别"                                   │
│  输出：11 个一级分类，32 个二级分类                        │
│  回答："分类体系是什么"                                   │
└──────────────────────┬───────────────────────────────────┘
                       │ 提供分类标准
                       ▼
┌──────────────────────────────────────────────────────────┐
│  classification_agent_spec_v1.md (本文件)                │
│  职责：定义"如何执行分类"                                 │
│  输出：Primary + Secondary + Confidence + Notes          │
│  回答："这个项目属于哪个类别"                              │
└──────────────────────┬───────────────────────────────────┘
                       │ 提供分类结果
                       ▼
┌──────────────────────────────────────────────────────────┐
│  scoring_agent (prompt_scoring_agent_v1.md 执行)         │
│  职责：定义"每个类别值多少分"                              │
│  输出：Career Alignment + Interest Match + ...           │
│  回答："这个项目值多少分"                                  │
└──────────────────────┬───────────────────────────────────┘
                       │ 提供评分结果
                       ▼
┌──────────────────────────────────────────────────────────┐
│  scoring_pipeline_schema_v1.md                          │
│  职责：定义"如何执行评分"                                 │
│  回答："评分流程是什么"                                    │
└──────────────────────────────────────────────────────────┘
```

### 12.2 各文档关系

| 文档 | 关系 |
|------|------|
| **interest_profile_v1.md** | Classification Agent 的分类逻辑间接服务于 Interest Profile。Primary Category 的 Tier 映射决定了该分类最终在 Interest Match 评分中的分数范围 |
| **scoring_strategy_v1.md** | Classification Agent 的输出（Primary Category）是 Scoring Strategy 的输入。两者的边界清晰：Taxonomy 负责分类，Scoring Strategy 负责评分。Classification Agent 的分类错误会直接导致 Scoring Strategy 的错误应用 |
| **project_classification_taxonomy_v1.md** | 这是 Classification Agent 的分类参考手册。Taxonomy 决定"有哪些类别"，Classification Agent 决定"这个项目属于哪个类别"。Taxonomy 是静态的（版本化更新），Classification Agent 是动态的（每次项目都执行分类）。当 Taxonomy 更新时，Classification Agent 的分类规则相应更新 |
| **prompt_scoring_agent_v1.md** | Classification Agent 的输出作为 Scoring Agent 的输入字段（Primary Category、Secondary Categories）出现在 Scoring Agent 的 System Prompt 上下文中。Classification Agent 的 Confidence Level 也传递给 Scoring Agent，影响 Scoring Agent 对分类结果的信任程度 |
| **scoring_pipeline_schema_v1.md** | Pipeline 的 Stage 3（Category Classification）对应 Classification Agent 的执行。Pipeline 定义"如何编排"，Classification Agent 定义"如何分类"。Classification Agent 的三个特殊机制（Emerging Category、Trend Override、Unclassified AI Project）在 Pipeline 的 Stage 3 中作为分类结果的分支处理 |
| **project_data_schema_v1.md（规划中）** | 提供 Classification Agent 的输入数据结构定义。Project Data Schema 定义"项目长什么样"（数据字段），Classification Agent 基于这些字段进行分类判断 |

### 12.3 核心职责划分总结

| 模块 | 职责 | 回答的问题 |
|------|------|-----------|
| Taxonomy | 分类体系 | "分类体系是什么？有哪些类别？" |
| **Classification Agent（本文件）** | **执行分类** | **"这个项目属于哪个类别？"** |
| Scoring Agent | 执行评分 | "这个项目值多少分？" |
| Scoring Pipeline | 编排流程 | "如何将分类和评分组织成流程？" |

---

## 13. Future Evolution

### v2: 自动学习新分类

基于 Emerging Category 的历史数据，自动检测同一 Candidate Category 的重复出现。当同一 Candidate Category 出现 3 次以上时，自动生成 Taxonomy 更新建议。

**新增能力：**
- Emerging Category 项目的自动聚类
- Candidate Category 的频次统计和趋势分析
- 自动生成 Taxonomy 更新建议报告

### v3: 分类权重统计

记录每个分类的使用频次和 Confidence 分布，评估 Taxonomy 的覆盖质量。

**新增能力：**
- 按 Level-1 类别统计分类项目数量
- Confidence Level 的分布监控（如果某个类别的 Low Confidence 比例过高，说明该类别的定义需要优化）
- 分类-评分偏差分析（如果某个类别的项目评分普遍低于预期，检查分类是否准确）

### v4: 动态更新 Taxonomy

在 v2 和 v3 的基础上，实现 Taxonomy 的半自动更新。当新方向确认成型后，自动建议新增 Level-2 类别，经人工确认后生效。

**新增能力：**
- 基于 Emerging Category 的新增类别建议
- 基于使用率的类别合并/拆分建议
- 基于 Career Goal 变化的类别优先级调整建议

### 演进原则

1. **人工审批始终保留** — 任何 Taxonomy 的变更都需要人工确认，Classification Agent 不自动修改分类体系
2. **向后兼容** — 新版本不应破坏已分类项目的历史数据
3. **渐进式更新** — 每次更新只增加少数类别，不做大规模重构

---

*End of Classification Agent Spec v1. Compliant with PKIA v0.1 architecture.*