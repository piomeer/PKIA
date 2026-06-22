# Review: scoring_pipeline_schema_v1.md Consistency Audit

## Review Against project_data_schema_v1.md

**Date:** 2026-06-22
**Reviewer:** PKIA Architecture Audit
**Target:** docs/scoring_pipeline_schema_v1.md
**Reference:** docs/project_data_schema_v1.md

---

## 1. Executive Summary

`scoring_pipeline_schema_v1.md` defines a 10-stage pipeline for scoring projects. `project_data_schema_v1.md` defines a 6-stage data model (Raw → Normalized → Classified → Scored → Ranked → Report). The two documents share a common data flow but use incompatible stage boundaries, field naming conventions, and data structures.

The scoring pipeline was written before `project_data_schema_v1.md` existed and has not been updated to match it. The reference in §14 still says "Project Data Schema（规划中）"—indicating the document predates the Schema.

**Overall Consistency Score: 20/100**

The scoring pipeline is structurally sound as a process definition but has pervasive naming, ownership, and completeness gaps when measured against the Schema.

---

## 2. Consistency Score Breakdown

| Check | Score | Status |
|-------|-------|--------|
| 1. Field Naming Consistency | 10/100 | ❌ |
| 2. Stage Ownership Consistency | 20/100 | ❌ |
| 3. Stage Boundary Validation (Stage 2/3) | 10/100 | ❌ |
| 4. Pipeline Status Lifecycle | 0/100 | ❌ |
| 5. Data Lineage | 0/100 | ❌ |
| 6. Classification Output Compatibility | 20/100 | ❌ |
| 7. Scoring Output Compatibility | 30/100 | ❌ |
| 8. Batch vs Item Processing | 70/100 | ⚠️ |
| 9. No Silent Data Loss | 0/100 | ❌ |
| 10. Document Relationship Consistency | 30/100 | ❌ |
| **Overall** | **20/100** | ❌ |

---

## 3. Review Matrix

| Check | Status | Impact | Description |
|-------|--------|--------|-------------|
| 1 | ❌ FAIL | HIGH | Field names use Chinese, mixed case, wrong terms. Missing core fields entirely |
| 2 | ❌ FAIL | HIGH | Stage 2 contains Stage 3 fields. Stage 4-7 fragmented. Missing Stage 4 bundle fields |
| 3 | ❌ FAIL | HIGH | "项目领域" in Stage 2 is a classification concept. Pipeline admits it belongs to Stage 3 |
| 4 | ❌ FAIL | CRITICAL | pipeline_status completely absent across all 10 stages |
| 5 | ❌ FAIL | CRITICAL | project_id not mentioned in any stage |
| 6 | ❌ FAIL | HIGH | Classification output missing 3 of 5 required fields |
| 7 | ❌ FAIL | HIGH | Scoring output missing reasoning, career_goal_impact. Fragmented across 4 stages |
| 8 | ⚠️ WARN | LOW | Batch vs Item distinction is implicit, not explicit |
| 9 | ❌ FAIL | HIGH | No filtering mechanism, no retention of filtered projects |
| 10 | ❌ FAIL | MEDIUM | References Schema as "规划中", references prompt v1 instead of v2, missing classification_agent_spec |

---

## 4. Detailed Findings

### Check 1: Field Naming Consistency

#### Finding 1.1: Stage 1 output uses "Repo Name"

**Location:** `scoring_pipeline_schema_v1.md` §3 (Stage 1), line 64
**Current text:** "每个条目包含：Repo Name、Description、Stars 数、Topics 标签"
**Schema requirement:** `project_name` (snake_case, English)
**Violation:** Uses "Repo Name" which is explicitly prohibited by `project_data_schema_v1.md` §3.2.

#### Finding 1.2: Stage 1 output missing 7 required fields

**Location:** `scoring_pipeline_schema_v1.md` §3 (Stage 1), line 63-64
**Current fields:** Repo Name, Description, Stars, Topics
**Schema §5.2 required fields:** `project_id`, `project_name`, `owner`, `description`, `topics`, `stars`, `forks`, `language`, `source`, `collection_date`, `pipeline_status`
**Missing:** `project_id`, `owner`, `forks`, `language`, `source`, `collection_date`, `pipeline_status` (7 fields)
**Violation:** Stage 1 output is a subset of Schema requirements.

#### Finding 1.3: Stage 2 output uses Chinese field names

**Location:** `scoring_pipeline_schema_v1.md` §4 (Stage 2), lines 94-98
**Current fields:** 项目名称, 一句话描述, 核心能力, 项目标签, 项目领域
**Schema §3.1 requires:** All field names in snake_case English. Chinese field names are prohibited.
**Violation:** All 5 fields use Chinese names instead of English snake_case.

#### Finding 1.4: "核心能力" is not a Schema field

**Location:** `scoring_pipeline_schema_v1.md` §4 (Stage 2), line 96
**Current text:** "核心能力 | 该项目解决什么问题、提供什么能力 | Description 提炼"
**Schema requirement:** `extracted_keywords` (list[string], max 5)
**Violation:** "核心能力" is an invented field not present in the Schema. No structured constraint.

#### Finding 1.5: "项目领域" is not a Stage 2 field

**Location:** `scoring_pipeline_schema_v1.md` §4 (Stage 2), line 98
**Current text:** "项目领域 | 按 Interest Tiers 映射的领域标签 | Stage 3 完成"
**Schema requirement:** Classification fields belong to Stage 3 only.
**Violation:** See Check 3 for details.

#### Finding 1.6: Stage 3 output uses different field names than Schema

**Location:** `scoring_pipeline_schema_v1.md` §5 (Stage 3), lines 123-124
**Current text:** "Primary Category" and "Secondary Tags"
**Schema §7.2:** `primary_category`, `secondary_categories`
**Violation:** "Secondary Tags" vs `secondary_categories`. Also uses CamelCase instead of snake_case.

---

### Check 2: Stage Ownership Consistency

#### Finding 2.1: Stage 4-7 produce individual scores (fragmented ownership)

**Location:** `scoring_pipeline_schema_v1.md` §6-9
**Current structure:**
- Stage 4: Career Alignment (0~40)
- Stage 5: Interest Match (0~30)
- Stage 6: Trend Heat (0~20)
- Stage 7: Research Relevance (0~10)
- Stage 8: Total Score Calculation

**Schema §8 requirement:** All 4 scores + total_score + recommendation + reasoning + career_goal_impact are bundled into a single Stage 4 (Scoring Output).
**Violation:** The Pipeline fragments scoring into 4 separate stages. The Schema treats scoring as a single stage producing a composite output.

**Impact:** This is a *structural* difference, not just a naming issue. The Pipeline treats each score as an independent stage with independent outputs. The Schema treats all scores as part of a single Scoring Output Object. If the Pipeline is implemented as written, it would produce 4 separate partial outputs instead of one unified Scoring Output.

#### Finding 2.2: Missing `reasoning` in scoring output

**Location:** `scoring_pipeline_schema_v1.md` §6-10
**Current state:** `reasoning` is mentioned in §13 (principles) as a requirement, but is not included as an output field in any stage.
**Schema §8.2:** `reasoning` is a required field in Stage 4.
**Violation:** `reasoning` is conceptually required but structurally absent from all stage outputs.

#### Finding 2.3: Missing `career_goal_impact` in scoring output

**Location:** `scoring_pipeline_schema_v1.md` §6-10
**Current state:** Not mentioned anywhere.
**Schema §8.2-8.3:** `career_goal_impact` is a required field in Stage 4 with 4 sub-fields.
**Violation:** Completely absent.

#### Finding 2.4: Stage 10 output lacks Schema-mandated fields

**Location:** `scoring_pipeline_schema_v1.md` §12 (Stage 10), line 371
**Current output:** "排序后的项目列表，按推荐等级分组"
**Schema §9.2 required fields:** `rank` (integer 1~30), `ranking_group` (enum)
**Schema §10.3 required fields (if including Report):** `summary`, `recommended_read_time`, `daily_priority`
**Violation:** No `rank`, no `ranking_group`, no Report stage fields.

---

### Check 3: Stage Boundary Validation (Stage 2 vs Stage 3)

#### Finding 3.1: "项目领域" appears in Stage 2 output

**Location:** `scoring_pipeline_schema_v1.md` §4 (Stage 2), line 98
**Current text:** "项目领域 | 按 Interest Tiers 映射的领域标签 | Stage 3 完成"
**Schema §6.4:** "Stage 2 不产生任何与分类相关的字段"
**Schema §7:** Classification fields (`primary_category`, `secondary_categories`, `classification_confidence`, etc.) belong to Stage 3 only.

**Violation analysis:** The Pipeline document itself admits that "项目领域" is completed in Stage 3, yet places it in Stage 2's output. This is a self-contradictory stage boundary violation.

**Risk:** A Pipeline implementer reading this document would likely implement category mapping logic in Stage 2 (Normalization), which violates the "Classification First" principle and bypasses the Classification Agent entirely.

---

### Check 4: Pipeline Status Lifecycle

#### Finding 4.1: `pipeline_status` completely absent

**Location:** Entire document
**Current state:** Not mentioned in any of the 10 stages.
**Schema §11:** Defines `pipeline_status` lifecycle with 4 values: `PROMOTED`, `FILTERED_BY_CATEGORY`, `FILTERED_BY_SCORE`, `ARCHIVED`.

**Violation:** The Pipeline has no mechanism for tracking which projects are active, filtered, or archived. This makes it impossible to implement "No Silent Data Loss" (Schema Principle 4).

**Missing lifecycle points:**
- Stage 3 after classification: should set `FILTERED_BY_CATEGORY` for non-AI projects
- Stage 4-7 after scoring: should set `FILTERED_BY_SCORE` for IGNORE projects
- Stage 10 after ranking: should set `ARCHIVED`

---

### Check 5: Data Lineage

#### Finding 5.1: `project_id` completely absent

**Location:** Entire document
**Current state:** Not mentioned in any of the 10 stages.
**Schema §4.1:** `project_id` is the backbone of PKIA data lineage, must appear in all stages unchanged.
**Schema §12:** Defines complete lineage path from Stage 1 to Stage 6.

**Violation:** Without `project_id`, there is no way to trace a project from raw data to Daily Report through the scoring pipeline. This affects debugging, auditing, and traceback capabilities.

---

### Check 6: Classification Output Compatibility

#### Finding 6.1: Missing `classification_confidence`

**Location:** `scoring_pipeline_schema_v1.md` §5 (Stage 3), lines 123-124
**Current output:** "Primary Category" and "Secondary Tags"
**Schema §7.2:** Requires `primary_category`, `secondary_categories`, `classification_confidence`, `classification_notes`
**classification_agent_spec_v1.md §4:** Also requires `classification_confidence` (ENUM: HIGH/MEDIUM/LOW)

**Violation:** 2 of 4 required classification output fields are missing.

#### Finding 6.2: Missing `classification_notes`

**Location:** `scoring_pipeline_schema_v1.md` §5 (Stage 3)
**Current state:** Not mentioned.
**Schema §7.2:** `classification_notes` is required.
**classification_agent_spec_v1.md §4:** `classification_notes` is required, must explain Primary Category choice.

**Violation:** Classification reasoning is not carried forward.

---

### Check 7: Scoring Output Compatibility

#### Finding 7.1: Scoring output fragmented across 4 stages

**Location:** `scoring_pipeline_schema_v1.md` §6-9
**Current structure:** Individual stages produce individual scores.
**Schema §8:** Single Stage 4 produces all scores + total_score + recommendation + reasoning + career_goal_impact.

**While this structural difference may be intentional** (the Pipeline chooses to separate scoring dimensions into individual stages for process clarity), it creates a compatibility issue: the Schema expects a single combined output per project, while the Pipeline produces 4 separate outputs that would need to be merged.

#### Finding 7.2: Missing `reasoning`

**Location:** `scoring_pipeline_schema_v1.md` §6-10
**Current state:** Not an output field. Mentioned in §13 as a principle.
**Schema §8.2:** Required field.
**prompt_scoring_agent_v2.md §12:** Required in output format.

**Violation:** `reasoning` is structurally absent from all stage outputs.

#### Finding 7.3: Missing `career_goal_impact`

**Location:** `scoring_pipeline_schema_v1.md` §6-10
**Current state:** Not mentioned.
**Schema §8.2-8.3:** Required. Contains 4 sub-fields.
**prompt_scoring_agent_v2.md §12:** Included in output format.

**Violation:** Completely absent.

---

### Check 8: Batch vs Item Processing

#### Finding 8.1: Implicit but not explicit

**Location:** `scoring_pipeline_schema_v1.md` §12 (Stage 10)
**Current text:** "将所有评分完成的项目排序" — implies batch processing.
**Schema §13:** Requires explicit distinction: Stage 1-4 = Item Processing, Stage 5-6 = Batch Processing.

**Verdict:** The pipeline correctly places ranking in Stage 10 (which is batch processing). The distinction is implied by the ranking operation but never explicitly stated. No ownership violation, but could be clearer.

**Impact:** LOW. The implicit distinction is correct. Adding explicit labeling would improve clarity but is not a correctness issue.

---

### Check 9: No Silent Data Loss

#### Finding 9.1: No filtering mechanism defined

**Location:** Entire document
**Current state:** Stage 9 defines Recommendation (Ignore is a valid output), but there is no description of what happens to Ignored projects. The output "排序后的项目列表" implies all 30 projects are passed through, but there is no data retention mechanism for filtered projects.
**Schema §11.3:** Requires retention of filtered projects with `pipeline_status` marking for audit, statistics, and debugging.

**Violation:** Without `pipeline_status`, there is no mechanism to track filtered projects. If the Pipeline implementation discards Ignored projects, those projects are lost with no audit trail.

---

### Check 10: Document Relationship Consistency

#### Finding 10.1: Schema referenced as "规划中"

**Location:** `scoring_pipeline_schema_v1.md` §14, line 419
**Current text:** "**Project Data Schema（规划中）**" — with description including "本文件与 Project Data Schema 共同构成..."
**Current state:** `project_data_schema_v1.md` exists and is published.
**Violation:** The reference is outdated. It should say "Project Data Schema" without "规划中".

#### Finding 10.2: References `prompt_scoring_agent_v1.md` instead of v2

**Location:** `scoring_pipeline_schema_v1.md` §14, line 420
**Current text:** "**prompt_scoring_agent_v1.md**"
**Current state:** `prompt_scoring_agent_v2.md` exists and is the active version.
**Violation:** References the outdated v1 prompt. v2 includes `career_goal_impact` and updated confidence format.

#### Finding 10.3: Missing `classification_agent_spec_v1.md` reference

**Location:** `scoring_pipeline_schema_v1.md` §14
**Current state:** Does not mention classification_agent_spec_v1.md.
**Current state:** `classification_agent_spec_v1.md` defines Stage 3 (Classification) execution.
**Violation:** The Pipeline's Stage 3 (Category Classification) should reference the Classification Agent spec.

#### Finding 10.4: Missing `report_generation_pipeline_v1.md` reference

**Location:** `scoring_pipeline_schema_v1.md` §14
**Current state:** Does not mention report_generation_pipeline_v1.md.
**Current state:** `report_generation_pipeline_v1.md` consumes Pipeline Stage 10 output.
**Violation:** The downstream consumer of the Pipeline's ranking output is not identified.

---

## 5. P0 Critical Issues

These issues must be fixed before the Pipeline can be considered Schema-compliant.

| ID | Issue | Location | Fix Summary |
|----|-------|----------|-------------|
| P0-1 | `pipeline_status` absent | Entire doc | Add to all 10 stages with lifecycle rules |
| P0-2 | `project_id` absent | Entire doc | Add as mandatory field in all stage outputs |
| P0-3 | Stage 2 contains "项目领域" | §4 line 98 | Remove, belongs to Stage 3 |
| P0-4 | Stage 2 "核心能力" not in Schema | §4 line 96 | Replace with `extracted_keywords` |
| P0-5 | Stage 1 missing 7 required fields | §3 lines 63-64 | Add `project_id`, `owner`, `forks`, `language`, `source`, `collection_date`, `pipeline_status` |
| P0-6 | Chinese field names in Stage 2 output | §4 lines 94-98 | Convert to snake_case English |
| P0-7 | "Repo Name" in Stage 1 output | §3 line 64 | Change to `project_name` |
| P0-8 | Classification output missing 3 fields | §5 lines 123-124 | Add `classification_confidence`, `classification_notes`, `pipeline_status` |
| P0-9 | Scoring output missing `reasoning` | §6-10 | Add as required output field |
| P0-10 | Scoring output missing `career_goal_impact` | §6-10 | Add as required output field |

---

## 6. P1 Recommended Fixes

| ID | Issue | Location | Fix Summary |
|----|-------|----------|-------------|
| P1-1 | Stage 3 output uses "Secondary Tags" | §5 line 124 | Change to `secondary_categories` |
| P1-2 | No batch/item processing distinction | §12 / §3-9 | Add explicit labeling |
| P1-3 | Schema referenced as "规划中" | §14 line 419 | Remove "规划中" marker |
| P1-4 | References prompt v1 instead of v2 | §14 line 420 | Update to `prompt_scoring_agent_v2.md` |
| P1-5 | Missing classification_agent_spec reference | §14 | Add reference |
| P1-6 | Missing report_generation_pipeline reference | §14 | Add reference |
| P1-7 | Stage 4-7 fragmentation vs Schema bundling | §6-9 vs Schema §8 | Add note explaining mapping between Pipeline stages and Schema Stage 4 |
| P1-8 | Stage 10 output missing `rank` and `ranking_group` | §12 line 371 | Add as structured output fields |

---

## 7. Suggested Patch Order

| Step | Focus | Dependencies | Estimated Patches |
|------|-------|-------------|-------------------|
| 1 | P0-2: Add `project_id` to all stages | None | ~5 locations |
| 2 | P0-1: Add `pipeline_status` lifecycle | None | ~8 locations |
| 3 | P0-5: Expand Stage 1 output | None | §3 rewrite |
| 4 | P0-3 + P0-4: Fix Stage 2 boundary | Step 3 | §4 rewrite |
| 5 | P0-7: `project_name` in Stage 1 | Step 3 | §3 update |
| 6 | P0-6: English snake_case in Stage 2 | Step 4 | §4 update |
| 7 | P0-8: Add missing classification fields | None | §5 update |
| 8 | P0-9 + P0-10: Add `reasoning` + `career_goal_impact` | None | §6-9 update |
| 9 | P1-1: "Secondary Tags" → `secondary_categories` | None | §5 update |
| 10 | P1-8: `rank` + `ranking_group` | Step 1-2 | §12 update |
| 11 | P1-3 to P1-6: Document references | None | §14 rewrite |
| 12 | P1-2 + P1-7: Process notes | None | §2, §13 update |

---

## 8. Expected Score After Fix

| Check | Current | After P0 Fixes | After All Fixes |
|-------|---------|----------------|-----------------|
| 1. Field Naming | 10 | 50 | 100 |
| 2. Stage Ownership | 20 | 60 | 90 |
| 3. Stage Boundary | 10 | 100 | 100 |
| 4. Pipeline Status | 0 | 100 | 100 |
| 5. Data Lineage | 0 | 100 | 100 |
| 6. Classification Output | 20 | 100 | 100 |
| 7. Scoring Output | 30 | 70 | 100 |
| 8. Batch vs Item | 70 | 70 | 100 |
| 9. No Silent Data Loss | 0 | 70 | 100 |
| 10. Document Relationships | 30 | 50 | 100 |
| **Overall** | **20/100** | **77/100** | **99/100** |

---

## 9. Summary of All Findings

| # | Type | Severity | Location | Summary |
|---|------|----------|----------|---------|
| 1.1 | Naming | HIGH | §3 line 64 | "Repo Name" instead of `project_name` |
| 1.2 | Missing | HIGH | §3 lines 63-64 | 7 required fields absent from Stage 1 |
| 1.3 | Naming | HIGH | §4 lines 94-98 | Chinese field names (prohibited by Schema §3.1) |
| 1.4 | Missing | HIGH | §4 line 96 | "核心能力" not a Schema field; `extracted_keywords` missing |
| 1.5 | Boundary | HIGH | §4 line 98 | "项目领域" is a Stage 3 concept |
| 1.6 | Naming | MEDIUM | §5 lines 123-124 | "Secondary Tags" vs `secondary_categories` |
| 2.1 | Structure | MEDIUM | §6-9 | Scoring fragmented into 4 stages vs Schema's single stage |
| 2.2 | Missing | HIGH | §6-10 | `reasoning` absent from all stage outputs |
| 2.3 | Missing | HIGH | §6-10 | `career_goal_impact` absent |
| 2.4 | Missing | MEDIUM | §12 line 371 | `rank`, `ranking_group` absent |
| 3.1 | Boundary | CRITICAL | §4 line 98 | Stage 2 contains Stage 3 field |
| 4.1 | Missing | CRITICAL | Entire doc | `pipeline_status` completely absent |
| 5.1 | Missing | CRITICAL | Entire doc | `project_id` completely absent |
| 6.1 | Missing | HIGH | §5 | `classification_confidence` absent |
| 6.2 | Missing | HIGH | §5 | `classification_notes` absent |
| 7.1 | Structure | MEDIUM | §6-9 | Fragmented scoring output |
| 7.2 | Missing | HIGH | §6-10 | `reasoning` absent |
| 7.3 | Missing | HIGH | §6-10 | `career_goal_impact` absent |
| 8.1 | Clarity | LOW | §12 | Batch/Item distinction implicit |
| 9.1 | Design | HIGH | Entire doc | No filtering/data retention mechanism |
| 10.1 | Outdated | MEDIUM | §14 line 419 | Schema referenced as "规划中" |
| 10.2 | Outdated | MEDIUM | §14 line 420 | References v1 prompt instead of v2 |
| 10.3 | Missing | MEDIUM | §14 | classification_agent_spec not referenced |
| 10.4 | Missing | MEDIUM | §14 | report_generation_pipeline not referenced |

---

*End of Review. Audit of scoring_pipeline_schema_v1.md against project_data_schema_v1.md.*