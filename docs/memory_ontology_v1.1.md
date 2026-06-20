# PKIA L2 Memory Ontology — 正式规范 v1.1

> **文档状态**: Architecture Freeze Document  
> **所属系统**: Personal Knowledge Intelligence Agent (PKIA)  
> **层级**: L2 — Long-Term Memory Layer  
> **底层存储**: MCP Memory Server · Knowledge Graph · Append-only Architecture  
> **版本**: 1.1  
> **更新日期**: 2026-06-20  
> **规范约束**: 后续所有实现必须遵循本规范，未经架构评审不得偏离。

---

## 1. Purpose

### 1.1 为什么需要 L2

LLM 原生无状态。每次对话都是独立的推理过程，无法跨 session 保持对用户身份、偏好、项目上下文和历史决策的认知。L2 层作为 PKIA 的长期语义记忆，解决了以下根本问题：

- **身份遗忘**: Agent 每次重启后不记得用户是谁、研究领域是什么、长期目标是什么。
- **上下文碎片化**: 多轮对话中，关键事实散落在历史窗口之外，无法被检索和引用。
- **决策不连贯**: 两次独立推理可能做出矛盾的选择（如第一次选择 A 方案，第二次选择与 A 冲突的 B 方案）。
- **注意力漂移**: Agent 容易被当前 prompt 中的最新信息牵引，忽略之前沉淀的确定性事实。

L2 层的核心价值在于：**让 Agent 拥有「不忘记」的能力**，在任何 session 中都能基于累积的确定性知识做出一致决策。

### 1.2 为什么采用 Knowledge Graph

向量 RAG 擅长语义相似度检索，但在以下场景存在根本局限：

- **精确事实检索**: "用户的 research_field 是什么？"——向量检索返回的是相似文本片段，而非确定的键值对。
- **多跳推理**: "找出与当前项目相关的所有历史决策"——需要在实体间沿关系链遍历，向量检索无法直接完成。
- **版本追溯**: "这个配置项在变更前是什么值？"——向量存储没有版本或替换语义。
- **约束验证**: "同一个 slot 是否已有 ACTIVE 记录？"——图结构支持精确的 slot 查询，向量只能近似匹配。

Knowledge Graph 提供的是**确定性拓扑**，实体 + 关系 + 状态构成可验证的事实网络，解决了向量 RAG 的模糊性和不可追溯性。

### 1.3 为什么采用 Append-only

Append-only 架构的核心原则是：**不删除，只追加**。理由如下：

- **可审计性**: 每一次记忆变更都有记录，可以追溯到任何时间点的记忆状态。
- **错误恢复**: 如果 Agent 写入了错误记忆，不会覆盖正确数据，而是追加一条修正记录，历史可查。
- **状态机合法性**: 记忆节点带有生命周期状态（ACTIVE / DEPRECATED 等），旧节点通过状态迁移而非物理删除来退出活跃集合。
- **并发安全**: 不存在「读-改-写」的竞争条件，新节点只是追加写入，不会破坏已有节点。

### 1.4 为什么保留历史记忆

- **溯源需求**: 当需要理解「为什么某个配置被弃用」时，DEPRECATED 节点记录了原始值和弃用原因。
- **冲突仲裁**: 当两个 Agent 决策产生矛盾时，历史记忆链提供仲裁依据（哪个在先？哪个已被显式替换？）。
- **学习信号**: Agent 的行为模式可以从历史记忆的变更序列中分析得出（例如：用户频繁修改某一偏好，说明该偏好定义可能不合理）。
- **回滚能力**: 如果需要回退到之前的记忆状态，历史记录提供了完整的快照链。

---

## 2. Design Goals

### 2.1 Append-only Memory

所有记忆操作仅为**追加新节点**，禁止物理删除或原地修改已有节点。状态的变更通过新节点的生命周期状态表达，而非覆盖旧数据。

**设计含义**:
- 每个 `Memory_Node` 一旦创建即为不可变记录。
- 对同一事实的新认知通过创建新的 `Memory_Node` 并调整旧节点状态来实现。
- 存储空间是单调增长的，需要引入归档机制（见第 12 章）。

### 2.2 Event Sourcing

记忆变更本身就是事件流。每个 `Memory_Node` 的创建都对应一次状态变更事件。重放事件流可以还原任意时间点的记忆快照。

**设计含义**:
- `created_at` 是事件的时间戳。
- `SUPERSEDED_BY` 关系构成事件之间的因果关系链。
- Agent 可以通过重放事件流来「回忆」记忆的演化过程。

### 2.3 Traceability

每一条记忆都必须可追溯其来源和演化历史。不允许存在「孤儿记忆」。

**设计含义**:
- 每个节点必须有 `source_type` 字段（用户显式 / Agent 推断 / 系统生成）。
- 状态变更必须通过关系链连接（新节点通过 `SUPERSEDED_BY` 指向旧节点）。
- 任何 ACTIVE 节点都必须能够沿 `SUPERSEDED_BY` 链追溯到最初的版本。

### 2.4 Conflict Resolution

当同一 slot 存在多个候选记忆时，系统必须能够自动或半自动地解决冲突，保证每个 slot 有且仅有一个 ACTIVE 节点。

**设计含义**:
- Slot 是冲突检测的基本单元（category + key + context）。
- 写入新节点时自动检测目标 slot 是否已有 ACTIVE 节点。
- 冲突时：旧节点标记为 DEPRECATED，新节点标记为 ACTIVE，两者之间建立 `SUPERSEDED_BY` 关系。

### 2.5 Context-Aware Retrieval

记忆检索必须支持上下文限定。同一 key 在不同 context 下应当有不同的 ACTIVE 值。

**设计含义**:
- `context` 字段是检索的限定维度。
- 全局偏好的 context 为空或 "global"。
- 项目特定配置的 context 为项目 ID。
- 检索接口必须优先匹配精确 context，回退到通用 context。

### 2.6 Long-Term Agent Support

L2 层必须支持 Agent 在长时间尺度（数周、数月、数年）上的稳定运行。

**设计含义**:
- `expires_at` 字段支持记忆的自动过期。
- `reinforcement_count` 字段支持记忆的强化学习。
- Tier 系统定义了不同层级记忆的生命周期策略。
- 归档机制防止存储无限增长。

---

## 3. Core Entity Model

### 3.1 Memory_Node

`Memory_Node` 是 L2 层的基本信息单元。每一条确定性的知识、偏好、项目上下文或工作记录都以一个 `Memory_Node` 实例存在。

#### 字段定义

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `node_id` | string | 是 | 全局唯一标识符。格式: `mem_<uuid>`。在 MCP 图中对应 entity name。 |
| `category` | string | 是 | 记忆分类。取值为 Tier 系统中的层级标识: `identity` / `preference` / `project` / `working`。 |
| `key` | string | 是 | 记忆键名。在同一 category 内唯一标识一个记忆维度。使用 snake_case。 |
| `value` | string | 是 | 记忆值。可以是任意字符串，但建议保持结构化的 JSON 字符串以便解析。 |
| `context` | string | 否 | 上下文限定符。用于区分同一 key 在不同场景下的不同值。空字符串表示全局。 |
| `status` | string | 是 | 生命周期状态。取值为: `ACTIVE` / `DRAFT` / `DEPRECATED` / `ARCHIVED`。 |
| `confidence` | float | 否 | 置信度。取值范围 [0.0, 1.0]。默认 1.0。DRAFT 节点通常低于 0.8。 |
| `source_type` | string | 是 | 记忆来源。取值为: `USER_EXPLICIT` / `AGENT_INFERRED` / `SYSTEM_GENERATED`。 |
| `created_at` | string | 是 | 创建时间。ISO 8601 格式，UTC。 |
| `updated_at` | string | 否 | 最后更新时间。ISO 8601 格式，UTC。仅 reinforcement 操作更新此字段。 |
| `expires_at` | string | 否 | 过期时间。ISO 8601 格式，UTC。过期后自动转为 ARCHIVED。 |
| `version` | int | 是 | 版本号。从 1 开始递增。同一 slot 的后续节点版本号 +1。 |
| `reinforcement_count` | int | 是 | 强化计数。重复观察时递增，不创建新节点。初始值为 1。 |

#### 字段解释

- **node_id**: 每个 Memory_Node 的唯一标识。在 MCP Knowledge Graph 中直接映射为 entity name。生成策略为 UUID v4，确保分布式环境下的无冲突创建。
- **category**: 记忆所属层级，直接对应第 4 章的 Memory Tier System。决定了记忆的生命周期策略、检索优先级和归档策略。
- **key**: 记忆的逻辑键名。设计原则是自解释且可组合。例如 `response_language`、`research_field`、`current_active_project`。
- **value**: 记忆的实际内容。对于简单类型直接存储标量值；对于结构化数据推荐存储为 JSON 字符串（如 `{"model": "gpt-4", "temperature": 0.7}`）。
- **context**: 上下文限定符，是实现 Context-Aware Retrieval 的核心机制。同一 key 在不同 context 下可以有不同 ACTIVE 值。空字符串表示该记忆不限定上下文（全局适用）。
- **status**: 记忆的当前生命周期状态。只有 ACTIVE 状态的节点参与正常的检索流程。DRAFT 状态需要用户确认才能转为 ACTIVE。
- **confidence**: 表示 Agent 对该记忆的确定程度。AGENT_INFERRED 的记忆通常初始置信度较低（0.5-0.8），需要后续交互验证。USER_EXPLICIT 的记忆置信度为 1.0。
- **source_type**: 记录记忆的创建者。USER_EXPLICIT 具有最高优先级，AGENT_INFERRED 需要升级确认，SYSTEM_GENERATED 来自系统内部运作。
- **created_at**: 记忆的出生时间戳。用于事件溯源、时间线排序和生命周期管理。
- **updated_at**: 仅当 `reinforcement_count` 变更时更新。纯时间戳记录，表示最后一次被「强化」的时间。
- **expires_at**: 记忆的死亡时间戳。用于 Tier4 Working 等临时记忆的自动清理。超过此时间后，记忆自动转为 ARCHIVED。
- **version**: 同一 slot 的版本计数器。用于追踪记忆的迭代历史。初始版本为 1，每次被 SUPERSEDED 时新节点版本 +1。
- **reinforcement_count**: 记忆的强化学习计数器。当 Agent 接收到与现有 ACTIVE 记忆一致的新信息时，不创建新节点，仅增加此计数。这是 Append-only 架构中唯一允许的「修改」操作。

---

## 4. Memory Tier System

记忆按语义层级划分为四个 Tier，每个 Tier 有不同的生命周期、优先级和访问模式。

### 4.1 Tier1 Identity — 身份层

**定义**: 用户的固定身份属性。变化频率极低（月/年级别）。

**示例**:
| key | value | 说明 |
|-----|-------|------|
| `education` | `"计算机科学与技术 硕士"` | 教育背景 |
| `research_field` | `"知识图谱 · 自然语言处理"` | 研究领域 |
| `career_goal` | `"构建个人知识智能体系统"` | 职业目标 |
| `location` | `"Asia/Tokyo"` | 时区/地理位置 |

**生命周期**: 永久保留。不自动过期，不归档。即使被 DEPRECATED，也保留为历史记录。

**优先级**: 最高。在所有检索中排在首位。

**变更频率**: 原则上仅由用户显式修改。Agent 推断的身份信息必须以 `confidence < 0.8` 的 DRAFT 状态写入，等待用户确认。

### 4.2 Tier2 Preference — 偏好层

**定义**: 用户的交互偏好和行为习惯。变化频率低（周/月级别）。

**示例**:
| key | value | 说明 |
|-----|-------|------|
| `response_language` | `"zh-CN"` | 回复语言偏好 |
| `explanation_style` | `"detail_first"` | 解释风格: detail_first / summary_first / example_driven |
| `verbosity` | `"concise"` | 详细程度: concise / balanced / detailed |
| `code_style` | `"pythonic"` | 代码风格偏好 |

**生命周期**: 长期保留。允许用户显式修改。Agent 可以根据交互模式推断偏好并以 DRAFT 状态提交建议。

**优先级**: 高。在身份层之后，项目层之前。

**变更频率**: 可随用户习惯变化，但建议 Agent 推断的偏好变更需要用户确认才能从 DRAFT 转为 ACTIVE。

### 4.3 Tier3 Project — 项目层

**定义**: 当前活跃项目的上下文信息。变化频率中（天/周级别）。

**示例**:
| key | value | 说明 |
|-----|-------|------|
| `current_active_project` | `"PKIA_Project"` | 当前活跃项目 |
| `project_phase` | `"architecture_design"` | 项目阶段 |
| `project_constraint` | `"8GB VRAM limit"` | 项目约束 |
| `tech_stack` | `"Dify · Python · Next.js"` | 技术栈信息 |

**生命周期**: 与项目生命周期绑定。项目结束后可转为 ARCHIVED。

**优先级**: 中。在偏好层之后，工作层之前。

**变更频率**: 随项目进展更新。Agent 可以主动记录项目状态变更。

### 4.4 Tier4 Working — 工作层

**定义**: 临时工作记忆。变化频率高（分钟/小时级别）。

**示例**:
| key | value | 说明 |
|-----|-------|------|
| `ongoing_task` | `"生成 L2 Memory Ontology 文档"` | 当前任务描述 |
| `temporary_note` | `"需要注意 Append-only 的归档策略"` | 临时笔记 |
| `investigation_topic` | `"MCP Memory Server 的写入性能"` | 调研主题 |
| `session_context` | `"上一轮讨论到 Conflict Resolution"` | Session 上下文 |

**生命周期**: 短期。自动过期（通常 24-72 小时）。不主动归档，过期后自动清理。

**优先级**: 低。仅在活跃 session 中参与检索，跨 session 不保留。

**变更频率**: 频繁变更。Agent 可以自由读写，无需用户确认。

### 4.5 Tier 生命周期总结

| Tier | 保留策略 | 过期时间 | 归档策略 | 用户确认要求 |
|------|----------|---------|---------|-------------|
| Tier1 Identity | 永久 | 无 | 不归档 | 严格 |
| Tier2 Preference | 长期 | 可配置（默认无） | 不归档 | 建议 |
| Tier3 Project | 项目周期 | 项目结束 | 项目结束后归档 | 可选 |
| Tier4 Working | 短期 | 24-72 小时 | 过期即清理 | 不需要 |

---

## 5. Memory Lifecycle

### 5.1 状态定义

| 状态 | 说明 | 是否参与检索 | 是否可被 SUPERSEDED |
|------|------|------------|-------------------|
| `ACTIVE` | 当前生效的记忆，参与正常检索 | 是 | 是 |
| `DRAFT` | 待确认的记忆，Agent 推断但未获用户确认 | 仅显式查询 | 是（但应优先确认） |
| `DEPRECATED` | 已被新版本替换的旧记忆 | 否 | 否（已是最旧版本链尾） |
| `ARCHIVED` | 过期或被归档的记忆，仅用于历史追溯 | 否 | 否 |

### 5.2 状态转换图

```
                          ┌─────────────────┐
                          │                 │
                          │     DRAFT       │ ◄──── AGENT_INFERRED 写入
                          │                 │
                          └────────┬────────┘
                                   │
                                   │ 用户确认 / confidence ≥ 阈值
                                   ▼
              ┌───────────────────────────────────────┐
              │                                       │
   USER_EXPLICIT 写入 ──► │       ACTIVE                │ ◄──── 新节点写入（已有 ACTIVE）
              │                                       │
              └────────┬──────────────────┬───────────┘
                       │                  │
                       │ 被新版本替换      │ 过期 / 项目结束
                       ▼                  ▼
              ┌─────────────────┐  ┌─────────────────┐
              │                 │  │                 │
              │   DEPRECATED    │  │    ARCHIVED     │
              │                 │  │                 │
              └─────────────────┘  └─────────────────┘
```

**转换路径**:

1. `USER_EXPLICIT` → 直接写入 **ACTIVE**
2. `AGENT_INFERRED` → 写入 **DRAFT**
3. **DRAFT** → **ACTIVE**: 用户显式确认，或 Agent 后续观测到足够证据使 confidence ≥ 0.9
4. **ACTIVE** → **DEPRECATED**: 同一 slot 有新 ACTIVE 节点写入（Slot-Based Conflict Resolution）
5. **ACTIVE** → **ARCHIVED**: 节点过期（expires_at 到达）或所属项目结束
6. **DRAFT** → **DEPRECATED**: 长时间未确认（默认 7 天）且被新 DRAFT 替换
7. **DEPRECATED** / **ARCHIVED**: 最终状态，不可再转换

### 5.3 转换触发条件

| 转换 | 触发条件 | 执行者 |
|------|---------|--------|
| → DRAFT | Agent 从对话或行为中推断出一条记忆 | Agent |
| → ACTIVE (from USER_EXPLICIT) | 用户显式提供信息 | Agent |
| → ACTIVE (from DRAFT) | 用户确认 / 独立证据源验证 / confidence ≥ 0.9 | Memory Governor |
| → DEPRECATED | 同一 slot 有新 ACTIVE 节点写入 | Memory Governor |
| → ARCHIVED | expires_at 到达 / 项目归档信号 | Memory Governor（定时任务） |

---

## 6. Slot-Based Conflict Resolution

### 6.1 Slot 定义

Slot 是冲突检测和版本管理的基本单位，由三个维度组成：

```
slot = category + ":" + key + "@" + context
```

**示例**:
| Slot 表达式 | 含义 |
|-------------|------|
| `preference:response_language@global` | 全局回复语言偏好 |
| `identity:research_field@global` | 全局研究领域 |
| `project:project_phase@PKIA_Project` | PKIA 项目的当前阶段 |
| `working:ongoing_task@session_20260620` | 20260620 session 的当前任务 |

### 6.2 冲突约束

**核心规则**: 同一个 slot 在任何时间点只能有一个 `ACTIVE` 节点。

这意味着：
- 当新的记忆写入目标 slot 时，如果该 slot 已存在 ACTIVE 节点，则新节点替换旧节点。
- 替换操作通过状态迁移完成：旧节点 → DEPRECATED，新节点 → ACTIVE。
- 新旧节点之间建立 `SUPERSEDED_BY` 关系（从新节点指向旧节点）。

### 6.3 SUPERSEDED_BY 机制

当冲突发生时，Memory Governor 执行以下操作：

1. 查询 slot `preference:response_language@global` 的当前 ACTIVE 节点（node_id: `mem_001`）
2. 创建新节点 `mem_002`，status = ACTIVE，version = 2
3. 将 `mem_001` 的 status 改为 DEPRECATED
4. 建立关系: `mem_002` — SUPERSEDED_BY → `mem_001`

**最终状态**:
```
mem_002 (ACTIVE, v2) ── SUPERSEDED_BY ──► mem_001 (DEPRECATED, v1)
```

### 6.4 冲突检测流程

```
请求写入: category=preference, key=response_language, context=global
                    │
                    ▼
        Memory Governor.slot_exists(category, key, context)?
                    │
          ┌─────────┴──────────┐
          YES                   NO
          │                     │
          ▼                     ▼
    当前 ACTIVE 节点          直接创建新节点
    是否存在？                 status=ACTIVE
          │
    ┌─────┴─────┐
    YES          NO
    │            │
    ▼            ▼
  检查是否       slot 存在但无
  同一 value    ACTIVE（全为
    │           DEPRECATED）
    │            │
    │            ▼
    │          创建新节点
    │          status=ACTIVE
    │
┌───┴───┐
相同    不同
│       │
▼       ▼
强化    创建新节点
计数+1  status=ACTIVE
        旧节点→DEPRECATED
        建立 SUPERSEDED_BY
```

---

## 7. Relationship Model

L2 层使用 MCP Knowledge Graph 的关系机制建立记忆节点之间的语义连接。以下为规范定义的五种关系类型。

### 7.1 关系定义总览

| 关系类型 | 方向 | 用途 |
|---------|------|------|
| `HAS_MEMORY` | PKIA_Project → Memory_Node | 实体拥有某条记忆 |
| `HAS_DECISION` | Memory_Node → Memory_Node | 一条记忆引用了另一条记忆作为决策依据 |
| `SUPERSEDED_BY` | New_Node → Old_Node | 新版本替换了旧版本 |
| `DERIVED_FROM` | Inferred_Node → Source_Node | 推断记忆来源于某条源记忆 |
| `CONTRADICTS` | Node_A → Node_B | 两条记忆存在矛盾 |

### 7.2 HAS_MEMORY

**用途**: 将 PKIA 实体与其记忆节点关联。是 L2 层拓扑的主干关系。

**方向**: 实体（如 PKIA_Project）→ Memory_Node

**基数**: 一个实体可以有多个 `HAS_MEMORY` 关系。

**示例**:
```
PKIA_Project ── HAS_MEMORY ──► mem_response_language
PKIA_Project ── HAS_MEMORY ──► mem_research_field
PKIA_Project ── HAS_MEMORY ──► mem_current_project
```

### 7.3 HAS_DECISION

**用途**: 记录一条记忆是基于哪些记忆做出的决策。提供决策可追溯性。

**方向**: 决策结果 → 决策依据

**示例**:
```
mem_preference_change (ACTIVE)
    ── HAS_DECISION ──► mem_original_preference (DEPRECATED)
    ── HAS_DECISION ──► mem_user_feedback_log (ARCHIVED)
```

### 7.4 SUPERSEDED_BY

**用途**: 版本替换关系。指向被替换的旧版本。

**方向**: 新版本 → 旧版本

**约束**: SUPERSEDED_BY 链必须是单向无环的。

**示例**:
```
mem_v3 (ACTIVE) ── SUPERSEDED_BY ──► mem_v2 (DEPRECATED)
    ── SUPERSEDED_BY ──► mem_v1 (DEPRECATED)
```

**追溯**: 沿 SUPERSEDED_BY 链可以回溯完整版本历史。

### 7.5 DERIVED_FROM

**用途**: 记录推断型记忆的来源。仅用于 AGENT_INFERRED 类型的节点。

**方向**: 推断结果 → 来源

**示例**:
```
mem_inferred_language (DRAFT, confidence=0.7)
    ── DERIVED_FROM ──► mem_conversation_log_001 (ARCHIVED)
```

### 7.6 CONTRADICTS

**用途**: 记录两条记忆之间存在矛盾。当 Agent 检测到不一致时使用。

**方向**: 新证据 → 旧证据

**示例**:
```
mem_new_evidence (ACTIVE)
    ── CONTRADICTS ──► mem_old_claim (DEPRECATED)
```

**注意**: `CONTRADICTS` 通常伴随一个解析动作（一条记忆被 DEPRECATED 或被标记为低置信度）。不应存在两条 ACTIVE 记忆互相 `CONTRADICTS`。

---

## 8. Reinforcement Mechanism

### 8.1 定义

`reinforcement_count` 是一个 Memory_Node 的**强化计数器**，记录该记忆被独立「观测到」或「确认」的次数。

### 8.2 核心原则

当 Agent 接收到与现有 ACTIVE 记忆一致的新信息时，**不创建新节点**，仅增加现有节点的 `reinforcement_count` 和更新 `updated_at`。

### 8.3 触发条件

以下情况触发强化计数递增：

1. **用户重复确认**: 用户再次表达了与已有记忆一致的偏好。
2. **独立证据验证**: 从不同来源（如另一个 API、另一段对话历史）获得了相同的信息。
3. **行为模式匹配**: Agent 观察到用户行为与已有记忆一致（例如：用户始终使用中文提问，与 `response_language=zh-CN` 的记忆一致）。

### 8.4 作用

- **置信度提升**: 每次强化计数递增，节点的 `confidence` 按公式 `confidence = 1 - (1 - initial_confidence)^reinforcement_count` 增长（当 `reinforcement_count` 足够大时趋近于 1.0）。
- **优先级排序**: 在检索结果中，`reinforcement_count` 更高的节点排在前面。
- **抗噪能力**: 低强化计数的记忆更容易被新证据替换。

### 8.5 示例

**场景**: 用户第一次说「请用中文回复」。

```
节点: mem_001
category: preference
key: response_language
value: "zh-CN"
context: global
status: ACTIVE
confidence: 1.0       (USER_EXPLICIT，初始即为 1.0)
source_type: USER_EXPLICIT
reinforcement_count: 1
created_at: 2026-06-20T10:00:00Z
```

**场景**: 后续对话中，用户再次用中文提问，Agent 检测到行为与已有记忆一致。

```
reinforcement_count: 1 → 2
confidence: 1.0 (已经是最大值，不变)
updated_at: 2026-06-20T12:00:00Z
```

**场景**: Agent 从对话中推断用户的偏好（AGENT_INFERRED）。

```
节点: mem_002
category: preference
key: explanation_style
value: "example_driven"
context: global
status: DRAFT
confidence: 0.6
source_type: AGENT_INFERRED
reinforcement_count: 1
created_at: 2026-06-20T14:00:00Z
```

**场景**: 之后再次观察到用户偏好示例驱动的解释方式。

```
reinforcement_count: 1 → 2
confidence: 0.6 → 0.84 (1 - (1-0.6)^2)
updated_at: 2026-06-20T16:00:00Z
```

当 `reinforcement_count` 累积到使 `confidence ≥ 0.9` 时，Memory Governor 可自动将 DRAFT 提升为 ACTIVE。

---

## 9. Retrieval Interfaces

以下为 L2 层的逻辑检索接口定义。接口是功能规格，不涉及具体实现语言。

### 9.1 get_active_memory()

**功能**: 获取指定 slot 的当前 ACTIVE 记忆。

**请求**:
```
category: string           (必需)  记忆分类
key: string                (必需)  记忆键名
context: string            (可选)  上下文，默认空字符串
confidence_threshold: float (可选)  置信度阈值，默认 0.5
```

**处理逻辑**:
1. 查询 slot = `category:key@context` 中 status = ACTIVE 的节点
2. 如果精确 context 匹配命中，返回该节点
3. 如果未命中且 context 非空，回退到 context = "" 查询
4. 如果仍无结果，返回空（no memory found）
5. 如果命中结果 confidence < threshold，返回空

**返回**:
```
node: Memory_Node | null    匹配的节点
chain: Memory_Node[]        版本链（可选，返回该 slot 的所有历史版本）
```

**示例**:
```
> get_active_memory(category="preference", key="response_language", context="global")
< node: mem_001 (ACTIVE, value="zh-CN", confidence=1.0, version=2)
< chain: [mem_001 (ACTIVE, v2), mem_000 (DEPRECATED, v1)]
```

### 9.2 get_context_memory()

**功能**: 获取指定上下文下的所有 ACTIVE 记忆。

**请求**:
```
context: string              (必需) 上下文标识符
tier_filter: string[]        (可选) 限定返回的 Tier，默认返回所有
confidence_threshold: float  (可选) 置信度阈值，默认 0.0
```

**处理逻辑**:
1. 查询所有 context 字段匹配的 status = ACTIVE 节点
2. 如果指定了 tier_filter，仅返回属于指定 tier 的节点
3. 如果指定了 confidence_threshold，过滤低于阈值的节点

**返回**:
```
nodes: Memory_Node[]    匹配的记忆节点列表
```

**示例**:
```
> get_context_memory(context="PKIA_Project", tier_filter=["project"])
< nodes: [
<   { key: "project_phase", value: "architecture_design", ... },
<   { key: "project_constraint", value: "8GB VRAM limit", ... }
< ]
```

### 9.3 trace_memory()

**功能**: 沿关系链追溯记忆的完整历史。

**请求**:
```
node_id: string              (必需) 起始节点 ID
direction: string            (可选) "forward" | "backward"，默认 "backward"
max_depth: int               (可选) 最大追溯深度，默认 10
```

**处理逻辑**:
1. 根据 `direction` 决定追溯方向：
   - **backward**: 沿 `SUPERSEDED_BY` 关系向旧版本追溯（默认）
   - **forward**: 沿 `SUPERSEDED_BY` 的反向关系向新版本追溯
2. 每次跳转时，同时记录 `DERIVED_FROM` 关系指向的节点（如果有）
3. 达到 `max_depth` 或无法继续跳转时停止

**返回**:
```
timeline: TraceNode[]    按时间排列的追溯链
```

**TraceNode 结构**:
```
{
  node: Memory_Node,
  relationships: [         连接当前节点与下一跳的关系
    { type: "SUPERSEDED_BY" | "DERIVED_FROM", target_id: string }
  ]
}
```

**示例**:
```
> trace_memory(node_id="mem_003", direction="backward")
< timeline: [
<   { node: mem_003 (ACTIVE, v3, 2026-06-20), relationships: [{ type: "SUPERSEDED_BY", target_id: "mem_002" }] },
<   { node: mem_002 (DEPRECATED, v2, 2026-06-18), relationships: [
<       { type: "SUPERSEDED_BY", target_id: "mem_001" },
<       { type: "DERIVED_FROM", target_id: "mem_conv_001" }
<   ]},
<   { node: mem_001 (DEPRECATED, v1, 2026-06-15), relationships: [] }
< ]
```

---

## 10. Memory Governor

Memory Governor 是位于 Agent 和 MCP Memory Server 之间的**记忆治理层**。它不直接存储记忆，而是负责所有写入操作的校验、路由和生命周期管理。

### 10.1 架构位置

```
Agent / Workflow Node
        │
        ▼
┌─────────────────────────────────────────────┐
│          Memory Governor                     │
│                                             │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ │
│  │ Duplicate │ │   Slot    │ │  Version  │ │
│  │ Detection │ │ Validation│ │ Management│ │
│  └───────────┘ └───────────┘ └───────────┘ │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ │
│  │ Conflict  │ │Reinforce- │ │ Lifecycle │ │
│  │ Resolution│ │   ment    │ │Enforcement│ │
│  └───────────┘ └───────────┘ └───────────┘ │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
        MCP Memory Server
        (Knowledge Graph)
```

### 10.2 核心职责

#### 10.2.1 Duplicate Detection

校验写入的 `(category, key, context, value)` 是否与现有 ACTIVE 节点完全一致。

- **命中**: 不创建新节点，仅对现有节点执行 `reinforcement_count + 1`。
- **未命中**: 继续后续校验流程。

#### 10.2.2 Slot Validation

校验 slot 的唯一性约束：

- 如果目标 slot 已有 ACTIVE 节点且 value 不同，触发 Conflict Resolution。
- 如果目标 slot 已有 ACTIVE 节点且 value 相同，触发 Duplicate Detection（同上）。
- 如果目标 slot 无 ACTIVE 节点，允许直接创建。

#### 10.2.3 Version Management

- 查询目标 slot 的最高 `version`。
- 新节点的 `version = max_version + 1`。
- 将旧 ACTIVE 节点的 status 设为 DEPRECATED。

#### 10.2.4 Conflict Resolution

执行第 6 章定义的冲突解决流程：

1. 创建新节点，status = ACTIVE
2. 旧节点 status → DEPRECATED
3. 建立 SUPERSEDED_BY 关系（新 → 旧）

#### 10.2.5 Reinforcement Update

满足强化条件时：

1. 递增目标节点的 `reinforcement_count`
2. 更新 `updated_at`
3. 按公式更新 `confidence`
4. 如果 confidence ≥ 0.9 且当前 status = DRAFT，自动提升为 ACTIVE

#### 10.2.6 Lifecycle Enforcement

- **过期检查**: 定期扫描 `expires_at` 已到达的 ACTIVE 节点，转为 ARCHIVED。
- **DRAFT 超时**: 超过 7 天未确认的 DRAFT 节点自动转为 DEPRECATED。
- **Tier4 清理**: 定期清理过期的 Tier4 Working 记忆。

### 10.3 写入流程图

```
Agent 调用 write_memory(category, key, value, context, source_type)
                    │
                    ▼
         ┌─────────────────────┐
         │ Duplicate Detection │ ──── 命中 ────► Reinforcement Update ──► 完成
         └─────────┬───────────┘
                   │ 未命中
                   ▼
         ┌─────────────────────┐
         │   Slot Validation   │
         └─────────┬───────────┘
                   │
          ┌────────┴────────┐
          │                 │
    已有 ACTIVE         无冲突
          │                 │
          ▼                 ▼
   ┌──────────────┐   ┌──────────────┐
   │Conflict      │   │Version       │
   │Resolution    │   │Assignment    │
   └──────────────┘   └──────────────┘
          │                 │
          └──────┬──────────┘
                 ▼
         ┌──────────────┐
         │Create Node   │
         │via MCP       │
         └──────────────┘
                 │
                 ▼
         ┌──────────────┐
         │Update Status │
         │(if conflict) │
         └──────────────┘
                 │
                 ▼
               完成
```

---

## 11. Example Records

### 11.1 ACTIVE 示例

一个用户显式设置的身份记忆：

```json
{
  "node_id": "mem_a1b2c3d4",
  "category": "identity",
  "key": "research_field",
  "value": "知识图谱 · 自然语言处理",
  "context": "global",
  "status": "ACTIVE",
  "confidence": 1.0,
  "source_type": "USER_EXPLICIT",
  "created_at": "2026-06-15T09:00:00Z",
  "updated_at": "2026-06-15T09:00:00Z",
  "expires_at": null,
  "version": 1,
  "reinforcement_count": 3
}
```

对应的 MCP 关系:
```
PKIA_Project ── HAS_MEMORY ──► mem_a1b2c3d4
```

### 11.2 DEPRECATED 示例

被新版本替换的旧偏好记忆：

```json
{
  "node_id": "mem_x9y8z7w6",
  "category": "preference",
  "key": "response_language",
  "value": "en-US",
  "context": "global",
  "status": "DEPRECATED",
  "confidence": 1.0,
  "source_type": "USER_EXPLICIT",
  "created_at": "2026-06-01T10:00:00Z",
  "updated_at": "2026-06-10T14:00:00Z",
  "expires_at": null,
  "version": 1,
  "reinforcement_count": 5
}
```

对应的 MCP 关系:
```
PKIA_Project ── HAS_MEMORY ──► mem_x9y8z7w6
mem_a1b2c3d5 (ACTIVE, v2) ── SUPERSEDED_BY ──► mem_x9y8z7w6 (DEPRECATED, v1)
```

### 11.3 SUPERSEDED_BY 完整示例

一个完整的三版本替换链：

**v1 — 初始设置**
```json
{
  "node_id": "mem_v1_abc",
  "category": "preference",
  "key": "explanation_style",
  "value": "summary_first",
  "context": "global",
  "status": "DEPRECATED",
  "confidence": 1.0,
  "source_type": "USER_EXPLICIT",
  "created_at": "2026-06-01T10:00:00Z",
  "updated_at": "2026-06-01T10:00:00Z",
  "expires_at": null,
  "version": 1,
  "reinforcement_count": 2
}
```

**v2 — 用户修改**
```json
{
  "node_id": "mem_v2_def",
  "category": "preference",
  "key": "explanation_style",
  "value": "detail_first",
  "context": "global",
  "status": "DEPRECATED",
  "confidence": 1.0,
  "source_type": "USER_EXPLICIT",
  "created_at": "2026-06-10T14:00:00Z",
  "updated_at": "2026-06-10T14:00:00Z",
  "expires_at": null,
  "version": 2,
  "reinforcement_count": 1
}
```

**v3 — 当前生效**
```json
{
  "node_id": "mem_v3_ghi",
  "category": "preference",
  "key": "explanation_style",
  "value": "example_driven",
  "context": "global",
  "status": "ACTIVE",
  "confidence": 0.84,
  "source_type": "AGENT_INFERRED",
  "created_at": "2026-06-20T16:00:00Z",
  "updated_at": "2026-06-20T16:00:00Z",
  "expires_at": null,
  "version": 3,
  "reinforcement_count": 2
}
```

**关系拓扑**:
```
mem_v3_ghi (ACTIVE, v3, AGENT_INFERRED)
    ── SUPERSEDED_BY ──► mem_v2_def (DEPRECATED, v2, USER_EXPLICIT)
        ── SUPERSEDED_BY ──► mem_v1_abc (DEPRECATED, v1, USER_EXPLICIT)

PKIA_Project ── HAS_MEMORY ──► mem_v3_ghi
PKIA_Project ── HAS_MEMORY ──► mem_v2_def
PKIA_Project ── HAS_MEMORY ──► mem_v1_abc
```

### 11.4 DRAFT 示例

Agent 推断的待确认记忆：

```json
{
  "node_id": "mem_draft_001",
  "category": "preference",
  "key": "code_style",
  "value": "pythonic",
  "context": "global",
  "status": "DRAFT",
  "confidence": 0.65,
  "source_type": "AGENT_INFERRED",
  "created_at": "2026-06-20T15:00:00Z",
  "updated_at": "2026-06-20T15:00:00Z",
  "expires_at": "2026-06-27T15:00:00Z",
  "version": 1,
  "reinforcement_count": 1
}
```

对应的 MCP 关系:
```
PKIA_Project ── HAS_MEMORY ──► mem_draft_001
mem_draft_001 ── DERIVED_FROM ──► mem_conversation_log_042 (源证据)
```

---

## 12. Future Extensions

以下方向为未来的版本规划，不在当前 v1.1 规范的范围之内。列于此作为架构预留。

### 12.1 Hybrid Vector + Graph Retrieval

**方向**: 将向量语义检索与图结构检索结合。

**设想**: 对于无法精确匹配 slot 的查询，先通过向量相似度找到候选节点，再通过图关系过滤和排序。适用于「模糊回忆」场景，如 Agent 说「我记得用户好像提过关于代码风格的内容」。

### 12.2 Semantic Memory Search

**方向**: 支持自然语言查询记忆。

**设想**: Agent 可以直接说「用户对解释风格有什么偏好？」，系统自动将自然语言映射到 `category:preference, key:explanation_style`，返回 ACTIVE 节点。

### 12.3 Memory Decay

**方向**: 随时间自动降低记忆的置信度和优先级。

**设想**: 长期未被强化（`updated_at` 距今较久）的记忆，其 `confidence` 按时间衰减函数逐步降低，最终自动转为 ARCHIVED。防止记忆「永久有效」导致过期认知持续影响 Agent 行为。

### 12.4 Multi-User Support

**方向**: 支持多个用户的记忆隔离与共享。

**设想**: 每个 `Memory_Node` 增加 `owner_id` 字段。系统支持用户私有记忆空间和共享记忆空间。身份层和偏好层按用户隔离，工作层支持跨用户共享。

### 12.5 Automatic Summarization

**方向**: 自动从大量历史记忆中生成摘要。

**设想**: 当一个 slot 的版本链过长时（如 50+ 次变更），自动生成摘要节点，概括变更历史的核心脉络。摘要节点可作为快速检索入口，替代遍历整个版本链。

---

> **文档结束**  
> 本规范为 PKIA L2 Memory Ontology v1.1 的官方 Architecture Freeze Document。  
> 所有后续实现必须遵循本规范。如需偏离，必须经过架构评审并更新本文档版本号。