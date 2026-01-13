# Tasks: Add Agent ID to Hierarchy API and Stream Events

**Input**: Design documents from `/specs/001-add-agent-id/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Database Schema Changes)

**Purpose**: 数据库模型扩展，为所有用户故事提供基础

- [X] T001 [P] Add `global_supervisor_agent_id` field to HierarchyTeam model in `src/db/models.py`
- [X] T002 [P] Add `supervisor_agent_id` field to Team model in `src/db/models.py`
- [X] T003 [P] Add `agent_id` field to Worker model in `src/db/models.py`
- [X] T004 [P] Add `agent_id` field to ExecutionEvent model in `src/db/models.py`
- [X] T005 Update `HierarchyTeam.to_dict()` to include `global_supervisor_agent_id` in `src/db/models.py`
- [X] T006 Update `Team.to_dict()` to include `supervisor_agent_id` in `src/db/models.py`
- [X] T007 Update `Worker.to_dict()` to include `agent_id` in `src/db/models.py`
- [X] T008 Update `ExecutionEvent.to_dict()` to include `agent_id` in `src/db/models.py`

---

## Phase 2: Foundational (API Schema & Validation)

**Purpose**: API 请求/响应 Schema 和验证逻辑，BLOCKS 所有用户故事

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T009 Create `AgentConfig` schema class in `src/api/schemas/hierarchy_schemas.py`
- [X] T010 Update `HierarchyCreateRequest` to support `global_supervisor_agent` object in `src/api/schemas/hierarchy_schemas.py`
- [X] T011 Update `TeamConfig` to support `team_supervisor_agent` object in `src/api/schemas/hierarchy_schemas.py`
- [X] T012 Update `WorkerConfig` to support `agent_id` field in `src/api/schemas/hierarchy_schemas.py`
- [X] T013 Implement `check_agent_ids_unique_in_hierarchy()` validation function in `src/db/repositories/hierarchy_repo.py`
- [X] T014 Update `HierarchyRepository.create()` to call uniqueness validation in `src/db/repositories/hierarchy_repo.py`

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Create Hierarchy with Agent IDs (Priority: P1) 🎯 MVP

**Goal**: API 调用者可以在创建 Hierarchy 时为每个 Agent 指定 `agent_id`

**Independent Test**: 调用 `/api/executor/v1/hierarchies/create`，传入 `agent_id`，验证返回数据包含所有 `agent_id`

### Implementation for User Story 1

- [X] T015 [US1] Update `hierarchies/create` route to parse `global_supervisor_agent` in `src/api/routes/hierarchies.py`
- [X] T016 [US1] Update `hierarchies/create` route to parse `team_supervisor_agent` for each team in `src/api/routes/hierarchies.py`
- [X] T017 [US1] Update `hierarchies/create` route to parse `agent_id` for each worker in `src/api/routes/hierarchies.py`
- [X] T018 [US1] Implement backward compatibility: auto-generate UUID when `agent_id` not provided in `src/api/routes/hierarchies.py`
- [X] T019 [US1] Implement backward compatibility: map `global_prompt` to `global_supervisor_agent.prompt` in `src/api/routes/hierarchies.py`
- [X] T020 [US1] Update `HierarchyRepository.create()` to save `agent_id` fields in `src/db/repositories/hierarchy_repo.py`
- [X] T021 [US1] Update create response to return `global_supervisor_agent` with `agent_id` in `src/api/routes/hierarchies.py`
- [X] T022 [US1] Add 400 error response for duplicate `agent_id` within hierarchy in `src/api/routes/hierarchies.py`

**Checkpoint**: User Story 1 完成 - 可以创建带 agent_id 的 Hierarchy

---

## Phase 4: User Story 2 - Stream Events Include Agent ID (Priority: P1)

**Goal**: 前端收到的 `llm_stream` 等 LLM 事件包含 `agent_id` 字段

**Independent Test**: 启动执行任务，监听 stream 事件，验证每个事件都包含正确的 `agent_id`

### Implementation for User Story 2

- [X] T023 [US2] Add `agent_id` field to `CallerContext` dataclass in `src/streaming/llm_callback.py`
- [X] T024 [US2] Update `CallerContext.global_supervisor()` to accept and store `agent_id` in `src/streaming/llm_callback.py`
- [X] T025 [US2] Update `CallerContext.team_supervisor()` to accept and store `agent_id` in `src/streaming/llm_callback.py`
- [X] T026 [US2] Update `CallerContext.worker()` to accept and store `agent_id` in `src/streaming/llm_callback.py`
- [X] T027 [US2] Update `CallerContext.to_event_fields()` to return only `agent_id` (remove deprecated fields) in `src/streaming/llm_callback.py`
- [X] T028 [US2] Update `SSEManager.emit()` timestamp to millisecond precision in `src/streaming/sse_manager.py`
- [X] T029 [US2] Remove `llm_output` event emission, keep only `llm_stream` in `src/streaming/llm_callback.py`
- [X] T030 [US2] Update `run_manager._execute_run()` to pass `agent_id` to `CallerContext` in `src/runner/run_manager.py`
- [X] T031 [US2] Update `run_manager.event_callback()` to extract and save `agent_id` in `src/runner/run_manager.py`
- [X] T032 [US2] Update `HierarchyExecutor` to pass `agent_id` when creating callback handlers in `src/core/hierarchy_executor.py`
- [X] T033 [US2] Update `hierarchy_system.py` to pass `agent_id` to LLM callback for Global Supervisor in `src/core/hierarchy_system.py`
- [X] T034 [US2] Update `hierarchy_system.py` to pass `agent_id` to LLM callback for Team Supervisor in `src/core/hierarchy_system.py`
- [X] T035 [US2] Update `hierarchy_system.py` to pass `agent_id` to LLM callback for Worker in `src/core/hierarchy_system.py`

**Checkpoint**: User Story 2 完成 - Stream 事件包含正确的 agent_id

---

## Phase 5: User Story 3 - Query Hierarchy Returns Agent IDs (Priority: P2)

**Goal**: 查询 Hierarchy 详情时返回所有 Agent 的 `agent_id`

**Independent Test**: 调用 `/api/executor/v1/hierarchies/get`，验证返回数据包含所有层级的 `agent_id`

### Implementation for User Story 3

- [X] T036 [US3] Update `HierarchyTeam.to_dict()` to return `global_supervisor_agent` object structure in `src/db/models.py`
- [X] T037 [US3] Update `Team.to_dict()` to return `team_supervisor_agent` object structure in `src/db/models.py`
- [X] T038 [US3] Update `hierarchies/get` route response format in `src/api/routes/hierarchies.py`
- [X] T039 [US3] Update `hierarchies/list` route response format in `src/api/routes/hierarchies.py`

**Checkpoint**: User Story 3 完成 - 查询返回完整的 agent_id 信息

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: 测试脚本更新和文档

- [X] T040 [P] Update `test_stream.py` to use new API request format with `agent_id`
- [X] T041 [P] Update `test_stream_raw.py` to use new API request format with `agent_id`
- [ ] T042 Run `quickstart.md` validation scenarios manually
- [ ] T043 Verify backward compatibility with old API format (no `agent_id`)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies - can start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 completion - BLOCKS all user stories
- **Phase 3 (US1)**: Depends on Phase 2 - Create Hierarchy with agent_id
- **Phase 4 (US2)**: Depends on Phase 2 AND Phase 3 (needs agent_id stored to emit in events)
- **Phase 5 (US3)**: Depends on Phase 2 AND Phase 3 (needs agent_id stored to return in query)
- **Phase 6 (Polish)**: Depends on all user stories

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - No dependencies on other stories
- **User Story 2 (P1)**: Depends on US1 (needs stored agent_id to emit in stream events)
- **User Story 3 (P2)**: Depends on US1 (needs stored agent_id to return in queries)

### Parallel Opportunities

**Phase 1** - All tasks T001-T004 can run in parallel (different fields in same file, but logically separate):
```
T001 || T002 || T003 || T004
Then: T005, T006, T007, T008
```

**Phase 2** - Schema tasks can be done sequentially but validation can be parallel after:
```
T009 → T010 → T011 → T012
Then: T013 || T014
```

**User Story 2** - Multiple file changes can run in parallel:
```
T023-T029 (llm_callback.py, sse_manager.py) || T030-T031 (run_manager.py)
Then: T032 || T033-T035
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (database fields)
2. Complete Phase 2: Foundational (API schema & validation)
3. Complete Phase 3: User Story 1 (create with agent_id)
4. **STOP and VALIDATE**: Test creating hierarchy with agent_id
5. Deploy/demo if ready

### Full Feature Delivery

1. MVP (US1) → Test create functionality
2. Add US2 (Stream events) → Test agent_id in events
3. Add US3 (Query returns agent_id) → Test query functionality
4. Polish → Update test scripts, validate all scenarios

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story
- T001-T008: 数据库模型变更，需要重启服务生效
- T029: 移除 `llm_output` 事件，前端需要自行累积 `llm_stream`
- T018-T019: 向后兼容关键任务
- Commit after each phase completion
