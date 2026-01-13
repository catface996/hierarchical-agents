# Internal API Contracts: Stream Event Run Isolation

**Feature**: 003-run-event-isolation
**Date**: 2025-01-01

## Overview

This feature does not introduce new HTTP endpoints. Instead, it defines internal Python API contracts for the callback registration system. These are the interfaces that must be maintained for run isolation to work correctly.

---

## Callback Registry API

**Module**: `src/streaming/llm_callback.py`

### register_event_callback

```python
def register_event_callback(run_id: int, callback: Optional[Callable[[Dict[str, Any]], None]]) -> None:
    """
    Register an event callback for a specific run.

    Args:
        run_id: Unique run identifier (positive integer)
        callback: Event callback function, or None to deregister

    Thread Safety: Thread-safe (uses internal lock)

    Example:
        # Register
        register_event_callback(42, lambda event: sse_manager.emit(event))

        # Deregister
        register_event_callback(42, None)
    """
```

### get_event_callback

```python
def get_event_callback(run_id: int) -> Optional[Callable[[Dict[str, Any]], None]]:
    """
    Get the event callback for a specific run.

    Args:
        run_id: Unique run identifier

    Returns:
        Callback function if registered, None otherwise

    Thread Safety: Thread-safe (uses internal lock)
    """
```

### register_cancellation_checker

```python
def register_cancellation_checker(run_id: int, checker: Optional[Callable[[], bool]]) -> None:
    """
    Register a cancellation checker for a specific run.

    Args:
        run_id: Unique run identifier
        checker: Function returning True if cancelled, or None to deregister

    Thread Safety: Thread-safe (uses internal lock)

    Example:
        cancel_flag = threading.Event()
        register_cancellation_checker(42, lambda: cancel_flag.is_set())
    """
```

### get_cancellation_checker

```python
def get_cancellation_checker(run_id: int) -> Optional[Callable[[], bool]]:
    """
    Get the cancellation checker for a specific run.

    Args:
        run_id: Unique run identifier

    Returns:
        Checker function if registered, None otherwise

    Thread Safety: Thread-safe (uses internal lock)
    """
```

---

## Run ID Context API

**Module**: `src/streaming/llm_callback.py`

### set_current_run_id

```python
def set_current_run_id(run_id: int) -> None:
    """
    Set the run_id for the current execution thread.

    Used to establish context before execution starts.

    Args:
        run_id: Unique run identifier

    Note: Thread-specific (uses thread ID as key)
    """
```

### get_current_run_id

```python
def get_current_run_id() -> Optional[int]:
    """
    Get the run_id for the current execution thread.

    Returns:
        run_id if set, None otherwise

    Note: Thread-specific (uses thread ID as key)
    """
```

### clear_current_run_id

```python
def clear_current_run_id() -> None:
    """
    Clear the run_id for the current execution thread.

    Should be called after execution completes.
    """
```

---

## Callback Handler Factory

**Module**: `src/streaming/llm_callback.py`

### create_callback_handler

```python
def create_callback_handler(
    caller_context: CallerContext,
    event_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    verbose: bool = False,
    run_id: Optional[int] = None
) -> LLMCallbackHandler:
    """
    Create an LLM callback handler with source attribution.

    Args:
        caller_context: Identity of the calling agent
        event_callback: Direct callback (optional, overrides registry lookup)
        verbose: Enable debug output to stdout
        run_id: Run identifier for registry-based callback lookup

    Returns:
        Configured LLMCallbackHandler instance

    Usage:
        handler = create_callback_handler(
            CallerContext.worker("w1", "Worker", "TeamA"),
            run_id=42
        )
    """
```

---

## Event Format Contract

Events emitted through callbacks must conform to this structure:

```python
{
    "source": {
        "agent_id": str,      # Unique agent identifier
        "agent_type": str,    # "global_supervisor" | "team_supervisor" | "worker"
        "agent_name": str,    # Human-readable name
        "team_name": str | None  # Team name (null for global)
    },
    "event": {
        "category": str,      # "lifecycle" | "llm" | "dispatch" | "system"
        "action": str         # Category-specific action
    },
    "data": {
        # Action-specific payload
    }
}
```

### LLM Event Actions

| Action | Data Fields | Description |
|--------|-------------|-------------|
| `stream` | `{"content": str}` | Streaming text output |
| `reasoning` | `{"content": str}` | Reasoning/thinking text |
| `tool_call` | `{"tool_name": str, "tool_count": int}` | Tool invocation |

### Lifecycle Event Actions

| Action | Data Fields | Description |
|--------|-------------|-------------|
| `started` | `{"task": str}` | Run started |
| `completed` | `{"result": str, "statistics": dict}` | Run completed successfully |
| `failed` | `{"error": str, "details": str}` | Run failed |
| `cancelled` | `{}` | Run was cancelled |

---

## Usage Contract

### Registration Lifecycle

```python
# 1. At run start (in RunManager._execute_run)
register_event_callback(run_id, event_callback)
register_cancellation_checker(run_id, cancellation_checker)
set_current_run_id(run_id)

# 2. Pass run_id to execution
config_dict['run_id'] = run_id

# 3. During execution (in hierarchy_system.py)
# WorkerAgentFactory reads run_id and passes to callback handlers

# 4. At run end (in finally block)
register_event_callback(run_id, None)
register_cancellation_checker(run_id, None)
clear_current_run_id()
```

### Cross-Thread Callback Lookup

```python
# In LLMCallbackHandler.__call__ (may be called from any thread)
callback = self.event_callback
if callback is None and self.run_id is not None:
    callback = get_event_callback(self.run_id)  # Thread-safe lookup

if callback:
    callback(event_data)
# If no callback found, event is silently dropped (graceful degradation)
```

---

## Backward Compatibility

Legacy APIs are preserved but delegate to the new run_id-based system:

```python
# These work when set_current_run_id was called
def set_global_event_callback(callback):
    run_id = get_current_run_id()
    if run_id is not None:
        register_event_callback(run_id, callback)

def get_global_event_callback():
    run_id = get_current_run_id()
    if run_id is not None:
        return get_event_callback(run_id)
    return None
```

**Note**: These legacy APIs only work within the thread that called `set_current_run_id`. For cross-thread scenarios, use the explicit run_id-based APIs.
