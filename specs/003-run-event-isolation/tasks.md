# Tasks: Stream Event Run Isolation

**Input**: Design documents from `/specs/003-run-event-isolation/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Not explicitly requested - skipping test tasks

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify existing infrastructure and prepare for implementation

- [x] T001 Verify run_id field exists in HierarchyConfigRequest in src/core/api_models.py
- [x] T002 Verify threading.Lock import available in src/streaming/llm_callback.py
- [x] T003 [P] Verify WorkerAgentFactory exists in src/core/hierarchy_system.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core callback registry infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Implement global callback registry `_callback_registry: Dict[int, Callable]` in src/streaming/llm_callback.py
- [x] T005 Implement global checker registry `_checker_registry: Dict[int, Callable]` in src/streaming/llm_callback.py
- [x] T006 Implement `_registry_lock = threading.Lock()` for thread-safe access in src/streaming/llm_callback.py
- [x] T007 Implement `register_event_callback(run_id, callback)` function in src/streaming/llm_callback.py
- [x] T008 Implement `get_event_callback(run_id)` function in src/streaming/llm_callback.py
- [x] T009 Implement `register_cancellation_checker(run_id, checker)` function in src/streaming/llm_callback.py
- [x] T010 Implement `get_cancellation_checker(run_id)` function in src/streaming/llm_callback.py
- [x] T011 Implement run_id context tracking (`set_current_run_id`, `get_current_run_id`, `clear_current_run_id`) in src/streaming/llm_callback.py
- [x] T012 Implement backward-compatible legacy APIs (`set_global_event_callback`, `get_global_event_callback`) in src/streaming/llm_callback.py

**Checkpoint**: Foundation ready - callback registry infrastructure complete

---

## Phase 3: User Story 1 - Isolated Event Streams (Priority: P1) 🎯 MVP

**Goal**: Events from one run NEVER appear in another run's stream when multiple runs execute concurrently

**Independent Test**: Start two runs simultaneously with the same hierarchy. Subscribe to each run's SSE stream. Verify that each stream only receives events with matching run_id.

### Implementation for User Story 1

- [x] T013 [US1] Add `run_id: Optional[int]` parameter to `LLMCallbackHandler.__init__` in src/streaming/llm_callback.py
- [x] T014 [US1] Store `self.run_id = run_id` in LLMCallbackHandler constructor in src/streaming/llm_callback.py
- [x] T015 [US1] Update `LLMCallbackHandler.__call__` to lookup callback via `get_event_callback(self.run_id)` when `event_callback` is None in src/streaming/llm_callback.py
- [x] T016 [US1] Add `run_id` parameter to `create_callback_handler()` factory function in src/streaming/llm_callback.py
- [x] T017 [US1] Add `_current_run_id: Optional[int]` class variable to WorkerAgentFactory in src/core/hierarchy_system.py
- [x] T018 [US1] Implement `WorkerAgentFactory.set_current_run_id(run_id)` static method in src/core/hierarchy_system.py
- [x] T019 [US1] Update worker callback creation to pass `run_id=WorkerAgentFactory._current_run_id` in src/core/hierarchy_system.py
- [x] T020 [US1] Update team supervisor callback creation to pass `run_id=WorkerAgentFactory._current_run_id` in src/core/hierarchy_system.py
- [x] T021 [US1] Update global supervisor callback creation to pass `run_id=WorkerAgentFactory._current_run_id` in src/core/hierarchy_system.py
- [x] T022 [US1] Call `WorkerAgentFactory.set_current_run_id(config.run_id)` at start of `HierarchyExecutor.execute()` in src/core/hierarchy_executor.py
- [x] T023 [US1] Call `WorkerAgentFactory.set_current_run_id(None)` in finally block of `HierarchyExecutor.execute()` in src/core/hierarchy_executor.py
- [x] T024 [US1] Update `RunManager._execute_run` to call `register_event_callback(run_id, event_callback)` in src/runner/run_manager.py
- [x] T025 [US1] Update `RunManager._execute_run` to call `set_current_run_id(run_id)` before execution in src/runner/run_manager.py
- [x] T026 [US1] Add `config_dict['run_id'] = run_id` before calling execute_hierarchy in src/runner/run_manager.py
- [x] T027 [US1] Call `register_event_callback(run_id, None)` in finally block of `RunManager._execute_run` in src/runner/run_manager.py
- [x] T028 [US1] Call `clear_current_run_id()` in finally block of `RunManager._execute_run` in src/runner/run_manager.py

**Checkpoint**: User Story 1 complete - basic event isolation works for concurrent runs

---

## Phase 4: User Story 2 - Event Integrity Under Load (Priority: P2)

**Goal**: Event isolation works correctly under high concurrent load (5+ concurrent runs)

**Independent Test**: Start 5+ runs concurrently, each with a unique task identifier. Verify all events in each stream contain only the correct run_id and task-specific content.

### Implementation for User Story 2

- [x] T029 [US2] Verify `_registry_lock` uses `threading.Lock()` (not RLock) for minimal contention in src/streaming/llm_callback.py
- [x] T030 [US2] Ensure lock critical sections are minimal (only dict access) in all registry functions in src/streaming/llm_callback.py
- [x] T031 [US2] Verify graceful degradation - silent drop when callback lookup returns None in LLMCallbackHandler.__call__ in src/streaming/llm_callback.py

**Checkpoint**: User Story 2 complete - isolation works under high concurrent load

---

## Phase 5: User Story 3 - Cancellation Isolation (Priority: P3)

**Goal**: Cancelling one run only affects that specific run; other concurrent runs continue unaffected

**Independent Test**: Start two runs, cancel one mid-execution. Verify the cancelled run stops and the other run continues to completion.

### Implementation for User Story 3

- [x] T032 [US3] Update `RunManager._execute_run` to call `register_cancellation_checker(run_id, lambda: cancel_flag.is_set())` in src/runner/run_manager.py
- [x] T033 [US3] Update `LLMCallbackHandler.__call__` to check cancellation via `get_cancellation_checker(self.run_id)` in src/streaming/llm_callback.py
- [x] T034 [US3] Raise `InterruptedError` when cancellation checker returns True in LLMCallbackHandler.__call__ in src/streaming/llm_callback.py
- [x] T035 [US3] Call `register_cancellation_checker(run_id, None)` in finally block of `RunManager._execute_run` in src/runner/run_manager.py

**Checkpoint**: User Story 3 complete - cancellation is isolated per-run

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Cleanup and validation

- [x] T036 Remove any legacy thread-local callback variables if present in src/streaming/llm_callback.py
- [x] T037 Run existing test suite (`pytest tests/`) to verify no regressions
- [x] T038 Run manual concurrent run test per quickstart.md validation steps
- [x] T039 Verify server logs show correct run_id in callback invocations

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - US1 can proceed after Foundational (Phase 2)
  - US2 can proceed after US1 (extends isolation to load scenarios)
  - US3 can proceed after US1 (extends isolation to cancellation)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 - validates isolation under load
- **User Story 3 (P3)**: Depends on US1 - extends isolation to cancellation

### Within Each User Story

- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- T001, T002, T003 can run in parallel (different files)
- T004-T012 are sequential within llm_callback.py (same file)
- T017-T021 are sequential within hierarchy_system.py (same file)
- Different user stories can be worked on by different team members after US1 completes

---

## Parallel Example: User Story 1

```bash
# These tasks modify the same file (llm_callback.py), so run sequentially:
Task: T013 → T014 → T015 → T016

# These tasks modify hierarchy_system.py, run sequentially:
Task: T017 → T018 → T019 → T020 → T021

# These tasks modify different files, can run in parallel:
Task: T022, T023 (hierarchy_executor.py)
Task: T024-T028 (run_manager.py)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (verify infrastructure)
2. Complete Phase 2: Foundational (callback registry)
3. Complete Phase 3: User Story 1 (basic isolation)
4. **STOP and VALIDATE**: Test with two concurrent runs
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Registry infrastructure ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Load test → Deploy/Demo
4. Add User Story 3 → Cancellation test → Deploy/Demo
5. Each story adds value without breaking previous stories

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Most tasks modify existing files (no new files needed)
- The implementation largely exists already - tasks verify and refine
