"""concurrency_gate — Bernstein Multi-Agent Concurrency Safety Gate."""
from __future__ import annotations

import sys
from typing import Any, Dict, List, Set, Tuple

def parse_task_spec(task_spec: str) -> Dict[str, Any]:
    """Format: 'task_id:write_target1,write_target2'."""
    parts = task_spec.split(":")
    task_id = parts[0].strip()
    targets = [t.strip() for t in parts[1].split(",") if t.strip()] if len(parts) > 1 else []
    return {"id": task_id, "writes": set(targets)}

def partition_into_stages(tasks: List[Dict[str, Any]]) -> Tuple[List[List[Dict[str, Any]]], List[str]]:
    """Partitions tasks into parallel execution stages based on Bernstein's condition (disjoint writes)."""
    stages: List[List[Dict[str, Any]]] = []
    conflicts: List[str] = []
    remaining = list(tasks)

    while remaining:
        current_stage: List[Dict[str, Any]] = []
        current_stage_writes: Set[str] = set()
        next_remaining: List[Dict[str, Any]] = []

        for t in remaining:
            conflict = current_stage_writes.intersection(t["writes"])
            if conflict:
                conflicts.append(f"Task '{t['id']}' conflicts on writes {conflict} with current stage")
                next_remaining.append(t)
            else:
                current_stage.append(t)
                current_stage_writes.update(t["writes"])

        stages.append(current_stage)
        remaining = next_remaining

    return stages, conflicts
