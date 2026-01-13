# Feature Specification: Stream Event Run Isolation

**Feature Branch**: `003-run-event-isolation`
**Created**: 2025-01-01
**Status**: Draft
**Input**: User description: "我需要一个stream event，在不同的run之间，做彻底的线程隔离的方案"

## Background & Problem Statement

When multiple runs execute concurrently using the same hierarchy team, stream events (especially LLM streaming output) can leak between runs, causing:
- Events from Run A appearing in Run B's stream
- Incorrect data displayed to users in the frontend
- Difficulty debugging and tracking execution flows

The root cause is that callback mechanisms may not properly isolate event routing when:
- Multiple runs share the same execution environment
- Internal thread pools are used by underlying libraries (e.g., strands-agents)
- Global or shared state is accessed across concurrent executions

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Isolated Event Streams (Priority: P1)

As a user monitoring a run execution, I want to see ONLY the events belonging to my run, so that I can accurately track the progress and results of my specific task without confusion from other concurrent runs.

**Why this priority**: This is the core value proposition - without proper isolation, the entire streaming feature is unreliable and confusing for users.

**Independent Test**: Start two runs simultaneously with the same hierarchy. Subscribe to each run's SSE stream. Verify that each stream only receives events with matching run_id.

**Acceptance Scenarios**:

1. **Given** Run A and Run B are executing concurrently, **When** Run A's agent generates LLM output, **Then** only Run A's SSE stream receives the `llm.stream` event
2. **Given** Run A and Run B are executing concurrently, **When** Run B completes, **Then** only Run B's SSE stream receives the `lifecycle.completed` event
3. **Given** Run A and Run B use the same hierarchy team, **When** both runs generate events simultaneously, **Then** each event is routed exclusively to its corresponding run's stream

---

### User Story 2 - Event Integrity Under Load (Priority: P2)

As a system operator, I want event isolation to work correctly even under high concurrent load, so that the system remains reliable during peak usage.

**Why this priority**: After basic isolation works, ensuring it scales is essential for production reliability.

**Independent Test**: Start 5+ runs concurrently, each with a unique task identifier in the payload. Verify all events in each stream contain only the correct run_id and task-specific content.

**Acceptance Scenarios**:

1. **Given** 5 concurrent runs with unique tasks, **When** all runs complete, **Then** each run's event stream contains 0 cross-contaminated events
2. **Given** multiple runs executing at different speeds, **When** a fast run completes before a slow run, **Then** the slow run continues receiving its events without interruption

---

### User Story 3 - Cancellation Isolation (Priority: P3)

As a user who wants to cancel a specific run, I want the cancellation to affect only the targeted run, leaving other concurrent runs unaffected.

**Why this priority**: Cancellation is a secondary operation that depends on proper isolation being in place first.

**Independent Test**: Start two runs, cancel one mid-execution. Verify the cancelled run stops and the other run continues to completion.

**Acceptance Scenarios**:

1. **Given** Run A and Run B are executing concurrently, **When** user cancels Run A, **Then** Run A stops and receives `lifecycle.cancelled` event while Run B continues unaffected
2. **Given** Run A is cancelled, **When** Run B completes normally, **Then** Run B's stream shows `lifecycle.completed` without any cancellation artifacts

---

### Edge Cases

- What happens when a run completes while another run's callback is being processed?
- How does the system handle rapid successive runs (one starts immediately after another completes)?
- What happens if the underlying thread pool reaches capacity during concurrent runs?
- How does the system behave if Redis becomes temporarily unavailable during concurrent runs?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST route each stream event exclusively to its originating run's SSE connection
- **FR-002**: System MUST include run_id in every event to enable verification of correct routing
- **FR-003**: System MUST maintain event isolation across all event types (lifecycle, llm, dispatch, system)
- **FR-004**: System MUST support callback lookup from any thread, regardless of which thread registered the callback
- **FR-005**: System MUST clean up run-specific resources (callbacks, checkers) when a run completes or fails
- **FR-006**: Cancellation checker MUST only affect the specific run it was registered for
- **FR-007**: System MUST preserve event ordering within each individual run's stream
- **FR-008**: System MUST handle graceful degradation - if isolation mechanism fails, events should be dropped rather than cross-contaminated

### Key Entities

- **Run**: A single execution instance with unique ID, associated hierarchy, task, and isolated event stream
- **Event Callback**: A function registered per-run that routes events to the correct SSE stream
- **Cancellation Checker**: A function registered per-run that checks if that specific run should be cancelled
- **Callback Registry**: A thread-safe mapping from run_id to callback functions, accessible from any thread

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Zero cross-contaminated events when running 10 concurrent runs with the same hierarchy
- **SC-002**: Each run's event stream contains only events with matching run_id (100% accuracy)
- **SC-003**: Cancellation of one run has zero impact on other concurrent runs (measured by other runs completing successfully)
- **SC-004**: Event isolation works correctly regardless of execution timing - fast runs, slow runs, simultaneous completions
- **SC-005**: System can handle at least 10 concurrent runs without event isolation failures

## Assumptions

- The underlying execution framework (strands-agents) may use internal thread pools that are not under our direct control
- Event callbacks may be invoked from threads different from where they were registered
- Run IDs are unique and sequential integers
- Redis Stream storage is already in place for event persistence (per feature 002)
- The SSE Manager already creates per-run instances with isolated memory queues
