# PKIA Runtime Document Style Guide v1

> **Document Type**: Process Standard
> **Status**: Active
> **Version**: v1.1
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
├── runtime_boundary_v1.md                  [active]
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
| `Runtime Design v1.0.md` | Superseded predecessor to `runtime_boundary_v1.md`. Retained for historical reference. | — |
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

The canonical Rule Registry is maintained in §7.2. All downstream documents reference rules from that registry and may add new rules by appending to the sequence.

### 4.2 Rule Referencing

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

## 6. Runtime Document Lifecycle (文档生命周期)

所有 Runtime 架构文档必须在头部（Metadata）显式声明其当前所处的生命周期状态。状态推进必须遵循严格的单向流程，以明确开发启动的边界。

| 状态标识 | 阶段定义 | 变更控制 (Mutation Control) |
| :--- | :--- | :--- |
| **Draft (草稿)** | 初始起草与构思阶段。 | 允许自由修改与重构。 |
| **Review (评审)** | 架构工作坊讨论与推演阶段。 | 允许基于讨论结果进行大幅修订。 |
| **Approved (已批准)** | 架构设计已达成一致，准备指导开发。 | 锁定主体结构，仅允许 Typo 或细节微调。 |
| **Frozen (已冻结)** | 对应的代码实现或工作流搭建已正式启动。 | **绝对禁止修改**。如需重大变更，必须通过新增 ADR (架构决策记录) 进行版本迭代。 |

---

## 7. Runtime Rule Numbering (运行时核心规则编号规范)

为了在跨文档讨论、Issue 追踪、以及代码注释中实现精准引用，所有决定系统行为的运行时法则必须拥有全局唯一的永久编号。

### 7.1 编号原则

- **格式定义：** 采用 `R-XX`（两位或多位数字）格式。
- **追加递增 (Append-Only)：** 新增规则必须使用当前最大编号 +1，严禁在中间插入编号。
- **永久不可变 (Immutable ID)：** 规则编号一旦分配，永久绑定该规则。即使规则在未来版本中被废弃（Deprecated），该编号也**绝对禁止重新分配**给其他新规则。

### 7.2 核心运行时法则注册表 (Runtime Rule Registry)

*(系统已确立的基础法则，新文档需遵循此表引用)*

#### R-01: Validation Isolation

All LLM Node output must be routed directly to a Validation Code Node. LLM output must never connect directly to a business logic node.

Rationale: Guarantees structural integrity before downstream processing.

#### R-02: Append-Only Object

Runtime always maintains a single canonical Project Object. Stages may only append or transform fields. Re-instantiating the object is forbidden.

Rationale: Preserves data lineage and field ownership per `project_data_schema_v1.md`.

#### R-03: Fail-Fast Iteration

When a single item inside a batch Iteration triggers a deterministic exception, that item is dropped immediately without affecting other items in the same batch.

Rationale: Isolates failure to the failing item. Prevents one bad record from blocking the remaining 29.

#### R-04: Workflow SSOT

The Dify-exported `.yml` file is the single source of truth for workflow configuration and must be tracked in Git.

Rationale: Enables diff, review, and rollback of workflow changes.

#### R-05: Aggregator Anarchy

Variable Aggregator nodes do not guarantee output array order matching input order. Final sorting must be performed by a dedicated Ranker node.

Rationale: Prevents silent correctness bugs caused by assumed iteration ordering.

---

## 8. Cross-Reference Rules

### 8.1 Owner Document Rule

Each concept has exactly one owner document. When another document needs to refer to that concept, it cites the owner document rather than re-explaining.

```markdown
See runtime_boundary_v1.md §4.5 for Scoring runtime assignment.
The validation strategy follows failure_handling_v1.md §3.
```

### 8.2 File Path Convention

Cross-references use relative paths from `docs/runtime/`:

```markdown
See ../scoring_pipeline_schema_v2.md §8 for score field definitions.
See runtime_boundary_v1.md §4.4 for Classification boundary.
```

### 8.3 No Duplication Rule

If a concept must be referenced in multiple documents, the reference uses a short summary (≤2 sentences) plus a pointer to the owner document. Full explanations belong only in the owner document.

### 8.4 Frozen Document References

Runtime documents frequently reference frozen baseline documents. These references must:

1. Use the frozen document's relative path from `docs/`
2. Include the specific section number
3. Add a brief note that the referenced document is frozen:

```markdown
Per project_data_schema_v1.md §8.2 (frozen), total_score must equal the sum of four dimensions.
```

---

## 9. Writing Guidelines

### 9.1 Decisions Only

Runtime Architecture documents contain only **finalized decisions**.

Each entry describes:

- **What** was decided
- **Why** (rationale, constraints considered)
- **Who** made the decision (if relevant)

### 9.2 What Must Be Excluded

- ❌ Open Questions — move to a Discussion document or GitHub Issue
- ❌ TODO items — incomplete work has no place in a finalized decision document
- ❌ "Maybe" or "Consider" phrasing — every statement must reflect a decision, not a possibility
- ❌ Future discussion references — future work belongs in `Future Considerations` sections only

When a decision is genuinely unresolved, the document either:

- Marks the module as `Pending` with clear verification criteria (see OQ convention in runtime_boundary_v1.md)
- Defers to a later document in the hierarchy

### 9.3 Language Style

- Direct, declarative sentences: "Collector uses Code Node." not "Collector could potentially use Code Node."
- Present tense: "Validation follows LLM Node." not "Validation will follow LLM Node after deployment."
- Active voice: "Workflow orchestrates retry." not "Retry is orchestrated by the Workflow."
- Technical precision: avoid marketing terms like "robust", "seamless", "future-proof"

### 9.4 Diagram Usage

ASCII diagrams are preferred. If graphics are used, provide an ASCII fallback for diff compatibility.

### 9.5 Code Blocks

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

## 10. Version History

| Version | Date | Author | Change Summary |
|---------|------|--------|----------------|
| v1 | 2026-07 | PKIA MVP Agent | Initial release. Defines Runtime document hierarchy, standard structure, naming conventions, rule system (R-01~R-05), cross-reference rules, and writing guidelines. |
| v1.1 | 2026-07 | PKIA MVP Agent | Added §6 Runtime Document Lifecycle (Draft→Review→Approved→Frozen). Added §7 Runtime Rule Numbering with canonical rule registry. Replaced rule definitions with R-01 (Validation Isolation), R-02 (Append-Only Object), R-03 (Fail-Fast Iteration), R-04 (Workflow SSOT), R-05 (Aggregator Anarchy). Renumbered sections §6→§8, §7→§9, §8→§10, §9→§11. |

---

## 11. Related Documents

| Document | Relationship |
|----------|--------------|
| `Runtime Design v1.0.md` | Existing draft Runtime Boundary document. Naming does not conform to this style guide (uses spaces and PascalCase). Will be renamed to `runtime_boundary_v1.md` in its next revision. |
| `pkia_v0.1_baseline.md` | Frozen release baseline. All Runtime documents must operate within its scope. |
| `project_data_schema_v1.md` | Data contract referenced throughout Runtime documents. |
| `scoring_pipeline_schema_v2.md` | Business specification that Runtime documents translate to Dify implementation. |
| `.opencode.md` | L1 Constitution. Memory governance and bootstrap protocol. |

---

**Design Note (DN-01):** The legacy file `docs/runtime/Runtime Design v1.0.md` has been superseded by `runtime_boundary_v1.md`. It is retained for historical reference only. The naming has been aligned with the snake_case convention.

---

*End of Runtime Document Style Guide v1.*
