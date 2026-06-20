"""
pkia_memory.slot_index — In-memory Slot Index.

Builds and maintains a dictionary that maps ``slot_id`` → ``SlotInfo``.

Each slot_id is ``category:key@context`` (e.g. ``preference:response_language@global``).

Responsibilities:
  - Index all MemoryNodes by slot_id on startup (populate from parsed data).
  - Lookup the current ACTIVE node for any slot in O(1).
  - Track version_count so the Governor can assign the next version.
  - Track all node_ids belonging to a slot for version-chain traversal.
"""

from __future__ import annotations

from typing import Optional

from .models import MemoryNode, SlotInfo


class SlotIndex:
    """
    Fast in-memory lookup for memory slots.

    Usage::

        index = SlotIndex()
        index.index_node(node)           # register a parsed MemoryNode
        info = index.get_slot(slot_id)   # -> SlotInfo | None
        active = index.get_active(slot_id)  # -> MemoryNode | None
    """

    def __init__(self) -> None:
        # slot_id → SlotInfo
        self._slots: dict[str, SlotInfo] = {}

        # node_id → MemoryNode (all nodes, regardless of status)
        self._nodes: dict[str, MemoryNode] = {}

    # ── population ─────────────────────────────────────────────────────

    def index_node(self, node: MemoryNode) -> None:
        """
        Register a parsed MemoryNode into the index.

        Called during bootstrap for every node loaded from the graph,
        and after every successful write.
        """
        self._nodes[node.node_id] = node

        if node.slot_id not in self._slots:
            self._slots[node.slot_id] = SlotInfo(slot_id=node.slot_id)

        self._slots[node.slot_id].add_node(node)

    def get_node(self, node_id: str) -> Optional[MemoryNode]:
        """Retrieve a single node by its node_id."""
        return self._nodes.get(node_id)

    def all_nodes(self) -> list[MemoryNode]:
        """Return all indexed nodes (for bootstrap iteration)."""
        return list(self._nodes.values())

    # ── lookup ─────────────────────────────────────────────────────────

    def get_slot(self, slot_id: str) -> Optional[SlotInfo]:
        """Return the SlotInfo for a given slot_id, or None if unknown."""
        return self._slots.get(slot_id)

    def get_active(self, slot_id: str) -> Optional[MemoryNode]:
        """
        Return the ACTIVE MemoryNode for a given slot_id.

        Returns None if:
          - the slot does not exist, or
          - no node in the slot has status=ACTIVE.
        """
        info = self._slots.get(slot_id)
        if info is None or info.active_node_id is None:
            return None
        return self._nodes.get(info.active_node_id)

    def get_slot_nodes(self, slot_id: str) -> list[MemoryNode]:
        """
        Return all nodes belonging to a slot (all statuses).

        The result is sorted by version ascending (oldest first).

        Used for:
          - version chain traversal
          - trace_memory backward direction
        """
        info = self._slots.get(slot_id)
        if info is None:
            return []
        nodes = [self._nodes[nid] for nid in info._node_ids if nid in self._nodes]
        nodes.sort(key=lambda n: n.version)
        return nodes

    def get_nodes_by_context(self, context: str) -> list[MemoryNode]:
        """
        Return all ACTIVE nodes that match a given context.

        Used by ``get_context_memory()``.
        """
        result: list[MemoryNode] = []
        for node in self._nodes.values():
            if node.context == context and node.is_active:
                result.append(node)
        return result

    def has_slot(self, slot_id: str) -> bool:
        """Check whether a slot exists in the index."""
        return slot_id in self._slots

    # ── mutation ───────────────────────────────────────────────────────

    def update_node_status(self, node_id: str, new_status: str) -> None:
        """
        Change the status of an existing node (in memory only).

        The caller (Governor) is responsible for persisting this change
        via MCP *after* updating the in-memory index.
        """
        node = self._nodes.get(node_id)
        if node is None:
            return

        from .models import MemoryStatus
        old_status = node.status
        node.status = MemoryStatus(new_status)

        # If the node was ACTIVE and is no longer, refresh slot's active pointer.
        if old_status == MemoryStatus.ACTIVE and node.status != MemoryStatus.ACTIVE:
            info = self._slots.get(node.slot_id)
            if info is not None and info.active_node_id == node_id:
                info.active_node_id = None

        # If the node became ACTIVE, update the slot pointer.
        if node.status == MemoryStatus.ACTIVE:
            info = self._slots.get(node.slot_id)
            if info is not None:
                info.active_node_id = node_id
                info.last_updated = node.updated_at

    def reinforce_node(self, node_id: str) -> None:
        """
        Increment reinforcement_count and update confidence.

        Called when duplicate detection triggers W02.
        """
        node = self._nodes.get(node_id)
        if node is None:
            return

        from datetime import datetime
        node.reinforcement_count += 1
        node.updated_at = datetime.utcnow()

        # Recalculate confidence.
        # Formula: confidence = 1 - (1 - initial_confidence)^count
        # For USER_EXPLICIT nodes, initial is 1.0 so this is a no-op.
        if node.confidence < 1.0:
            initial = node.confidence / max(node.reinforcement_count - 1, 1)
            new_conf = 1.0 - (1.0 - initial) ** node.reinforcement_count
            node.confidence = round(min(new_conf, 1.0), 4)

    # ── introspection ──────────────────────────────────────────────────

    @property
    def slot_count(self) -> int:
        return len(self._slots)

    @property
    def node_count(self) -> int:
        return len(self._nodes)

    def list_slots(self) -> list[str]:
        """Return all known slot_ids (sorted)."""
        return sorted(self._slots.keys())