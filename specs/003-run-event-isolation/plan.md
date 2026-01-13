# Implementation Plan: Stream Event Run Isolation

**Branch**: `003-run-event-isolation` | **Date**: 2025-01-01 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-run-event-isolation/spec.md`

## Summary

Implement thread-safe event isolation for concurrent runs by using a run_id-keyed callback registry instead of thread-local storage. This ensures LLM streaming events are correctly routed to their originating run's SSE connection even when callbacks are invoked from strands-agents' internal thread pools.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: Flask 3.0+, strands-agents 0.1.0+, SQLAlchemy 2.0+, Redis 5.0+
**Storage**: MySQL/PostgreSQL (via SQLAlchemy ORM), Redis (for event streams)
**Testing**: pytest (existing test suite in `/tests/`)
**Target Platform**: Linux server (EC2), also supports local development on macOS
**Project Type**: Single project (API server with streaming support)
**Performance Goals**: Support 10+ concurrent runs without event cross-contamination
**Constraints**: Must work with strands-agents' internal ThreadPoolExecutor callbacks
**Scale/Scope**: Multi-tenant execution service with concurrent run isolation

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. URL Namespace Convention | ✅ PASS | No new endpoints; existing `/api/executor/v1/runs/*` unchanged |
| II. RESTful API Design | ✅ PASS | No API changes required |
| III. Hierarchical Agent Architecture | ✅ PASS | Preserves Global → Team → Worker hierarchy |
| IV. Streaming & Real-time Events | ✅ PASS | Core feature enhancement for SSE isolation |
| V. Database Agnosticism | ✅ PASS | No database schema changes |
| VI. Server Configuration | ✅ PASS | Port 8082 unchanged |
| VII. Database Table Naming | ✅ N/A | No new tables |

**Gate Status**: ✅ PASS - No violations

## Project Structure

### Documentation (this feature)

```text
specs/003-run-event-isolation/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── core/
│   ├── api_models.py       # Data models (run_id field exists)
│   ├── hierarchy_executor.py   # Execution orchestration (set/clear run_id)
│   └── hierarchy_system.py     # Agent factories (WorkerAgentFactory.set_current_run_id)
├── streaming/
│   ├── llm_callback.py     # ⭐ PRIMARY: Run-ID based callback registry
│   ├── sse_manager.py      # Per-run SSE managers
│   ├── event_store.py      # Redis Stream storage
│   └── redis_client.py     # Redis client
├── runner/
│   └── run_manager.py      # ⭐ Run lifecycle, callback registration
├── api/
│   └── routes/runs.py      # Run API endpoints
└── db/
    └── repositories/run_repo.py  # Run persistence

tests/
├── test_api.py             # API tests
├── test_http_server.py     # HTTP server tests
└── [other existing tests]
```

**Structure Decision**: Single project structure retained. Changes focus on `src/streaming/llm_callback.py` and `src/runner/run_manager.py` where callback registry logic already exists.

## Complexity Tracking

> No violations to justify - all implementation fits within existing architecture.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | - | - |
