# PKIA Runtime Document Style Guide v1

> **Document Type**: Process Standard
> **Status**: Active
> **Last Updated**: 2026-07
> **Namespace**: pkia_mvp

---

## 1. Purpose

### 1.1 Why Runtime Documents Exist

Runtime documents bridge the gap between **Business Specification** (frozen baseline documents) and **Implementation** (Dify workflow DSL, Python code).

Each layer serves a distinct purpose:

| Layer | Purpose | Audience | Example Document |
|-------|---------|----------|------------------|
| **Business Specification** | Define *what* the system does and *why* | Product / Architect | `scoring_pipeline_schema_v2.md` |
| **Runtime Architecture** | Define *which runtime component* does it and *how it connects* | Engineer / Implementer | `runtime_boundary_v1.md` |
| **Implementation** | The actual Dify workflow DSL, Python adapter code | Machine | `workflow-*.yml`, `collector.py` |

Runtime documents are the translation layer between specification and code.

### 1.2 What Runtime Documents Are Not

- Not a replacement for any frozen baseline document
- Not a coding tutorial
- Not a discussion log or meeting minutes
- Not a project management tracker

---

## 2. Runtime Document Hierarchy

### 2.1 Document Tree

```
docs/runtime/
├── runtime_document_style_guide_v1.md     (this file)
├── runtime_architecture_overview_v1.md     [planned]
├── runtime_boundary_v1.md                  [draft: Runtime Design v1.0]
├── node_mapping_v1.md                      [planned]
├── data_flow_v1.md                         [planned]
├── node_io_contract_v1.md                  [planned]
├── failure_handling_v1.md                  [planned]
└── deployment_v1.md                        [planned]
```

### 2.2 Document Responsibilities

| Document | Responsibility | What It Answers |
|----------|----------------|------------------|
| `runtime_document_style_guide_v1.md` | Writing standard for all Runtime documents | How must Runtime documents be written? |
| `runtime_architecture_overview_v1.md` | High-level runtime architecture map, component inventory, tool selection rationale | What are the runtime components and why were they chosen? |
| `runtime_boundary_v1.md` | Runtime owner for each pipeline stage, Dify vs Python boundary decisions | Who executes each stage? |
| `node_mapping_v1.md` | Concrete Dify workflow node types, node parameters, node wiring | Which Dify node type implements each boundary? |
| `data_flow_v1.md` | Data passing between stages, variable naming, iteration strategy, aggregation points | How does data move through the workflow? |
| `node_io_contract_v1.md` | Exact input/output schema for each Dify node, JSON structure, field-level validation rules | What exactly goes in and out of each node? |
| `failure_handling_v1.md` | Retry strategy, fallback logic, error codes, degradation modes | What happens when something fails? |
| `deployment_v1.md` | Scheduling, triggers, environment setup, storage adapter connection, monitoring | How is the workflow deployed and operated? |

### 2.3 No Overlap Rule

Each concept belongs to exactly one document. If a concept appears in two documents, one must reference the other without duplication.

---

## 3. Standard Document Structure

### 3.1 Required Skeleton

Every Runtime document MUST use exactly the following top-level sections:

```
1 Purpose
2 Scope
3 Design Principles
4 Main Design
5 Runtime Rules (optional)
6 Related Documents
7 Version History
```

No additional top-level sections are permitted.

### 3.2 Subsection Rules

- Subsections follow decimal numbering: `4.1`, `4.1.1`
- A section must have either zero subsections or two or more (never leave a section with a single child)
- Maximum heading depth: `###` (third level)

### 3.3 Header Block

Each document starts with a header block:

```markdown
# PKIA <Document Title> v<version>

> **Document Type**: <Process Standard | Design Decision | Reference>
> **Status**: <Active | Draft | Deprecated>
> **Last Updated**: <YYYY-MM>
> **Namespace**: pkia_mvp
```

---

## 4. Runtime Rule Convention

### 4.1 Rule IDs

All Runtime Rules follow this format:

```
R-XX: <rule title>
```

Rules are numbered sequentially (R-01, R-02, ...). IDs are never reused.

### 4.2 Initial Rules

The following rules are established in this document. Each downstream Runtime document may add new rules.

#### R-01: LLM Node Requires Validation Node

Every LLM Node must be followed by a Code Node that validates output format, field completeness, and enum legality.

Rationale: LLM output cannot be guaranteed structurally valid. Validation ensures pipeline integrity.

#### R-02: Append-Only Object Mutation

Each pipeline stage adds fields to the project object. No stage modifies or removes fields owned by an earlier stage.

Rationale: Ensures data lineage traceability per `project_data_schema_v1.md` §12.

#### R-03: Workflow Is SSOT for Orchestration

Dify Workflow is the single source of truth for orchestration logic — branching, iteration, retry, and sequencing. Python scripts must not contain orchestration logic.

Rationale: Keeps orchestration visible, testable, and modifiable through the Dify UI.

#### R-04: Dify First, Python Minimal

A capability must be implemented in Dify unless proven infeasible. Python adapters handle only I/O that Dify cannot (e.g., HTML parsing with BeautifulSoup).

Rationale: Minimizes external dependencies and keeps the pipeline self-contained within Dify.

#### R-05: Config Over Hardcode

All numeric thresholds, limits, and tunable parameters must be declared as Workflow Start Variables or Environment Variables. Zero magic numbers in Prompt or Code Node logic.

Rationale: Enables tuning without redeployment or prompt editing.

### 4.3 Rule Referencing

Rules are referenced by ID in other documents:

```markdown
This follows R-01 (LLM Node Requires Validation Node).
Design Note: Exception to R-04 — HTML parsing requires Python.
```

---

## 5. Naming Convention

### 5.1 Document Name

All Runtime document filenames use **snake_case**:

- ✅ `runtime_boundary_v1.md`
- ✅ `node_mapping_v1.md`
- ✅ `data_flow_v1.md`
- ❌ `Runtime Design v1.0.md`
- ❌ `NodeMappingV1.md`
- ❌ `node-mapping-v1.md`

Version suffix: `_v<major>.md` (e.g., `_v1.md`, `_v2.md`).

### 5.2 Rule IDs

Format: `R-XX` where XX is a zero-padded two-digit number.

- ✅ `R-01`, `R-12`
- ❌ `R1`, `Rule 12`, `rule_five`

### 5.3 Node IDs

Dify node identifiers use **snake_case**, prefixed by stage number:

- ✅ `s1_collector`, `s3_classifier`, `s8_scorer`
- ❌ `CollectorNode`, `classifier-node`

### 5.4 Variable Names

Workflow and Code Node variables use **snake_case**:

- ✅ `total_score`, `normalized_description`, `ranking_group`
- ❌ `totalScore`, `NormalizedDescription`, `ranking-group`

### 5.5 Object Names

Pipeline data objects use **PascalCase** with descriptive prefixes:

- ✅ `RawProject`, `NormalizedProject`, `ScoredProject`
- ❌ `raw`, `project_obj`, `scored_project_object`

### 5.6 Version Naming

All Runtime documents follow: `v<major>`.

- Major version increments when the document content undergoes significant revision
- No minor/patch versioning in filenames (use `Version History` section for tracking minor changes)

---

## 6. Cross-Reference Rules

### 6.1 Owner Document Rule

Each concept has exactly one owner document. When another document needs to refer to that concept, it cites the owner document rather than re-explaining.

```markdown
See runtime_boundary_v1.md §4.5 for Scoring runtime assignment.
The validation strategy follows failure_handling_v1.md §3.
```

### 6.2 File Path Convention

Cross-references use relative paths from `docs/runtime/`:

```markdown
See ../scoring_pipeline_schema_v2.md §8 for score field definitions.
See runtime_boundary_v1.md §4.4 for Classification boundary.
```

### 6.3 No Duplication Rule

If a concept must be referenced in multiple documents, the reference uses a short summary (≤2 sentences) plus a pointer to the owner document. Full explanations belong only in the owner document.

### 6.4 Frozen Document References

Runtime documents frequently reference frozen baseline documents. These references must:

1. Use the frozen document's relative path from `docs/`
2. Include the specific section number
3. Add a brief note that the referenced document is frozen:

```markdown
Per project_data_schema_v1.md §8.2 (frozen), total_score must equal the sum of four dimensions.
```

---

## 7. Writing Guidelines

### 7.1 Decisions Only

Runtime Architecture documents contain only **finalized decisions**.

Each entry describes:

- **What** was decided
- **Why** (rationale, constraints considered)
- **Who** made the decision (if relevant)

### 7.2 What Must Be Excluded

- ❌ Open Questions — move to a Discussion document or GitHub Issue
- ❌ TODO items — incomplete work has no place in a finalized decision document
- ❌ "Maybe" or "Consider" phrasing — every statement must reflect a decision, not a possibility
- ❌ Future discussion references — future work belongs in `Future Considerations` sections only

When a decision is genuinely unresolved, the document either:

- Marks the module as `Pending` with clear verification criteria (see OQ convention in runtime_boundary_v1.md)
- Defers to a later document in the hierarchy

### 7.3 Language Style

- Direct, declarative sentences: "Collector uses Code Node." not "Collector could potentially use Code Node."
- Present tense: "Validation follows LLM Node." not "Validation will follow LLM Node after deployment."
- Active voice: "Workflow orchestrates retry." not "Retry is orchestrated by the Workflow."
- Technical precision: avoid marketing terms like "robust", "seamless", "future-proof"

### 7.4 Diagram Usage

ASCII diagrams are preferred. If graphics are used, provide an ASCII fallback for diff compatibility.

### 7.5 Code Blocks

Inline commands: backticks. Multi-line code blocks with language declaration:

````markdown
```json
{
  "project_id": "gt-20260614-openmanus",
  "total_score": 96
}
```
````

---

## 8. Version History

| Version | Date | Author | Change Summary |
|---------|------|--------|----------------|
| v1 | 2026-07 | PKIA MVP Agent | Initial release. Defines Runtime document hierarchy, standard structure, naming conventions, rule system, cross-reference rules, and writing guidelines. |

---

## 9. Related Documents

| Document | Relationship |
|----------|--------------|
| `Runtime Design v1.0.md` | Existing draft Runtime Boundary document. Naming does not conform to this style guide (uses spaces and PascalCase). Will be renamed to `runtime_boundary_v1.md` in its next revision. |
| `pkia_v0.1_baseline.md` | Frozen release baseline. All Runtime documents must operate within its scope. |
| `project_data_schema_v1.md` | Data contract referenced throughout Runtime documents. |
| `scoring_pipeline_schema_v2.md` | Business specification that Runtime documents translate to Dify implementation. |
| `.opencode.md` | L1 Constitution. Memory governance and bootstrap protocol. |

---

**Design Note (DN-01):** The existing file `docs/runtime/Runtime Design v1.0.md` uses a naming convention (`PascalCase with spaces and a dot version`) that differs from this style guide's snake_case standard (`runtime_boundary_v1.md`). This is acknowledged as a legacy naming artifact. The file content is compatible with the Runtime document hierarchy (it covers the `runtime_boundary_v1.md` slot). The naming will be aligned in a future cleanup pass. No frozen documents are affected.

---

*End of Runtime Document Style Guide v1.*
