# PKIA MVP Progress

> **Namespace**: pkia_mvp  
> **文件**: `progress/pkia_mvp.md`  
> **用途**: PKIA MVP 产品开发进度

---

## Current Phase
**Phase 0: 文档收尾 — 已完成**

P0 文档补丁全部完成，PKIA MVP v0.1 Baseline 已锁定。

---

## Active Tasks
- 等待 Phase 1 实现指令（GitHub Trending Collector 第一版）

---

## Completed Tasks

### Phase 0: 文档收尾（2026-06-24）

| 任务 | 状态 | 说明 |
|------|------|------|
| P0-1: report_generation_pipeline_v1.md Schema 补丁 | ✅ 完成 | 添加 `project_id`, `pipeline_status`, `career_goal_impact`；修复文档引用；Section B 展示添加职业目标影响字段；排序键添加 `project_id` 确定性键 |
| P0-2: daily_report_spec_v1.md Career Goal Impact 展示补丁 | ✅ 完成 | Section B 展示添加结构化职业目标影响；Section A 移除 Arxiv 统计行；移除所有 Arxiv 引用；添加 Ignore 统计行 |
| P0-3: scoring_pipeline_schema_v1.md 标记 DEPRECATED | ✅ 完成 | 添加 DEPRECATED 标志，指向 v2 作为替代 |
| P0-4: L2 图谱补充 PKIA 文档实体 | ✅ 完成 | 新增 9 个实体 + 8 条关系 |
| P0-5: L3 进度文件更新 | ✅ 完成 | 本文件 |
| **P0-6: pkia_v0.1_baseline.md 创建** | ✅ **完成** | Release Baseline，锁定实现范围（13 Frozen + 2 DEPRECATED） |

### 此前完成

- L2 Memory System 已就绪
- Governor MVP v0.1 已验证 (23/23 测试通过)
- 持久化层已部署
- Memory Sync 已部署
- PKIA 文档体系已完成（24 份文档）
- Schema 一致性审查全部通过

---

## Relevant L2 Memories

| Slot | Value |
|------|-------|
| `project:user_memory_file@global` | pkia-user-memory.json |
| `identity:verification_marker@global` | P0-B_Verification |

## Active Decisions

- **Three-Tier Memory System** (ACTIVE): L1 Constitution → L2 Knowledge Graph → L3 Progress
- **PKIA on Dify Platform** (ACTIVE): Dify Backend (Python Flask) + Dify Frontend (Next.js/React)
- **Memory Governance Frozen** (ACTIVE): Ontology, Schema, Governor, Persistence, Sync components frozen
- **Phase 1 实施路线** (ACTIVE): 1A-2B-3C-4A（先补文档 + Python 采集 + Dify Workflow 处理 + Markdown 日报 + GitHub Only）
- **PKIA v0.1 Baseline** (ACTIVE): 13 Frozen Documents, Success Criteria defined, Excluded Features documented

## Current Constraints

- Memory Governance Freeze
- PKIA v0.1 Baseline Frozen: 13 份核心文档禁止修改
- Dify 后端规范: Python Flask, DDD, SQLAlchemy, ruff linting
- Dify 前端规范: Next.js + TypeScript + React, pnpm
- 无用户确认禁止 git push

## Working Context

- **System State**: PKIA Phase 0 complete, Baseline locked, ready for Phase 1
- **Active Governance**: Memory Governance FROZEN + Baseline FROZEN
- **Key Architecture Decisions**:
  - Scoring Pipeline v2 → F4/F5
  - v0.1 实现范围: data_collection_strategy_v1.md (GitHub Only)
  - 实现载体: Python 脚本采集 + Dify Workflow 处理
  - 日报交付: Markdown (pkia/reports/YYYY-MM-DD.md)
- **Baseline 关键排除**: Arxiv, MCP Ecosystem, Memory Ecosystem, Multi-Source, Feedback Learning, Auto Prompt, Web UI, 实时推送, 多用户

## Blockers

- 等待用户指定 Phase 1 第一个实现目标

## Next Steps

Phase 1 建议按依赖链实施：

1. **GitHub Trending Collector** — Python 脚本，抓取 Top 30，生成 `project_id`
2. **Project Normalizer** — 清洗 description、提取 keywords
3. **Dify Workflow 骨架** — Stage 1→2→3 数据流
4. **Classification Agent** — Dify LLM Node
5. **Scoring Agent v2** — Dify LLM Node
6. **Daily Report 文本输出** — Markdown 格式

---

*最后更新: 2026-06-24 22:32 JST*