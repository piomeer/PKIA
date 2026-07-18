# Runtime

## 什么是 Runtime

Runtime 定义了一个项目中的 AI 代理如何运作。

本目录包含两个相互独立的 Runtime 层：

| 层级 | 描述 | 适用对象 |
|------|------|----------|
| **Agent Runtime** | 描述 AI 代理的工作生命周期：角色分工、规划、执行、验证、文档生命周期 | 所有项目（通用） |
| **PKIA Runtime** | 描述 PKIA 数据管道的运行时：Dify Workflow 节点映射、数据流、故障处理、部署 | PKIA 项目 |

## Agent Runtime vs PKIA Runtime

```
Agent Runtime (通用层)
    ↓
    描述 AI 代理的行为规范
    ↓
    适用于：Personal Wiki / PKIA / 未来所有 AI 项目
    ↓
    文件：docs/runtime/agent/

PKIA Runtime (项目层)
    ↓
    描述 PKIA 管道的技术实现
    ↓
    适用于：PKIA MVP v0.1
    ↓
    文件：docs/runtime/pkia/
```

## 阅读顺序

如果你是第一次接触 Runtime，请按以下顺序阅读：

**Step 1 — Agent Runtime（必读）**

```text
docs/runtime/agent/01_workflow.md                任务生命周期总览
        ↓
docs/runtime/agent/02_planning.md                OpenSpec 规划职责
        ↓
docs/runtime/agent/03_execution.md               Superpowers 执行职责
        ↓
docs/runtime/agent/04_context.md                 上下文加载策略
        ↓
docs/runtime/agent/05_review.md                  验证门禁
        ↓
docs/runtime/agent/06_development_constitution.md 不可变规则
        ↓
docs/runtime/agent/07_agent_roles.md             代理角色分工
        ↓
docs/runtime/agent/08_artifact_lifecycle.md      文档生命周期
```

**Step 2 — PKIA Runtime（按需阅读）**

```text
docs/runtime/pkia/runtime_architecture_overview_v1.md    拓扑总图与索引入口
        ↓
docs/runtime/pkia/runtime_boundary_v1.md                运行时职责边界
        ↓
docs/runtime/pkia/node_mapping_v1.md                    物理节点映射
        ↓
docs/runtime/pkia/data_flow_v1.md                       数据流
        ↓
docs/runtime/pkia/node_io_contract_v1.md                IO 契约
        ↓
docs/runtime/pkia/failure_handling_v1.md                故障处理
        ↓
docs/runtime/pkia/deployment_v1.md                      部署
```

## 文档树

```
docs/runtime/
├── README.md                               ← 本文件：Runtime 入口
│
├── agent/                                  ← Agent Runtime Layer
│   ├── 01_workflow.md                      ← 任务生命周期
│   ├── 02_planning.md                      ← 规划规范
│   ├── 03_execution.md                     ← 执行规范
│   ├── 04_context.md                       ← 上下文策略
│   ├── 05_review.md                        ← 验证门禁
│   ├── 06_development_constitution.md      ← 不可变规则
│   ├── 07_agent_roles.md                   ← 代理角色分工
│   └── 08_artifact_lifecycle.md            ← 文档生命周期
│
└── pkia/                                   ← PKIA Pipeline Runtime
    ├── runtime_architecture_overview_v1.md  ← 拓扑总图
    ├── runtime_boundary_v1.md               ← 运行时边界
    ├── node_mapping_v1.md                   ← 节点映射
    ├── data_flow_v1.md                      ← 数据流
    ├── node_io_contract_v1.md              ← IO 契约
    ├── failure_handling_v1.md               ← 故障处理
    ├── deployment_v1.md                     ← 部署
    ├── runtime_document_style_guide_v1.md   ← 写作规范
    └── runtime_glossary_v1.md               ← 术语表
```

## 给新成员

如果你是刚加入项目的新代理：

1. 先读 `docs/runtime/agent/01_workflow.md` — 理解一个任务如何走完完整生命周期
2. 按阅读顺序依次读完 Agent Runtime 其余文档
3. 如果涉及 PKIA 开发，再按需阅读 PKIA Runtime 文档
4. 如需了解项目全貌，返回 `AGENTS.md`
