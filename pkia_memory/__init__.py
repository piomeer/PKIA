# PKIA L2 Memory OS — Governor MVP v0.1
#
# This package implements the Memory Governor for PKIA's L2 Long-Term Memory Layer.
# Architecture: Slot Index Strategy A
#   - Bootstrap: reads JSON Lines file directly (read_graph equivalent)
#   - Index: in-memory Slot Index + Relation Index
#   - Write: generates MCP command payloads for the Agent to execute
#   - MCP Memory Server: persistence layer only
#
# See: docs/memory_ontology_v1.1.md
# See: docs/memory_schema_v1.0.md
# See: docs/mcp_capability_audit.md