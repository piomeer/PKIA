# Memory Boundary Definition v1.0

> **文档状态**: Architecture Freeze Document  
> **版本**: 1.0  
> **更新日期**: 2026-06-21  
> **用途**: 明确区分 Workspace Memory 与 User Memory 的职责边界

---

## 1. Workspace Memory Definition

**定义**: 存储项目开发过程中的架构决策、技术方案、项目历史和开发上下文。

**文件**: `cline-memory.json`

**保存内容**:

| 类别 | 示例 | 说明 |
|------|------|------|
| 架构决策 | Memory_Ontology, Schema_v1.0 | 系统架构的冻结规范 |
| 项目历史 | Development_History, Changelog | 开发过程中的里程碑和决策点 |
| 开发过程 | Governor_MVP, Test_Suite | 实现过程中的技术方案 |
| 技术方案 | Dify_Platform_Integration | 技术选型与集成方案 |
| Agent 行为记录 | Agent_Session_Log | Agent 运行的上下文和状态 |

**存储策略**:
- 文件作为 Schema v1.0 定义的完整 Memory_Node 存储
- 支持版本链 (SUPERSEDED_BY) 和冲突仲裁
- 文件是 Append-only JSON Lines，从文件重建索引
- 数据由 Governor 直接写入文件，MCP 仅作查询接口

**数据生产者**: Cline Agent（开发智能体）

**数据消费者**: Cline Agent（同一 workspace）

---

## 2. User Memory Definition

**定义**: 存储用户的长期个人记忆，包括身份、偏好、项目上下文、事实和决策。

**预留文件**: `pkia-user-memory.json`（尚未创建）

**保存内容**:

| 类别 | 示例 | 对应 Ontology Tier |
|------|------|-------------------|
| Identity | education, research_field, career_goal | Tier1 Identity |
| Preference | response_language, explanation_style | Tier2 Preference |
| Project | current_active_project, project_phase | Tier3 Project |
| Fact | learned_skills, completed_courses | Tier3 Project |
| Decision | architecture_choice, tool_selection | Tier3 Project |

**存储策略**（未来实现）:
- 复用 Schema v1.0 定义的 Memory_Node 模型
- 使用独立的 JSON Lines 文件隔离用户数据
- 支持 Workspace Memory 的完整能力（版本链、冲突仲裁、持久化）
- 通过命名空间 `workspace/*` 和 `user/*` 区分

**数据生产者**: 用户（通过对话界面）

**数据消费者**: PKIA Agent（所有 workspace）

---

## 3. 共享内容

以下内容允许在 Workspace Memory 和 User Memory 之间迁移：

| 内容 | 迁移方向 | 条件 |
|------|---------|------|
| 用户明确表达的偏好 | Workspace → User | 用户确认后迁移 |
| Agent 推断的偏好（已验证） | Workspace → User | confidence ≥ 0.9 后迁移 |
| 项目配置 | Workspace ↔ User | 双向同步 |
| 长期事实 | Workspace → User | 用户确认后迁移 |

**迁移触发条件**:
- 用户显式要求「记住这个」
- Agent 检测到同一 memory 被 reinforce 超过 3 次
- 架构决策被标记为「最终确定」

---

## 4. 禁止事项

### Workspace Memory 禁止

| 禁止项 | 说明 |
|--------|------|
| 存储用户长期身份信息 | 如真名、联系方式、教育背景 |
| 跨 workspace 携带用户偏好 | Workspace Memory 不跨 project 共享 |
| 存储敏感个人信息 | 如密码、API Key、私钥 |

### User Memory 禁止

| 禁止项 | 说明 |
|--------|------|
| 存储开发历史 | 如架构决策过程、Agent 调试日志 |
| 存储技术方案 | 如 Schema 版本、Governor 实现细节 |
| 存储 agent session 状态 | 如当前进度、任务上下文 |

---

## 5. 当前状态（v0.1）

当前仅实现了 **Workspace Memory**：

```
memory/
└── cline-memory.json        ✅ Workspace Memory（已实现）
└── pkia-user-memory.json    ❌ User Memory（预留，未创建）
```

**Architecture Decision**: 在当前 MVP 阶段，所有数据写入 `cline-memory.json`。User Memory 仅在架构层面预留，不实现。当需要分离时，workspace 相关的历史数据保留在 `cline-memory.json`，用户相关的记忆通过 Governor 迁移到 `pkia-user-memory.json`。

---

## 6. 后续迁移路线图

| 阶段 | 内容 | 时间 |
|------|------|------|
| v0.1 (当前) | 仅 Workspace Memory | ✅ |
| v0.2 | User Memory 文件创建 + Governor 多文件支持 | 待规划 |
| v0.3 | User Memory 数据迁移 | 待规划 |
| v0.4 | 跨 workspace User Memory 共享 | 待规划 |

---

> **文档结束**  
> 本规范定义了 Workspace Memory 与 User Memory 的职责边界，禁止事项和迁移策略。