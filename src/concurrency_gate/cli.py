"""CLI interface for concurrency-gate."""
import argparse
import json
import sys
from concurrency_gate.gate import parse_task_spec, partition_into_stages

def main() -> None:
    parser = argparse.ArgumentParser(
        description="concurrency-gate: Bernstein Multi-Agent Concurrency Safety Gate"
    )
    parser.add_argument("--task", action="append", help="Task spec in format 'task_id:target1,target2'")
    parser.add_argument("--verify-batch", type=str, help="Semicolon-separated task specs")
    parser.add_argument("--json", action="store_true", help="Output JSON receipt")

    args = parser.parse_args()
    raw_specs = args.task or []
    if args.verify_batch:
        raw_specs.extend([s.strip() for s in args.verify_batch.split(";") if s.strip()])

    if not raw_specs:
        raw_specs = [
            "research_core:docs/core.md",
            "research_api:docs/api.md",
            "update_core:docs/core.md",
            "update_tests:tests/test_core.py"
        ]

    tasks = [parse_task_spec(s) for s in raw_specs]
    stages, conflicts = partition_into_stages(tasks)
    max_concurrency = max(len(s) for s in stages) if stages else 0

    if args.json:
        res = {
            "status": "OK",
            "total_tasks": len(tasks),
            "stages_count": len(stages),
            "max_concurrency": max_concurrency,
            "stages": [[t["id"] for t in stage] for stage in stages],
            "conflicts_serialized": conflicts
        }
        print(json.dumps(res, indent=2))
        return

    print("\n⚡ Concurrency Safety Analysis (Bernstein Invariant):")
    print(f"  • Total Tasks: {len(tasks)}")
    print(f"  • Partitioned Stages (Execution Waves): {len(stages)}")
    print(f"  • Max Concurrent Subagents: {max_concurrency}")

    for idx, stage in enumerate(stages, 1):
        t_ids = [t["id"] for t in stage]
        print(f"    - Stage {idx} (Parallel): {', '.join(t_ids)}")

    if conflicts:
        print("\n⚠️ Resolved Conflicts (Serialized across stages):")
        for c in conflicts:
            print(f"    - {c}")

    print(
        f"\n[RECEIPT] status=OK sensor=concurrency_gate stages={len(stages)} "
        f"max_concurrency={max_concurrency} tasks={len(tasks)} safety=VERIFIED"
    )

if __name__ == "__main__":
    main()
