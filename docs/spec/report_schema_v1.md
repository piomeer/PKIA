# PKIA Markdown Daily Report — Schema v1

> **Document Type**: Specification
> **Status**: Active
> **Last Updated**: 2026-07-18
> **Source Implementation**: `pkia_reporter/reporter.py`

---

## 1. Purpose

本文档定义 PKIA Markdown 日报的固定格式规范。所有日报生成逻辑（当前为 `pkia_reporter/reporter.py`）必须遵循此格式。

本文档是 Reporter 模块的单向约束源（Single Source of Truth）。代码修改前应先更新本文档，反之亦然。

---

## 2. Title Format

```
# PKIA Daily Report — YYYY-MM-DD
```

- 固定前缀：`# PKIA Daily Report — `
- 日期格式：`YYYY-MM-DD`（ISO 8601）
- 标题后空一行，接 `---` 分隔线

示例：

```markdown
# PKIA Daily Report — 2026-07-18

---
```

---

## 3. 采集概览 (Section A)

标题为 `## 采集概览`。内容为固定表头的表格，包含以下行：

| 行标签 | 值格式 | 示例 |
|--------|--------|------|
| 日期 | `YYYY-MM-DD` | 2026-07-18 |
| 数据源 | 字符串 | GitHub Trending |
| 项目总数 | 整数 | 22 |
| 总 Stars | 整数，千分位逗号 | 1,474,018 |
| 主要语言 | `语言名 数量` 逗号分隔，取前 5（当前实现取前 5） | Python 22, Unknown 1 |

**Markdown 输出**：

```markdown
## 采集概览

| 指标 | 值 |
|------|-----|
| 日期 | 2026-07-18 |
| 数据源 | GitHub Trending |
| 项目总数 | 22 |
| 总 Stars | 1,474,018 |
| 主要语言 | Python 22, Unknown 1 |
```

---

## 4. 项目列表 (Section B)

标题为 `## 项目列表`。列表有两种输出模式，由数据源是否包含 Workflow 分析结果决定。

### 4.1 模式一：无 Workflow 数据（Collector 原始数据）

当 JSONL 中不存在 `classification`、`total_score`、`recommendation` 任一字段时，使用此模式。

**表头**：

```
| # | 项目名 | 描述 | Stars | 语言 | URL |
|---|--------|------|-------|------|-----|
```

**列规则**：

| 列 | 数据来源 | 格式规则 |
|----|----------|----------|
| # | 序号 | 从 1 开始递增 |
| 项目名 | `project_name` | 原值 |
| 描述 | `description` | 截断至 60 字符，超出部分以 `...` 结尾 |
| Stars | `stars` | 整数，千分位逗号 |
| 语言 | `language` | 原值，空时为 `-` |
| URL | `repo_url` | 完整 URL |

**示例**：

```
| # | 项目名 | 描述 | Stars | 语言 | URL |
|---|--------|------|-------|------|-----|
| 1 | yt-dlp | A feature-rich command-line audio/video downloa... | 177,219 | Python | https://github.com/yt-dlp/yt-dlp |
| 2 | langflow | Langflow is a powerful tool for building and dep... | 151,634 | Python | https://github.com/langflow-ai/langflow |
```

### 4.2 模式二：有 Workflow 数据

当 JSONL 中任意记录包含 `classification`、`total_score`、`recommendation` 任一字段时，使用此模式。

**表头**：

```
| # | 项目名 | 分类 | 总分 | 推荐 | Stars | 语言 |
|---|--------|------|------|------|-------|------|
```

**列规则**：

| 列 | 数据来源 | 格式规则 |
|----|----------|----------|
| # | 序号 | 从 1 开始递增 |
| 项目名 | `project_name` | 原值 |
| 分类 | `classification.primary_category` | 字符串，不存在时显示 `-` |
| 总分 | `total_score` | 整数，不存在时显示 `-` |
| 推荐 | `recommendation` | 枚举值（STRONG_RECOMMEND / RECOMMEND / OBSERVE / IGNORE），不存在时显示 `-` |
| Stars | `stars` | 整数，千分位逗号 |
| 语言 | `language` | 原值，空时为 `-` |

---

## 5. 阅读建议 (Section C)

标题为 `## 阅读建议`。排序规则：

| 模式 | 排序键 | 取值 |
|------|--------|------|
| 无 Workflow 数据 | `stars` | 降序取前三 |
| 有 Workflow 数据 | `total_score` | 降序取前三 |

**输出格式**：

```markdown
### Priority #1: {项目名}

{完整描述，不截断}

[GitHub]({repo_url})
```

有 Workflow 数据时，标题行尾部追加：

```
### Priority #1: {项目名} | 总分: {score} | 推荐: {recommendation}
```

---

## 6. 空报告格式

当无项目数据时（`load_json` 返回空列表），生成以下空报告：

```markdown
# PKIA Daily Report — YYYY-MM-DD

---

## 采集概览

今日无采集数据。请检查数据源连接或重试 `python -m pkia_reporter`。
```

---

## 7. 脚注规则

当报告模式为"无 Workflow 数据"（§4.1）时，在全文末尾（Section C 之后）追加：

```markdown
---

> **注**：当前数据来自 Collector 原始输出，Workflow 分析阶段（分类、评分、推荐）尚未执行。待 Dify Workflow 部署完成后，报告将自动展示分析结果。
```

当报告模式为"有 Workflow 数据"（§4.2）时，不追加脚注。

---

## 8. 文件命名规则

```
reports/YYYY-MM-DD.md
```

- 输出目录：通过 `--output-dir` 参数或 `PKIA_REPORTS_DIR` 环境变量指定，默认 `reports/`
- 文件名：`YYYY-MM-DD.md`
- 编码：UTF-8

---

## 9. 与 Implementation 的对应关系

本 Schema 对应 `pkia_reporter/reporter.py` 中的以下函数：

| Schema 章节 | 实现函数 | 行号 |
|-------------|----------|------|
| §2 Title | `_a()` | 91 |
| §3 采集概览 | `_a()` | 95-103 |
| §4.1 无 WF 表格 | `_b()` (has_wf=False) | 114-116, 131-135 |
| §4.2 有 WF 表格 | `_b()` (has_wf=True) | 111-113, 125-130 |
| §5 阅读建议 | `_c()` | 140-165 |
| §6 空报告 | `_empty_report()` | 179-189 |
| §7 脚注 | `_d_note()` | 168-176 |

---

## 10. 设计说明

### 10.1 模式切换条件

模式切换由 `_has_workflow_data()` 决定。判断逻辑为：任意记录包含 `classification`、`total_score`、`recommendation` 三个键之一，即判定为"有 Workflow 数据"。

此判定在报告生成时一次性完成，不对单条记录做逐条模式切换。

### 10.2 可配置的参数

| 参数 | 默认值 | 位置 |
|------|--------|------|
| 排序取前十 | 3 | `_c()` 硬编码 |
| 描述截断长度 | 60 字符 | `_truncate()` 硬编码 |
| 主要语言 Top N | 5 | `_a()` 硬编码 |
| 数据源标签 | `GitHub Trending` | `generate_report()` 参数 |

### 10.3 输入数据来源

当前实现读取 `pkia_project/pkia_storage.jsonl`（JSONL 格式，每行一条记录，含 `project_data` 嵌套包装），或兼容的 JSON 数组格式（`latest_run.json`）。JSONL 的嵌套包装在 `_normalize()` 中展平。

---

## 11. Related Documents

| Document | Relationship |
|----------|--------------|
| `pkia_reporter/reporter.py` | 本 Schema 的参考实现 |
| `pkia_reporter/__main__.py` | CLI 入口，调用本 Schema 定义的生成函数 |
| `pkia_project/pkia_storage.jsonl` | 默认数据源 |
| `daily_report_spec_v1.md` | Frozen baseline 日报规范。本 Schema 是其可执行格式的具体实现。 |

---

## 12. Version History

| Version | Date | Author | Change Summary |
|---------|------|--------|----------------|
| v1 | 2026-07-18 | PKIA MVP Agent | Initial release. Defines title format, overview table, two-mode project table, reading suggestions, empty report, and footnote rules. Mirrors `pkia_reporter/reporter.py` v1. |
