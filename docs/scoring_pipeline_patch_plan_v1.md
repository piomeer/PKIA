# PKIA Scoring Pipeline Patch Plan v1

---

## §1 Purpose

This document is a **Patch Plan**. It defines exactly how to fix all inconsistencies identified in `docs/review_scoring_pipeline_consistency_v1.md` so that `docs/scoring_pipeline_schema_v1.md` becomes fully compliant with `docs/project_data_schema_v1.md`.

The workflow is:

```
Review (identify issues) → Patch Plan (define fixes) → Patch (apply fixes)
```

This is step 2 — the migration plan between audit and execution.

### Key Constraints

- **Not a redesign** — the 10-stage pipeline structure is preserved intact
- **Not a rewrite** — only targeted patches to fix specific inconsistencies
- **Not a new pipeline design** — the existing scoring philosophy, stage sequence, and process logic remain unchanged
- **Only patching** — mechanical, boundary, mapping, and lifecycle fixes to align with the Schema

---

## §2 Scope

### Included Documents

| Document | Role in Patch |
|----------|---------------|
| `scoring_pipeline_schema_v1.md` | Target document — receives all patches |
| `project_data_schema_v1.md` | Source of truth — provides correct field definitions, ownership boundaries, lifecycle rules |
| `classification_agent_spec_v1.md` | Reference — ensures Stage 3 classification output compatibility |
| `prompt_scoring_agent_v2.md` | Reference — ensures Stage 4-7 scoring output compatibility |

### Excluded Documents

- `interest_profile_v1.md` — not affected by data structure patches
- `project_classification_taxonomy_v1.md` — not affected by data structure patches
- `scoring_strategy_v1.md` — not affected by data structure patches
- `scoring_examples_v1.1.md` — not affected by data structure patches
- `daily_report_spec_v1.md` — separate patch scope (defined in schema_consistency_patch_v1.md)
- `report_generation_pipeline_v1.md` — separate patch scope

### Dependencies

| Patch | Depends On | Reason |
|-------|------------|--------|
| P0-3 Stage 2/3 Boundary | P0-5 (Stage 1 output) | Stage 2 inherits from Stage 1 |
| P0-6 Chinese field names | P0-3 (Stage 2/3 boundary) | Both affect Stage 2 output, should be patched together |
| §6 Schema Mapping | P0-9, P0-10 (scoring fields) | Mapping depends on knowing all scoring fields |
| §7 Data Lineage | P0-2 (project_id) | Lineage requires project_id defined first |
| §8 Pipeline Status | P0-1 (pipeline_status) | Lifecycle requires pipeline_status defined first |

---

## §3 Patch Strategy

### Mechanical Fixes

Fix field names, types, and format mismatches between Pipeline documentation and Schema definitions.

**Rules:**
- Replace all Chinese field names with snake_case English equivalents
- Replace "Repo Name" with `project_name`
- Replace "Secondary Tags" with `secondary_categories`
- Ensure all enum values are uppercase (`HIGH`/`MEDIUM`/`LOW`, `STRONG_RECOMMEND`/`RECOMMEND`/`OBSERVE`/`IGNORE`)
- Ensure all field names use exactly the same spelling as the Schema

### Boundary Fixes

Fix stage boundary violations where fields appear in the wrong stage.

**Rules:**
- Stage 2 (Normalization) must not contain any classification fields
- Remove "项目领域" from Stage 2 — it belongs to Stage 3
- Replace "核心能力" with Schema-defined `extracted_keywords`
- Stage 1 (Raw) must not contain any scoring fields — verify compliance with Schema §5.3 forbidden field list

### Mapping Fixes

Add mapping notes where Pipeline structure differs intentionally from Schema structure.

**Rules:**
- Pipeline Stage 4-7 produce individual scores → Schema Stage 4 bundles all scores
- Add a mapping table in §6 explaining this is a 1:N relationship, not a conflict
- Pipeline Stage 8 (Total Score) → Schema Stage 4 field `total_score`
- Pipeline Stage 9 (Recommendation) → Schema Stage 4 field `recommendation`
- Pipeline Stage 10 (Ranking) → Schema Stage 5 (Ranking Output)

### Lifecycle Fixes

Add missing lifecycle fields and rules.

**Rules:**
- Add `pipeline_status` to all 10 stages with initial value and transition rules
- Add `project_id` to all 10 stages as a mandatory global identity field
- Define status transition points: PROMOTED → FILTERED_BY_CATEGORY → FILTERED_BY_SCORE → ARCHIVED
- Define which stages modify status and which stages only consume it

---

## §4 P0 Critical Fixes

### P0-1: `pipeline_status` absent

**Problem:** `pipeline_status` is not mentioned anywhere in the 10-stage pipeline. No mechanism exists to track which projects are active, filtered, or archived.

**Schema Decision:** `project_data_schema_v1.md` §11 defines `pipeline_status` as a global field present from Stage 1. Allowed values: `PROMOTED`, `FILTERED_BY_CATEGORY`, `FILTERED_BY_SCORE`, `ARCHIVED`.

**Patch Action:**
1. Add `pipeline_status: PROMOTED` to Stage 1 output (initial value)
2. Add note to Stage 3: after classification, set `FILTERED_BY_CATEGORY` for non-AI projects (Ignore list categories)
3. Add note to Stage 4-7: after scoring, set `FILTERED_BY_SCORE` for IGNORE projects
4. Add note to Stage 10: after ranking, set `ARCHIVED` for completed projects
5. Add `pipeline_status` to the output of every stage

**Expected Result:** All 10 stages have `pipeline_status` defined with clear transition rules. No silent data loss.

**Affected Sections:** §3, §5, §6, §7, §8, §9, §10, §11, §12

---

### P0-2: `project_id` absent

**Problem:** `project_id` is not mentioned in any stage. Without it, there is no way to trace a project from raw data to Daily Report.

**Schema Decision:** `project_data_schema_v1.md` §4.1 defines `project_id` as a mandatory global identity field, generated in Stage 1 and preserved unchanged through all stages.

**Patch Action:**
1. Add `project_id` to Stage 1 output as first field
2. Add `project_id` (inherited) to every subsequent stage's output definition
3. Add a rule: "project_id must not be modified by any stage"
4. Reference Schema §12 (Data Lineage Rules)

**Expected Result:** `project_id` appears in all 10 stages. A project can be traced end-to-end.

**Affected Sections:** §3-§12 (all stages)

---

### P0-3: Stage 2/3 Boundary — "项目领域"

**Problem:** Stage 2 output contains "项目领域" which is a classification concept. The pipeline document itself admits it belongs to Stage 3.

**Schema Decision:** `project_data_schema_v1.md` §6.4 states: "Stage 2 不产生任何与分类相关的字段". Classification fields belong to Stage 3 (§7).

**Patch Action:**
1. Remove "项目领域" from Stage 2 output table
2. Replace with `extracted_keywords` (defined in Schema §6.2)
3. Add a note to Stage 3 clarifying that category assignment is the Classification Agent's responsibility

**Expected Result:** Stage 2 contains no classification fields. The boundary between Normalization and Classification is clear.

**Affected Sections:** §4 (Stage 2), §5 (Stage 3)

---

### P0-4: "核心能力" → `extracted_keywords`

**Problem:** Stage 2 output has "核心能力" which is an invented field not present in the Schema. Its definition ("Description 提炼") has no structured constraint.

**Schema Decision:** `project_data_schema_v1.md` §6.2 defines `extracted_keywords` as a list of strings (max 5), extracted from Description and Topics.

**Patch Action:**
1. Replace "核心能力" with `extracted_keywords` (list[string], max 5)
2. Update field description to match Schema §6.3: "从 Description 和 Topics 中提取的核心关键词"

**Expected Result:** Stage 2 output contains Schema-defined `extracted_keywords` instead of the ambiguous "核心能力".

**Affected Sections:** §4 (Stage 2)

---

### P0-5: Missing Raw Project Fields

**Problem:** Stage 1 output defines only 4 fields (Repo Name, Description, Stars, Topics). Schema requires 11 fields.

**Schema Decision:** `project_data_schema_v1.md` §5.2 defines 11 fields for Stage 1: `project_id`, `project_name`, `owner`, `description`, `topics`, `stars`, `forks`, `language`, `source`, `collection_date`, `pipeline_status`.

**Patch Action:**
1. Replace the current 4-field list with Schema's complete 11-field list
2. Add the Schema's "禁止字段" list (§5.3) as a note

**Expected Result:** Stage 1 output definition matches Schema §5.2 exactly.

**Affected Sections:** §3 (Stage 1)

---

### P0-6: Chinese Field Names

**Problem:** Stage 2 output uses Chinese field names: 项目名称, 一句话描述, 核心能力, 项目标签, 项目领域

**Schema Decision:** `project_data_schema_v1.md` §3.1 requires all field names in snake_case English. Chinese field names are prohibited.

**Patch Action:**
Replace all Chinese field names:

| Chinese (Current) | English snake_case (Target) |
|-------------------|---------------------------|
| 项目名称 | `project_name` (inherited) |
| 一句话描述 | `normalized_description` |
| 核心能力 | `extracted_keywords` |
| 项目标签 | `topics` (inherited) |
| 项目领域 | (removed — belongs to Stage 3) |

**Expected Result:** Stage 2 output uses English snake_case field names matching Schema §6.2.

**Affected Sections:** §4 (Stage 2)

---

### P0-7: "Repo Name" → `project_name`

**Problem:** Stage 1 output uses "Repo Name" which is explicitly prohibited by Schema §3.2.

**Schema Decision:** `project_data_schema_v1.md` §3.2: `project_name` is the official field name. Variants like `repo_name`, `repository_name`, `name`, `projectName` are forbidden.

**Patch Action:**
1. Replace "Repo Name" with `project_name` in Stage 1 output list
2. Add a note: "project_name is the official identifier used across all PKIA documents"

**Expected Result:** Stage 1 uses `project_name` instead of "Repo Name".

**Affected Sections:** §3 (Stage 1)

---

### P0-8: Missing `classification_confidence`

**Problem:** Stage 3 output defines only "Primary Category" and "Secondary Tags". Schema requires `primary_category`, `secondary_categories`, `classification_confidence`, `classification_notes`.

**Schema Decision:** `project_data_schema_v1.md` §7.2 defines 4 required fields. `classification_confidence` uses `HIGH`/`MEDIUM`/`LOW` ENUM.

**Patch Action:**
1. Add `classification_confidence` (ENUM: `HIGH`/`MEDIUM`/`LOW`) to Stage 3 output
2. Add `classification_notes` to Stage 3 output
3. Rename "Primary Category" to `primary_category`
4. Rename "Secondary Tags" to `secondary_categories`
5. Add `pipeline_status` with option to set `FILTERED_BY_CATEGORY`

**Expected Result:** Stage 3 output matches Schema §7.2 and `classification_agent_spec_v1.md` §4.

**Affected Sections:** §5 (Stage 3)

---

### P0-9: Missing `reasoning`

**Problem:** `reasoning` is mentioned in §13 as a required principle but is not included as an output field in any stage.

**Schema Decision:** `project_data_schema_v1.md` §8.2 requires `reasoning` as a mandatory field in Stage 4 (Scoring Output).

**Patch Action:**
1. Add `reasoning` (string) to the output definition of Stage 8 (Total Score Calculation)
2. The `reasoning` field is produced by the Scoring Agent and consumed by the Report Generation Pipeline
3. Reference `prompt_scoring_agent_v2.md` §12 which includes `reasoning` in the output format

**Expected Result:** `reasoning` is an explicit output field of the scoring pipeline.

**Affected Sections:** §10 (Stage 8), §13 (principles reference)

---

### P0-10: Missing `career_goal_impact`

**Problem:** `career_goal_impact` is not mentioned anywhere in the pipeline. Schema requires it as a mandatory field.

**Schema Decision:** `project_data_schema_v1.md` §8.2-8.3 defines `career_goal_impact` as a required object with 4 sub-fields (`agent_application_engineer`, `ai_platform_engineer`, `llm_inference_optimization_engineer`, `multi_agent_system_engineer`).

**Patch Action:**
1. Add `career_goal_impact` (object with 4 enum sub-fields) to Stage 8 (Total Score Calculation) output
2. Add a note explaining the sub-field structure references Schema §8.3
3. Reference `prompt_scoring_agent_v2.md` §12 which includes Career Goal Impact in the output format

**Affected Sections:** §10 (Stage 8)

---

## §5 Stage-by-Stage Patch Plan

### Stage 1: Data Collection

| Aspect | Current State | Required Change |
|--------|---------------|-----------------|
| Output fields | Repo Name, Description, Stars, Topics | `project_id`, `project_name`, `owner`, `description`, `topics`, `stars`, `forks`, `language`, `source`, `collection_date`, `pipeline_status` |
| Field naming | "Repo Name" | `project_name` |
| `project_id` | Absent | Add as first output field |
| `pipeline_status` | Absent | Add with initial value `PROMOTED` |
| Missing fields | owner, forks, language, source, collection_date | Add all 5 |

**Schema References:** §5.2 (fields), §5.3 (forbidden fields), §4.1 (project_id), §11 (pipeline_status)
**Risk Level:** HIGH — Stage 1 is the entry point. Incorrect fields affect every downstream stage.

---

### Stage 2: Project Normalization

| Aspect | Current State | Required Change |
|--------|---------------|-----------------|
| Output fields | 项目名称, 一句话描述, 核心能力, 项目标签, 项目领域 | Inherit Stage 1 + `normalized_description`, `primary_language`, `extracted_keywords` |
| Field naming | Chinese | snake_case English |
| 项目领域 | Contains classification concept | Remove entirely |
| 核心能力 | Not in Schema | Replace with `extracted_keywords` |

**Schema References:** §6.2 (fields), §6.4 (no classification fields), §3.1 (naming rules)
**Risk Level:** HIGH — Stage 2 boundary violation is the most critical structural issue.

---

### Stage 3: Category Classification

| Aspect | Current State | Required Change |
|--------|---------------|-----------------|
| Output fields | Primary Category, Secondary Tags | `primary_category`, `secondary_categories`, `classification_confidence`, `classification_notes`, `pipeline_status` |
| Primary Category | Title case | `primary_category` (snake_case) |
| Secondary Tags | Not snake_case | `secondary_categories` |
| classification_confidence | Absent | Add ENUM: `HIGH`/`MEDIUM`/`LOW` |
| classification_notes | Absent | Add |
| pipeline_status | Absent | Add, with note about `FILTERED_BY_CATEGORY` |

**Schema References:** §7.2 (fields), §7.3 (confidence rules)
**Reference Documents:** `classification_agent_spec_v1.md` §4, `prompt_scoring_agent_v2.md` §2
**Risk Level:** HIGH — Missing confidence and notes affect Scoring Agent's ability to interpret classification quality.

---

### Stage 4-7: Scoring Stages

| Stage | Current State | Required Change |
|-------|---------------|-----------------|
| Stage 4 (Career Alignment) | Output: 0~40 score only | No structural change; add `pipeline_status` reference |
| Stage 5 (Interest Match) | Output: 0~30 score only | No structural change; add `pipeline_status` reference |
| Stage 6 (Trend Heat) | Output: 0~20 score only | No structural change; add `pipeline_status` reference |
| Stage 7 (Research Relevance) | Output: 0~10 score only | No structural change; add `pipeline_status` reference |

**Key Decision:** These 4 stages remain as independent stages producing individual scores. The Schema mapping (§6) explains how they collectively produce the Schema Stage 4 output.

**Risk Level:** LOW — No structural changes required. Only add `pipeline_status` notes.

---

### Stage 8: Total Score Calculation

| Aspect | Current State | Required Change |
|--------|---------------|-----------------|
| Output fields | Total Score: 0~100 | Add `reasoning` and `career_goal_impact` |
| `reasoning` | Absent | Add as required output field |
| `career_goal_impact` | Absent | Add with 4 sub-fields |

**Schema References:** §8.2 (all scoring fields), §8.3 (career_goal_impact sub-fields)
**Affected Sections:** §10 (Stage 8)
**Risk Level:** MEDIUM — Missing fields affect downstream Report Generation.

---

### Stage 9: Recommendation Assignment

| Aspect | Current State | Required Change |
|--------|---------------|-----------------|
| Output | Recommendation level | Add `pipeline_status: FILTERED_BY_SCORE` note for IGNORE projects |

**Schema References:** §8.4 (recommendation enum values)
**Risk Level:** LOW — Only add lifecycle note.

---

### Stage 10: Daily Report Ranking

| Aspect | Current State | Required Change |
|--------|---------------|-----------------|
| Output | "排序后的项目列表，按推荐等级分组" | Add `rank` (integer 1~30) and `ranking_group` (enum: STRONG_RECOMMEND/RECOMMEND/OBSERVE/IGNORE) |
| Batch/Item distinction | Implicit | Make explicit: "This stage is Batch Processing" |

**Schema References:** §9.2 (rank and ranking_group), §13 (batch vs item processing)
**Risk Level:** MEDIUM — Missing structured output fields.

---

## §6 Schema Mapping Rules

### Pipeline Stages to Schema Stages

The Pipeline has 10 stages. The Schema has 6 stages. The mapping is:

| Pipeline Stage | Pipeline Output | Schema Stage | Schema Fields | Relationship |
|----------------|----------------|--------------|---------------|--------------|
| 1. Data Collection | Raw project list | Stage 1 (Raw) | project_id, project_name, ... | 1:1 Direct |
| 2. Normalization | Normalized project | Stage 2 (Normalized) | normalized_description, ... | 1:1 Direct |
| 3. Classification | Primary Category + Tags | Stage 3 (Classification) | primary_category, ... | 1:1 Direct |
| 4. Career Alignment | 0~40 score | Stage 4 (Scoring) | career_alignment | 4:N Composite |
| 5. Interest Match | 0~30 score | Stage 4 (Scoring) | interest_match | 4:N Composite |
| 6. Trend Heat | 0~20 score | Stage 4 (Scoring) | trend_heat | 4:N Composite |
| 7. Research Relevance | 0~10 score | Stage 4 (Scoring) | research_relevance | 4:N Composite |
| 8. Total Score | 0~100 + reasoning | Stage 4 (Scoring) | total_score, reasoning, recommendation | 1:N Enriched |
| 9. Recommendation | STRONG_RECOMMEND... | Stage 4 (Scoring) | recommendation | 1:1 Direct |
| 10. Ranking | Ranked list | Stage 5 (Ranking) | rank, ranking_group | 1:1 Direct |

**Key Insight:** Pipeline Stage 4-7 are **scoring sub-steps** that collectively produce the Schema Stage 4 output. This is not a conflict — the Pipeline provides finer-grained process documentation. The mapping table clarifies the relationship.

### Mapping Rule

Pipeline Stage 4 + 5 + 6 + 7 + 8 + 9 → Schema Stage 4 (Scoring Output Object)

The Scoring Output Object contains:
- `career_alignment` (produced by Pipeline Stage 4)
- `interest_match` (produced by Pipeline Stage 5)
- `trend_heat` (produced by Pipeline Stage 6)
- `research_relevance` (produced by Pipeline Stage 7)
- `total_score` (produced by Pipeline Stage 8)
- `reasoning` (produced by Pipeline Stage 8)
- `recommendation` (produced by Pipeline Stage 9)
- `career_goal_impact` (produced by Pipeline Stage 8)

---

## §7 Data Lineage Integration

### `project_id` Flow

```
Stage 1 (Data Collection)
  └── project_id generated (based on collection_date + source + project_name)
        ↓
Stage 2 (Normalization)
  └── project_id inherited (unchanged)
        ↓
Stage 3 (Classification)
  └── project_id inherited (unchanged)
        ↓
Stage 4-7 (Scoring)
  └── project_id inherited (unchanged)
        ↓
Stage 8 (Total Score)
  └── project_id inherited (unchanged)
        ↓
Stage 9 (Recommendation)
  └── project_id inherited (unchanged)
        ↓
Stage 10 (Ranking)
  └── project_id inherited (unchanged)
        ↓
Report Generation
  └── project_id inherited (unchanged)
```

### Lineage Rules to Add

1. `project_id` is generated in Stage 1 and must never be modified
2. Every stage's output must include `project_id` as a mandatory field
3. If a stage encounters a project without `project_id`, it must fail (do not generate a new one)
4. The `project_id` value must remain identical across all 10 stages for the same project

### Reference

`project_data_schema_v1.md` §12 (Data Lineage Rules) provides the definitive lineage path.

---

## §8 Pipeline Status Lifecycle

### Status Transition Flow

```
Stage 1:  pipeline_status = PROMOTED (initial)
  │
  ▼
Stage 3:  Classification decides
  ├── AI-related project → PROMOTED (continue to scoring)
  └── Non-AI project (Ignore list) → FILTERED_BY_CATEGORY (terminate)
          │
          ▼
        ARCHIVED
  │
  ▼
Stage 8:  Total Score decides
  ├── Score ≥ 40 → PROMOTED (continue to ranking/report)
  └── Score < 40 (IGNORE) → FILTERED_BY_SCORE (terminate)
          │
          ▼
        ARCHIVED
  │
  ▼
Stage 10: After ranking → ARCHIVED (all projects)
```

### Stage Ownership of `pipeline_status`

| Stage | Can Set Status | Can Only Read Status | Status Values |
|-------|---------------|---------------------|---------------|
| 1 | ✅ Initialize | — | `PROMOTED` |
| 2 | ❌ | ✅ Read | Inherits from Stage 1 |
| 3 | ✅ Update | ✅ Read | `PROMOTED` or `FILTERED_BY_CATEGORY` |
| 4-7 | ❌ | ✅ Read | Inherits from Stage 3 |
| 8 | ✅ Update | ✅ Read | `PROMOTED` or `FILTERED_BY_SCORE` |
| 9 | ❌ | ✅ Read | Inherits from Stage 8 |
| 10 | ✅ Update | ✅ Read | Set `ARCHIVED` on completion |

**No Silent Data Loss:** Projects with `FILTERED_BY_CATEGORY` or `FILTERED_BY_SCORE` status are retained in historical data. They do not enter the Daily Report body but their statistics appear in Section A.

### Reference

`project_data_schema_v1.md` §11 (Pipeline Status Rules) defines all 4 enum values with their meanings.

---

## §9 Expected Consistency Score

| Check | Current | After P0 Fix | After All Fixes |
|-------|---------|--------------|-----------------|
| 1. Field Naming | 10 | 50 | 100 |
| 2. Stage Ownership | 20 | 60 | 100 |
| 3. Stage Boundary | 10 | 100 | 100 |
| 4. Pipeline Status | 0 | 100 | 100 |
| 5. Data Lineage | 0 | 100 | 100 |
| 6. Classification Output | 20 | 100 | 100 |
| 7. Scoring Output | 30 | 70 | 100 |
| 8. Batch vs Item | 70 | 70 | 100 |
| 9. No Silent Data Loss | 0 | 80 | 100 |
| 10. Document Relationships | 30 | 50 | 100 |
| **Overall** | **20/100** | **78/100** | **100/100** |

---

## §10 Execution Order

The recommended order for applying patches to `scoring_pipeline_schema_v1.md`:

### Step 1: Lifecycle Foundations (P0-1, P0-2)
**Patches:** P0-1 (pipeline_status), P0-2 (project_id)
**Why first:** These two fields are the backbone of traceability and status tracking. Every other patch references them.

### Step 2: Stage 1 Rewrite (P0-5, P0-7)
**Patches:** P0-5 (missing raw fields), P0-7 (project_name)
**Why second:** Stage 1 is the entry point. Its output structure must be correct before downstream stages can be fixed.

### Step 3: Stage 2 Boundary Fix (P0-3, P0-4, P0-6)
**Patches:** P0-3 (stage 2/3 boundary), P0-4 (extracted_keywords), P0-6 (Chinese field names)
**Why third:** Stage 2 is the most problematic stage. All three issues should be fixed together.

### Step 4: Stage 3 Classification Fix (P0-8)
**Patches:** P0-8 (classification_confidence, classification_notes)
**Why fourth:** Depends on Step 2 (Stage 2 output determines Stage 3 input).

### Step 5: Scoring Output Enrichment (P0-9, P0-10)
**Patches:** P0-9 (reasoning), P0-10 (career_goal_impact)
**Why fifth:** These fields are added to Stage 8. Minor changes with no dependencies on earlier steps.

### Step 6: Stage 10 Ranking Fix
**Patches:** Add `rank`, `ranking_group`, explicit batch processing label
**Why sixth:** Independent of previous steps. Scheduled last due to lower impact.

### Step 7: Document References Update
**Patches:** 
- Remove "规划中" from Schema reference
- Update `prompt_scoring_agent_v1.md` → `prompt_scoring_agent_v2.md`
- Add `classification_agent_spec_v1.md` reference
- Add `report_generation_pipeline_v1.md` reference
**Why seventh:** References should be accurate, but don't affect pipeline logic.

### Step 8: Add Schema Mapping Notes
**Patches:** Add §6 mapping table, add batch/item processing notes, add pipeline status lifecycle section
**Why eighth:** Documentation improvements that clarify the relationship between Pipeline and Schema.

---

## §11 Success Criteria

After all patches are applied to `scoring_pipeline_schema_v1.md`, the following conditions must be met:

### Field Compliance

| Condition | Check |
|-----------|-------|
| All field names use snake_case English | ✅ |
| `project_id` appears in all 10 stages | ✅ |
| `pipeline_status` appears in all 10 stages with lifecycle rules | ✅ |
| Stage 1 output matches Schema §5.2 (11 fields) | ✅ |
| Stage 2 output matches Schema §6.2 (3 derived fields) | ✅ |
| Stage 3 output matches Schema §7.2 (5 fields) | ✅ |
| Stage 8 output includes `reasoning` and `career_goal_impact` | ✅ |
| Stage 10 output includes `rank` and `ranking_group` | ✅ |
| No Chinese field names remain | ✅ |
| No "Repo Name" remains | ✅ |
| No "项目领域" remains in Stage 2 | ✅ |

### Boundary Compliance

| Condition | Check |
|-----------|-------|
| Stage 2 contains no classification fields | ✅ |
| Stage 1 contains no scoring fields | ✅ |

### Lifecycle Compliance

| Condition | Check |
|-----------|-------|
| `pipeline_status` transitions are defined for all 4 values | ✅ |
| FILTERED_BY_CATEGORY projects are described as retained | ✅ |
| FILTERED_BY_SCORE projects are described as retained | ✅ |
| ARCHIVED state is the terminal state | ✅ |

### Document Relations Compliance

| Condition | Check |
|-----------|-------|
| Schema not referenced as "规划中" | ✅ |
| References `prompt_scoring_agent_v2.md` (not v1) | ✅ |
| References `classification_agent_spec_v1.md` | ✅ |
| References `report_generation_pipeline_v1.md` | ✅ |

### Score Target

**Final Consistency Score: 100/100** — All 10 checks from the review must pass.

---

*End of Patch Plan v1. Defines 10 P0 fixes + stage-by-stage patch instructions for scoring_pipeline_schema_v1.md.*