"""
pkia_memory.memory_service — Bootstrap loader & MCP command builder.

This module handles two concerns:

1. **Bootstrap**: reads the JSON Lines file directly (equivalent to
   MCP's ``read_graph()``) and yields parsed MemoryNodes and relations.

2. **MCP command building**: generates the dict payloads that the Agent/Cline
   will send via MCP tools (``create_entities``, ``create_relations``,
   ``add_observations``).  The Governor itself does **not** call MCP — it
   returns structured payload descriptions, and the Agent executes them.

This separation lets us test the Governor logic without a live MCP server.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
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


# ── Bootstrap ───────────────────────────────────────────────────────────

def load_json_lines(path: str | Path) -> tuple[list[MemoryNode], list[RelationRecord]]:
    """
    Parse a JSON Lines file into MemoryNodes and RelationRecords.

    This is the bootstrap entry point.  Call it once during Governor startup::

        nodes, relations = load_json_lines("pkia-memory.json")
        slot_index.index_nodes(nodes)
        relation_index.index_relations(relations)

    The file format matches MCP Memory Server's dump (``read_graph()``),
    where each line is either an ``entity`` or a ``relation``.
    """
    nodes: list[MemoryNode] = []
    relations: list[RelationRecord] = []

    p = Path(path)
    if not p.exists():
        # No data yet — return empty.
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

    return nodes, relations


def _parse_entity(obj: dict) -> Optional[MemoryNode]:
    """Parse a single JSON Lines entity line into a MemoryNode."""
    name = obj.get("name", "")
    entity_type = obj.get("entityType", "")
    observations: list[str] = obj.get("observations", [])

    # Only parse entities that are MemoryNodes (entityType=MemoryNode)
    # or generic entities that happen to carry memory-like observations.
    # For bootstrapping, we attempt to parse any entity that has
    # "category" and "key" in its observations.
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


# ── Node ID generation ─────────────────────────────────────────────────

def new_node_id() -> str:
    """Generate a unique node_id: ``mem_<uuid4>``."""
    return f"mem_{uuid.uuid4().hex}"


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