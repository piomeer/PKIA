# PKIA Phase 1 Implementation Status

> **Namespace**: pkia_mvp
> **文件**: `progress/pkia_phase1_status.md`
> **用途**: 追踪 Phase 1 (Runtime 实现) 的端到端链路验证状态与遗留问题
> **文档状态**: Active — 不冻结，随实现进展更新

---

## 1. Phase 1 完成状态

**Phase 1 MVP 已完成：Collector → Dify Workflow 触发 → Storage 持久化链路已跑通。**

| 阶段 | 状态 | 说明 |
|------|------|------|
| 架构设计 | ✅ 完成 | 8 份 Runtime 文档已发布 (Approved) |
| 链路验证 | ✅ 完成 | 端到端链路已通过 EXP-010 验证 |
| Collector 实现 | ✅ 完成 | HTTP → Code Node 链路就绪 |
| Storage Adapter 基础功能 | ✅ 完成 | 基础接收与持久化已实现 |
| 遗留待办 | ⏳ 进行中 | 见 §2 |

---

## 2. 已知待解决问题

| 编号 | 原级别 | 当前级别 | 描述 | 状态 |
|------|--------|----------|------|------|
| P0-1 | P0 | ✅ 已解决 | Dify Workflow Pipeline 未实现 → 端到端链路已通过 EXP-010 验证 | 已关闭 |
| P0-2 | P0 | P1 | Storage Adapter 已实现基础接收与持久化，分析/查询能力待扩展 | 降级 |
| P1-1 | — | P1 | Classification + Scoring LLM Node Prompt 尚未部署到 Dify 实例 | 待办 |
| P1-2 | — | P2 | Ranking Code Node 未实现 (依赖 Aggregator 顺序确认) | 待办 |

---

## 3. 实验台账 (Experiment Ledger)

| 编号 | 名称 | 状态 | 备注 |
|------|------|------|------|
| EXP-001 | GitHub Trending HTML 解析可行性 | ✅ 成功 | Code Node 可稳定解析 Trending HTML 结构 |
| EXP-002 | Iteration 并发 30 项目压力测试 | ✅ 成功 | 单 Workflow 内 30 沙盒隔离有效 |
| EXP-003 | Variable Aggregator 顺序验证 | ⚠️ 有条件 | 确认 R-05: 不保证输入顺序, Ranker 需重排序 |
| EXP-004 | Classification Prompt 输出格式 | ✅ 成功 | JSON 输出满足 Validation Gate 断言 |
| EXP-005 | Scoring Prompt 四维评分一致性 | ✅ 成功 | 单次调用四维评分无内部矛盾 |
| EXP-006 | Validation Gate 断言拦截 | ✅ 成功 | 格式异常 LLM 输出正确拦截并触发 Drop |
| EXP-007 | Template Node Markdown 渲染 | ✅ 成功 | Jinja2 模板输出 6 章节完整日报 |
| EXP-008 | Storage Adapter HTTP 接收 | ✅ 成功 | FastAPI 端点正确接收并写文件 |
| EXP-009 | 采集失败 Fallback | ✅ 成功 | 昨日数据缓存正常加载 |
| EXP-010 | 端到端链路完整性 | ✅ 成功 | Collector → Workflow → Storage 全链路已验证通过 |

---

## 4. 风险跟踪

| 风险 | 级别 | 状态 |
|------|------|------|
| Dify Batch Processing 能力 | MEDIUM | 设计中已确认, 生产待验证 |
| LLM 输出可靠性 | HIGH | Validation Gate 已设计, 生产待部署 |
| Storage Adapter 扩展性 | LOW | 基础功能就绪, 分析能力待 P1 |

---

## 5. Related Documents

| Document | Relationship |
|----------|--------------|
| `pkia_v0.1_baseline.md` | 锁定 Phase 1 实现范围 (Frozen). 本文件跟踪其范围内实现的进展。 |
| `progress/pkia_mvp.md` | L3 核心进度文件。本文件是其 Phase 1 状态的详细补充。 |
| `docs/runtime/runtime_boundary_v1.md` | 定义 Runtime 职责划分。本文件跟踪其实现进展。 |
| `docs/runtime/deployment_v1.md` | 定义 Storage Adapter 规范。本文件跟踪其部署状态。 |
