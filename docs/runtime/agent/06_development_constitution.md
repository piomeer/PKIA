# 06 — Development Constitution

> **Purpose**: Define immutable development rules.

---

**Rule 1: Specification Before Implementation**

No code is written before a specification exists. Every non-trivial task begins with OpenSpec.

**Rule 2: Approval Before Execution**

No implementation starts before the human approves the specification.

**Rule 3: Follow the Spec**

Implementation must match the approved specification. Deviations require replanning.

**Rule 4: Architecture Changes Require Replanning**

If implementation reveals an architecture issue, stop and return to PLANNING. Do not redesign during execution.

**Rule 5: Verification Before Commit**

Every commit must pass all verification gates (see 05_review.md). No skipping gates.

**Rule 6: Commit Only Verified Work**

Unfinished or failing work is never committed.

**Rule 7: Requirements Changes Restart Planning**

If requirements change mid-task, pause execution and return to PLANNING. Do not adapt during execution.

**Rule 8: Document the State**

After every task, update `progress/<namespace>.md` with current state, active decisions, and blockers.

---

**No implementation details. These rules apply to every task, every agent, every project.**
