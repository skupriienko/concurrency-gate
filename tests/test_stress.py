import time
from concurrency_gate.gate import parse_task_spec, partition_into_stages

def test_stress_concurrency_gate():
    # 2,000 tasks with intentional write conflicts on 5 shared files
    specs = []
    for i in range(2000):
        target = f"file_{i % 5}.txt"
        specs.append(f"task_{i}:{target}")

    t0 = time.perf_counter()
    tasks = [parse_task_spec(s) for s in specs]
    stages, conflicts = partition_into_stages(tasks)
    duration = time.perf_counter() - t0

    assert len(stages) == 400
    assert len(conflicts) > 0
    assert duration < 2.0, f"Partitioning 2,000 tasks took {duration}s (expected <2.0s)"
