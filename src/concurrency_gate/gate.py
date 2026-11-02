"""concurrency_gate — Bernstein Multi-Agent Concurrency Safety Gate."""

from __future__ import annotations

import re
from typing import Any


def parse_task_spec(task_spec: str) -> dict[str, Any]:
    """Format: 'task_id:write_target1,write_target2'. Validates non-empty IDs."""
    if not task_spec or not task_spec.strip():
        return {"id": "", "writes": set()}

    parts = task_spec.strip().split(":", 1)
    task_id = re.sub(r"[^a-zA-Z0-9_-]", "_", parts[0].strip())
    if not task_id:
        task_id = f"task_{hash(task_spec) % 10000:04d}"

    targets = []
    if len(parts) > 1:
        targets = [t.strip() for t in parts[1].split(",") if t.strip()]

    return {"id": task_id, "writes": set(targets)}


def partition_into_stages(
    tasks: list[dict[str, Any]],
) -> tuple[list[list[dict[str, Any]]], list[str]]:
    """Partitions tasks into parallel execution stages based on Bernstein's condition (disjoint writes)."""
    valid_tasks = [t for t in tasks if t.get("id")]
    stages: list[list[dict[str, Any]]] = []
    conflicts: list[str] = []
    remaining = list(valid_tasks)

    while remaining:
        current_stage: list[dict[str, Any]] = []
        current_stage_writes: set[str] = set()
        next_remaining: list[dict[str, Any]] = []

        for t in remaining:
            conflict = current_stage_writes.intersection(t["writes"])
            if conflict:
                conflicts.append(
                    f"Task '{t['id']}' conflicts on writes {sorted(conflict)} with current stage"
                )
                next_remaining.append(t)
            else:
                current_stage.append(t)
                current_stage_writes.update(t["writes"])

        stages.append(current_stage)
        remaining = next_remaining

    return stages, conflicts
