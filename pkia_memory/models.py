"""
pkia_memory.models — Core data types for L2 Memory OS.

Defines the in-memory representations of:
  - MemoryNode: a single memory record (the fundamental unit)
  - SlotInfo: the index entry for a slot
  - RelationRecord: a directed edge between two nodes
  - WriteRequest: a parsed write operation ready for Governor processing
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


# ── Enums ──────────────────────────────────────────────────────────────

class MemoryStatus(str, Enum):
    ACTIVE = "ACTIVE"
    DRAFT = "DRAFT"
    DEPRECATED = "DEPRECATED"
    ARCHIVED = "ARCHIVED"


class SourceType(str, Enum):
    USER_EXPLICIT = "USER_EXPLICIT"
    AGENT_INFERRED = "AGENT_INFERRED"
    SYSTEM_GENERATED = "SYSTEM_GENERATED"


class Category(str, Enum):
    IDENTITY = "identity"
    PREFERENCE = "preference"
    PROJECT = "project"
    WORKING = "working"


# ── Core data types ────────────────────────────────────────────────────

@dataclass
class MemoryNode:
    """
    A single memory record, parsed from MCP Entity.observations.

    This is the fundamental unit of the L2 Memory OS. Every fact, preference,
    project context, or working note is stored as a MemoryNode.

    Timestamp fields (created_at, updated_at):
      - created_at: set once on creation, never modified.
      - updated_at: updated on every state change (reinforce, supersede, status change).
      - For legacy records loaded from disk, these may be None if the
        observation data did not contain them. All new writes always include both.
    """

    node_id: str
    category: str
    key: str
    value: str
    context: str
    status: MemoryStatus
    confidence: float
    source_type: SourceType
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    version: int = 1
    reinforcement_count: int = 1

    # ── derived ────────────────────────────────────────────────────────

    @property
    def slot_id(self) -> str:
        """The unique slot identifier: category:key@context."""
        return f"{self.category}:{self.key}@{self.context}"

    @property
    def is_active(self) -> bool:
        return self.status == MemoryStatus.ACTIVE

    @property
    def is_draft(self) -> bool:
        return self.status == MemoryStatus.DRAFT

    def is_same_value_as(self, other: MemoryNode) -> bool:
        """True if value is identical (used for duplicate detection)."""
        return self.value == other.value

    # ── observation parsing ────────────────────────────────────────────

    @classmethod
    def from_observations(cls, node_id: str, observations: list[str]) -> "MemoryNode":
        """
        Parse a MemoryNode from MCP Entity.observations.

        Observation format: ``field_name: field_value``
        Example: ``"category: identity"``

        Backward compatible: missing ``created_at`` or ``updated_at``
        observations result in ``None`` (no crash).
        """
        raw: dict[str, str] = {}
        for obs in observations:
            if ": " in obs:
                key, val = obs.split(": ", 1)
                raw[key.strip()] = val.strip()
            elif ":" in obs:
                key, val = obs.split(":", 1)
                raw[key.strip()] = val.strip()

        def _get(k: str, default: str = "") -> str:
            return raw.get(k, default)

        def _parse_dt(s: str) -> Optional[datetime]:
            if not s:
                return None
            try:
                return datetime.fromisoformat(s)
            except ValueError:
                return None

        return cls(
            node_id=node_id,
            category=_get("category"),
            key=_get("key"),
            value=_get("value"),
            context=_get("context", ""),
            status=MemoryStatus(_get("status", "ACTIVE")),
            confidence=float(_get("confidence", "1.0")),
            source_type=SourceType(_get("source_type", "USER_EXPLICIT")),
            created_at=_parse_dt(_get("created_at")),
            updated_at=_parse_dt(_get("updated_at")),
            expires_at=_parse_dt(_get("expires_at")),
            version=int(_get("version", "1")),
            reinforcement_count=int(_get("reinforcement_count", "1")),
        )

    # ── observation generation ─────────────────────────────────────────

    def to_observations(self) -> list[str]:
        """Serialize this node back to MCP Entity.observations format."""
        obs = [
            f"node_id: {self.node_id}",
            f"category: {self.category}",
            f"key: {self.key}",
            f"value: {self.value}",
            f"context: {self.context}",
            f"status: {self.status.value}",
            f"confidence: {self.confidence}",
            f"source_type: {self.source_type.value}",
            f"version: {self.version}",
            f"reinforcement_count: {self.reinforcement_count}",
        ]
        if self.created_at is not None:
            obs.append(f"created_at: {self.created_at.isoformat()}")
        if self.updated_at is not None:
            obs.append(f"updated_at: {self.updated_at.isoformat()}")
        if self.expires_at is not None:
            obs.append(f"expires_at: {self.expires_at.isoformat()}")
        return obs


@dataclass
class SlotInfo:
    """
    In-memory index entry for a single slot.

    Tracks the currently ACTIVE node, version count, and all nodes
    that belong to this slot for fast lookup without querying MCP.
    """

    slot_id: str
    active_node_id: Optional[str] = None
    version_count: int = 0
    last_updated: Optional[datetime] = None

    # In-memory cache of all nodes belonging to this slot (by node_id).
    _node_ids: set[str] = field(default_factory=set)

    def add_node(self, node: MemoryNode) -> None:
        self._node_ids.add(node.node_id)
        if node.version > self.version_count:
            self.version_count = node.version
        if node.is_active:
            self.active_node_id = node.node_id
            self.last_updated = node.updated_at if node.updated_at else node.created_at


@dataclass
class RelationRecord:
    """
    A directed relation between two entities.

    Stored in the in-memory Relation Index for fast lookup.
    """

    source_id: str      # "from" field
    target_id: str      # "to" field
    relation_type: str  # e.g. "HAS_MEMORY", "SUPERSEDED_BY"


@dataclass
class WriteRequest:
    """
    A parsed write request from the caller, ready for Governor processing.

    The Governor will inspect this against the Slot Index and decide:
      - create (new slot)  →  W05
      - reinforce (same value)  →  W02
      - supersede (different value)  →  W04
    """

    category: str
    key: str
    value: str
    context: str = ""
    source_type: SourceType = SourceType.USER_EXPLICIT
    confidence: float = 1.0
    expires_at: Optional[datetime] = None

    @property
    def slot_id(self) -> str:
        return f"{self.category}:{self.key}@{self.context}"