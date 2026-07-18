# PKIA Runtime Boundary v1

> **Document Type**: Design Decision
> **Status**: Approved
> **Last Updated**: 2026-07
> **Namespace**: pkia_mvp

---

## 1. Purpose

This document defines the Runtime Boundary for the PKIA MVP v0.1 pipeline.

It answers exactly one question:

> **For each pipeline stage, which runtime component is responsible?**

The following concerns are owned by other Runtime documents and are not covered here:

- Node Mapping (node parameters, wiring) → `node_mapping_v1.md`
- Data Flow (variable passing, iteration strategy) → `data_flow_v1.md`
- IO Contract (input/output JSON schemas) → `node_io_contract_v1.md`
- Failure Handling (retry, fallback, degradation) → `failure_handling_v1.md`
- Deployment (scheduling, triggers, environment) → `deployment_v1.md`

---

## 2. Scope

### 2.1 In Scope

- Runtime component assignment for each pipeline stage (Stage 1–10 + Report + Storage)
- Architecture principles governing component selection
- Cross-cutting concerns (validation, configuration)
- HTML parsing verification item for the Collector stage

### 2.2 Out of Scope

- Business process definition (see `scoring_pipeline_schema_v2.md`, `report_generation_pipeline_v1.md`)
- Data structure definition (see `project_data_schema_v1.md`)
- Prompt content design (see `classification_agent_spec_v1.md`, `prompt_scoring_agent_v2.md`)
- Concrete node parameter configuration (see `node_mapping_v1.md`)

### 2.3 Baseline Constraints

Per `pkia_v0.1_baseline.md` (frozen):

- Single data source: GitHub Trending
- Linear pipeline: Collect → Normalize → Classify → Score → Rank → Output
- Daily frequency, Top 30 items
- Output: Markdown at `pkia/reports/YYYY-MM-DD.md`

---

## 3. Design Principles

### P-01: Dify First

A capability must be implemented using Dify built-in nodes unless proven infeasible. External code is the exception, not the default.

### P-02: Python Minimal

Python adapters exist only for I/O that Dify cannot perform (HTML parsing, external service communication). Python never contains business logic.

### P-03: Workflow SSOT

The Dify-exported `.yml` file is the single source of truth for workflow configuration (R-04). Orchestration logic — branching, iteration, retry, sequencing — lives in the Workflow, not in scripts.

### P-04: Storage Adapter Pattern

The Workflow delivers finalized content via HTTP POST. A Storage Adapter receives the payload and decides persistence strategy (Markdown file for v0.1). The Workflow never knows where data ends up.

### P-05: Fat Object

A single canonical Project Object accumulates fields as it passes through pipeline stages. Stages append or transform fields; no stage re-instantiates the object (R-02).

### P-06: Append-Only Mutation

Each stage adds fields owned by that stage. No stage modifies or removes fields owned by an earlier stage. Field ownership is defined by `project_data_schema_v1.md` §14.

---

## 4. Main Design

### 4.1 Boundary Overview

| Module | Pipeline Stage | Runtime Owner |
|--------|---------------|---------------|
| Collector | Stage 1 | HTTP Node → Code Node |
| Normalizer | Stage 2 | Code Node |
| Classification | Stage 3 | LLM Node |
| Classification Validation | Stage 3 | Code Node |
| Scoring | Stage 4–7 | LLM Node |
| Score Aggregation | Stage 8 | Code Node |
| Recommendation | Stage 9 | Code Node |
| Ranking | Stage 10 | Code Node |
| Report Rendering | Report | Template Node |
| Storage | Post-Report | HTTP → Storage Adapter |
| Validation | Cross-cutting | Code Node (after each LLM Node) |
| Retry | Cross-cutting | Workflow |
| Configuration | Cross-cutting | Start Variables / Environment Variables |

### 4.2 Collector (Stage 1)

**Responsibility**: Fetch GitHub Trending HTML, extract project metadata, generate `project_id`, output RawProject.

**Decision**: HTTP Node → Code Node.

The HTTP Node fetches the GitHub Trending page. The Code Node extracts structured fields (project_name, owner, description, topics, stars, forks, language) and generates `project_id` per `project_data_schema_v1.md` §4.1.

**Open Verification — HTML Parsing Strategy**: The only unresolved item is whether the Code Node's JavaScript runtime can reliably parse GitHub Trending's HTML structure. Two strategies are under evaluation:

| Strategy | Method | Condition |
|----------|--------|-----------|
| Code Node parsing | Regex/DOM within Dify Code Node | Adopted if parsing is stable |
| Python adapter | BeautifulSoup via external script | Used if Code Node parsing is unreliable |

This verification is the single remaining open item for the entire Runtime Boundary. Collector ownership is finalized; only the parsing method is pending.

**Output**: RawProject, matching `project_data_schema_v1.md` §5.

### 4.3 Normalizer (Stage 2)

**Responsibility**: Clean description (≤200 chars), normalize language, extract keywords (≤5, Topics-first).

**Decision**: Code Node.

Rationale: Pure deterministic transformation. No semantic understanding required.

**Output**: NormalizedProject, matching `project_data_schema_v1.md` §6.

### 4.4 Classification (Stage 3)

**Responsibility**: Assign primary_category, secondary_categories, classification_confidence, classification_notes.

**Decision**:

| Role | Owner |
|------|-------|
| Classification inference | LLM Node |
| Output validation | Code Node (immediately following) |

The LLM Node executes the classification prompt (`classification_agent_spec_v1.md`). The Validation Code Node enforces R-01 (Validation Isolation): checks JSON parse success, enum legality (HIGH/MEDIUM/LOW), taxonomy membership, and required field completeness.

Projects classified as Ignore categories (Frontend, Mobile, Blockchain, Crypto, NFT, Web3) receive `pipeline_status: FILTERED_BY_CATEGORY` and exit the pipeline before scoring per R-03 (Fail-Fast Iteration).

**Output**: ClassifiedProject, matching `project_data_schema_v1.md` §7.

### 4.5 Scoring (Stage 4–9)

**Responsibility**: Four-dimension scoring (Career Alignment, Interest Match, Trend Heat, Research Relevance), total_score calculation, recommendation assignment, career_goal_impact, reasoning.

**Decision**:

| Role | Owner |
|------|-------|
| Four-dimension scoring | LLM Node |
| `total_score` (sum of 4 dimensions) | Code Node |
| `recommendation` (threshold mapping) | Code Node |
| Output validation | Code Node |

The LLM Node executes `prompt_scoring_agent_v2.md`. The Code Node enforces `total_score = career_alignment + interest_match + trend_heat + research_relevance` and maps score to recommendation per thresholds: 90+ → STRONG_RECOMMEND, 70–89 → RECOMMEND, 40–69 → OBSERVE, 0–39 → IGNORE.

Projects scoring below 40 receive `pipeline_status: FILTERED_BY_SCORE` and exit before ranking.

**Output**: ScoredProject, matching `project_data_schema_v1.md` §8.

### 4.6 Ranking (Stage 10)

**Responsibility**: Sort all 30 scored projects into ranking groups and assign rank (1–30).

**Decision**: Code Node.

Sorting pipeline (per `scoring_pipeline_schema_v2.md` §13):
1. `ranking_group`: STRONG_RECOMMEND > RECOMMEND > OBSERVE > IGNORE
2. `total_score`: descending
3. `career_alignment`: descending
4. `interest_match`: descending
5. `project_id`: ascending (deterministic tiebreaker)

The Code Node receives a JSON array via Variable Aggregator. Because Variable Aggregator does not guarantee input order (R-05), the Code Node always performs a full sort and never assumes pre-ordered input.

**Output**: RankedProject, matching `project_data_schema_v1.md` §9.

### 4.7 Report Rendering

**Responsibility**: Render ranked projects as a 6-section Markdown daily report.

**Decision**: Template Node (Jinja2).

The Template Node renders the report matching `daily_report_spec_v1.md` §3 (Section A–F). It handles empty-result scenarios (no Strong Recommend items, all items Ignored, collection failure) per `report_generation_pipeline_v1.md` §10.

**Output**: `pkia/reports/YYYY-MM-DD.md`.

### 4.8 Storage

**Responsibility**: Persist the finalized daily report.

**Decision**: HTTP → Storage Adapter (P-04).

The Workflow sends the rendered Markdown content via HTTP POST. A Storage Adapter receives the payload and writes it to `pkia/reports/YYYY-MM-DD.md`. The Adapter encapsulates all persistence logic — the Workflow never knows the storage target.

For v0.1 the Adapter writes Markdown files. Future versions can add SQLite, OSS, or other backends without workflow modification.

### 4.9 Validation

**Responsibility**: Enforce output correctness after every LLM-dependent stage.

**Decision**: Code Node (R-01).

Every LLM Node output is routed through a Validation Code Node before reaching downstream logic. Validation covers: JSON parse, required field completeness, enum legality, field type correctness, field range checks.

### 4.10 Configuration

All tunable parameters are declared as Workflow Start Variables or Environment Variables. No hardcoded values in prompts or Code Node logic.

| Variable | Type | Default | Scope |
|----------|------|---------|-------|
| `TOP_N` | integer | 30 | Start Variable |
| `RECOMMEND_THRESHOLD_STRONG` | integer | 90 | Start Variable |
| `RECOMMEND_THRESHOLD_RECOMMEND` | integer | 70 | Start Variable |
| `RECOMMEND_THRESHOLD_OBSERVE` | integer | 40 | Start Variable |
| `COLLECTION_TIME` | string | "00:00 UTC" | Environment Variable |
| `RETRY_MAX` | integer | 3 | Start Variable |

---

## 5. Runtime Rules

This document follows the canonical Rule Registry in `runtime_document_style_guide_v1.md` §7.2. The following rules are applied:

| Rule | Title | Application |
|------|-------|-------------|
| R-01 | Validation Isolation | Code Node after every LLM Node (§4.4, §4.5, §4.9) |
| R-02 | Append-Only Object | Single canonical object through all stages (§3 P-05, P-06) |
| R-03 | Fail-Fast Iteration | FILTERED items exit before scoring/ranking (§4.4, §4.5) |
| R-05 | Aggregator Anarchy | Ranker never assumes input order; always full sort (§4.6) |

---

## 6. Related Documents

| Document | Relationship |
|----------|--------------|
| `runtime_document_style_guide_v1.md` | Defines the writing standard this document follows. Canonical Runtime Rule Registry. |
| `pkia_v0.1_baseline.md` | Frozen release baseline. Scope and constraints for all Runtime decisions. |
| `project_data_schema_v1.md` | Data contract. Defines field ownership and stage output structures referenced throughout §4. |
| `scoring_pipeline_schema_v2.md` | Defines 10-stage pipeline that this document assigns to runtime components. |
| `report_generation_pipeline_v1.md` | Defines 7-stage report generation. Report Rendering boundary follows its rules. |
| `daily_report_spec_v1.md` | Defines 6-section Markdown format. Template Node output target. |
| `data_collection_strategy_v1.md` | Defines Top 30, daily frequency, GitHub-only constraints for Collector. |
| `classification_agent_spec_v1.md` | Classification prompt. LLM Node input for §4.4. |
| `prompt_scoring_agent_v2.md` | Scoring prompt. LLM Node input for §4.5. |
| `Runtime Design v1.0.md` | Predecessor draft document. Superseded by this document. |

---

## 7. Version History

| Version | Date | Author | Change Summary |
|---------|------|--------|----------------|
| v1 | 2026-07 | PKIA MVP Agent | Initial release. Refactored from `Runtime Design v1.0.md`. Collector decision finalized (HTTP → Code Node). Principles consolidated to P-01–P-06. All open questions, future considerations, and discussion removed per style guide §9.2. |
