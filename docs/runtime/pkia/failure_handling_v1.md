# PKIA Failure Handling v1

> **Document Type**: Design Decision
> **Status**: Approved
> **Last Updated**: 2026-07
> **Namespace**: pkia_mvp

---

## 1. Purpose

本文档定义 PKIA MVP v0.1 运行时架构中的**故障处理策略**。它仅关注失败场景：当系统无法正常执行预期路径时，应该做什么。

本文档回答：

> **故障发生时，系统如何响应？**

业务状态迁移（正常流转）由 `data_flow_v1.md` 负责，本文档不重复。

---

## 2. Scope

### 2.1 In Scope

- 故障分类体系：可恢复 vs 不可恢复
- Retry 策略：HTTP 重试、LLM 重试
- Timeout 策略：HTTP 超时、LLM 超时
- Drop 机制：项目级脱落（非阻断）
- Abort 机制：工作流级终止（阻断）
- Fallback 策略：降级行为
- 异常日志规范：WARNING / ERROR 级别

### 2.2 Out of Scope

- 正常业务状态迁移（参见 `data_flow_v1.md` §4.2）
- 正常流程日志（参见 `deployment_v1.md`）
- 节点职责边界（参见 `node_io_contract_v1.md`）

---

## 3. Design Principles

本文档继承 `runtime_boundary_v1.md` 的 P-01~P-06 原则。以下原则在故障处理层面有直接体现：

| Principle | Failure Handling 体现 |
|-----------|----------------------|
| P-02 (Python Minimal) | 故障恢复不依赖外部脚本；Workflow 内置 retry 机制 |
| P-03 (Workflow SSOT) | 重试策略在 Workflow 节点配置中声明，不在脚本中 |
| R-03 (Fail-Fast Iteration) | 单项目失败不阻断其他项目，但致命错误仍可 Abort |

---

## 4. Main Design

### 4.1 故障分类体系

故障按影响范围分为两级：

| 级别 | 标识 | 影响范围 | 处理方式 |
|------|------|----------|----------|
| **项目级 (Item Failure)** | FAILED / SKIPPED | 仅影响单个项目 | Drop — 项目脱落，同批次不受影响 |
| **工作流级 (Workflow Failure)** | ABORTED | 影响整个工作流 | Abort — 工作流终止，保留上次成功数据 |

### 4.2 项目级故障 (Item Failure)

#### 4.2.1 触发条件

| 故障类型 | 触发条件 | 状态值 |
|----------|----------|--------|
| Validation Fail | LLM 输出不符合 IO Contract （`node_io_contract_v1.md` §4.4） | SKIPPED |
| LLM Timeout | LLM Node 超时，未返回有效输出 | FAILED |
| LLM Internal Error | LLM 返回异常（如 content filter 拦截） | FAILED |

#### 4.2.2 Drop 机制

当项目级故障触发时：

```
1. Validation Gate / Error Handler 捕获异常
2. 记录结构化日志 (WARNING 级别)
3. 项目标记为对应状态 (SKIPPED 或 FAILED)
4. 项目不进入 Node 4 (Variable Aggregator)
5. 同批次其他 29 个项目继续执行
```

此机制确保 1/30 的失败不阻断剩余 29 个项目。

#### 4.2.3 项目级故障不重试

Item Failure 不触发重试。原因：

- LLM 输出失败后重试大概率产生相同结果（成本浪费）
- 30 个项目的样本量足够；丢失 1~2 个不影响日报质量
- Fail-fast 优于重试等待（符合 P-01 确定性原则）

### 4.3 工作流级故障 (Workflow Failure)

#### 4.3.1 触发条件

| 故障类型 | 触发条件 | 严重级别 |
|----------|----------|----------|
| HTTP Unreachable | Node 1 获取 GitHub Trending 返回 403/500 或连接超时 | ERROR — Abort |
| Storage Unreachable | Node 7 推送至 Storage Adapter 失败（连接拒绝） | ERROR — Abort |
| Workflow Config Error | Start Variables 缺失或类型不匹配 | ERROR — Abort |

#### 4.3.2 Abort 机制

当工作流级故障触发时：

```
1. 重试耗尽后仍失败
2. 记录致命日志 (ERROR 级别)
3. 工作流标记为 FAILED
4. 保留上次成功采集的数据作为降级结果
```

#### 4.3.3 Fallback 策略

| 故障场景 | Fallback |
|----------|----------|
| GitHub Trending 不可达 | 日报展示："数据采集失败，展示昨日数据"。使用上次成功采集的数据生成日报。 |
| Storage Adapter 不可达 | 保留 Markdown 内容在 Workflow 变量中，人工介入恢复。 |
| 全部 30 项目均为 Ignore | 日报仅含 Section A + "今日所有项目均不符合兴趣画像"。 |

### 4.4 Retry 策略

#### 4.4.1 HTTP Retry (Node 1, Node 7)

| 参数 | 值 |
|------|-----|
| 最大重试次数 | 3 (configurable via `RETRY_MAX`) |
| 重试间隔 | 5 秒 |
| 退避策略 | 固定间隔（v0.1），未引入指数退避 |
| 触发条件 | HTTP 状态码 ≥ 500 或 网络超时 |

#### 4.4.2 LLM Timeout

| 参数 | 值 |
|------|-----|
| 超时时间 | 60 秒（v0.1 建议值） |
| 超时处理 | 项目标记为 FAILED → Drop |
| 说明 | LLM 超时不重试（见 §4.2.3） |

#### 4.4.3 Retry 与 Idempotency

所有可重试操作（HTTP GET、LLM 推理）均为幂等。重试不会产生副作用。

### 4.5 Timeout 策略

| 组件 | 超时值 | 超时后果 |
|------|--------|----------|
| Node 1 HTTP 请求 | 30 秒 | 触发 HTTP Retry |
| Node 3-1 LLM 调用 | 60 秒 | 项目 FAILED → Drop |
| Node 3-3 LLM 调用 | 60 秒 | 项目 FAILED → Drop |
| Node 7 HTTP 请求 | 30 秒 | 触发 HTTP Retry |

### 4.6 异常日志规范

所有故障必须输出结构化日志。日志分为 WARNING（非致命）和 ERROR（致命）两个级别。

#### WARNING (非致命 — 项目级故障)

| 场景 | 日志内容 | 节点 |
|------|----------|------|
| Validation Gate 捕获格式异常 | `Project dropped. reason=JSON parse failed. project_id=<id>. confidence=LOW` | Node 3-2 / 3-4 |
| LLM 超时 | `Project dropped. reason=LLM timeout (60s). project_id=<id>.` | Node 3-1 / 3-3 |
| HTTP 重试触发 | `GitHub fetch retry triggered. attempt=N. node=Node1` | Node 1 |

格式规范：

```
<component>. <event>. <key=value>.
```

#### ERROR (致命 — 工作流级故障)

| 场景 | 日志内容 |
|------|----------|
| 数据源不可达 | `GitHub source unavailable. http_code=503. Workflow ABORTED. fallback=last_successful_data.` |
| 存储不可达 | `Storage Adapter unreachable. http_code=connection_refused. Workflow ABORTED. output_lost=true.` |
| 配置异常 | `Workflow configuration error. missing_variable=TOP_N. Workflow ABORTED.` |

---

## 5. Runtime Rules

| Rule | Title | Application |
|------|-------|-------------|
| R-01 | Validation Isolation | Validation Gate 捕获 LLM 输出格式异常，触发 Drop (§4.2) |
| R-03 | Fail-Fast Iteration | 项目级故障不阻断批次 (§4.2.2)；工作流级故障终止全部 (§4.3.2) |
| R-04 | Workflow SSOT | 重试配置在 Workflow 节点中声明，不在脚本中 (§4.4) |

---

## 6. Related Documents

| Document | Relationship |
|----------|--------------|
| `data_flow_v1.md` | 定义 Validation Gate 的断言逻辑。本文档定义断言失败后的处理策略。 |
| `node_io_contract_v1.md` | 定义契约违反的标准。本文档定义违反后的重试/Drop/Abort 行为。 |
| `node_mapping_v1.md` | 定义哪些节点参与故障处理。MD-01 Fail-Fast Isolation 是故障处理的上游决策。 |
| `deployment_v1.md` | 定义正常流程的 INFO 级别日志。本文档仅覆盖 WARNING 和 ERROR 级别。 |

---

## 7. Version History

| Version | Date | Author | Change Summary |
|---------|------|--------|----------------|
| v1 | 2026-07 | PKIA MVP Agent | Initial release. Fault classification, Drop mechanism, Abort mechanism, Retry/Timeout strategy, WARNING/ERROR logging. Refactored from `runtime_architecture_and_node_mapping_specification_v1.md`. |

---

## 7. Implementation Status

| 组件 | 状态 |
|------|------|
| Collector | ✅ Implemented |
| Dify Workflow Trigger | ✅ Implemented |
| Storage Adapter (接收端点) | ✅ Implemented |
| Normalization (Stage 2) | ❌ Not Started |
| Classification (Stage 3) | ❌ Not Started |
| 4-Dim Scoring (Stages 4-7) | ❌ Not Started |
| Total Score/Ranking (Stages 8-10) | ❌ Not Started |
| Reporter | ❌ Not Started |
| Launcher | ❌ Not Started |

Cross-cutting failure handling (Retry, Drop, Abort, Fallback) applies to all components but has not been deployed to Dify Workflow configuration. |
