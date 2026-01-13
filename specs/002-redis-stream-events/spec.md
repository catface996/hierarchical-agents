# Feature Specification: Redis Stream 事件存储

**Feature Branch**: `002-redis-stream-events`
**Created**: 2025-01-01
**Status**: Draft
**Input**: 将 execution event 写入 Redis Stream，替代 MySQL 存储，提升实时事件处理性能。Redis 在本地 Docker 环境中部署。

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 实时事件流订阅 (Priority: P1)

用户启动一个层级团队运行任务后，通过 SSE 接口实时接收执行过程中产生的所有事件（LLM 输出、工具调用、状态变更等），事件无延迟、无丢失地按顺序推送到客户端。

**Why this priority**: 实时事件流是系统核心功能，直接影响用户对任务执行过程的可见性和交互体验。

**Independent Test**: 启动一个运行任务，通过 SSE 连接订阅事件流，验证所有事件按顺序实时到达。

**Acceptance Scenarios**:

1. **Given** 用户已启动一个运行任务, **When** 用户通过 SSE 接口订阅事件流, **Then** 用户实时收到所有执行事件，事件按产生顺序到达
2. **Given** 用户正在订阅事件流, **When** LLM 产生流式输出, **Then** 用户在 100ms 内收到对应的 stream 事件
3. **Given** 用户正在订阅事件流, **When** 运行完成或失败, **Then** 用户收到 lifecycle.completed 或 lifecycle.failed 事件

---

### User Story 2 - 断线重连恢复 (Priority: P2)

用户在订阅事件流过程中发生网络断线，重新连接后能够从断点继续接收事件，不丢失断线期间产生的事件。

**Why this priority**: 网络不稳定是常见场景，断线恢复能力直接影响用户体验和数据完整性。

**Independent Test**: 订阅事件流后模拟断线，重连时携带上次收到的事件 ID，验证能从断点继续接收。

**Acceptance Scenarios**:

1. **Given** 用户断线前收到事件 ID 为 X, **When** 用户重连并携带 ID X, **Then** 用户从 ID X+1 开始继续接收后续事件
2. **Given** 断线期间产生了 100 个事件, **When** 用户重连, **Then** 用户能收到所有断线期间产生的事件

---

### User Story 3 - 历史事件回放 (Priority: P3)

用户可以查询已完成运行的历史事件记录，用于问题排查、审计或回顾执行过程。

**Why this priority**: 历史回放是辅助功能，主要用于事后分析，优先级低于实时功能。

**Independent Test**: 查询一个已完成运行的事件列表，验证返回完整有序的事件记录。

**Acceptance Scenarios**:

1. **Given** 运行已完成并产生了 500 个事件, **When** 用户查询该运行的事件列表, **Then** 返回全部 500 个事件，按时间顺序排列
2. **Given** 运行完成超过 24 小时, **When** 用户查询事件列表, **Then** 仍能获取完整的事件记录

---

### Edge Cases

- 当事件写入存储失败时，系统如何处理？（不应阻塞主流程，记录错误日志）
- 当存储服务不可用时，系统如何降级？（返回适当错误信息，不影响任务执行）
- 当单个运行产生超过 10000 个事件时，如何处理？（自动清理旧事件，保留最近 N 条）
- 当多个客户端同时订阅同一运行的事件流时，如何处理？（支持多客户端并发订阅）

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 系统 MUST 将每个执行事件写入持久化存储，包含完整的事件结构（run_id, timestamp, sequence, source, event, data）
- **FR-002**: 系统 MUST 支持按运行 ID 订阅实时事件流，新事件在产生后 100ms 内可被订阅者接收
- **FR-003**: 系统 MUST 支持从指定位置开始读取事件，用于断线重连场景
- **FR-004**: 系统 MUST 保证同一运行内事件的顺序性，按 sequence 严格递增
- **FR-005**: 系统 MUST 支持按运行 ID 查询历史事件列表，返回完整有序的事件记录
- **FR-006**: 系统 MUST 在运行结束后自动设置事件数据过期时间，避免无限增长
- **FR-007**: 系统 MUST 支持多客户端同时订阅同一运行的事件流
- **FR-008**: 系统 MUST 在事件存储服务不可用时提供适当的错误处理，不阻塞任务执行

### Key Entities

- **ExecutionEvent**: 执行事件记录，包含运行标识、时间戳、序列号、来源信息、事件类型、事件数据
- **EventStream**: 按运行 ID 组织的事件流，支持顺序写入、范围读取、实时订阅

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 事件从产生到可被订阅者接收的延迟不超过 100ms（P95）
- **SC-002**: 支持单个运行存储至少 10000 个事件
- **SC-003**: 支持至少 100 个客户端同时订阅不同运行的事件流
- **SC-004**: 断线重连后 100% 恢复断线期间的事件，无数据丢失
- **SC-005**: 事件存储服务故障时，任务执行不受影响，仅事件功能降级
- **SC-006**: 历史事件查询响应时间不超过 1 秒（1000 条事件以内）

## Assumptions

- 事件数据保留期为运行结束后 24 小时，之后自动清理
- 单个事件的数据大小不超过 1MB
- 事件写入采用异步方式，不阻塞主执行流程
- 本地开发环境使用 Docker 部署的存储服务
