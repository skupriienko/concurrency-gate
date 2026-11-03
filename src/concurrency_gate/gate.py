"""concurrency_gate — Bernstein Multi-Agent Concurrency Safety Gate."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class TaskSpec:
    """Atomic task specification with explicit read/write sets."""

    id: str
    writes: frozenset[str] = field(default_factory=frozenset)
    reads: frozenset[str] = field(default_factory=frozenset)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "writes": sorted(self.writes),
            "reads": sorted(self.reads),
        }


@dataclass(frozen=True)
class Stage:
    """A parallel execution wave containing conflict-free tasks."""

    index: int
    tasks: list[TaskSpec]

    @property
    def task_ids(self) -> list[str]:
        return [t.id for t in self.tasks]

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": self.index,
            "tasks": [t.to_dict() for t in self.tasks],
        }


@dataclass(frozen=True)
class PartitionResult:
    """Outcome of Bernstein concurrency partitioning."""

    stages: list[Stage]
    conflicts: list[str]
    total_tasks: int
    max_concurrency: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_tasks": self.total_tasks,
            "stages_count": len(self.stages),
            "max_concurrency": self.max_concurrency,
            "conflicts": self.conflicts,
            "stages": [s.to_dict() for s in self.stages],
        }


class ConcurrencyGate:
    """Evaluates Bernstein conditions and partitions tasks into parallel execution stages."""

    @staticmethod
    def parse_task(task_spec: str) -> TaskSpec:
        """Parses 'task_id:write1,write2'."""
        if not task_spec or not task_spec.strip():
            return TaskSpec(id="", writes=frozenset(), reads=frozenset())

        parts = task_spec.strip().split(":", 1)
        raw_id = parts[0].strip()
        task_id = re.sub(r"[^a-zA-Z0-9_-]", "_", raw_id)
        if not task_id:
            task_id = f"task_{abs(hash(task_spec)) % 10000:04d}"

        writes: set[str] = set()
        reads: set[str] = set()

        if len(parts) > 1:
            rest = parts[1].strip()
            if "w=" in rest or "r=" in rest:
                sub_parts = rest.split(":")
                for sp in sub_parts:
                    if sp.startswith("w="):
                        writes.update(t.strip() for t in sp[2:].split(",") if t.strip())
                    elif sp.startswith("r="):
                        reads.update(t.strip() for t in sp[2:].split(",") if t.strip())
            else:
                writes.update(t.strip() for t in rest.split(",") if t.strip())

        return TaskSpec(id=task_id, writes=frozenset(writes), reads=frozenset(reads))

    def partition(self, tasks: list[TaskSpec]) -> PartitionResult:
        """Greedy wave partitioning enforcing disjoint write sets."""
        valid_tasks = [t for t in tasks if t.id]
        stages: list[Stage] = []
        conflicts: list[str] = []
        remaining = list(valid_tasks)

        stage_idx = 1
        while remaining:
            current_tasks: list[TaskSpec] = []
            current_writes: set[str] = set()
            next_remaining: list[TaskSpec] = []

            for t in remaining:
                if not current_writes.isdisjoint(t.writes):
                    conflicts.append(f"Task '{t.id}' conflicts with current stage")
                    next_remaining.append(t)
                else:
                    current_tasks.append(t)
                    current_writes.update(t.writes)

            stages.append(Stage(index=stage_idx, tasks=current_tasks))
            stage_idx += 1
            remaining = next_remaining

        max_conc = max((len(s.tasks) for s in stages), default=0)
        return PartitionResult(
            stages=stages,
            conflicts=conflicts,
            total_tasks=len(tasks),
            max_concurrency=max_conc,
        )


_DEFAULT_GATE = ConcurrencyGate()


def parse_task_spec(task_spec: str) -> dict[str, Any]:
    task = _DEFAULT_GATE.parse_task(task_spec)
    return {"id": task.id, "writes": set(task.writes)}


def partition_into_stages(
    tasks: list[dict[str, Any]],
) -> tuple[list[list[dict[str, Any]]], list[str]]:
    task_specs = [
        TaskSpec(
            id=t["id"],
            writes=frozenset(t.get("writes", [])),
            reads=frozenset(t.get("reads", [])),
        )
        for t in tasks
    ]
    res = _DEFAULT_GATE.partition(task_specs)
    legacy_stages = [[{"id": t.id, "writes": set(t.writes)} for t in s.tasks] for s in res.stages]
    return legacy_stages, res.conflicts
