# Feature Specification: Add Agent ID to Hierarchy API and Stream Events

**Feature Branch**: `001-add-agent-id`
**Created**: 2025-12-30
**Status**: Draft
**Input**: User description: "在 llm_stream 事件中添加 agentId，标注是哪个 agent 的输出。agent_id 在创建 hierarchy 时由用户传入。"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create Hierarchy with Agent IDs (Priority: P1)

作为 API 调用者，我需要在创建 Hierarchy Team 时为每个 Agent（Global Supervisor、Team Supervisor、Worker）指定 `agent_id`，以便后续在 stream 事件中能够识别输出来源。

**Why this priority**: 这是功能的入口点，没有传入 `agent_id`，后续的 stream 事件就无法包含该字段。

**Independent Test**: 调用 `/api/executor/v1/hierarchies/create` 接口，传入包含 `agent_id` 的请求体，验证创建成功且返回的数据包含所有 `agent_id`。

**Acceptance Scenarios**:

1. **Given** 用户准备创建 Hierarchy, **When** 调用 create 接口并为 Global Supervisor Agent 指定 `agent_id`, **Then** 系统成功保存该 `agent_id`
2. **Given** 用户准备创建 Hierarchy, **When** 调用 create 接口并为每个 Team Supervisor Agent 指定 `agent_id`, **Then** 系统成功保存所有 Team Supervisor 的 `agent_id`
3. **Given** 用户准备创建 Hierarchy, **When** 调用 create 接口并为每个 Worker Agent 指定 `agent_id`, **Then** 系统成功保存所有 Worker 的 `agent_id`

---

### User Story 2 - Stream Events Include Agent ID (Priority: P1)

作为前端开发人员，当我收到 `llm_stream` 等 LLM 相关事件时，我需要看到 `agent_id` 字段，以便知道这个输出来自哪个 Agent。

**Why this priority**: 这是本功能的核心需求，与 User Story 1 同等重要。

**Independent Test**: 启动执行任务，监听 stream 事件，验证每个 LLM 事件都包含创建时传入的 `agent_id`。

**Acceptance Scenarios**:

1. **Given** Hierarchy 已创建且 Global Supervisor 有 `agent_id="gs-001"`, **When** 执行任务且 Global Supervisor 输出, **Then** `llm_stream` 事件的 data 中 `agent_id="gs-001"`
2. **Given** Hierarchy 已创建且 Team Supervisor 有 `agent_id="ts-001"`, **When** 执行任务且该 Team Supervisor 输出, **Then** `llm_stream` 事件的 data 中 `agent_id="ts-001"`
3. **Given** Hierarchy 已创建且 Worker 有 `agent_id="w-001"`, **When** 执行任务且该 Worker 输出, **Then** `llm_stream` 事件的 data 中 `agent_id="w-001"`

---

### User Story 3 - Query Hierarchy Returns Agent IDs (Priority: P2)

作为 API 调用者，当我查询 Hierarchy 详情时，返回的数据应包含所有 Agent 的 `agent_id`，以便我能够建立 `agent_id` 到 Agent 信息的映射。

**Why this priority**: 依赖于 P1 功能，用于前端构建 Agent 信息映射表。

**Independent Test**: 调用 `/api/executor/v1/hierarchies/get` 接口，验证返回数据包含所有层级的 `agent_id`。

**Acceptance Scenarios**:

1. **Given** 已创建包含 `agent_id` 的 Hierarchy, **When** 调用 get 接口查询, **Then** 返回的 `global_supervisor_agent` 包含 `agent_id`
2. **Given** 已创建包含 `agent_id` 的 Hierarchy, **When** 调用 get 接口查询, **Then** 返回的每个 Team 的 `team_supervisor_agent` 包含 `agent_id`
3. **Given** 已创建包含 `agent_id` 的 Hierarchy, **When** 调用 get 接口查询, **Then** 返回的每个 Worker 包含 `agent_id`

---

### Edge Cases

- 如果用户未传入 `agent_id`，系统应自动生成一个 UUID 作为默认值
- `agent_id` 在同一 Hierarchy Team 内必须唯一，创建时如有重复则返回 400 错误
- 更新 Hierarchy 时，`agent_id` 可以被修改（但仍需保证 Hierarchy 内唯一）
- 不同 Hierarchy 之间可以使用相同的 `agent_id`

## Requirements *(mandatory)*

### Functional Requirements

#### API 协议重构

- **FR-001**: `/api/executor/v1/hierarchies/create` 接口请求体 MUST 支持新的 Agent 结构
- **FR-002**: 请求体 MUST 包含 `global_supervisor_agent` 对象，用于配置 Global Supervisor Agent
- **FR-003**: 每个 Team 对象 MUST 包含 `team_supervisor_agent` 对象，用于配置 Team Supervisor Agent
- **FR-004**: Worker 配置 MUST 支持 `agent_id` 字段

#### Agent ID 字段

- **FR-005**: `global_supervisor_agent.agent_id` MUST 是可选字段，未传入时系统自动生成
- **FR-006**: `team_supervisor_agent.agent_id` MUST 是可选字段，未传入时系统自动生成
- **FR-007**: Worker 的 `agent_id` MUST 是可选字段，未传入时系统自动生成
- **FR-008**: `agent_id` MUST 是字符串类型，最大长度 100 字符
- **FR-008a**: `agent_id` MUST 在同一 Hierarchy Team 内唯一，创建/更新时系统 MUST 校验唯一性
- **FR-008b**: 如果同一 Hierarchy 内 `agent_id` 重复，系统 MUST 返回 400 错误并说明冲突的 `agent_id`

#### 数据存储

- **FR-009**: `hierarchy_team` 表 MUST 新增 `global_supervisor_agent_id` 字段
- **FR-010**: `team` 表 MUST 新增 `supervisor_agent_id` 字段
- **FR-011**: `worker` 表 MUST 新增 `agent_id` 字段

#### Stream 事件

- **FR-012**: 所有 LLM 相关事件（`llm_stream`、`llm_reasoning`、`llm_tool_call`）MUST 在 data 中包含 `agent_id` 字段
- **FR-012b**: 移除 `llm_output` 事件类型，仅使用 `llm_stream` 实时输出
- **FR-012a**: 所有 Stream Event MUST 在 data 中包含 `run_id` 字段
- **FR-013**: `execution_event` 表 MUST 新增 `agent_id` 字段用于持久化

#### Stream Event 简化

- **FR-014**: LLM 相关事件 MUST 移除冗余字段 `_is_global_supervisor`、`_team_name`、`_is_team_supervisor`、`_worker_name`
- **FR-015**: `timestamp` 字段 MUST 精确到毫秒（格式：`2025-12-30T10:30:00.123Z`）

#### 向后兼容

- **FR-016**: 旧版不包含 `agent_id` 的请求 MUST 仍然能够正常工作（自动生成 `agent_id`）

### Key Entities

#### 新 API 请求体结构

```json
{
  "name": "研究团队",
  "description": "可选描述",
  "global_supervisor_agent": {
    "agent_id": "gs-research-001",
    "prompt": "你是首席科学家...",
    "model_id": "可选",
    "temperature": 0.7,
    "max_tokens": 2048
  },
  "execution_mode": "sequential",
  "enable_context_sharing": true,
  "teams": [
    {
      "name": "理论研究组",
      "team_supervisor_agent": {
        "agent_id": "ts-theory-001",
        "prompt": "你是理论研究组负责人...",
        "model_id": "可选",
        "temperature": 0.7,
        "max_tokens": 2048
      },
      "prevent_duplicate": true,
      "share_context": false,
      "workers": [
        {
          "agent_id": "w-theory-expert-001",
          "name": "理论专家",
          "role": "理论研究员",
          "system_prompt": "你是理论专家...",
          "tools": [],
          "temperature": 0.7,
          "max_tokens": 2048
        }
      ]
    }
  ]
}
```

#### Stream Event 结构（简化后）

```json
{
  "event": "llm_stream",
  "data": {
    "content": "输出内容...",
    "agent_id": "w-theory-expert-001",
    "timestamp": "2025-12-30T10:30:00.123Z",
    "run_id": "abc-123-def"
  }
}
```

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% 的 LLM 相关事件包含 `agent_id` 字段
- **SC-002**: 创建 Hierarchy 时传入的 `agent_id` 与 stream 事件中的 `agent_id` 100% 一致
- **SC-003**: 旧版 API 请求（不含 `agent_id`）仍能正常工作，系统自动生成 `agent_id`
- **SC-004**: 前端开发人员能够通过 `agent_id` 直接定位到具体的 Agent，无需复杂的映射逻辑

## Clarifications

### Session 2025-12-30

- Q: 系统是否应该强制 `agent_id` 唯一？ → A: 在单个 Hierarchy Team 内唯一
- Q: 对 `agent_id` 的格式是否有额外校验要求？ → A: 仅基本校验（非空字符串，最大 100 字符）
- Q: Stream event 是否简化？ → A: 移除冗余字段，仅保留 `agent_id`、`content`、`timestamp`、`run_id`
- Q: timestamp 精度？ → A: 精确到毫秒（格式：`2025-12-30T10:30:00.123Z`）
- Q: run_id 是否包含在所有事件中？ → A: 是，所有 Stream Event 必须包含 run_id
- Q: llm_stream 和 llm_output 的区别？ → A: 简化为仅保留 llm_stream，移除 llm_output

## Assumptions

- `agent_id` 在单个 Hierarchy Team 内唯一，系统在创建时校验唯一性
- `global_supervisor_agent.prompt` 字段对应现有的 `global_prompt` 字段
- API 协议变更需要更新相关文档和测试脚本
