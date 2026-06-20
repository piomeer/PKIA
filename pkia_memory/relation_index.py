"""
pkia_memory.relation_index — In-memory Relation Index.

Builds and maintains bidirectional indexes for quick relation traversal.

MCP Memory Server does not support querying relations by type or direction,
so the Governor maintains two in-memory maps:

  - forward:  source_id → { relation_type → [target_id, ...] }
  - reverse:  target_id → { relation_type → [source_id, ...] }

Responsibilities:
  - Index all relations on startup (from read_graph data).
  - Lookup SUPERSEDED_BY targets (for version chain traversal).
  - Lookup HAS_MEMORY targets (for entity → memory resolution).
  - Trace version chains in both directions.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Optional

from .models import RelationRecord


class RelationIndex:
    """
    Bidirectional in-memory relation index.

    Usage::

        index = RelationIndex()
        index.index_relation(RelationRecord(from, to, "SUPERSEDED_BY"))

        # Find what mem_v3 supersedes:
        index.get_targets("mem_v3", "SUPERSEDED_BY")  # -> ["mem_v2"]

        # Find what supersedes mem_v2:
        index.get_sources("mem_v2", "SUPERSEDED_BY")  # -> ["mem_v3"]
    """

    def __init__(self) -> None:
        # forward: source_id → relation_type → [target_id, ...]
        self._forward: dict[str, dict[str, list[str]]] = defaultdict(
            lambda: defaultdict(list)
        )
        # reverse: target_id → relation_type → [source_id, ...]
        self._reverse: dict[str, dict[str, list[str]]] = defaultdict(
            lambda: defaultdict(list)
        )

        # Flat list of all relation records (for iteration).
        self._all: list[RelationRecord] = []

    # ── population ─────────────────────────────────────────────────────

    def index_relation(self, record: RelationRecord) -> None:
        """Register a single relation record."""
        self._all.append(record)
        self._forward[record.source_id][record.relation_type].append(record.target_id)
        self._reverse[record.target_id][record.relation_type].append(record.source_id)

    def index_relations(self, records: list[RelationRecord]) -> None:
        """Bulk register relations (used during startup)."""
        for record in records:
            self.index_relation(record)

    # ── forward lookup ─────────────────────────────────────────────────

    def get_targets(self, source_id: str, relation_type: str) -> list[str]:
        """
        Return all target entity names for a given source and relation type.

        Example: ``get_targets("mem_v3", "SUPERSEDED_BY")``
          returns ``["mem_v2"]``
        """
        return list(self._forward.get(source_id, {}).get(relation_type, []))

    def has_target(self, source_id: str, relation_type: str, target_id: str) -> bool:
        """Check if a specific relation exists."""
        return target_id in self._forward.get(source_id, {}).get(relation_type, [])

    # ── reverse lookup ─────────────────────────────────────────────────

    def get_sources(self, target_id: str, relation_type: str) -> list[str]:
        """
        Return all source entity names that point to this target.

        Example: ``get_sources("mem_v2", "SUPERSEDED_BY")``
          returns ``["mem_v3"]``  (mem_v3 supersedes mem_v2)
        """
        return list(self._reverse.get(target_id, {}).get(relation_type, []))

    # ── relation-type queries ──────────────────────────────────────────

    def get_relations_by_type(self, relation_type: str) -> list[RelationRecord]:
        """Return all relations of a given type."""
        return [
            r for r in self._all if r.relation_type == relation_type
        ]

    def get_relations_from(self, source_id: str) -> list[RelationRecord]:
        """Return all relations where source_id is the source."""
        type_map = self._forward.get(source_id, {})
        result: list[RelationRecord] = []
        for rtype, targets in type_map.items():
            for t in targets:
                result.append(RelationRecord(
                    source_id=source_id,
                    target_id=t,
                    relation_type=rtype,
                ))
        return result

    # ── version chain traversal ────────────────────────────────────────

    def trace_backward(self, node_id: str, max_depth: int = 10) -> list[str]:
        """
        Follow SUPERSEDED_BY relations backward (new → old).

        Returns a chain of node_ids from the input node toward the oldest version.
        The input node is the first element.
        """
        chain: list[str] = []
        current = node_id
        for _ in range(max_depth):
            chain.append(current)
            targets = self.get_targets(current, "SUPERSEDED_BY")
            if not targets:
                break
            current = targets[0]  # Follow the first SUPERSEDED_BY (should be only one)
        return chain

    def trace_forward(self, node_id: str, max_depth: int = 10) -> list[str]:
        """
        Follow SUPERSEDED_BY relations forward (old → new).

        Returns a chain of node_ids from the input node toward the newest version.
        The input node is the first element.
        """
        chain: list[str] = []
        current = node_id
        for _ in range(max_depth):
            chain.append(current)
            sources = self.get_sources(current, "SUPERSEDED_BY")
            if not sources:
                break
            current = sources[0]
        return chain

    # ── introspection ──────────────────────────────────────────────────

    @property
    def relation_count(self) -> int:
        return len(self._all)

    def list_relation_types(self) -> set[str]:
        """Return all relation types present in the index."""
        types: set[str] = set()
        for record in self._all:
            types.add(record.relation_type)
        return types