# PKIA 项目阶段性复盘与思考报告 v1

> **生成日期**: 2026-07-09
> **覆盖范围**: 从项目立项至 Runtime Architecture 目录重构完成
> **数据来源**: git log (37 commits), progress 文件, docs/ 目录 (66+ 文档), pkia_memory (1,424 行 Python)

---

## 1. 全景状态机 (Macro Status)

### 1.1 当前开发节点

```
Memory Governance (Phase 0A): ████████████████████████████████ 100% — Frozen
PKIA MVP Phase 0 (Phase 0B): ████████████████████████████████ 100% — Baseline Locked
PKIA MVP Phase 1 (Phase 1):  ████████░░░░░░░░░░░░░░░░░░░░░░  25% — Runtime 文档完成, 代码 0%
                                  ↑ 当前所在位置
```

### 1.2 已成功闭环的关键里程碑

| # | 里程碑 | 时间 | 关键产出 | 状态 |
|---|--------|------|----------|------|
| M1 | L2 Memory Ontology v1.1 | 06-14 | 12 章 Ontology 规范 | ✅ 冻结 |
| M2 | MCP Memory Server Capability Audit | 06-14 | 能力差距分析报告 | ✅ 关闭 |
| M3 | Governor MVP v0.1 | 06-15 | 5 模块, 1,279 行, 30 测试 | ✅ 冻结 |
| M4 | Memory Schema v1.0 | 06-16 | 可落地的 MCP Schema | ✅ 冻结 |
| M5 | Schema 一致性审查 + P0 补丁 | 06-18~20 | 10 个 P0 问题全部修复, 10 份审查文档 | ✅ 关闭 |
| M6 | Scoring Pipeline Schema v2 | 06-20 | 重写 Pipeline 定义, 吸收所有补丁 | ✅ 冻结 |
| M7 | Memory Sync 体系 (Protocol + Enforcement + Audit) | 06-21~22 | 三级同步体系 + 5 份 Receipt | ✅ 冻结 |
| M8 | Memory Governance Freeze | 06-22 | 10 组件冻结声明 | ✅ 生效 |
| M9 | L3 Namespace Architecture Migration | 06-22 | 单文件 PROGRESS.md → 多文件 progress/ | ✅ 完成 |
| M10 | Bootstrap Protocol v1.0 → v1.1 | 06-22~23 | L2 强制提取 + Working Context + Integrity Check | ✅ 完成 |
| M11 | PKIA MVP v0.1 Baseline | 06-24 | 13 份冻结文档, 成功标准, 排除项 | ✅ 锁定 |
| M12 | Runtime Architecture 文档集合 | 07-08~09 | 8 份活跃文档, 2 份 Superseded | ✅ 完成 |

### 1.3 全链路数据流 (概念层面)

```

   [Memory System]                          [PKIA MVP Pipeline]
   L1 .clinerules/.opencode.md             GitHub Trending
        ↓                                          ↓
   L2 Governor + Memory Graph              HTTP Collector → Code Normalizer
        ↓                                          ↓
   L3 progress/pkia_mvp.md                 LLM Classification
        ↓                                          ↓
   (Memory Gov FROZEN)                     LLM Unified Scoring
        ↓                                          ↓
   (PKIA MVP v0.1 显式排除 Memory 集成)     Code Ranker → Template Report
```

**关键关系**: 两组系统共存但不耦合。Memory Governance 已冻结，PKIA MVP Pipeline 的实现不依赖 L2 Memory。

---

## 2. 核心机制沉淀 (Core Mechanisms)

### 2.1 Governor MVP — Slot Index 写入决策树

**位置**: `pkia_memory/governor.py` (421 行)

这是整个项目中实现最完整的算法模块。写入决策树解决了在不可靠的 MCP 环境下保持记忆一致性的核心问题：

```
write(request)
  ├── slot 无 ACTIVE? → _action_create()
  ├── slot 有 ACTIVE?
  │   ├── value 相同? → _action_reinforce()
  │   └── value 不同?
  │       ├── C01: USER_EXPLICIT > AGENT_INFERRED? → reject
  │       ├── C02: old.confidence > new.confidence? → reject
  │       └── 通过 → _action_supersede()
```

**发挥作用的场景**: 多 Agent 并发写入同一记忆槽时的冲突解决。通过 SourceType 优先级（USER_EXPLICIT > AGENT_INFERRED > SYSTEM_GENERATED）和 Confidence 比较，确保用户显式设定的记忆不会被 Agent 推论覆盖。

### 2.2 Fat Object + Append-Only 数据模型

**位置**: `runtime_boundary_v1.md` P-05/P-06, `data_flow_v1.md` §4.1

单一 Canonical Object 贯穿 6 个 Schema Stage，每阶段仅追加字段，产生如下演化链：

```
RawProject → NormalizedProject → ClassifiedProject → ScoredProject → RankedProject → ReportItem
(11 fields)   (3 added)            (4 added)           (8 added)       (2 added)       (3 added)
```

**发挥作用的场景**: 确保 `project_id` 从采集到日报输出的全链路可追溯。任何阶段的调试都可以通过 `project_id` 回溯到原始 GitHub 数据。此机制直接解决了 PRD 中"看过就忘、找不到源头"的核心痛点。

### 2.3 Dify First, Python Minimal (P-01/P-02 + R-03 + R-05)

这是一个经过至少 3 轮迭代才收敛的架构决策。初始方案假设 Python 独立脚本 + Dify Workflow，经过 Workshop 推演后完全重构为 Dify Native Runtime：

| 版本 | Collector | Ranking | Report | Python 依赖 |
|------|-----------|---------|--------|-------------|
| Baseline (§6.2) | Python 脚本 | 未指定 | 未指定 | 高 |
| Runtime Boundary v1 (初版) | HTTP+Code (Pending) / Python (backup) | Python | Python | 中 |
| Node Mapping v1 (终版) | HTTP+Code (已决) | Code Node (R-05 aware) | Template Node | **极少** |

**发挥作用的场景**: 将 Python 限制为仅 Storage Adapter 一个组件（写文件 I/O），所有业务逻辑（分类、评分、排序、渲染）都在 Dify 内置节点中完成。消除了 Python 脚本群带来的状态耦合与单点故障风险。

### 2.4 Validation Gate + Fail-Fast 断言链

**位置**: `data_flow_v1.md` §4.5, `node_mapping_v1.md` §4.3

每个 LLM Node 后串联一个 Code Node，执行 5 层断言：

```
LLM 输出 → JSON Parse → 必填字段 → 枚举值 → 字段类型 → 字段范围
                   全部通过 → 继续
                   任一失败 → Drop (SKIPPED, 不影响同批次)
```

**发挥作用的场景**: LLM 不能保证 100% 输出格式合法。Validation Gate 将 LLM 输出与业务逻辑隔离，确保格式异常在第一时间被捕获，而不是在后续节点中引发难以调试的连锁故障。

### 2.5 Three-Tier Memory Architecture

**位置**: `.clinerules` / `.opencode.md` §5

```
L1 宪法层:   .clinerules / .opencode.md     — 智能体行为边界
L2 图谱层:   Governor + project-memory.json  — 长期结构化记忆
L3 进度层:   progress/<namespace>.md          — 短期任务进度
```

**发挥作用的场景**: 确保多 Agent 切换场景下的状态连续性。新 Agent 启动时通过 Bootstrap Protocol 自动加载 L2 图谱 + L3 进度，无需用户重复描述上下文。

---

## 3. 工程折中与避坑指南 (Trade-offs & Lessons Learned)

### 3.1 Trade-off: 文档先行 vs. 代码先行

| 选择 | 文档先行 |
|------|----------|
| **后果** | 66 份文档, 13 份冻结, 0 行业务代码 |
| **收益** | 所有架构决策在实现前已被充分讨论、审查、冻结。不存在"边写边改"导致的返工。 |
| **成本** | 需要 3+ 周才能看到第一行代码。Phase 0 文档收尾 + Phase 1 Runtime 文档就用了 2 周。 |
| **教训** | 对于基础设施型项目（Memory OS、数据 Pipeline），文档先行是值得的。对于探索型项目（Prompt Engineering），应代码先行。 |

### 3.2 Trade-off: Schema 冻结边界 (10 P0 修复的代价)

**背景**: 审查发现 Scoring Pipeline Schema v1 存在 10 个 P0 一致性问题（字段命名不一致、`project_id` 缺失、中文字段名等）。

**决策**: 不修复 v1，直接重写 v2，吸收所有补丁。

**后果**: v1→v2 重写耗时显著，但换来了一份无历史包袱的 Schema。

**教训**: 
- Schema First 虽好，但第一版 Schema 几乎必然有遗漏
- 文档间的交叉引用（Classification Agent ←→ Scoring Agent ←→ Data Schema）是 P0 问题的重灾区
- 每次 Schema 变更的时间成本约为 3 次修改（改 Schema → 改 Agent Spec → 改 Pipeline Spec）

### 3.3 Trade-off: Unified Scoring vs. 四独立 LLM 调用

| 维度 | 四独立调用 | 统一评分 (MD-02) |
|------|-----------|------------------|
| Token 消耗 | 高 (4× 上下文 + 4× 输出) | 低 (1× 上下文 + 1× 输出) |
| 评分一致性 | 可能不一致（同一项目维间矛盾） | 天然一致（同一次推理） |
| 可调试性 | 高（每维度独立追踪） | 低（一整个 LLM 输出块） |
| 输出校验复杂度 | 4 次独立校验 | 1 次校验但 Schema 更大 |

**选择**: Unified Scoring (MD-02)。理由：Token 节省 + 一致性收益超过可调试性损失。

### 3.4 Trade-off: Variable Aggregator 顺序不保证 (R-05)

**背景**: Dify 的 Variable Aggregator 不保证输出顺序与输入顺序一致。这是 Dify 平台特性，不是 Bug。

**影响**: Ranking Code Node 不能假设输入已排序。

**解决**: 每个项目的 `project_id` 携带确定性排序权重。Ranker 节点不再依赖输入顺序，始终执行完整的 5 级排序（ranking_group → total_score → career_alignment → interest_match → project_id）。

**教训**: 发现 Dify 平台约束的时机越早越好。在 Runtime Boundary 阶段就暴露此约束（通过 Workshop 推演），避免了在实现阶段才发现时的被动重构。

### 3.5 已否决的方案清单

| 否决方案 | 否决原因 | 当前方案 |
|----------|----------|----------|
| Python 脚本群实现全 Pipeline | 状态耦合, 单点故障, 偏离 Dify 平台定位 | Dify Native Workflow |
| 四独立 LLM 评分调用 | Token 浪费, 维度间可能矛盾 | Unified Scoring (MD-02) |
| Python 拼接 Markdown | 不可维护, 偏离 Template Node 定位 | Template Node (Jinja2) |
| 独立 runtime_decisions_v1.md | ADR 非 Runtime 专属, 未来统一 docs/adr/ | 已取消 |
| Collector 纯 Python Adapter | 违反 P-01 Dify First | HTTP Node → Code Node |

---

## 4. 核心规律与原则体系

### 4.1 已建立的原则层级

```
P-01~P-06  (runtime_boundary_v1.md)   — 全局架构原则, 锁定不新增
R-01~R-05  (style_guide §7.2)        — 运行时规则, 追加递增
MD-01~MD-02 (node_mapping_v1.md)      — 映射决策, 局部命名空间
R-XX 规则编号一旦分配, 永久不可变 (Immutable ID)
```

### 4.2 被实践证明有效的思考框架

**"Dify First" 问题检查清单**（适用于每个阶段）:

```
□ 这个能力可以用 Dify 内置节点实现吗？
   ├─ 是 → Dify Node
   └─ 否
       □ 是否可以用 Dify Code Node + 标准库实现？
          ├─ 是 → Code Node
          └─ 否 → Python Adapter (仅 I/O, 不含业务逻辑)
```

**"State Machine 归属" 判定规则**（适用于每个涉及状态的概念）:

```
□ 这个状态描述的是正常业务流转？
   → data_flow_v1.md
□ 这个状态描述的是异常/失败后的处理？
   → failure_handling_v1.md
```

---

## 5. 文档体系现状

### 5.1 按子系统统计

| 子系统 | 文档数量 | 代码行数 | 状态 |
|--------|----------|----------|------|
| Memory Governance | ~12 份 | 1,424 (Python) | ✅ Frozen |
| PKIA MVP Business Spec | 13 份 (frozen) + 2 (deprecated) | 0 | ✅ Frozen |
| Runtime Architecture | 8 份 (active) + 2 (superseded) | 0 | ✅ Approved |
| PKIA MVP Implementation | 0 | 0 | ⏳ 未开始 |

### 5.2 文档覆盖率 (vs Baseline Success Criteria)

| 检查项 | 标准 | 状态 |
|--------|------|------|
| 采集完整性 (30 项目) | 定义在 baseline §9 | 未实现 |
| 数据血缘 (project_id) | 定义在 data_flow_v1.md §4.1 | 设计就绪 |
| 分类覆盖率 | 定义在 node_io_contract_v1.md §4.2.2 | 设计就绪 |
| 评分一致性 | 定义在 data_flow_v1.md §4.5 | 设计就绪 |
| 推荐分布 | 定义在 node_mapping_v1.md §4.2 | 设计就绪 |
| 日报结构 | 定义在 deployment_v1.md §4.1 | 设计就绪 |
| 失败降级 | 定义在 failure_handling_v1.md §4.3.3 | 设计就绪 |

---

## 6. 下一阶段目标 (Next Actionable Steps)

### P0: GitHub Trending Collector 第一版实现

| 维度 | 说明 |
|------|------|
| 目标 | 实现 Node 1 (HTTP) + Node 2 (Code) 或 Python Adapter |
| 前置依赖 | Runtime 文档已就绪 |
| 关键验证点 | Code Node 能否稳定解析 GitHub Trending HTML |
| 预计复杂度 | 中 |
| 输出 | `scripts/pkia/collector.py` 或 Dify Workflow 片段 |

### P0: Dify Workflow 骨架 (Node 1→2→3 数据链)

| 维度 | 说明 |
|------|------|
| 目标 | 搭建 Global Ingestion + Iteration 的基本数据流 |
| 前置依赖 | Collector 实现 |
| 关键验证点 | Iteration 节点的 30 项目展开与 Variable Aggregator 收拢 |
| 预计复杂度 | 中-高 |
| 输出 | Dify Workflow `.yml` 导出文件 |

### P1: Classification + Scoring LLM Node 配置

| 维度 | 说明 |
|------|------|
| 目标 | 将 `classification_agent_spec_v1.md` 和 `prompt_scoring_agent_v2.md` 转化为可部署的 LLM Node |
| 前置依赖 | Workflow 骨架就绪 |
| 关键验证点 | LLM 输出格式符合 Validation Gate 断言 |
| 预计复杂度 | 中 |
| 输出 | Dify LLM Node Prompt 配置 |

### P2: Ranking Code Node + Template Node 实现

| 维度 | 说明 |
|------|------|
| 目标 | 实现 Node 5 (Ranker) + Node 6 (Template) |
| 前置依赖 | Scoring 完成 |
| 关键验证点 | Aggregator 顺序不保证时的 Ranker 正确性 (R-05) |
| 预计复杂度 | 中 |
| 输出 | Dify Code Node + Template Node |

### P2: Storage Adapter

| 维度 | 说明 |
|------|------|
| 目标 | 本地 Python FastAPI 服务接收 Workflow HTTP POST |
| 前置依赖 | Report Rendering 完成 |
| 关键验证点 | Adapter 写文件路径符合 `pkia/reports/YYYY-MM-DD.md` |
| 预计复杂度 | 低 |
| 输出 | `scripts/pkia/storage_adapter.py` |

---

## 7. 风险延续

从第 1 次架构审查延续至今的风险变化：

| 风险 | 初始等级 | 当前等级 | 变化原因 |
|------|----------|----------|----------|
| Dify Batch Processing 能力 | HIGH | MEDIUM | Runtime 设计已确认 Iteration + Aggregator + Code Node 可完成, 但尚未实战验证 |
| LLM 输出可靠性 | HIGH | HIGH | 未变。Validation Gate 已设计但未部署 |
| Python 依赖膨胀 | MEDIUM | LOW | 已通过 P-01/P-02 原则控制, Python 仅限于 Storage Adapter |
| Variable Aggregator 顺序 | 未识别 | KNOWN | 已发现并记录为 R-05, Ranking 设计已适应 |

---

*End of PKIA Retrospective Report v1*
