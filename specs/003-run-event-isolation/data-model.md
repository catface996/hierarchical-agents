# Data Model: Stream Event Run Isolation

**Feature**: 003-run-event-isolation
**Date**: 2025-01-01

## Overview

This feature introduces no new database entities. It enhances the in-memory callback registration system to support run-level isolation. The key entities are runtime data structures, not persisted models.

---

## Runtime Entities

### CallbackRegistry

**Purpose**: Thread-safe storage for per-run event callbacks

| Field | Type | Description |
|-------|------|-------------|
| `_callback_registry` | `Dict[int, Callable]` | Maps run_id → event callback function |
| `_checker_registry` | `Dict[int, Callable]` | Maps run_id → cancellation checker function |
| `_registry_lock` | `threading.Lock` | Synchronization primitive for thread-safe access |

**Location**: `src/streaming/llm_callback.py`

**State Transitions**:
```
Empty → Registered → Active → Deregistered → Empty
         ↑                      ↓
         └──────────────────────┘ (reuse after cleanup)
```

**Lifecycle**:
1. **Registered**: `register_event_callback(run_id, callback)` called at run start
2. **Active**: Callbacks invoked during execution
3. **Deregistered**: `register_event_callback(run_id, None)` called at run end

---

### LLMCallbackHandler

**Purpose**: Per-agent callback handler that routes events to correct run

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `caller_context` | `CallerContext` | Agent identity (who is calling) | Required |
| `event_callback` | `Optional[Callable]` | Direct callback (if known) | Optional |
| `run_id` | `Optional[int]` | Run identifier for registry lookup | Optional but recommended |
| `verbose` | `bool` | Enable debug output | Default: False |
| `tool_count` | `int` | Counter for tool invocations | Default: 0 |
| `_buffer` | `List[str]` | Text accumulation buffer | Default: [] |

**Location**: `src/streaming/llm_callback.py`

**Invariants**:
- Either `event_callback` or `run_id` must be provided for events to emit
- If both provided, `event_callback` takes precedence
- Handler is immutable after creation (except counters)

---

### CallerContext

**Purpose**: Identifies the source agent for event attribution

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `agent_id` | `str` | Unique agent identifier | Required, non-empty |
| `agent_type` | `AgentType` | Type enum | Required |
| `agent_name` | `str` | Human-readable name | Required |
| `team_name` | `Optional[str]` | Team name (for non-global agents) | Required for Worker/TeamSupervisor |

**Location**: `src/streaming/llm_callback.py`

**AgentType Enum**:
```python
class AgentType(str, Enum):
    GLOBAL_SUPERVISOR = "global_supervisor"
    TEAM_SUPERVISOR = "team_supervisor"
    WORKER = "worker"
```

---

### RunContext (in WorkerAgentFactory)

**Purpose**: Tracks current run_id for callback creation

| Field | Type | Description |
|-------|------|-------------|
| `_current_run_id` | `Optional[int]` | Current run being executed |

**Location**: `src/core/hierarchy_system.py` (WorkerAgentFactory class variable)

**Note**: This is a class-level variable, not a thread-local. Safe because:
- Set at execution start in main thread
- Read during agent creation (same thread context)
- Cleared at execution end

---

## Existing Entities (Unchanged)

### ExecutionRun (Database)

No changes to schema. Existing fields used:

| Field | Type | Description |
|-------|------|-------------|
| `id` | `int` | Primary key, used as run_id for isolation |
| `status` | `RunStatus` | Execution state |
| `hierarchy_id` | `str` | Reference to hierarchy team |

### SSEManager (Runtime)

No changes. Already creates per-run instances:

| Field | Type | Description |
|-------|------|-------------|
| `run_id` | `int` | Identifies which run this manager serves |
| `queue` | `Queue` | Memory queue for events |
| `closed` | `bool` | Whether stream has ended |

---

## Relationships

```
┌─────────────────────────────────────────────────────────────────┐
│                        CallbackRegistry                         │
│  _callback_registry: Dict[run_id → Callable]                   │
│  _checker_registry: Dict[run_id → Callable]                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ lookup by run_id
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      LLMCallbackHandler                         │
│  run_id: int (for lookup)                                       │
│  caller_context: CallerContext (for attribution)               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ emit to
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         SSEManager                              │
│  run_id: int (instance per run)                                │
│  queue: Queue (isolated per run)                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Validation Rules

### Run ID Validation
- Must be positive integer
- Must exist in `ExecutionRun` table
- Must be registered before callback invocation

### Callback Registration
- Only one callback per run_id at a time
- Re-registration overwrites previous
- Deregistration is idempotent (safe to call multiple times)

### Thread Safety
- All registry access must use `_registry_lock`
- Lock acquisition is blocking (no timeout)
- Critical sections should be minimal

---

## Migration Notes

**No database migration required** - this feature only changes runtime data structures.

Existing runs will continue to work because:
1. Backward-compatible API preserved (`set_global_event_callback` still works)
2. Single-run scenarios don't need explicit run_id
3. run_id field already exists in HierarchyConfigRequest
