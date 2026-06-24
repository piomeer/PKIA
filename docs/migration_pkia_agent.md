# PKIA Agent Migration Context

> **生成时间**: 2026-06-23 22:45 JST
> **用途**: 跨 Agent 迁移时的上下文传递文档
> **源命名空间**: `pkia_mvp`

---

## 1. 当前任务进度与未完成 TODO

### ✅ 已完成

#### PKIA 文档体系（核心文档 — 8 份）

| # | 文档 | 状态 | 说明 |
|---|------|------|------|
| 1 | `docs/pkia-v01-prd.md` | ✅ 已完成 | 产品需求文档 v0.1 |
| 2 | `docs/interest_profile_v1.md` | ✅ 已完成 | 兴趣画像（S/A/B/Ignore Tier 定义） |
| 3 | `docs/scoring_strategy_v1.md` | ✅ 已完成 | Career Alignment 评分策略 |
| 4 | `docs/scoring_examples_v1.1.md` | ✅ 已完成 | 11 个 Few-shot 评分案例 |
| 5 | `docs/project_classification_taxonomy_v1.md` | ✅ 已完成 | 分类体系（11 个 Level-1, 32 个 Level-2） |
| 6 | `docs/classification_agent_spec_v1.md` | ✅ **已补丁** | 分类 Agent 规范（Schema 一致性已修复） |
| 7 | `docs/prompt_scoring_agent_v2.md` | ✅ **已补丁** | 评分 Agent Prompt v2（Schema 一致性已修复） |
| 8 | `docs/project_data_schema_v1.md` | ✅ 已完成 | 数据契约（6 阶段数据结构定义） |

#### PKIA 文档体系（流程/审查/补丁 — 8 份）

| # | 文档 | 状态 | 说明 |
|---|------|------|------|
| 9 | `docs/data_collection_strategy_v1.md` | ✅ 已完成 | 数据采集策略 |
| 10 | `docs/workflow_v0.1_design.md` | ✅ 已完成 | Workflow 设计草稿 |
| 11 | `docs/daily_report_spec_v1.md` | ✅ 已完成 | 日报展示规范 |
| 12 | `docs/report_generation_pipeline_v1.md` | ✅ 已完成 | 报告生成流水线 |
| 13 | `docs/scoring_pipeline_schema_v1.md` | ✅ **已存档** | 评分流水线 v1（被 v2 替代） |
| 14 | `docs/scoring_pipeline_schema_v2.md` | ✅ **新创建** | 评分流水线 v2（Schema 100% 合规） |
| 15 | `docs/scoring_pipeline_patch_plan_v1.md` | ✅ 已完成 | v2 创建的补丁计划 |
| 16 | `docs/review_scoring_pipeline_consistency_v1.md` | ✅ 已完成 | v1 审查报告（20/100 → 100/100） |
| 17 | `docs/schema_consistency_patch_v1.md` | ✅ 已完成 | 全局 Schema 一致性补丁计划 |
| 18 | `docs/review_project_data_schema_consistency.md` | ✅ 已完成 | Schema 创建前的一致性审查 |
| 19 | `docs/review_classification_agent_patch_v1.md` | ✅ 已完成 | classification_agent_spec 补丁审查 |
| 20 | `docs/review_prompt_scoring_agent_v2_patch_v1.md` | ✅ 已完成 | prompt_scoring_agent 补丁审查 |

#### 三层记忆系统基础设施

| 项目 | 状态 | 说明 |
|------|------|------|
| Governor MVP v0.1 | ✅ 已完成 | 23/23 测试通过 |
| 持久化层 | ✅ 已部署 | SQLite 持久化 |
| Memory Sync | ✅ 已部署 | L2 ↔ L3 同步机制 |
| Agent Bootstrap Protocol v1.0 | ✅ 已部署 | Agent 启动生命周期 |
| Bootstrap Protocol v1.1 | ✅ 已部署 | 更新版协议 |
| Memory Governance | ✅ 已部署 | 冻结/同步/审计全链路 |

### 🔄 进行中 / 待处理

| 优先级 | 任务 | 说明 |
|--------|------|------|
| P0 | **scoring_pipeline_schema_v1.md 正式废弃** | v2 已创建，v1 应标记为 DEPRECATED |
| P0 | **report_generation_pipeline_v1.md Schema 一致性补丁** | 输入字段表需要对齐 Schema（缺 project_id, pipeline_status, career_goal_impact）|
| P0 | **daily_report_spec_v1.md Career Goal Impact 展示补丁** | 日报格式未体现结构化 career_goal_impact |
| P1 | PKIA MVP 实际实现（数据采集模块） | F1: GitHub Trending 采集 |
| P1 | PKIA MVP 分类 Agent 集成 | F2: 分类 Agent 集成 |
| P1 | PKIA MVP 评分 Agent 集成 | F3: 评分 Agent 集成 |
| P1 | PKIA MVP Daily Report 生成 | F4: 日报生成 |

### ⛔ 已知卡点

| 卡点 | 说明 |
|------|------|
| Memory Bouncer Script 未创建 | `utils/memory_bouncer.py` 尚不存在 |
| scoring_pipeline_schema_v1.md 仍存在 | 需要决定是否保留还是删除（建议保留为历史参考，v2 替代） |

---

## 2. 动态共识与临时规则（尚未固化的决策）

### 2.1 Schema 一致性原则（已应用于 3 个文档的补丁）

以下规则在补丁过程中形成，尚未独立成文档，但已在 3 次补丁中实际应用：

| 规则 | 说明 | 应用位置 |
|------|------|----------|
| **Fields use snake_case English** | 所有字段名使用小写加下划线英文，禁止中文字段名 | classification_agent_spec §3/§4, scoring_pipeline_v2 |
| **classification_confidence is ENUM** | 只允许 `HIGH`/`MEDIUM`/`LOW`，禁止百分比 | classification_agent_spec §1/§4/§7, prompt_scoring_agent_v2 §2 |
| **pipeline_status lifecycle** | PROMOTED → FILTERED_BY_CATEGORY → FILTERED_BY_SCORE → ARCHIVED | classification_agent_spec §4.1, scoring_pipeline_v2 §14 |
| **project_id is mandatory** | 必须贯穿所有 Stage，永不修改 | classification_agent_spec §4.3, scoring_pipeline_v2 §15 |
| **Classification First** | Stage 3 完成分类后才允许评分；Stage 2 不含分类字段 | scoring_pipeline_v2 §5 |
| **No Cross-Stage Ownership** | 字段只能在其所属 Stage 产生 | classification_agent_spec §4.2, scoring_pipeline_v2 §3 |

### 2.2 Pipeline ↔ Schema 映射规则

Pipeline 10 个 Stage 与 Schema 6 个 Stage 的映射关系是 **4:N Composite**，不是冲突：

| Pipeline | Schema | 关系 |
|----------|--------|------|
| Stage 1 | Stage 1 (Raw) | 1:1 Direct |
| Stage 2 | Stage 2 (Normalized) | 1:1 Direct |
| Stage 3 | Stage 3 (Classification) | 1:1 Direct |
| Stage 4-7 (4 个独立分数) | Stage 4 (Scoring Output) | **4:N Composite** |
| Stage 8-9 (总分 + 推荐) | Stage 4 (Scoring Output) | **1:N Enriched** |
| Stage 10 | Stage 5 (Ranking) | 1:1 Direct |

Pipeline 的评分阶段（Stage 4-7）是更细粒度的过程分解，它们在实现层面最终合并为 Schema 的单一 Scoring Output Object。这不是结构冲突，而是不同的抽象层级。

### 2.3 Agent Bootstrap Protocol v1.0 的强制前提

每次 Agent 启动时必须执行：
1. 读取 `START_HERE.md`
2. 读取 `.clinerules`
3. 读取 `progress/<namespace>.md`
4. 查询 L2 图谱（Governor.get_active 或 search_nodes）
5. 生成 Bootstrap Summary 后方可开始实现工作

### 2.4 Completion Gate 规则（不可违反）

`attempt_completion` 前必须确认：
- L2 Review Complete
- L3 Review Complete
- Receipt Generated（如需）

任一未通过 = Gate OPEN，禁止 attempt_completion。

### 2.5 `attempt_completion` 格式

每次必须包含：
```
Memory Sync:
  L2: [updated|skipped] — [slots]
  L3: [updated|skipped] — [sections]
  Receipt: [generated|skipped]
  Gate: [CLOSED|OPEN]
```

---

## 3. L2 图谱最新状态与未同步节点

### 3.1 最新图谱查询结果

查询时间: 2026-06-23 20:30 JST (通过 `memory.read_graph`)

**PKIA 核心实体:**

| Entity | Type | Key Observations |
|--------|------|-----------------|
| `PKIA_Project` | Project | 个人知识智能体，构建于 Dify Platform，三层记忆系统 |
| `Dify_Platform` | Platform | 开源 LLM 应用开发平台，作为 PKIA 的底层实现平台 |
| `Dify_Backend` | Component | Python Flask，DDD 架构 |
| `Dify_Frontend` | Component | Next.js + TypeScript |
| `Three_Tier_Memory_System` | Architecture | L1 .clinerules / L2 cline-memory.json / L3 progress/ |
| `Memory_Bouncer_Script` | Script | 位于 `utils/memory_bouncer.py`，尚未创建 |

### 3.2 缺失的 L2 节点（需要但尚未写入图谱的实体）

以下实体已在文档体系中存在，但未写入 L2 图谱：

| 应新增 Entity | Type | 建议 Observations |
|---------------|------|-------------------|
| `PKIA_v0.1_PRD` | Document | 产品需求文档，定稿 2026-06-14，信息源 Arxiv + GitHub Trending |
| `Project_Data_Schema_v1` | Document | 6 阶段数据契约，2026-06-19 定稿 |
| `Scoring_Pipeline_Schema_v2` | Document | 评分流水线 v2，2026-06-23 创建 |
| `Classification_Taxonomy_v1` | Document | 11 个 Level-1, 32 个 Level-2 类别 |
| `Career_Goal_Profile` | Profile | 4 级职业目标（Agent App Engineer → AI Platform Engineer → LLM Inference → Multi-Agent） |
| `Interest_Tier_S` | Concept | S Tier: Agent, Agent Memory, Multi-Agent, AI Engineering, LLM Inference |
| `Interest_Tier_A` | Concept | A Tier: MCP, RAG, AI Infrastructure, LLMOps, Frontier AI |
| `Interest_Tier_B` | Concept | B Tier: Knowledge Graph, Distributed Systems |

### 3.3 应新增的 L2 关系

| From | To | Relation Type |
|------|----|---------------|
| `PKIA_Project` | `Project_Data_Schema_v1` | `HAS_DATA_CONTRACT` |
| `PKIA_Project` | `Scoring_Pipeline_Schema_v2` | `HAS_PIPELINE` |
| `PKIA_Project` | `Classification_Taxonomy_v1` | `USES_CLASSIFICATION` |
| `PKIA_Project` | `Career_Goal_Profile` | `HAS_CAREER_GOALS` |
| `Project_Data_Schema_v1` | `Scoring_Pipeline_Schema_v2` | `GOVERNS` |
| `Scoring_Pipeline_Schema_v2` | `report_generation_pipeline_v1.md` | `FEEDS_INTO` |

### 3.4 清理建议

- `MuKG_Project` 及相关实体（TransE, FB15k-237, Bottleneck_Phase1_IDMapping 等）属于遗留项目，可以考虑从活动 L2 视图中移除或标记为 ARCHIVED
- `Memory_Bouncer_Script` 节点标注为尚未创建，状态应更新

---

## 4. 关键决策日志

| 日期 | 决策 | 理由 |
|------|------|------|
| 2026-06-14 | PKIA v0.1 仅限 Arxiv + GitHub Trending 两个信息源 | PRD v0.1 约束 |
| 2026-06-14 | Career Alignment 评分采用 40/30/20/10/0 四级体系 | 职业目标权重差异化 |
| 2026-06-15 | S Tier 新增 LLM Inference / LLM Serving / Inference Optimization | 与职业目标 #3 对齐 |
| 2026-06-19 | `project_data_schema_v1.md` 成为唯一数据契约 | Single Source of Truth |
| 2026-06-20 | Confidence 统一为 `HIGH`/`MEDIUM`/`LOW` 枚举 | 消除百分比 vs 枚举冲突 |
| 2026-06-21 | `classification_agent_spec_v1.md` 完成 Schema 一致性补丁 | 6 项补丁，30→100/100 |
| 2026-06-21 | `prompt_scoring_agent_v2.md` 完成 Schema 一致性补丁 | 8 项补丁，30→100/100 |
| 2026-06-22 | `scoring_pipeline_schema_v1.md` 审查评分 20/100 | 10 个 P0 问题 |
| 2026-06-22 | 三层记忆系统 + Memory Governance 全链路部署完成 | Governor/持久化/Sync/Enforcement |
| 2026-06-23 | Bootstrap Protocol v1.1 发布（关闭 L1 命名空间歧义） | 替代 v1.0 |
| 2026-06-23 | `scoring_pipeline_schema_v2.md` 创建，替代 v1 | Schema 100% 合规 |

---

## 5. 当前文档体系索引

### PKIA 核心文档（23 份）

```
docs/
├── pkia-v01-prd.md                         — 产品需求文档
├── workflow_v0.1_design.md                 — Workflow 设计草稿
├── interest_profile_v1.md                  — 兴趣画像
├── scoring_strategy_v1.md                  — 评分策略
├── scoring_examples_v1.md                  — 评分案例 v1
├── scoring_examples_v1.1.md                — 评分案例 v1.1
├── project_classification_taxonomy_v1.md   — 分类体系
├── classification_agent_spec_v1.md         — 分类 Agent 规范 ✅ 已补丁
├── prompt_scoring_agent_v1.md              — 评分 Prompt v1（历史）
├── prompt_scoring_agent_v2.md              — 评分 Prompt v2 ✅ 已补丁
├── project_data_schema_v1.md               — 数据契约
├── data_collection_strategy_v1.md          — 数据采集策略
├── scoring_pipeline_schema_v1.md           — 评分流水线 v1（已存档）
├── scoring_pipeline_schema_v2.md           — 评分流水线 v2（活跃）
├── scoring_pipeline_patch_plan_v1.md       — 补丁计划
├── report_generation_pipeline_v1.md        — 报告生成流水线
├── daily_report_spec_v1.md                 — 日报规范
│
├── schema_consistency_patch_v1.md          — Schema 一致性补丁计划
├── review_project_data_schema_consistency.md  — Schema 创建前审查
├── review_classification_agent_patch_v1.md    — 分类 Agent 补丁审查
├── review_prompt_scoring_agent_v2_patch_v1.md — 评分 Prompt 补丁审查
├── review_scoring_pipeline_consistency_v1.md  — 评分流水线审查
│
└── migration_pkia_agent.md                 — 本文件（迁移上下文）
```

### 三层记忆系统文档

```
docs/
├── agent_bootstrap_protocol_v1.0.md         — Bootstrap 协议 v1.0
├── bootstrap_protocol_v1.1.md               — Bootstrap 协议 v1.1
├── bootstrap_v1.1_migration_report.md        — v1.1 迁移报告
├── agent_memory_integration_v1.0.md         — 记忆集成流程
├── l3_namespace_architecture_v1.0.md         — L3 命名空间架构
├── memory_boundary_v1.0.md                  — 记忆边界定义
├── memory_schema_v1.0.md                    — 记忆 Schema
├── memory_ontology_v1.1.md                  — 记忆本体论
├── memory_sync_protocol_v1.0.md             — 同步协议
├── memory_sync_enforcement_v1.0.md          — 强制执行规则
├── memory_sync_audit_v1.0.md                — 审计机制
├── memory_sync_receipt_template.md           — Receipt 模板
├── memory_governance_freeze_v1.0.md          — 冻结范围
│
├── persistence_strategy_report.md
├── persistence_implementation_report.md
├── governor_test_report.md
├── p0_verification_report.md
├── memory_refactor_report.md
├── memory_backend_cutover_report.md
├── memory_governance_deployment_report.md
├── memory_governance_deployment_audit.md
├── memory_governance_freeze_report.md
├── memory_governance_rule_block.md
├── governance_verification_scenario.md
├── mcp_capability_audit.md
├── memory_sync_gap_analysis.md
├── memory_sync_validation_report.md
├── memory_sync_audit_report.md
├── timestamp_extension_report.md
└── migration_memory_agent.md
```

---

## 6. 下一个 Agent 的启动指令

### Bootstrap 步骤

```bash
1. 读取 START_HERE.md
2. 读取 .clinerules
3. 确定命名空间（如果任务是 PKIA MVP 实现 → pkia_mvp；其他见 .clinerules §5.8）
4. 加载 progress/<namespace>.md
5. 查询 L2 图谱（use_mcp_tool memory → read_graph 或 search_nodes）
6. 读取 docs/migration_pkia_agent.md（本文件）
7. 生成 Bootstrap Summary
8. 开始实现工作
```

### 优先级建议

如果任务是继续 PKIA MVP 实现，建议按以下顺序：

1. **P0**: 完成 `report_generation_pipeline_v1.md` 的 Schema 一致性补丁
2. **P0**: 完成 `daily_report_spec_v1.md` 的 Career Goal Impact 展示补丁
3. **P1**: GitHub Trending 数据采集模块实现
4. **P1**: Dify Workflow 中集成 Classification Agent
5. **P1**: Dify Workflow 中集成 Scoring Agent (v2 Prompt)
6. **P1**: Daily Report 生成
7. **P1**: 兴趣标注系统

### 关键约束

- 禁止 `git push` 未经用户确认
- 禁止手动编辑 `cline-memory.json`
- 禁止 `print()` — 使用 `logger = logging.getLogger(__name__)`
- 禁止直接读取环境变量 — 通过 `configs.dify_config`
- 禁止使用 `Any` 类型
- Completion Gate 未关闭时禁止 `attempt_completion`

---

*End of Migration Context. Generated for cross-Agent continuity.*