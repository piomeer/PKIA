"""
P1 Governor Test Suite — MVP v0.1.

Verifies core invariants from memory_schema_v1.0.md:

  1. Single ACTIVE Per Slot
  2. SUPERSEDED_BY Chain Integrity (no cycles, no forks)
  3. Monotonic Version Rule
  4. Conflict Resolution Priority
  5. Bootstrap Consistency (rebuild from file preserves state)
  6. Trace Completeness

Each test uses a temporary JSON Lines file so it does NOT touch
the real cline-memory.json.
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from pkia_memory.models import (
    MemoryStatus,
    RelationRecord,
    SourceType,
    WriteRequest,
)
from pkia_memory.governor import Governor


class TestGovernor(unittest.TestCase):
    """Governor MVP v0.1 — Schema v1.0 core invariant tests."""

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        )
        self.tmp.close()
        self.path = Path(self.tmp.name)

    def tearDown(self):
        os.unlink(self.path)

    # ── Helper ─────────────────────────────────────────────────────────

    def _make_gov(self) -> Governor:
        gov = Governor()
        gov.startup(self.path)
        return gov

    # ═══════════════════════════════════════════════════════════════════
    # 1. Single ACTIVE Per Slot
    # ═══════════════════════════════════════════════════════════════════

    def test_single_active_per_slot_create_then_supersede(self):
        """
        After supersede, only the new node should be ACTIVE.
        The old node must be DEPRECATED.
        """
        gov = self._make_gov()

        # Create v1.
        r1 = gov.write(WriteRequest(category="preference", key="theme", value="dark", context="global"))
        self.assertEqual(r1["action"], "created")
        v1_id = r1["node_id"]

        # Supersede → v2.
        r2 = gov.write(WriteRequest(category="preference", key="theme", value="light", context="global"))
        self.assertEqual(r2["action"], "superseded")
        v2_id = r2["node_id"]

        # Only v2 should be ACTIVE.
        active = gov.get_active("preference:theme@global")
        self.assertIsNotNone(active)
        self.assertEqual(active.node_id, v2_id)
        self.assertEqual(active.status, MemoryStatus.ACTIVE)

        # v1 must be DEPRECATED.
        v1_node = gov.get_node(v1_id)
        self.assertIsNotNone(v1_node)
        self.assertEqual(v1_node.status, MemoryStatus.DEPRECATED)

    def test_reinforce_does_not_create_duplicate_active(self):
        """
        Reinforcing the same value must NOT create a new ACTIVE node.
        The same node remains ACTIVE with incremented count.
        """
        gov = self._make_gov()

        r1 = gov.write(WriteRequest(category="preference", key="language", value="zh-CN", context="global"))
        self.assertEqual(r1["action"], "created")

        r2 = gov.write(WriteRequest(category="preference", key="language", value="zh-CN", context="global"))
        self.assertEqual(r2["action"], "reinforced")

        active = gov.get_active("preference:language@global")
        self.assertIsNotNone(active)
        self.assertEqual(active.reinforcement_count, 2)
        self.assertEqual(active.version, 1)

        # Only one node in the slot.
        nodes = gov.get_slot_nodes("preference:language@global")
        self.assertEqual(len(nodes), 1)

    # ═══════════════════════════════════════════════════════════════════
    # 2. SUPERSEDED_BY Chain Integrity
    # ═══════════════════════════════════════════════════════════════════

    def test_superseded_chain_is_linear(self):
        """
        Chain: v1 → SUPERSEDED_BY → v2 → SUPERSEDED_BY → v3
        Each node should have exactly one SUPERSEDED_BY target
        (except the oldest which has none).
        """
        gov = self._make_gov()

        values = ["alpha", "beta", "gamma"]
        node_ids = []
        for val in values:
            r = gov.write(WriteRequest(category="preference", key="letter", value=val, context="global"))
            node_ids.append(r["node_id"])

        # v3 supersedes v2 supersedes v1.
        targets_v3 = gov.relation_index.get_targets(node_ids[2], "SUPERSEDED_BY")
        self.assertEqual(targets_v3, [node_ids[1]])

        targets_v2 = gov.relation_index.get_targets(node_ids[1], "SUPERSEDED_BY")
        self.assertEqual(targets_v2, [node_ids[0]])

        targets_v1 = gov.relation_index.get_targets(node_ids[0], "SUPERSEDED_BY")
        self.assertEqual(targets_v1, [])

        # No cycles: verify with trace forward/backward.
        chain = gov.relation_index.trace_backward(node_ids[2])
        self.assertEqual(chain, [node_ids[2], node_ids[1], node_ids[0]])

    def test_superseded_chain_no_forks(self):
        """
        Writing to the same slot multiple times must produce a linear chain,
        not a fork (each node supersedes at most one other node).
        """
        gov = self._make_gov()

        ids = []
        for i in range(5):
            r = gov.write(WriteRequest(category="identity", key="color", value=f"c{i}", context="global"))
            ids.append(r["node_id"])

        # Each node except the last should have exactly one superseder.
        for i in range(4):
            sources = gov.relation_index.get_sources(ids[i], "SUPERSEDED_BY")
            self.assertEqual(len(sources), 1, f"Node {i} should have exactly one superseder")
            self.assertEqual(sources[0], ids[i + 1])

        # The newest node should have no superseder.
        sources_newest = gov.relation_index.get_sources(ids[4], "SUPERSEDED_BY")
        self.assertEqual(sources_newest, [])

    # ═══════════════════════════════════════════════════════════════════
    # 3. Monotonic Version Rule
    # ═══════════════════════════════════════════════════════════════════

    def test_version_monotonically_increments(self):
        """Version numbers must be 1, 2, 3, ... — strictly increasing."""
        gov = self._make_gov()

        versions = []
        for val in ["v1", "v2", "v3", "v4"]:
            r = gov.write(WriteRequest(category="preference", key="version_test", value=val, context="global"))
            versions.append(r["version"])

        self.assertEqual(versions, [1, 2, 3, 4])

        # Verify via slot index as well.
        nodes = gov.get_slot_nodes("preference:version_test@global")
        actual_versions = [n.version for n in nodes]
        self.assertEqual(actual_versions, [1, 2, 3, 4])

    def test_reinforce_does_not_change_version(self):
        """Reinforce must NOT increment version."""
        gov = self._make_gov()

        r1 = gov.write(WriteRequest(category="identity", key="email", value="a@b.com", context="global"))
        self.assertEqual(r1["version"], 1)

        gov.write(WriteRequest(category="identity", key="email", value="a@b.com", context="global"))
        gov.write(WriteRequest(category="identity", key="email", value="a@b.com", context="global"))

        active = gov.get_active("identity:email@global")
        self.assertEqual(active.version, 1)

    # ═══════════════════════════════════════════════════════════════════
    # 4. Conflict Resolution Priority
    # ═══════════════════════════════════════════════════════════════════

    def test_user_explicit_wins_over_agent_inferred(self):
        """C01: USER_EXPLICIT must reject AGENT_INFERRED."""
        gov = self._make_gov()

        # First: user sets a preference explicitly.
        gov.write(WriteRequest(
            category="preference", key="style", value="dark",
            context="global",
            source_type=SourceType.USER_EXPLICIT,
            confidence=1.0,
        ))

        # Agent tries to override with inferred value.
        result = gov.write(WriteRequest(
            category="preference", key="style", value="light",
            context="global",
            source_type=SourceType.AGENT_INFERRED,
            confidence=0.7,
        ))

        self.assertEqual(result["action"], "rejected",
                         "C01: AGENT_INFERRED must be rejected when USER_EXPLICIT exists")

        # The active node must still be the original.
        active = gov.get_active("preference:style@global")
        self.assertEqual(active.value, "dark")
        self.assertEqual(active.source_type, SourceType.USER_EXPLICIT)

    def test_agent_inferred_can_be_superseded_by_user(self):
        """C01 reverse: AGENT_INFERRED can be superseded by USER_EXPLICIT."""
        gov = self._make_gov()

        gov.write(WriteRequest(
            category="preference", key="style", value="auto",
            context="global",
            source_type=SourceType.AGENT_INFERRED,
            confidence=0.6,
        ))

        result = gov.write(WriteRequest(
            category="preference", key="style", value="dark",
            context="global",
            source_type=SourceType.USER_EXPLICIT,
            confidence=1.0,
        ))

        self.assertEqual(result["action"], "superseded",
                         "USER_EXPLICIT must supersede AGENT_INFERRED")

        active = gov.get_active("preference:style@global")
        self.assertEqual(active.value, "dark")

    def test_higher_confidence_wins_same_source_type(self):
        """C02: Higher confidence must win when source_type is the same."""
        gov = self._make_gov()

        # Create with low confidence.
        gov.write(WriteRequest(
            category="preference", key="model", value="gpt-3.5",
            context="global",
            source_type=SourceType.AGENT_INFERRED,
            confidence=0.5,
        ))

        # Try to replace with even lower confidence → should reject.
        result = gov.write(WriteRequest(
            category="preference", key="model", value="gpt-4",
            context="global",
            source_type=SourceType.AGENT_INFERRED,
            confidence=0.3,
        ))

        self.assertEqual(result["action"], "rejected",
                         "C02: Lower confidence must be rejected")

        # Replace with higher confidence → should succeed.
        result2 = gov.write(WriteRequest(
            category="preference", key="model", value="gpt-4",
            context="global",
            source_type=SourceType.AGENT_INFERRED,
            confidence=0.8,
        ))

        self.assertEqual(result2["action"], "superseded",
                         "C02: Higher confidence must supersede")

        active = gov.get_active("preference:model@global")
        self.assertEqual(active.value, "gpt-4")

    def test_same_source_type_same_confidence_newest_wins(self):
        """C03+C04: Equal confidence → newest wins (by timestamp)."""
        gov = self._make_gov()

        gov.write(WriteRequest(
            category="preference", key="editor", value="vim",
            context="global",
            source_type=SourceType.AGENT_INFERRED,
            confidence=0.7,
        ))

        result = gov.write(WriteRequest(
            category="preference", key="editor", value="vscode",
            context="global",
            source_type=SourceType.AGENT_INFERRED,
            confidence=0.7,
        ))

        self.assertEqual(result["action"], "superseded",
                         "C03: Equal confidence → newest supersedes")

        active = gov.get_active("preference:editor@global")
        self.assertEqual(active.value, "vscode")

    # ═══════════════════════════════════════════════════════════════════
    # 5. Bootstrap Consistency
    # ═══════════════════════════════════════════════════════════════════

    def test_bootstrap_recovers_slot_index(self):
        """After restart, Slot Index must contain all slots."""
        gov1 = self._make_gov()
        gov1.write(WriteRequest(category="identity", key="lang", value="python", context="global"))
        gov1.write(WriteRequest(category="preference", key="theme", value="light", context="global"))
        gov1.write(WriteRequest(category="project", key="name", value="PKIA", context="test"))

        # Rebuild.
        gov2 = self._make_gov()

        self.assertEqual(gov2.slot_index.slot_count, 3)
        slots = gov2.slot_index.list_slots()
        self.assertIn("identity:lang@global", slots)
        self.assertIn("preference:theme@global", slots)
        self.assertIn("project:name@test", slots)

    def test_bootstrap_recovers_relation_index(self):
        """After restart, Relation Index must contain HAS_MEMORY and SUPERSEDED_BY."""
        gov1 = self._make_gov()
        gov1.write(WriteRequest(category="preference", key="a", value="x", context="global"))
        gov1.write(WriteRequest(category="preference", key="a", value="y", context="global"))

        gov2 = self._make_gov()

        # Should have HAS_MEMORY (2) + SUPERSEDED_BY (1) = 3 relations.
        self.assertEqual(gov2.relation_index.relation_count, 3)
        types = gov2.relation_index.list_relation_types()
        self.assertIn("HAS_MEMORY", types)
        self.assertIn("SUPERSEDED_BY", types)

    def test_bootstrap_recovers_active_status(self):
        """After restart, only the newest version must be ACTIVE."""
        gov1 = self._make_gov()
        gov1.write(WriteRequest(category="preference", key="b", value="first", context="global"))
        gov1.write(WriteRequest(category="preference", key="b", value="second", context="global"))
        gov1.write(WriteRequest(category="preference", key="b", value="third", context="global"))

        gov2 = self._make_gov()

        active = gov2.get_active("preference:b@global")
        self.assertIsNotNone(active)
        self.assertEqual(active.value, "third")
        self.assertEqual(active.version, 3)

        nodes = gov2.get_slot_nodes("preference:b@global")
        self.assertEqual(len(nodes), 3)
        for n in nodes:
            if n.version < 3:
                self.assertEqual(n.status, MemoryStatus.DEPRECATED,
                                 f"v{n.version} must be DEPRECATED after rebuild")

    # ═══════════════════════════════════════════════════════════════════
    # 6. Trace Completeness
    # ═══════════════════════════════════════════════════════════════════

    def test_trace_backward_full_history(self):
        """trace_memory(backward) must return the complete version chain."""
        gov = self._make_gov()

        created_ids = []
        for val in ["v1", "v2", "v3", "v4"]:
            r = gov.write(WriteRequest(category="preference", key="trace_test", value=val, context="global"))
            created_ids.append(r["node_id"])

        # Trace backward from the newest.
        timeline = gov.trace_memory(created_ids[3], direction="backward")

        self.assertEqual(len(timeline), 4)
        # Order: v4 → v3 → v2 → v1
        self.assertEqual(timeline[0]["node_id"], created_ids[3])
        self.assertEqual(timeline[0]["version"], 4)
        self.assertEqual(timeline[1]["node_id"], created_ids[2])
        self.assertEqual(timeline[1]["version"], 3)
        self.assertEqual(timeline[2]["node_id"], created_ids[1])
        self.assertEqual(timeline[2]["version"], 2)
        self.assertEqual(timeline[3]["node_id"], created_ids[0])
        self.assertEqual(timeline[3]["version"], 1)

        # Each trace node should have SUPERSEDED_BY relationships (except oldest).
        self.assertEqual(len(timeline[0]["relationships"]), 1)
        self.assertEqual(timeline[0]["relationships"][0]["type"], "SUPERSEDED_BY")
        self.assertEqual(timeline[3]["relationships"], [])

    def test_trace_forward_from_oldest(self):
        """trace_memory(forward) from the oldest must reach the newest."""
        gov = self._make_gov()

        values = ["first", "second", "third"]
        ids = []
        for val in values:
            r = gov.write(WriteRequest(category="preference", key="fw_test", value=val, context="global"))
            ids.append(r["node_id"])

        # Trace forward from the oldest.
        timeline = gov.trace_memory(ids[0], direction="forward")

        self.assertEqual(len(timeline), 3)
        self.assertEqual(timeline[0]["node_id"], ids[0])
        self.assertEqual(timeline[0]["version"], 1)
        self.assertEqual(timeline[2]["node_id"], ids[2])
        self.assertEqual(timeline[2]["version"], 3)

    def test_trace_bootstrap_preserves_chain(self):
        """After rebuild, trace_memory must still return the full chain."""
        gov1 = self._make_gov()
        ids = []
        for val in ["a", "b", "c"]:
            r = gov1.write(WriteRequest(category="preference", key="chain", value=val, context="global"))
            ids.append(r["node_id"])

        gov2 = self._make_gov()

        timeline = gov2.trace_memory(ids[2], direction="backward")
        self.assertEqual(len(timeline), 3)
        self.assertEqual(timeline[0]["version"], 3)
        self.assertEqual(timeline[2]["version"], 1)


if __name__ == "__main__":
    unittest.main()