"""
pkia_memory.memory_service — Bootstrap loader, MCP command builder & file persistence.

This module handles three concerns:

1. **Bootstrap**: reads the JSON Lines file directly (equivalent to
   MCP's ``read_graph()``) and yields parsed MemoryNodes and relations.

2. **MCP command building**: generates the dict payloads that the Agent/Cline
   will send via MCP tools (``create_entities``, ``create_relations``,
   ``add_observations``).  The Governor itself does **not** call MCP — it
   returns structured payload descriptions, and the Agent executes them.

3. **File persistence**: appends entities, relations, and observations to
   the JSON Lines file (``pkia-memory.json``).  This is the ONLY durable
   storage layer.  MCP memory is ephemeral and rebuilt on restart.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .models import (
    Category,
    MemoryNode,
    MemoryStatus,
    RelationRecord,
    SourceType,
    WriteRequest,
)

# ── Storage path (set once during Governor.startup()) ───────────────────

_STORAGE_PATH: Optional[Path] = None


def set_storage_path(path: str | Path) -> None:
    """Set the global storage path for persistence operations."""
    global _STORAGE_PATH
    _STORAGE_PATH = Path(path)


def get_storage_path() -> Optional[Path]:
    """Return the current storage path, or None if not set."""
    return _STORAGE_PATH


# ── Bootstrap ───────────────────────────────────────────────────────────

def load_json_lines(path: str | Path) -> tuple[list[MemoryNode], list[RelationRecord]]:
    """
    Parse a JSON Lines file into MemoryNodes and RelationRecords.

    This is the bootstrap entry point, called once during Governor startup::

        nodes, relations = load_json_lines("pkia-memory.json")
        for node in nodes:
            slot_index.index_node(node)
        relation_index.index_relations(relations)

    The file format supports:
      - ``type="entity"``  → parsed into MemoryNode
      - ``type="relation"`` → parsed into RelationRecord
      - ``type="observation_update"`` → applied as a status change on the entity
    """
    nodes: list[MemoryNode] = []
    relations: list[RelationRecord] = []
    # Observation updates that need to be replayed after loading all entities.
    pending_updates: list[dict] = []

    p = Path(path)
    if not p.exists():
        return nodes, relations

    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            typ = obj.get("type")
            if typ == "entity":
                node = _parse_entity(obj)
                if node is not None:
                    nodes.append(node)
            elif typ == "relation":
                rel = _parse_relation(obj)
                if rel is not None:
                    relations.append(rel)
            elif typ == "observation_update":
                pending_updates.append(obj)

    # Replay observation updates against loaded nodes.
    for update in pending_updates:
        _apply_observation_update(nodes, update)

    return nodes, relations


def _parse_entity(obj: dict) -> Optional[MemoryNode]:
    """Parse a single JSON Lines entity line into a MemoryNode."""
    name = obj.get("name", "")
    entity_type = obj.get("entityType", "")
    observations: list[str] = obj.get("observations", [])

    if entity_type == "MemoryNode":
        return MemoryNode.from_observations(name, observations)

    # Fallback: check if this entity has memory fields even without
    # the correct entityType (handles legacy data).
    obs_text = " ".join(observations)
    if "category:" in obs_text and "key:" in obs_text:
        return MemoryNode.from_observations(name, observations)

    return None


def _parse_relation(obj: dict) -> Optional[RelationRecord]:
    """Parse a single JSON Lines relation line."""
    from_id = obj.get("from", "")
    to_id = obj.get("to", "")
    rel_type = obj.get("relationType", "")

    if not from_id or not to_id or not rel_type:
        return None

    return RelationRecord(
        source_id=from_id,
        target_id=to_id,
        relation_type=rel_type,
    )


def _apply_observation_update(nodes: list[MemoryNode], update: dict) -> None:
    """
    Apply an observation_update to the set of loaded nodes.

    observation_update lines record runtime state changes (reinforcement count,
    status changes, etc.) that happened after the entity was created.
    During bootstrap replay, we apply these so the in-memory index reflects
    the most recent state.

    Supported observation keys:
      - ``status: DEPRECATED`` → set node.status = DEPRECATED
      - ``status: ARCHIVED``   → set node.status = ARCHIVED
      - ``reinforcement_count: N`` → ignored at bootstrap (runtime state)
    """
    entity_name = update.get("entityName", "")
    new_obs: list[str] = update.get("observations", [])

    # Find the matching node.
    for node in nodes:
        if node.node_id == entity_name:
            for obs in new_obs:
                if obs.startswith("status: "):
                    new_status = obs.split("status: ", 1)[1].strip()
                    node.status = MemoryStatus(new_status)
            break


# ── Node ID generation ─────────────────────────────────────────────────

def new_node_id() -> str:
    """Generate a unique node_id: ``mem_<uuid4>``."""
    return f"mem_{uuid.uuid4().hex}"


# ── File persistence layer ─────────────────────────────────────────────
#
# These functions append data to pkia-memory.json in JSON Lines format.
# They are the ONLY persistent storage — MCP memory is ephemeral.
#
# All writes are append-only.  Historical records are never modified.
# The file grows monotonically, which is by design (Append-only Architecture).

def append_to_file(line: dict) -> None:
    """
    Append a single JSON Lines object to the storage file.

    The file is opened in append mode and the line is written as a single
    JSON line followed by a newline.  This is atomic at the OS level for
    typical line sizes (< PIPE_BUF).

    Raises:
        RuntimeError: if storage path has not been set via set_storage_path().
    """
    path = get_storage_path()
    if path is None:
        raise RuntimeError(
            "Storage path not set. Call set_storage_path() before writing."
        )

    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(line, ensure_ascii=False))
        f.write("\n")


def append_entity_to_file(node: MemoryNode) -> None:
    """
    Append a MemoryNode as a JSON Lines entity line to the storage file.

    The entity line uses the same format as MCP Memory Server's dump::

        {"type":"entity","name":"mem_<uuid>","entityType":"MemoryNode","observations":[...]}
    """
    line = {
        "type": "entity",
        "name": node.node_id,
        "entityType": "MemoryNode",
        "observations": node.to_observations(),
    }
    append_to_file(line)


def append_relation_to_file(record: RelationRecord) -> None:
    """
    Append a relation as a JSON Lines relation line to the storage file.

    The relation line uses the same format as MCP Memory Server's dump::

        {"type":"relation","from":"...","to":"...","relationType":"..."}
    """
    line = {
        "type": "relation",
        "from": record.source_id,
        "to": record.target_id,
        "relationType": record.relation_type,
    }
    append_to_file(line)


def append_observation_to_file(node_id: str, observations: list[str]) -> None:
    """
    Append an observation update marker to the storage file.

    Because observations are part of the entity line, and we cannot modify
    historical lines, we append a special marker that records the update
    as an event::

        {"type":"observation_update","entityName":"mem_<id>","observations":[...],"timestamp":"..."}

    During bootstrap, ``load_json_lines()`` will replay these updates
    against the loaded entities so that in-memory state is recovered
    (e.g. status changes, reinforcement count).
    """
    _now = datetime.now(timezone.utc)
    line = {
        "type": "observation_update",
        "entityName": node_id,
        "observations": observations,
        "timestamp": _now.isoformat(),
    }
    append_to_file(line)


# ── MCP command builders ───────────────────────────────────────────────
#
# These functions generate the payload dicts that the Agent will send
# to MCP tools.  The Governor returns these from ``write_memory()``,
# and the Agent (Cline) executes them with ``use_mcp_tool``.
#
# Each function returns a list of tool-call descriptors:
#
#   {
#       "tool": "create_entities" | "create_relations" | "add_observations",
#       "arguments": { ... }   # the arguments object for that MCP tool
#   }

def build_create_entity(node: MemoryNode) -> dict:
    """
    Build an MCP ``create_entities`` payload for a single MemoryNode.

    Returns::

        {
            "tool": "create_entities",
            "arguments": {
                "entities": [
                    {
                        "name": "mem_<uuid>",
                        "entityType": "MemoryNode",
                        "observations": [...]
                    }
                ]
            }
        }
    """
    return {
        "tool": "create_entities",
        "arguments": {
            "entities": [
                {
                    "name": node.node_id,
                    "entityType": "MemoryNode",
                    "observations": node.to_observations(),
                }
            ]
        },
    }


def build_create_relations(relations: list[RelationRecord]) -> dict:
    """
    Build an MCP ``create_relations`` payload.

    Returns::

        {
            "tool": "create_relations",
            "arguments": {
                "relations": [
                    {"from": "...", "to": "...", "relationType": "..."},
                    ...
                ]
            }
        }
    """
    return {
        "tool": "create_relations",
        "arguments": {
            "relations": [
                {
                    "from": r.source_id,
                    "to": r.target_id,
                    "relationType": r.relation_type,
                }
                for r in relations
            ]
        },
    }


def build_add_observations(node_id: str, observations: list[str]) -> dict:
    """
    Build an MCP ``add_observations`` payload.

    Used for reinforcement updates (appending new count and timestamp).
    """
    return {
        "tool": "add_observations",
        "arguments": {
            "observations": [
                {
                    "entityName": node_id,
                    "contents": observations,
                }
            ]
        },
    }


# ── Convenience: build full write result ───────────────────────────────

def build_create_result(node: MemoryNode, relations: list[RelationRecord]) -> dict:
    """
    Build the full MCP command set for creating a new node with relations.

    Returns a list of command descriptors in dependency order::

        [
            { "tool": "create_entities", "arguments": {...} },   # 1. create node
            { "tool": "create_relations", "arguments": {...} },  # 2. link relations
        ]
    """
    return {
        "commands": [
            build_create_entity(node),
            build_create_relations(relations),
        ]
    }


def build_supersede_result(
    new_node: MemoryNode,
    old_node_id: str,
) -> dict:
    """
    Build the MCP command set for a supersede operation.

    Steps:
      1. Create the new node (ACTIVE).
      2. Append "status: DEPRECATED" observation to the old node.
      3. Create SUPERSEDED_BY relation from new node to old node.
      4. Create HAS_MEMORY relation from PKIA_Project to new node.
    """
    return {
        "commands": [
            build_create_entity(new_node),
            build_add_observations(
                old_node_id,
                [f"status: {MemoryStatus.DEPRECATED.value}"],
            ),
            build_create_relations([
                RelationRecord(
                    source_id=new_node.node_id,
                    target_id=old_node_id,
                    relation_type="SUPERSEDED_BY",
                ),
                RelationRecord(
                    source_id="PKIA_Project",
                    target_id=new_node.node_id,
                    relation_type="HAS_MEMORY",
                ),
            ]),
        ]
    }


def build_reinforce_result(node_id: str, count: int, updated_at: str) -> dict:
    """
    Build the MCP command set for a reinforcement update.

    Only appends the new ``reinforcement_count`` and ``updated_at``
    observations.  (The old values remain for auditability.)
    """
    return {
        "commands": [
            build_add_observations(node_id, [
                f"reinforcement_count: {count}",
                f"updated_at: {updated_at}",
            ]),
        ]
    }