# PKIA Deployment v1

> **Document Type**: Design Decision
> **Status**: Approved
> **Last Updated**: 2026-07
> **Namespace**: pkia_mvp

---

## 1. Purpose

本文档定义 PKIA MVP v0.1 运行时架构的**部署配置**。它描述了工作流如何被触发、在什么环境中运行、如何与外部系统对接，以及如何观测其运行状态。

本文档回答：

> **工作流如何部署、触发、配置和观测？**

---

## 2. Scope

### 2.1 In Scope

- 运行时执行时序（Runtime Sequence）
- 触发器配置（定时调度）
- 环境配置（Start Variables + Environment Variables）
- Storage Adapter 规范（API 端点、数据格式）
- Runtime Metrics（暂存于此，未来剥离）
- 正常流程日志（INFO 级别）

### 2.2 Out of Scope

- 异常处理与重试策略（参见 `failure_handling_v1.md`）
- 节点拓扑与映射（参见 `node_mapping_v1.md`）
- IO 数据契约（参见 `node_io_contract_v1.md`）

---

## 3. Design Principles

本文档继承 `runtime_boundary_v1.md` 的 P-01~P-06 原则。以下原则在部署层面有直接体现：

| Principle | Deployment 体现 |
|-----------|----------------|
| P-04 (Storage Adapter) | Node 7 通过 HTTP 解耦，Workflow 不感知存储后端 |
| P-03 (Workflow SSOT) | 部署配置在 Dify 导出的 `.yml` 中管理 |

---

## 4. Main Design

### 4.1 Runtime Sequence (执行时序)

一次完整的 PKIA Daily Run 按以下顺序执行：

```
时间轴
 │
 ├─ [00:00 UTC] Schedule Trigger
 │
 ├─ Node 1 (HTTP) ──── GitHub Trending 获取
 │   └─ 成功 → HTML 传递至 Node 2
 │   └─ 失败 → Retry (最多 3 次) → Fallback 至昨日数据
 │
 ├─ Node 2 (Code) ──── HTML 解析 + 字段规整
 │   └─ 产出: 30 个 RawProject 对象 (Array)
 │
 ├─ Node 3 (Iteration) ──── Batch 处理 (并发 30)
 │   ├─ Node 3-1 (LLM):  30 × Classification
 │   ├─ Node 3-2 (Code):  30 × Validation I
 │   ├─ Node 3-3 (LLM):  30 × Unified Scoring
 │   └─ Node 3-4 (Code):  30 × Calculation + Validation II
 │
 ├─ Node 4 (Aggregator) ──── 收拢存活项目
 │
 ├─ Node 5 (Code) ──── 全局排序 + 分组 + 排名
 │
 ├─ Node 6 (Template) ──── Markdown 渲染
 │
 ├─ Node 7 (HTTP) ──── 推送至 Storage Adapter
 │
 └─ [~00:15 UTC] Workflow Complete
     └─ 日报存储至 pkia/reports/YYYY-MM-DD.md
```

### 4.2 触发器配置

| 配置项 | 值 |
|--------|-----|
| 触发方式 | Dify Schedule Trigger (Cron) |
| 触发时间 | 每日 00:00 UTC |
| 失败处理 | 跳过当日执行，保留上次成功数据 |
| 重试当日 | 不重试。次日调度自动恢复。 |

### 4.3 环境配置

#### 4.3.1 Workflow Start Variables

| 变量名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `TOP_N` | integer | 30 | 每日采集项目上限 |
| `RECOMMEND_THRESHOLD_STRONG` | integer | 90 | Strong Recommend 下限 |
| `RECOMMEND_THRESHOLD_RECOMMEND` | integer | 70 | Recommend 下限 |
| `RECOMMEND_THRESHOLD_OBSERVE` | integer | 40 | Observe 下限 |
| `RETRY_MAX` | integer | 3 | HTTP 最大重试次数 |
| `GITHUB_TRENDING_URL` | string | `https://github.com/trending` | 采集目标 URL |
| `STORAGE_ADAPTER_URL` | string | `http://localhost:8000/report` | Storage Adapter 端点 |

#### 4.3.2 Environment Variables

| 变量名 | 示例值 | 说明 |
|--------|--------|------|
| `PKIA_REPORTS_DIR` | `/home/mahe/dify/pkia/reports` | 日报存储目录（Storage Adapter 使用） |
| `PKIA_LOG_LEVEL` | `INFO` | Python Adapter 日志级别 |
| `PKIA_TIMEZONE` | `Asia/Tokyo` | 日报日期使用的时区 |

### 4.4 Storage Adapter 规范

#### 4.4.1 架构

```
Dify Workflow          Storage Adapter               Filesystem
    │                       │                            │
    │  HTTP POST            │                            │
    │  /report              │                            │
    │  Body: Markdown text  │                            │
    │──────────────────────>│                            │
    │                       │  Write to file             │
    │                       │───────────────────────────>│
    │                       │                            │
    │  200 OK               │                            │
    │<──────────────────────│                            │
```

#### 4.4.2 API 端点

| 属性 | 值 |
|------|-----|
| Method | POST |
| Path | `/report` |
| Content-Type | `text/markdown` |
| Header | `X-Date: YYYY-MM-DD` |
| Body | Markdown 日报全文 |
| Success Response | `200 OK` |
| Failure Response | `500 Internal Server Error` |

#### 4.4.3 Adapter 职责

Storage Adapter（本地 Python FastAPI 服务）负责：

1. 接收 Workflow 推送的 Markdown 内容
2. 生成文件名为 `YYYY-MM-DD.md`
3. 写入 `PKIA_REPORTS_DIR` 目录
4. 返回 200 确认

Adapter 是 v0.1 Runtime 中唯一的 Python 组件。其存在不违反 P-02 (Python Minimal) —— Adapter 仅负责 I/O（写文件），不包含任何业务逻辑。

### 4.5 Runtime Metrics (运行时指标)

> **NOTE**: 此部分属于运行时可观测性 (Observability) 范畴，未来将剥离至独立的 `observability_v1.md` 文档中。

#### 4.5.1 指标定义

| 观测域 | 指标名 | 类型 | 来源节点 |
|--------|--------|------|----------|
| 采集健康度 | `projects_collected` | gauge (0~30) | Node 2 |
| 采集健康度 | `github_latency_ms` | histogram | Node 1 |
| 大模型消耗 | `classification_token_usage` | counter | Node 3-1 |
| 大模型消耗 | `scoring_token_usage` | counter | Node 3-3 |
| 大模型消耗 | `llm_latency_ms` | histogram | Node 3-1, 3-3 |
| 数据质量 | `validation_failed_count` | counter | Node 3-2, 3-4 |
| 数据质量 | `projects_dropped_count` | counter | Node 3-2, 3-4 |
| 产出统计 | `strong_recommend_count` | gauge | Node 5 |
| 产出统计 | `total_ranked_items` | gauge | Node 5 |

#### 4.5.2 采集方式

v0.1 通过结构化日志输出指标。各节点在关键边界输出 JSON 格式的指标行：

```
[METRIC] projects_collected=30 source=github_trending
[METRIC] classification_token_usage=45000 node=3-1
[METRIC] validation_failed_count=2 node=3-2
[METRIC] strong_recommend_count=3 node=5
```

未来 `observability_v1.md` 将定义指标的标准推送机制（如 Prometheus Pushgateway 或 OpenTelemetry）。

### 4.6 正常流程日志 (INFO Level)

以下日志反映正常执行流程，与 `failure_handling_v1.md` 的 WARNING/ERROR 级别互补。

| 节点 | 日志内容 | 触发时机 |
|------|----------|----------|
| Node 2 | `Top 30 projects extracted successfully.` | 解析完成 |
| Node 5 | `Ranking completed. X items ranked into A/B/C/D groups.` | 排序完成 |
| Node 7 | `Markdown output pushed to Storage Adapter. path=pkia/reports/YYYY-MM-DD.md` | 推送成功 |
| Workflow | `PKIA daily run completed. duration=Ns` | 全部流程结束 |

---

## 5. Runtime Rules

| Rule | Title | Application |
|------|-------|-------------|
| P-04 | Storage Adapter Pattern | Workflow 通过 HTTP POST 推送，不感知存储后端 (§4.4) |
| R-04 | Workflow SSOT | 部署配置在 Dify `.yml` 中管理；Start Variables 不硬编码 (§4.3) |

---

## 6. Related Documents

| Document | Relationship |
|----------|--------------|
| `runtime_boundary_v1.md` | 定义 Storage Adapter 与 Configuration 的归属决策。 |
| `failure_handling_v1.md` | 定义 WARNING/ERROR 级别日志。本文档的 INFO 日志与其互补。 |
| `node_mapping_v1.md` | 定义节点编号与类型。本文档的序列对应其映射。 |
| `data_collection_strategy_v1.md` | 定义采集策略（每日一次，Top 30）。本文档的触发器配置以此为依据。 |

---

## 7. Version History

| Version | Date | Author | Change Summary |
|---------|------|--------|----------------|
| v1 | 2026-07 | PKIA MVP Agent | Initial release. Runtime sequence, trigger config, environment variables, Storage Adapter spec, Metrics (with observability note), INFO logging. Refactored from `runtime_architecture_and_node_mapping_specification_v1.md`. |

---

## 7. Implementation Status

| 组件 | 状态 |
|------|------|
| Collector | ✅ Implemented |
| Dify Workflow Trigger | ✅ Implemented |
| Storage Adapter (接收端点) | ✅ Implemented |
| Launcher | ❌ Not Started (Cron scheduling pending Dify deployment) |
