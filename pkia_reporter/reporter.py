import os
import json
import logging
from datetime import date, datetime

logger = logging.getLogger("pkia.reporter")

DEFAULT_STORAGE = os.getenv(
    "PKIA_STORAGE_PATH",
    os.path.join(os.getcwd(), "pkia_project", "pkia_storage.jsonl"),
)

WORKFLOW_FIELDS = {"classification", "scores", "total_score", "recommendation"}


def load_json(source: str) -> list[dict]:
    if not os.path.exists(source):
        logger.error("Data file not found: %s", source)
        return []

    with open(source, "r", encoding="utf-8") as f:
        raw = f.read().strip()

    if raw.startswith("["):
        data = json.loads(raw)
    else:
        data = [json.loads(line) for line in raw.splitlines() if line.strip()]

    data = [_normalize(r) for r in data]
    logger.info("Loaded %d projects from %s", len(data), source)
    return data


def _normalize(record: dict) -> dict:
    """Flatten JSONL wrapper into a flat project object."""
    inner = record.pop("project_data", {})
    if isinstance(inner, dict):
        record = {**inner, **record}
    return record


def _has_workflow_data(projects: list[dict]) -> bool:
    return any(
        "classification" in p or "total_score" in p or "recommendation" in p
        for p in projects
    )


def generate_report(
    projects: list[dict],
    report_date: str | None = None,
    source_label: str = "GitHub Trending",
) -> str:
    if not projects:
        return _empty_report(report_date)

    dt = report_date or str(date.today())
    has_wf = _has_workflow_data(projects)

    lines: list[str] = []
    _a(lines, projects, dt, source_label)
    _b(lines, projects, has_wf)
    _c(lines, projects, has_wf)
    if not has_wf:
        _d_note(lines)
    lines.append("")
    return "\n".join(lines)


def write_report(content: str, output_dir: str, report_date: str | None = None) -> str:
    os.makedirs(output_dir, exist_ok=True)
    dt = report_date or str(date.today())
    path = os.path.join(output_dir, f"{dt}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info("Report written to %s (%d bytes)", path, len(content.encode("utf-8")))
    return path


def _a(lines: list[str], projects: list[dict], dt: str, source_label: str):
    stars_total = sum(p.get("stars", 0) for p in projects)
    top_langs: dict[str, int] = {}
    for p in projects:
        lang = p.get("language") or "Unknown"
        top_langs[lang] = top_langs.get(lang, 0) + 1
    lang_summary = ", ".join(
        f"{lang} {count}"
        for lang, count in sorted(top_langs.items(), key=lambda x: -x[1])[:5]
    )

    lines.append(f"# PKIA Daily Report — {dt}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 采集概览")
    lines.append("")
    lines.append(f"| 指标 | 值 |")
    lines.append(f"|------|-----|")
    lines.append(f"| 日期 | {dt} |")
    lines.append(f"| 数据源 | {source_label} |")
    lines.append(f"| 项目总数 | {len(projects)} |")
    lines.append(f"| 总 Stars | {stars_total:,} |")
    lines.append(f"| 主要语言 | {lang_summary} |")
    lines.append("")


def _b(lines: list[str], projects: list[dict], has_wf: bool):
    lines.append("## 项目列表")
    lines.append("")

    if has_wf:
        header = "| # | 项目名 | 分类 | 总分 | 推荐 | Stars | 语言 |"
        sep    = "|---|--------|------|------|------|-------|------|"
    else:
        header = "| # | 项目名 | 描述 | Stars | 语言 | URL |"
        sep    = "|---|--------|------|-------|------|-----|"

    lines.append(header)
    lines.append(sep)

    for i, p in enumerate(projects, 1):
        name = p.get("project_name", "?")
        lang = p.get("language") or "-"

        if has_wf:
            cat = p.get("classification", {}).get("primary_category", "-")
            ts = p.get("total_score", "-")
            rec = p.get("recommendation", "-")
            star_str = f"{p.get('stars', 0):,}"
            lines.append(f"| {i} | {name} | {cat} | {ts} | {rec} | {star_str} | {lang} |")
        else:
            desc = _truncate(p.get("description", ""), 60)
            url = p.get("repo_url", "")
            star_str = f"{p.get('stars', 0):,}"
            lines.append(f"| {i} | {name} | {desc} | {star_str} | {lang} | {url} |")

    lines.append("")


def _c(lines: list[str], projects: list[dict], has_wf: bool):
    lines.append("## 阅读建议")
    lines.append("")

    sort_key = "total_score" if has_wf else "stars"
    top3 = sorted(projects, key=lambda p: -(p.get(sort_key, 0) or 0))[:3]

    for rank, p in enumerate(top3, 1):
        name = p.get("project_name", "?")
        desc = p.get("description", "")

        if has_wf:
            rec = p.get("recommendation", "")
            extra = f" | 总分: {p.get('total_score', '?')} | 推荐: {rec}" if rec else ""
        else:
            extra = ""

        lines.append(f"### Priority #{rank}: {name}{extra}")
        lines.append("")
        lines.append(f"{desc}")
        lines.append("")

        repo_url = p.get("repo_url", "")
        if repo_url:
            lines.append(f"[GitHub]({repo_url})")
        lines.append("")


def _d_note(lines: list[str]):
    lines.append("---")
    lines.append("")
    lines.append(
        "> **注**：当前数据来自 Collector 原始输出，"
        "Workflow 分析阶段（分类、评分、推荐）尚未执行。"
        "待 Dify Workflow 部署完成后，报告将自动展示分析结果。"
    )
    lines.append("")


def _empty_report(report_date: str | None) -> str:
    dt = report_date or str(date.today())
    return f"""# PKIA Daily Report — {dt}

---

## 采集概览

今日无采集数据。请检查数据源连接或重试 `python -m pkia_reporter`。

"""


def _truncate(text: str, n: int) -> str:
    return text[:n] + "..." if len(text) > n else text
