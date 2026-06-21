"""
Tests for the Governor persistence layer (P0.6).

Verifies that:
  1. create → entity + relation written to file
  2. reinforce → observation update appended to file
  3. supersede → new entity + status update + relations appended to file
  4. startup() → rebuilds indexes from file, recovers ACTIVE status
  5. startup on empty file → empty index

Each test uses a temporary JSON Lines file so it does NOT touch the
real pkia-memory.json.
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from pkia_memory.models import (
    MemoryNode,
    MemoryStatus,
    RelationRecord,
    SourceType,
    WriteRequest,
)
from pkia_memory.governor import Governor
from pkia_memory import memory_service as svc


def _count_lines(path: Path) -> int:
    """Count non-empty lines in a file."""
    with path.open("r", encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def _read_all_lines(path: Path) -> list[dict]:
    """Read all JSON Lines from a file."""
    result: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                result.append(json.loads(line))
    return result


class TestPersistence(unittest.TestCase):
    """Verify that Governor writes survive to disk and can be rebuilt."""

    def setUp(self):
        """Create a temporary JSON Lines file for each test."""
        self.tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        )
        self.tmp.close()
        self.path = Path(self.tmp.name)

    def tearDown(self):
        """Remove the temporary file."""
        os.unlink(self.path)

    # ── 1. Create ──────────────────────────────────────────────────────

    def test_create_writes_entity_and_relation_to_file(self):
        """After create(), the file should contain the entity + relation lines."""
        gov = Governor()
        gov.startup(self.path)

        before = _count_lines(self.path)

        result = gov.write(WriteRequest(
            category="preference",
            key="language",
            value="zh-CN",
            context="global",
        ))

        self.assertEqual(result["action"], "created")
        after = _count_lines(self.path)
        self.assertEqual(after - before, 2, "File should have 2 new lines")

        lines = _read_all_lines(self.path)
        entity_lines = [l for l in lines if l.get("type") == "entity"]
        relation_lines = [l for l in lines if l.get("type") == "relation"]
        self.assertEqual(len(entity_lines), 1)
        self.assertEqual(len(relation_lines), 1)
        self.assertEqual(relation_lines[0]["relationType"], "HAS_MEMORY")

    # ── 2. Reinforce ───────────────────────────────────────────────────

    def test_reinforce_appends_observation_marker(self):
        """Reinforcing the same value should append an observation_update."""
        gov = Governor()
        gov.startup(self.path)

        gov.write(WriteRequest(
            category="preference",
            key="language",
            value="zh-CN",
            context="global",
        ))

        before = _count_lines(self.path)

        result = gov.write(WriteRequest(
            category="preference",
            key="language",
            value="zh-CN",
            context="global",
        ))

        self.assertEqual(result["action"], "reinforced")
        after = _count_lines(self.path)
        self.assertEqual(after - before, 1, "Reinforce should append 1 line")

        lines = _read_all_lines(self.path)
        update_lines = [l for l in lines if l.get("type") == "observation_update"]
        self.assertGreaterEqual(len(update_lines), 1)
        last_update = update_lines[-1]
        obs_text = " ".join(last_update["observations"])
        self.assertIn("reinforcement_count: 2", obs_text)

    # ── 3. Supersede ───────────────────────────────────────────────────

    def test_supersede_appends_entity_status_and_relations(self):
        """Superseding should write: new entity + status update + 2 relations."""
        gov = Governor()
        gov.startup(self.path)

        gov.write(WriteRequest(
            category="preference",
            key="language",
            value="zh-CN",
            context="global",
        ))

        before = _count_lines(self.path)

        result = gov.write(WriteRequest(
            category="preference",
            key="language",
            value="en-US",
            context="global",
        ))

        self.assertEqual(result["action"], "superseded")
        after = _count_lines(self.path)
        self.assertEqual(after - before, 4, "Supersede should append 4 lines")

    # ── 4. Rebuild from file recovers ACTIVE status ────────────────────

    def test_rebuild_recovers_active_node(self):
        """After creating a node, a new Governor instance should see it as ACTIVE."""
        gov1 = Governor()
        gov1.startup(self.path)

        gov1.write(WriteRequest(
            category="identity",
            key="name",
            value="TestUser",
            context="global",
        ))

        gov2 = Governor()
        gov2.startup(self.path)

        active = gov2.get_active("identity:name@global")
        self.assertIsNotNone(active, "Rebuilt Governor should find the node")
        self.assertEqual(active.value, "TestUser")
        self.assertTrue(active.is_active)

    def test_rebuild_recovers_superseded_chain(self):
        """After supersede, a new Governor should see only v2 as ACTIVE."""
        gov1 = Governor()
        gov1.startup(self.path)

        gov1.write(WriteRequest(
            category="preference",
            key="theme",
            value="dark",
            context="global",
        ))
        gov1.write(WriteRequest(
            category="preference",
            key="theme",
            value="light",
            context="global",
        ))

        gov2 = Governor()
        gov2.startup(self.path)

        active = gov2.get_active("preference:theme@global")
        self.assertIsNotNone(active)
        self.assertEqual(active.value, "light")
        self.assertEqual(active.version, 2)

        nodes = gov2.get_slot_nodes("preference:theme@global")
        versions = {n.version: n.status for n in nodes}
        self.assertEqual(versions[1], MemoryStatus.DEPRECATED)
        self.assertEqual(versions[2], MemoryStatus.ACTIVE)

    def test_rebuild_recovers_reinforcement_count(self):
        """
        Reinforcement count is NOT recoverable from file (it's runtime state).
        After rebuild, the count should be 1 (the entity line's initial value).
        """
        gov1 = Governor()
        gov1.startup(self.path)

        gov1.write(WriteRequest(
            category="preference",
            key="verbosity",
            value="concise",
            context="global",
        ))
        gov1.write(WriteRequest(
            category="preference",
            key="verbosity",
            value="concise",
            context="global",
        ))

        gov2 = Governor()
        gov2.startup(self.path)

        active = gov2.get_active("preference:verbosity@global")
        self.assertIsNotNone(active)
        self.assertEqual(active.reinforcement_count, 1)

    # ── 5. Empty file startup ──────────────────────────────────────────

    def test_startup_empty_file_returns_empty_index(self):
        """Starting on an empty file should give an empty Governor."""
        gov = Governor()
        gov.startup(self.path)

        self.assertTrue(gov.is_ready)
        self.assertEqual(gov.slot_index.node_count, 0)
        self.assertEqual(gov.slot_index.slot_count, 0)

        result = gov.write(WriteRequest(
            category="identity",
            key="test",
            value="hello",
            context="global",
        ))
        self.assertEqual(result["action"], "created")


if __name__ == "__main__":
    unittest.main()