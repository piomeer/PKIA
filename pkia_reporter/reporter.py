import os
import json
import logging
from datetime import date, datetime

logger = logging.getLogger("pkia.reporter")


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

    logger.info("Loaded %d projects from %s", len(data), source)
    return data


def generate_report(
    projects: list[dict],
    report_date: str | None = None,
    source_label: str = "GitHub Trending",
) -> str:
    if not projects:
        return _empty_report(report_date)

    dt = report_date or projects[0].get("collection_time", "")[:10] or str(date.today())

    lines: list[str] = []
    _a(lines, projects, dt, source_label)
    _b(lines, projects)
    _c(lines, projects)
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


def _b(lines: list[str], projects: list[dict]):
    lines.append("## 项目列表")
    lines.append("")
    lines.append("| # | 项目名 | 描述 | Stars | 语言 | URL |")
    lines.append("|---|--------|------|-------|------|-----|")
    for i, p in enumerate(projects, 1):
        name = p.get("project_name", "?")
        desc = _truncate(p.get("description", ""), 60)
        stars = p.get("stars", 0)
        lang = p.get("language") or "-"
        url = p.get("repo_url", "")
        lines.append(f"| {i} | {name} | {desc} | {stars:,} | {lang} | {url} |")
    lines.append("")


def _c(lines: list[str], projects: list[dict]):
    lines.append("## 阅读建议")
    lines.append("")
    top3 = sorted(projects, key=lambda p: -p.get("stars", 0))[:3]
    for rank, p in enumerate(top3, 1):
        name = p.get("project_name", "?")
        desc = p.get("description", "")
        url = p.get("repo_url", "")
        lines.append(f"### Priority #{rank}: {name}")
        lines.append(f"")
        lines.append(f"{desc}")
        lines.append(f"")
        lines.append(f"[GitHub]({url})")
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
