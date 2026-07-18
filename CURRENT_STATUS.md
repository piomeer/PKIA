# PKIA — Current Status

> **Last updated**: 2026-07-18
> **This file is the single source of truth for project status.**

| 项目 | 值 |
|------|-----|
| Version | 0.1.0 |
| Updated | 2026-07-18 |
| Status | MVP |
| Current Milestone | Reporter ✅ / Launcher ✅ / Workflow MVP ✅ / P0 收口进行中 |

---

## 当前版本

PKIA v0.1 MVP

---

## 已完成模块

- **Collector**（`pkia_collector/`）— GitHub Trending 采集，已验证，可从 30 个项目中提取标准化字段
- **Reporter**（`pkia_reporter/`）— Markdown 日报生成，支持 `--date`/`--storage`/`--output-dir` 参数
- **Dify Workflow 触发**（`pkia_collector/runner.py`）— 采集结果序列化为 JSON 后推送至 Dify API，已验证
- **Storage Adapter**（`pkia_project/storage_adapter.py`）— FastAPI 接收端点，`POST /report` 接收 Markdown 写入 `pkia/reports/`，`GET /health` 健康检查，已验证
- **Launcher**（`run.py`）— 统一启动入口，5 步串行流程：Docker 检查 → Dify API 检查 → Storage Adapter 启动 → Collector 运行 → Report 生成
- **Memory Governor MVP v0.1**（`pkia_memory/`）— 5 模块，1,424 行 Python，28+ 单元测试（`tests/test_governor.py`），已冻结
- **端到端链路**：运行 `python run.py` 即可完成 Collector → Dify → Report 全流程（EXP-010 验证通过）
- **Memory Bouncer 脚本**（`utils/memory_bouncer.py`）— 已创建并验证，但尚未挂接至 pre-completion hook

---

## 未完成模块

| 模块 | 状态 | 说明 |
|------|------|------|
| Dify Workflow 分析阶段 (Stage 2-10) | ❌ 未实现 | Normalization / Classification / Scoring / Ranking 全部在 Dify Workflow 中定义但尚未部署至 Dify 实例 |
| Memory Bouncer 集成 | ⏳ 脚本就绪 | pre-completion hook 未挂接 |
| Advisor / Trending Analysis | ❌ 未开始 | P2 里程碑内容 |
| CI/CD | ❌ 未开始 | 无自动化测试/部署流水线 |

---

## 当前最高优先级（P0）

1. **文档与代码状态对齐** — Handover 文档、Runtime 文档需反映当前代码实现状态
2. ~~统一启动入口（run.py）~~ — ✅ 已完成
3. ~~实现 Reporter（产品闭环）~~ — ✅ 已完成
4. **Dify Workflow 部署** — 将设计文档中的 Classification / Scoring / Ranking 逻辑部署到实际 Dify 实例

---

## 已知问题

| 问题 | 严重度 | 说明 |
|------|--------|------|
| `.env` 包含明文 API Key | 🔴 安全 | `DIFY_API_KEY=app-...` 硬编码在版本控制中 |
| Storage Adapter 与 Collector 数据格式不一致 | 🟡 兼容性 | JSONL 嵌套 `project_data` vs JSON 平铺。Reporter 当前读平铺格式 |
| 残存 MuKG 实体在 L2 记忆文件中 | 🟡 遗留 | 未确认是否清理 |
| 无自动回滚/重试机制 | 🟡 可靠性 | `run.py` 无失败重试流水线 |
| 无 CI/CD | 🟡 工程 | 无自动化测试/部署 |

---

## 下一里程碑

| 阶段 | 目标 | 状态 |
|------|------|------|
| P0 收口 | 文档对齐 + Dify Workflow 部署 | 进行中 |
| P1 工程质量 | 异常处理、结构化日志、重试、配置外置 | 未开始 |
| P2 智能能力 | Memory 集成、KG、RAG、趋势分析 | 未开始 |

---

## 关键文件路径

| 用途 | 路径 |
|------|------|
| 启动入口 | `run.py` |
| 采集模块 | `pkia_collector/` |
| 日报生成 | `pkia_reporter/` |
| 存储服务 | `pkia_project/storage_adapter.py` |
| 存储数据 (JSONL) | `pkia_project/pkia_storage.jsonl` |
| 最新采集 (JSON) | `latest_run.json` |
| Memory Governor | `pkia_memory/` |
| 设计基线 | `docs/pkia_v0.1_baseline.md` |
| Runtime 架构 | `docs/runtime/pkia/` |
| 宪法/红线 | `.clinerules`, `.opencode.md` |
| L3 进度追踪 | `progress/pkia_mvp.md`, `progress/pkia_phase1_status.md` |
