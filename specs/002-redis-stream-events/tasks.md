# Tasks: Redis Stream 事件存储

**Input**: Design documents from `/specs/002-redis-stream-events/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/event-stream-api.md, quickstart.md

**Tests**: Tests are NOT explicitly requested in the feature specification. Test tasks are excluded.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths based on plan.md structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Redis environment setup and dependency configuration

- [x] T001 Add `redis>=5.0.0` dependency to requirements.txt
- [x] T002 Add `REDIS_URL=redis://localhost:6379/0` to .env.example
- [x] T003 Start Redis Docker container per quickstart.md instructions
- [x] T004 Verify Redis connection with ping test

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core EventStore implementation that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Create Redis connection module in src/streaming/redis_client.py with connection pooling and retry logic
- [x] T006 Create StreamEvent dataclass in src/streaming/event_store.py per data-model.md
- [x] T007 Implement EventStore.add() method for writing events to Redis Stream (XADD with MAXLEN)
- [x] T008 Implement EventStore.get_events() method for reading event range (XRANGE)
- [x] T009 Implement EventStore.set_expire() method for setting TTL on Stream
- [x] T010 Implement EventStore.delete() method for removing Stream
- [x] T011 Add error handling and logging for Redis operations (fail gracefully, don't block main flow)

**Checkpoint**: EventStore core functionality ready - user story implementation can now begin

---

## Phase 3: User Story 1 - 实时事件流订阅 (Priority: P1)

**Goal**: Users can subscribe to real-time event stream via SSE and receive all execution events in order with < 100ms latency

**Independent Test**: Start a run, subscribe via SSE `/runs/{id}/events/stream`, verify all events arrive in order in real-time

### Implementation for User Story 1

- [x] T012 [US1] Modify SSEManager.__init__() in src/streaming/sse_manager.py to accept EventStore instance
- [x] T013 [US1] Modify SSEManager.emit() to call EventStore.add() in addition to queue.put() (dual-write strategy)
- [x] T014 [US1] Update SSEManager.emit() to include Redis message ID in event data for client tracking
- [x] T015 [US1] Modify generate_events() in src/streaming/sse_manager.py to yield SSE `id:` field with Redis message ID
- [x] T016 [US1] Update run_manager.py event_callback() to use new SSEManager with EventStore
- [x] T017 [US1] Modify run_manager._execute_run() to call EventStore.set_expire() when run completes/fails
- [x] T018 [US1] Remove run_repo.add_event() calls from run_manager.py (events now go to Redis)

**Checkpoint**: User Story 1 complete - real-time SSE stream works with Redis persistence

---

## Phase 4: User Story 2 - 断线重连恢复 (Priority: P2)

**Goal**: Users can reconnect after network disconnection and receive all missed events from the breakpoint using Last-Event-ID

**Independent Test**: Subscribe to SSE, simulate disconnect, reconnect with Last-Event-ID header, verify all missed events are received

### Implementation for User Story 2

- [x] T019 [US2] Implement EventStore.get_events_after() method for reading events after a given ID (XRANGE with exclusive start)
- [x] T020 [US2] Modify SSE endpoint in src/api/routes/runs.py to read Last-Event-ID header from request
- [x] T021 [US2] Create helper function in runs.py to replay historical events from EventStore before starting live stream
- [x] T022 [US2] Update SSE stream endpoint to call replay function when Last-Event-ID is present
- [x] T023 [US2] Update SSEManager.generate_events() to handle initial historical event batch before live events

**Checkpoint**: User Story 2 complete - disconnect/reconnect works seamlessly with event recovery

---

## Phase 5: User Story 3 - 历史事件回放 (Priority: P3)

**Goal**: Users can query historical events for completed runs via REST API

**Independent Test**: Query `/runs/{id}/events` for a completed run, verify all events returned in order

### Implementation for User Story 3

- [x] T024 [P] [US3] Create EventListResponse schema in src/api/schemas/run_schemas.py per contracts/event-stream-api.md
- [x] T025 [US3] Implement GET /runs/{run_id}/events endpoint in src/api/routes/runs.py
- [x] T026 [US3] Add query parameters support (start_id, end_id, limit) per API contract
- [x] T027 [US3] Add pagination support with has_more and next_id fields in response
- [x] T028 [US3] Add error handling for RUN_NOT_FOUND (404) and RUN_EXPIRED (410) cases
- [x] T029 [US3] Add Swagger documentation for the new endpoint

**Checkpoint**: User Story 3 complete - historical event query API works

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Cleanup and optimization across all user stories

- [x] T030 [P] Remove ExecutionEvent model from src/db/models.py (optional, can keep for backup) - KEPT for backward compatibility
- [x] T031 [P] Remove add_event() and get_events() methods from src/db/repositories/run_repo.py
- [x] T032 Update constitution.md with Redis configuration if needed
- [x] T033 Verify all edge cases: Redis unavailable (graceful degradation), > 10000 events (MAXLEN works)
- [x] T034 Run quickstart.md validation - verify all code examples work

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User Story 1 must complete before User Story 2 (SSE changes needed first)
  - User Story 3 can run in parallel with User Story 2
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Depends only on Foundational (Phase 2)
- **User Story 2 (P2)**: Depends on User Story 1 (needs SSE with Redis message IDs)
- **User Story 3 (P3)**: Depends only on Foundational (Phase 2) - can parallel with US2

### Within Each User Story

- Models/schemas before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- Setup tasks T001-T002 can run in parallel
- Foundational tasks T005-T011 are sequential (build on each other)
- US1 tasks T012-T018 are mostly sequential (modify same files)
- US2 tasks T019-T023 are mostly sequential
- US3 task T024 can run in parallel with other US3 tasks
- Phase 6 tasks T030-T031 can run in parallel

---

## Parallel Example: User Story 3

```bash
# These can run in parallel:
Task T024: "Create EventListResponse schema in src/api/schemas/run_schemas.py"
Task T030: "Remove ExecutionEvent model from src/db/models.py"
Task T031: "Remove add_event() and get_events() methods from src/db/repositories/run_repo.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (Redis Docker + dependencies)
2. Complete Phase 2: Foundational (EventStore implementation)
3. Complete Phase 3: User Story 1 (Real-time SSE with Redis)
4. **STOP and VALIDATE**: Test real-time streaming works
5. Deploy/demo if ready - basic functionality complete

### Incremental Delivery

1. Setup + Foundational → Redis infrastructure ready
2. Add User Story 1 → Real-time streaming works → MVP!
3. Add User Story 2 → Disconnect recovery works
4. Add User Story 3 → Historical query API works
5. Polish → Clean up legacy MySQL event code

### File Change Summary

| File | Changes |
|------|---------|
| requirements.txt | Add redis>=5.0.0 |
| .env.example | Add REDIS_URL |
| src/streaming/redis_client.py | NEW: Redis connection module |
| src/streaming/event_store.py | NEW: EventStore class |
| src/streaming/sse_manager.py | MODIFY: Integrate EventStore, add message IDs |
| src/runner/run_manager.py | MODIFY: Use EventStore, remove MySQL event writes |
| src/api/routes/runs.py | MODIFY: Add Last-Event-ID support, add events endpoint |
| src/api/schemas/run_schemas.py | MODIFY: Add EventListResponse |
| src/db/models.py | OPTIONAL: Remove ExecutionEvent |
| src/db/repositories/run_repo.py | MODIFY: Remove event methods |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently testable after completion
- Dual-write strategy: events go to both Redis (persistence) and in-memory queue (low-latency SSE)
- Redis message IDs serve as SSE event IDs for seamless reconnection
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
