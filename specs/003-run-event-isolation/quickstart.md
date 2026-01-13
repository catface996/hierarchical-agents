# Quickstart: Stream Event Run Isolation

**Feature**: 003-run-event-isolation
**Date**: 2025-01-01

## Overview

This guide demonstrates how to test and verify run-level event isolation when running multiple concurrent executions with the same hierarchy team.

---

## Prerequisites

- Server running on port 8082
- Redis running (for event streaming)
- A hierarchy team created

## Testing Event Isolation

### 1. Create a Test Hierarchy

```bash
curl -X POST http://localhost:8082/api/executor/v1/hierarchies/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "isolation-test-team",
    "global_prompt": "You are a helpful assistant",
    "teams": [{
      "name": "TestTeam",
      "supervisor_prompt": "Delegate to workers",
      "workers": [{
        "name": "TestWorker",
        "role": "assistant",
        "system_prompt": "Answer questions helpfully",
        "tools": []
      }]
    }]
  }'
```

Save the returned `hierarchy_id`.

### 2. Start Two Concurrent Runs

Open two terminal windows and run simultaneously:

**Terminal 1:**
```bash
# Start Run A
curl -X POST http://localhost:8082/api/executor/v1/runs/start \
  -H "Content-Type: application/json" \
  -d '{
    "hierarchy_id": "<hierarchy_id>",
    "task": "Count from 1 to 10 slowly, saying each number"
  }'
# Note the run_id (e.g., 101)
```

**Terminal 2:**
```bash
# Start Run B
curl -X POST http://localhost:8082/api/executor/v1/runs/start \
  -H "Content-Type: application/json" \
  -d '{
    "hierarchy_id": "<hierarchy_id>",
    "task": "List the first 5 planets in the solar system"
  }'
# Note the run_id (e.g., 102)
```

### 3. Subscribe to Event Streams

Open two more terminals to watch the SSE streams:

**Terminal 3 (Run A's stream):**
```bash
curl -N http://localhost:8082/api/executor/v1/runs/stream \
  -H "Content-Type: application/json" \
  -d '{"run_id": 101}'
```

**Terminal 4 (Run B's stream):**
```bash
curl -N http://localhost:8082/api/executor/v1/runs/stream \
  -H "Content-Type: application/json" \
  -d '{"run_id": 102}'
```

### 4. Verify Isolation

**Expected Results:**

- Terminal 3 should ONLY show numbers (1, 2, 3... from Run A)
- Terminal 4 should ONLY show planets (Mercury, Venus... from Run B)
- No cross-contamination between streams

**Signs of Failure (should NOT happen):**

- Numbers appearing in Terminal 4
- Planets appearing in Terminal 3
- Events from one run appearing in the other's stream

---

## Python Test Script

For automated testing:

```python
#!/usr/bin/env python3
"""Test concurrent run isolation."""

import requests
import threading
import time
from collections import defaultdict

BASE_URL = "http://localhost:8082/api/executor/v1"

def start_run(hierarchy_id: str, task: str) -> int:
    """Start a run and return run_id."""
    response = requests.post(
        f"{BASE_URL}/runs/start",
        json={"hierarchy_id": hierarchy_id, "task": task}
    )
    return response.json()["data"]["run_id"]

def collect_events(run_id: int, events: list, stop_event: threading.Event):
    """Collect SSE events for a run."""
    response = requests.post(
        f"{BASE_URL}/runs/stream",
        json={"run_id": run_id},
        stream=True
    )

    for line in response.iter_lines():
        if stop_event.is_set():
            break
        if line and line.startswith(b"data:"):
            events.append(line.decode())

def test_isolation(hierarchy_id: str):
    """Test that events don't cross between runs."""
    # Start two runs with distinctive tasks
    run_a = start_run(hierarchy_id, "Say 'ALPHA' five times")
    run_b = start_run(hierarchy_id, "Say 'BETA' five times")

    events_a = []
    events_b = []
    stop = threading.Event()

    # Collect events in parallel
    t1 = threading.Thread(target=collect_events, args=(run_a, events_a, stop))
    t2 = threading.Thread(target=collect_events, args=(run_b, events_b, stop))

    t1.start()
    t2.start()

    # Wait for completion
    time.sleep(60)
    stop.set()

    t1.join(timeout=5)
    t2.join(timeout=5)

    # Check for cross-contamination
    events_a_text = " ".join(events_a)
    events_b_text = " ".join(events_b)

    alpha_in_b = "ALPHA" in events_b_text
    beta_in_a = "BETA" in events_a_text

    print(f"Run A events: {len(events_a)}")
    print(f"Run B events: {len(events_b)}")
    print(f"Cross-contamination: {alpha_in_b or beta_in_a}")

    if alpha_in_b:
        print("❌ FAIL: 'ALPHA' found in Run B's stream")
    if beta_in_a:
        print("❌ FAIL: 'BETA' found in Run A's stream")
    if not alpha_in_b and not beta_in_a:
        print("✅ PASS: No cross-contamination detected")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python test_isolation.py <hierarchy_id>")
        sys.exit(1)
    test_isolation(sys.argv[1])
```

---

## Cancellation Isolation Test

### Test that cancelling one run doesn't affect others:

**Terminal 1:** Start Run A (long task)
```bash
curl -X POST http://localhost:8082/api/executor/v1/runs/start \
  -H "Content-Type: application/json" \
  -d '{
    "hierarchy_id": "<hierarchy_id>",
    "task": "Write a very long essay about space exploration"
  }'
```

**Terminal 2:** Start Run B
```bash
curl -X POST http://localhost:8082/api/executor/v1/runs/start \
  -H "Content-Type: application/json" \
  -d '{
    "hierarchy_id": "<hierarchy_id>",
    "task": "What is 2+2?"
  }'
```

**Terminal 3:** Cancel Run A while both are running
```bash
curl -X POST http://localhost:8082/api/executor/v1/runs/cancel \
  -H "Content-Type: application/json" \
  -d '{"run_id": <run_a_id>}'
```

**Expected:**
- Run A's stream shows `lifecycle.cancelled` event
- Run B continues normally and shows `lifecycle.completed`

---

## Verifying Implementation

Check that callbacks are registered correctly:

```python
# In Python console connected to running server
from src.streaming.llm_callback import (
    _callback_registry,
    _checker_registry
)

# During execution, should show entries for active runs
print(f"Active callbacks: {list(_callback_registry.keys())}")
print(f"Active checkers: {list(_checker_registry.keys())}")

# After runs complete, registries should be empty for those run_ids
```

---

## Troubleshooting

### Events not appearing in stream

1. Check Redis is running: `redis-cli ping`
2. Verify run_id is correct
3. Check server logs for errors

### Cross-contamination detected

1. Verify all components use run_id-based APIs
2. Check that `register_event_callback(run_id, None)` is called in finally block
3. Ensure `run_id` is passed through the entire call chain

### Cancellation not isolated

1. Verify cancellation checker is registered with correct run_id
2. Check that `InterruptedError` is only raised for the cancelled run
3. Ensure each run has its own `threading.Event()` flag
