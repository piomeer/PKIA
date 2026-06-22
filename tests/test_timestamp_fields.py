"""
Tests for Memory Timestamp Extension v1.0.

Verifies:
  1. Create → created_at and updated_at both set, equal
  2. Reinforce → created_at unchanged, updated_at changes
  3. Supersede → old node updated_at updated, new node created_at == updated_at
  4. Persistence → timestamps survive restart
  5. Backward Compatibility → legacy records load without crash
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from pkia_memory.models import MemoryNode, MemoryStatus, SourceType, WriteRequest
from pkia_memory.governor import Governor


class TestTimestampFields(unittest.TestCase):
    """Memory Timestamp Extension v1.0 — Field behavior verification."""

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        )
        self.tmp.close()
        self.path = Path(self.tmp.name)

    def tearDown(self):
        os.unlink(self.path)

    # ── 1. Create ──────────────────────────────────────────────────────

    def test_create_sets_both_timestamps_equal(self):
        """Created node must have created_at == updated_at."""
        gov = Governor()
        gov.startup(self.path)

        result = gov.write(WriteRequest(
            category="preference", key="test_ts", value="v1",
            context="global",
        ))

        self.assertEqual(result["action"], "created")
        node = gov.get_node(result["node_id"])

        self.assertIsNotNone(node.created_at)
        self.assertIsNotNone(node.updated_at)
        self.assertEqual(node.created_at, node.updated_at)

    # ── 2. Reinforce ───────────────────────────────────────────────────

    def test_reinforce_updates_updated_at_only(self):
        """Reinforce must change updated_at but leave created_at unchanged."""
        gov = Governor()
        gov.startup(self.path)

        result = gov.write(WriteRequest(
            category="preference", key="reinforce_ts", value="v1",
            context="global",
        ))
        node_id = result["node_id"]
        node = gov.get_node(node_id)
        original_created = node.created_at
        original_updated = node.updated_at

        # Reinforce.
        gov.write(WriteRequest(
            category="preference", key="reinforce_ts", value="v1",
            context="global",
        ))

        node_after = gov.get_node(node_id)
        self.assertEqual(node_after.created_at, original_created,
                         "created_at must not change on reinforce")
        self.assertNotEqual(node_after.updated_at, original_updated,
                            "updated_at must change on reinforce")
        self.assertGreater(node_after.updated_at, original_updated,
                           "updated_at must advance on reinforce")

    # ── 3. Supersede ───────────────────────────────────────────────────

    def test_supersede_new_node_timestamps_equal(self):
        """New node from supersede must have created_at == updated_at."""
        gov = Governor()
        gov.startup(self.path)

        gov.write(WriteRequest(
            category="preference", key="supersede_ts", value="v1",
            context="global",
        ))

        result = gov.write(WriteRequest(
            category="preference", key="supersede_ts", value="v2",
            context="global",
        ))
        self.assertEqual(result["action"], "superseded")

        new_node = gov.get_node(result["node_id"])
        self.assertIsNotNone(new_node.created_at)
        self.assertIsNotNone(new_node.updated_at)
        self.assertEqual(new_node.created_at, new_node.updated_at)

    def test_supersede_old_node_updated_at_advances(self):
        """Old node's updated_at must advance when superseded."""
        gov = Governor()
        gov.startup(self.path)

        r1 = gov.write(WriteRequest(
            category="preference", key="supersede_ts2", value="v1",
            context="global",
        ))
        old_id = r1["node_id"]
        old_node_before = gov.get_node(old_id)
        old_updated_before = old_node_before.updated_at

        gov.write(WriteRequest(
            category="preference", key="supersede_ts2", value="v2",
            context="global",
        ))

        old_node_after = gov.get_node(old_id)
        self.assertGreater(old_node_after.updated_at, old_updated_before,
                           "old node's updated_at must advance after supersede")

    # ── 4. Persistence ─────────────────────────────────────────────────

    def test_timestamps_survive_restart(self):
        """After restart, timestamps must be correctly restored."""
        gov1 = Governor()
        gov1.startup(self.path)

        gov1.write(WriteRequest(
            category="preference", key="persist_ts", value="v1",
            context="global",
        ))

        # Rebuild.
        gov2 = Governor()
        gov2.startup(self.path)

        node = gov2.get_active("preference:persist_ts@global")
        self.assertIsNotNone(node)
        self.assertIsNotNone(node.created_at, "created_at must survive restart")
        self.assertIsNotNone(node.updated_at, "updated_at must survive restart")
        self.assertEqual(node.created_at, node.updated_at)

    # ── 5. Backward Compatibility ──────────────────────────────────────

    def test_legacy_record_missing_timestamps(self):
        """A record without created_at/updated_at must load without error."""
        # Write a legacy-format entity line directly to the file.
        legacy = {
            "type": "entity",
            "name": "mem_legacy_001",
            "entityType": "MemoryNode",
            "observations": [
                "node_id: mem_legacy_001",
                "category: identity",
                "key: legacy_field",
                "value: still_works",
                "context: global",
                "status: ACTIVE",
                "confidence: 1.0",
                "source_type: USER_EXPLICIT",
                "version: 1",
                "reinforcement_count: 1",
                # NOTE: no created_at, no updated_at
            ],
        }
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(legacy, ensure_ascii=False) + "\n")

        # Load — must not crash.
        gov = Governor()
        gov.startup(self.path)

        node = gov.get_active("identity:legacy_field@global")
        self.assertIsNotNone(node)
        self.assertIsNone(node.created_at, "Legacy record: created_at must be None")
        self.assertIsNone(node.updated_at, "Legacy record: updated_at must be None")
        self.assertEqual(node.value, "still_works")
        self.assertTrue(node.is_active)

    def test_mixed_legacy_and_new_records(self):
        """Mix of legacy and new records must load and index correctly."""
        # Write a legacy record first.
        legacy = {
            "type": "entity",
            "name": "mem_legacy_002",
            "entityType": "MemoryNode",
            "observations": [
                "node_id: mem_legacy_002",
                "category: preference", "key: legacy_mix", "value: old",
                "context: global", "status: ACTIVE", "confidence: 1.0",
                "source_type: USER_EXPLICIT", "version: 1", "reinforcement_count: 1",
            ],
        }
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(legacy, ensure_ascii=False) + "\n")

        gov = Governor()
        gov.startup(self.path)

        # Write a new record via Governor (includes timestamps).
        result = gov.write(WriteRequest(
            category="preference", key="new_mix", value="new_value",
            context="global",
        ))

        # Both should be accessible.
        legacy_node = gov.get_active("preference:legacy_mix@global")
        new_node = gov.get_active("preference:new_mix@global")

        self.assertIsNotNone(legacy_node)
        self.assertIsNone(legacy_node.created_at)

        self.assertIsNotNone(new_node)
        self.assertIsNotNone(new_node.created_at)

        # Version chain must be intact.
        self.assertEqual(gov.slot_index.node_count, 2)
        self.assertEqual(gov.slot_index.slot_count, 2)


if __name__ == "__main__":
    unittest.main()