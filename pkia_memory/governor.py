"""
pkia_memory.governor — Memory Governor: the central coordinator of L2 Memory OS.

The Governor sits between the Agent (caller) and the MCP Memory Server
(persistence layer).  It maintains in-memory Slot + Relation indexes so that
all reads are served from memory (fast, no MCP calls), and writes are
translated into MCP command payloads that the Agent executes.

Architecture::

    Agent / Cline
        │
        ▼
    Governor
        ├── SlotIndex        (in-memory: slot_id → active node)
        ├── RelationIndex    (in-memory: from→to bidirectional)
        └── memory_service   (JSON Lines loader + MCP command builder)
        │
        ▼
    MCP Memory Server
        └── pkia-memory.json (persistence only, no queries)

Lifecycle::

    1. governor.startup(path)   — loads JSON Lines, builds indexes
    2. governor.get_active(...) — O(1) lookup from SlotIndex
    3. governor.write(...)      — validate → decide → return MCP commands
    4. governor.shutdown()      — no-op (data persisted by MCP)

Write decisions (mapping from Schema v1.0 rule set)::

    W01  Duplicate Detection  →  value matches existing ACTIVE?
        YES → W02 Reinforce
        NO  → W03 Conflict Detection
    W03  Slot Conflict        →  slot has existing ACTIVE?
        YES → W04 Supersede
        NO  → W05 Create
    C01-C04  Conflict priority → source_type → confidence → time
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import (
    MemoryNode,
    MemoryStatus,
    RelationRecord,
    SourceType,
    WriteRequest,
)
from .slot_index import SlotIndex
from .relation_index import RelationIndex
from . import memory_service as svc

logger = logging.getLogger(__name__)


class Governor:
    """
    PKIA L2 Memory Governor.

    Usage::

        gov = Governor()
        gov.startup("pkia-memory.json")

        # Read
        node = gov.get_active("preference:response_language@global")

        # Write
        result = gov.write(WriteRequest(
            category="preference",
            key="response_language",
            value="zh-CN",
        ))
        # result["commands"] → list of MCP tool payloads for the Agent to execute
    """

    def __init__(self) -> None:
        self.slot_index = SlotIndex()
        self.relation_index = RelationIndex()
        self._storage_path: Optional[str] = None
        self._ready = False

    # ── Startup / Bootstrap ────────────────────────────────────────────

    def startup(self, storage_path: str | Path) -> None:
        """
        Load all data from the JSON Lines file and build in-memory indexes.

        This is the only expensive operation — it reads the full graph.
        After startup, all reads are O(1) from memory.
        """
        self._storage_path = str(storage_path)
        nodes, relations = svc.load_json_lines(storage_path)

        # Index all MemoryNodes.
        for node in nodes:
            self.slot_index.index_node(node)

        # Index all relations.
        self.relation_index.index_relations(relations)

        self._ready = True
        logger.info(
            "Governor started: %d nodes, %d slots, %d relations",
            self.slot_index.node_count,
            self.slot_index.slot_count,
            self.relation_index.relation_count,
        )

    @property
    def is_ready(self) -> bool:
        return self._ready

    # ── Read operations ────────────────────────────────────────────────

    def get_active(self, slot_id: str) -> Optional[MemoryNode]:
        """
        Return the ACTIVE MemoryNode for a given slot_id.

        Pure memory lookup — does not call MCP.
        """
        return self.slot_index.get_active(slot_id)

    def get_node(self, node_id: str) -> Optional[MemoryNode]:
        """Return any node by its node_id."""
        return self.slot_index.get_node(node_id)

    def get_slot_nodes(self, slot_id: str) -> list[MemoryNode]:
        """Return all versions of a slot (for version chain display)."""
        return self.slot_index.get_slot_nodes(slot_id)

    def get_context_memory(
        self,
        context: str,
        tier_filter: Optional[list[str]] = None,
    ) -> list[MemoryNode]:
        """
        Return all ACTIVE nodes in a given context.

        Optionally filter by tier (category).
        """
        nodes = self.slot_index.get_nodes_by_context(context)
        if tier_filter is not None:
            nodes = [n for n in nodes if n.category in tier_filter]
        # Sort: identity > preference > project > working
        _tier_order = {"identity": 0, "preference": 1, "project": 2, "working": 3}
        nodes.sort(key=lambda n: (_tier_order.get(n.category, 9), -n.reinforcement_count))
        return nodes

    def trace_memory(
        self,
        node_id: str,
        direction: str = "backward",
        max_depth: int = 10,
    ) -> list[dict]:
        """
        Trace the version chain of a memory node.

        Returns a list of TraceNode dicts (not MemoryNode objects) for
        JSON-serializable output.  Each TraceNode has::

            {
                "node_id": "...",
                "version": 3,
                "status": "ACTIVE",
                "value": "...",
                "relationships": [
                    {"type": "SUPERSEDED_BY", "target_id": "..."},
                ]
            }
        """
        node_ids: list[str] = []
        if direction == "backward":
            node_ids = self.relation_index.trace_backward(node_id, max_depth)
        else:
            node_ids = self.relation_index.trace_forward(node_id, max_depth)

        timeline: list[dict] = []
        for i, nid in enumerate(node_ids):
            node = self.slot_index.get_node(nid)
            if node is None:
                continue

            # Find relations from this node to the next in chain.
            rels: list[dict] = []
            if i + 1 < len(node_ids):
                next_id = node_ids[i + 1]
                if self.relation_index.has_target(nid, "SUPERSEDED_BY", next_id):
                    rels.append({"type": "SUPERSEDED_BY", "target_id": next_id})
                # Also check DERIVED_FROM
                derived = self.relation_index.get_targets(nid, "DERIVED_FROM")
                for d in derived:
                    rels.append({"type": "DERIVED_FROM", "target_id": d})

            timeline.append({
                "node_id": node.node_id,
                "version": node.version,
                "status": node.status.value,
                "value": node.value,
                "confidence": node.confidence,
                "source_type": node.source_type.value,
                "created_at": node.created_at.isoformat(),
                "relationships": rels,
            })

        return timeline

    # ── Write operations ───────────────────────────────────────────────

    def write(self, request: WriteRequest) -> dict:
        """
        Process a write request and return MCP command payloads.

        Decision tree (Schema v1.0 rules W01-W05, C01-C04):

        1. Check if the slot already has an ACTIVE node.
           - No ACTIVE  → W05 (create new)
           - Has ACTIVE → compare value → W02 (reinforce) or W04 (supersede)

        2. Return a dict with:
           - "action": "created" | "reinforced" | "superseded" | "rejected"
           - "node": the affected MemoryNode
           - "commands": list of MCP tool payloads (Agent must execute these)
           - "reason": explanation of the decision
        """
        if not self._ready:
            raise RuntimeError("Governor not started. Call startup() first.")

        active_node = self.slot_index.get_active(request.slot_id)

        # W05: No existing ACTIVE → create new.
        if active_node is None:
            return self._action_create(request)

        # W01: Duplicate detection — same value?
        if active_node.value == request.value:
            return self._action_reinforce(active_node)

        # W03 / C01-C04: Conflict — different value, run arbitration.
        return self._action_supersede(request, active_node)

    # ── Internal write actions ─────────────────────────────────────────

    def _action_create(self, request: WriteRequest) -> dict:
        """W05: Create a new node in an empty slot."""
        now = datetime.utcnow()
        node = MemoryNode(
            node_id=svc.new_node_id(),
            category=request.category,
            key=request.key,
            value=request.value,
            context=request.context,
            status=MemoryStatus.ACTIVE,
            confidence=request.confidence,
            source_type=request.source_type,
            created_at=now,
            updated_at=now,
            expires_at=request.expires_at,
            version=1,
            reinforcement_count=1,
        )

        # Register in memory index.
        self.slot_index.index_node(node)
        self.relation_index.index_relation(RelationRecord(
            source_id="PKIA_Project",
            target_id=node.node_id,
            relation_type="HAS_MEMORY",
        ))

        return {
            "action": "created",
            "node_id": node.node_id,
            "slot_id": node.slot_id,
            "version": node.version,
            "reason": f"New slot {node.slot_id}: created v{node.version}",
            "commands": svc.build_create_result(node, [
                RelationRecord("PKIA_Project", node.node_id, "HAS_MEMORY"),
            ]),
        }

    def _action_reinforce(self, active_node: MemoryNode) -> dict:
        """W02: Same value → reinforce existing node."""
        old_count = active_node.reinforcement_count
        self.slot_index.reinforce_node(active_node.node_id)

        return {
            "action": "reinforced",
            "node_id": active_node.node_id,
            "slot_id": active_node.slot_id,
            "version": active_node.version,
            "reinforcement_count": active_node.reinforcement_count,
            "reason": (
                f"Duplicate value for {active_node.slot_id}: "
                f"reinforcement_count {old_count} → {active_node.reinforcement_count}"
            ),
            "commands": svc.build_reinforce_result(
                node_id=active_node.node_id,
                count=active_node.reinforcement_count,
                updated_at=active_node.updated_at.isoformat(),
            ),
        }

    def _action_supersede(self, request: WriteRequest, old_node: MemoryNode) -> dict:
        """W04 + C01-C04: New value → supersede (or reject)."""
        # C01: USER_EXPLICIT always beats AGENT_INFERRED.
        if old_node.source_type == SourceType.USER_EXPLICIT and \
           request.source_type == SourceType.AGENT_INFERRED:
            return {
                "action": "rejected",
                "node_id": old_node.node_id,
                "slot_id": old_node.slot_id,
                "version": old_node.version,
                "reason": (
                    f"C01: USER_EXPLICIT value '{old_node.value}' takes priority "
                    f"over AGENT_INFERRED '{request.value}'"
                ),
                "commands": [],
            }

        # C01 reverse: Agent inferred → but user explicitly says otherwise.
        if old_node.source_type == SourceType.AGENT_INFERRED and \
           request.source_type == SourceType.USER_EXPLICIT:
            # Proceed with supersede — user always wins over agent inference.
            pass

        # C02-C04: Compare confidence if same source_type.
        if old_node.source_type == request.source_type:
            if old_node.confidence > request.confidence:
                return {
                    "action": "rejected",
                    "node_id": old_node.node_id,
                    "slot_id": old_node.slot_id,
                    "version": old_node.version,
                    "reason": (
                        f"C02: Existing confidence {old_node.confidence} > "
                        f"new confidence {request.confidence}"
                    ),
                    "commands": [],
                }
            # Equal confidence → newest wins (C03). Reinforcement count tiebreaker (C04).

        # ── Proceed with supersede ──────────────────────────────────────
        now = datetime.utcnow()
        new_version = old_node.version + 1

        new_node = MemoryNode(
            node_id=svc.new_node_id(),
            category=request.category,
            key=request.key,
            value=request.value,
            context=request.context,
            status=MemoryStatus.ACTIVE,
            confidence=request.confidence,
            source_type=request.source_type,
            created_at=now,
            updated_at=now,
            expires_at=request.expires_at,
            version=new_version,
            reinforcement_count=1,
        )

        # Update memory index.
        self.slot_index.index_node(new_node)
        self.slot_index.update_node_status(old_node.node_id, "DEPRECATED")

        # Update relation index.
        self.relation_index.index_relation(RelationRecord(
            source_id=new_node.node_id,
            target_id=old_node.node_id,
            relation_type="SUPERSEDED_BY",
        ))
        self.relation_index.index_relation(RelationRecord(
            source_id="PKIA_Project",
            target_id=new_node.node_id,
            relation_type="HAS_MEMORY",
        ))

        return {
            "action": "superseded",
            "node_id": new_node.node_id,
            "slot_id": new_node.slot_id,
            "version": new_node.version,
            "old_node_id": old_node.node_id,
            "old_version": old_node.version,
            "reason": (
                f"Superseded {old_node.slot_id}: "
                f"v{old_node.version} ({old_node.value}) → "
                f"v{new_node.version} ({new_node.value})"
            ),
            "commands": svc.build_supersede_result(new_node, old_node.node_id),
        }

    # ── Status ─────────────────────────────────────────────────────────

    def status(self) -> dict:
        """Return a snapshot of the Governor's current state (for debugging)."""
        return {
            "ready": self._ready,
            "storage_path": self._storage_path,
            "node_count": self.slot_index.node_count,
            "slot_count": self.slot_index.slot_count,
            "relation_count": self.relation_index.relation_count,
            "relation_types": sorted(self.relation_index.list_relation_types()),
            "slots": self.slot_index.list_slots(),
        }

    def shutdown(self) -> None:
        """
        Shutdown the Governor.

        Currently a no-op because data is persisted by MCP.
        Future versions may flush pending writes or close connections.
        """
        self._ready = False
        logger.info("Governor shut down.")