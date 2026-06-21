"""
One-shot L2 memory synchronization script.

Executes the Memory Sync Protocol v1.0 first real synchronization.

Writes long-term facts about Memory Architecture to cline-memory.json
via the Governor, and prints the MCP commands for Agent to execute.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pkia_memory.governor import Governor
from pkia_memory.models import WriteRequest, SourceType

MEMORY_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cline-memory.json")

gov = Governor()
gov.startup(MEMORY_FILE)

# ── Facts to sync (Ch2: 规范变化 + 长期事实) ──────────────────────

facts = [
    WriteRequest(
        category="project",
        key="workspace_memory_file",
        value="cline-memory.json",
        context="global",
        source_type=SourceType.USER_EXPLICIT,
    ),
    WriteRequest(
        category="project",
        key="user_memory_file",
        value="pkia-user-memory.json",
        context="global",
        source_type=SourceType.USER_EXPLICIT,
    ),
    WriteRequest(
        category="architecture",
        key="memory_architecture",
        value="Dual_Graph_Model",
        context="global",
        source_type=SourceType.USER_EXPLICIT,
    ),
    WriteRequest(
        category="architecture",
        key="memory_synchronization",
        value="Enabled_v1.0",
        context="global",
        source_type=SourceType.USER_EXPLICIT,
    ),
]

results = []
for f in facts:
    result = gov.write(f)
    results.append(result)
    print(f"[{result['action']}] {result['slot_id']} → {result['reason']}")
    if result.get("commands"):
        # Print MCP commands as JSON for the Agent to execute
        import json
        print(f"  MCP commands: {json.dumps(result['commands'], ensure_ascii=False, indent=2)}")

print(f"\n✅ L2 sync complete. Governor state: {gov.slot_index.node_count} nodes, {gov.slot_index.slot_count} slots")