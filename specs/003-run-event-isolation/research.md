# Research: Stream Event Run Isolation

**Feature**: 003-run-event-isolation
**Date**: 2025-01-01

## Research Summary

This document captures the technical research and decisions made for implementing run-level event isolation in the op-stack-executor streaming system.

---

## R-001: Cross-Thread Callback Mechanism

### Problem
When multiple runs execute concurrently, LLM callbacks are invoked from strands-agents' internal `ThreadPoolExecutor`, not from the thread that registered the callback. Thread-local storage (`threading.local()`) fails because the callback execution thread is different from the registration thread.

### Decision
**Use run_id-keyed global registry with thread-safe access**

```python
_callback_registry: Dict[int, Callable[[Dict[str, Any]], None]] = {}
_registry_lock = threading.Lock()

def register_event_callback(run_id: int, callback: Callable):
    with _registry_lock:
        _callback_registry[run_id] = callback

def get_event_callback(run_id: int) -> Optional[Callable]:
    with _registry_lock:
        return _callback_registry.get(run_id)
```

### Rationale
- Run IDs are unique and immutable per execution
- Global registry is accessible from any thread
- `threading.Lock()` provides thread-safe access with minimal contention
- Lookup by run_id is O(1) and doesn't depend on thread identity

### Alternatives Considered

| Alternative | Rejected Because |
|-------------|-----------------|
| Thread-local storage | strands-agents uses internal thread pool; callbacks execute in different threads |
| Context variables (`contextvars`) | Same issue - context doesn't propagate to ThreadPoolExecutor workers |
| Async context (`asyncio`) | System is synchronous; would require major refactoring |
| Monkey-patching strands-agents | Brittle; breaks on library updates |

---

## R-002: Run ID Propagation Strategy

### Problem
The `run_id` must be accessible in the LLMCallbackHandler when it's invoked from an arbitrary thread. How do we propagate the run_id through the call chain?

### Decision
**Explicit parameter passing through the entire call chain**

1. `run_manager.py` adds `run_id` to `config_dict`
2. `hierarchy_executor.py` reads `run_id` from config
3. `hierarchy_system.py` passes `run_id` to callback handler factory
4. `LLMCallbackHandler` stores `run_id` as instance attribute

### Rationale
- Explicit is better than implicit (Python philosophy)
- No hidden state or magic context lookup
- Each component clearly receives what it needs
- Easy to debug and trace

### Implementation Path

```
RunManager.start_run()
    ↓ config_dict['run_id'] = run_id
HierarchyExecutor.execute()
    ↓ WorkerAgentFactory.set_current_run_id(config.run_id)
WorkerAgentFactory.create_worker()
    ↓ run_id=WorkerAgentFactory._current_run_id
create_callback_handler(caller_context, run_id=run_id)
    ↓
LLMCallbackHandler.__init__(run_id=run_id)
    ↓ self.run_id = run_id
LLMCallbackHandler.__call__()
    ↓ callback = get_event_callback(self.run_id)
```

---

## R-003: Callback Cleanup Strategy

### Problem
When should callbacks and cancellation checkers be cleaned up? What happens if cleanup is delayed or fails?

### Decision
**Immediate cleanup in finally block with run_id-based deregistration**

```python
try:
    register_event_callback(run_id, event_callback)
    # ... execution ...
finally:
    register_event_callback(run_id, None)  # Deregister
```

### Rationale
- `finally` block guarantees cleanup even on exceptions
- Passing `None` removes entry from registry (not just sets value to None)
- No orphaned callbacks accumulate in memory
- Safe even if called multiple times

### Edge Cases Handled
- Run completes normally → cleanup in finally
- Run fails with exception → cleanup in finally
- Run is cancelled → cleanup in finally after InterruptedError
- Rapid successive runs → new registration overwrites old (same run_id won't be reused)

---

## R-004: Cancellation Isolation

### Problem
When one run is cancelled, how do we ensure only that specific run is affected?

### Decision
**Per-run cancellation checker registered with run_id**

```python
_checker_registry: Dict[int, Callable[[], bool]] = {}

# In RunManager:
cancel_flag = threading.Event()
register_cancellation_checker(run_id, lambda: cancel_flag.is_set())

# In LLMCallbackHandler.__call__:
checker = get_cancellation_checker(self.run_id)
if checker and checker():
    raise InterruptedError("Run was cancelled")
```

### Rationale
- Each run has its own `threading.Event()` cancel flag
- Checker is a closure over the specific run's flag
- Lookup by run_id ensures only that run sees cancellation
- Consistent pattern with event callbacks

---

## R-005: Graceful Degradation

### Problem
What happens if the callback registry lookup fails or returns None?

### Decision
**Silent drop - events are lost rather than cross-contaminated**

```python
callback = self.event_callback
if callback is None and self.run_id is not None:
    callback = get_event_callback(self.run_id)

if callback:  # Only emit if callback exists
    self._emit_event(callback, ...)
```

### Rationale
- Aligns with FR-008: "events should be dropped rather than cross-contaminated"
- No fallback to global/default callback
- Missing events are detectable (gaps in sequence)
- Safer than potentially routing to wrong run

---

## R-006: Thread Safety Analysis

### Problem
Multiple runs execute concurrently - what are the thread safety guarantees?

### Analysis

| Component | Thread Safety | Mechanism |
|-----------|--------------|-----------|
| `_callback_registry` | Thread-safe | `threading.Lock()` on all access |
| `_checker_registry` | Thread-safe | `threading.Lock()` on all access |
| `SSEManager` (per-run) | Thread-safe | Each run has isolated instance |
| `RunManager._active_runs` | Thread-safe | `threading.Lock()` on mutations |
| `LLMCallbackHandler` | Instance-isolated | One instance per agent per run |

### Decision
Current implementation is thread-safe. No additional synchronization needed.

---

## Dependencies & Best Practices

### strands-agents Callback Behavior
- Callbacks are invoked from internal `ThreadPoolExecutor`
- Thread identity is not preserved across calls
- Callback receives `**kwargs` with: `reasoningText`, `data`, `complete`, `current_tool_use`

### Redis Stream Best Practices
- Use `MAXLEN ~10000` to prevent unbounded growth
- Set TTL on streams after run completion (24 hours)
- Consumer groups not needed for current use case (single consumer per run)

### Python Threading Best Practices
- Prefer `threading.Lock()` over `RLock()` when recursion not needed
- Use context managers (`with lock:`) for automatic release
- Keep critical sections minimal to reduce contention

---

## Conclusion

All technical unknowns have been resolved. The implementation follows established patterns:
1. Run-ID keyed global registry for cross-thread callback access
2. Explicit parameter passing for run_id propagation
3. Immediate cleanup in finally blocks
4. Thread-safe access with minimal locking
5. Graceful degradation via silent drop

Ready to proceed to Phase 1: Design & Contracts.
