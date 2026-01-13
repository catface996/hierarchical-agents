# Implementation Plan: Add Agent ID to Hierarchy API and Stream Events

**Branch**: `001-add-agent-id` | **Date**: 2025-12-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-add-agent-id/spec.md`

## Summary

为 Hierarchy API 和 Stream Event 添加 `agent_id` 字段，使前端能够识别 LLM 输出来源。主要变更包括：
1. 重构 `/api/executor/v1/hierarchies/create` 请求体结构，支持 `global_supervisor_agent`、`team_supervisor_agent` 和 Worker 的 `agent_id`
2. 简化 Stream Event 结构，移除冗余字段，仅保留 `agent_id`、`content`、`timestamp`、`run_id`
3. `agent_id` 全局唯一，系统在创建时校验

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: Flask 3.0+, SQLAlchemy 2.0+, strands-agents, boto3
**Storage**: MySQL / PostgreSQL (via SQLAlchemy ORM)
**Testing**: pytest, test_stream.py, test_stream_raw.py
**Target Platform**: Linux server (EC2), AWS Lambda
**Project Type**: Single backend service (API server)
**Performance Goals**: N/A (feature enhancement, no new performance requirements)
**Constraints**: 向后兼容旧版 API 请求（不含 agent_id）
**Scale/Scope**: 现有系统扩展，影响 3 个数据表和 4 个事件类型

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. URL Namespace Convention | ✅ PASS | 使用现有 `/api/executor/v1/hierarchies/*` 端点 |
| II. RESTful API Design | ✅ PASS | POST 操作，JSON 格式，标准响应格式 |
| III. Hierarchical Agent Architecture | ✅ PASS | 保持 Global → Team → Worker 层级 |
| IV. Streaming & Real-time Events | ✅ PASS | 简化事件结构，保留核心字段 |
| V. Database Agnosticism | ✅ PASS | 使用 SQLAlchemy ORM |
| VI. Server Configuration | ✅ PASS | 不涉及服务器配置变更 |
| VII. Database Table Naming | ✅ PASS | 使用单数表名：hierarchy_team, team, worker, execution_event |

**Gate Result**: ✅ ALL PASSED - 可以继续

## Project Structure

### Documentation (this feature)

```text
specs/001-add-agent-id/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── hierarchy-api.yaml
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
src/
├── api/
│   ├── routes/
│   │   └── hierarchies.py    # API 路由 (修改)
│   └── schemas/
│       └── hierarchy_schemas.py  # 请求/响应 Schema (修改)
├── core/
│   ├── api_models.py         # 内部数据模型 (修改)
│   └── hierarchy_executor.py # 执行器 (修改)
├── db/
│   ├── models.py             # 数据库模型 (修改)
│   └── repositories/
│       └── hierarchy_repo.py # 仓库层 (修改)
├── runner/
│   └── run_manager.py        # 运行管理器 (修改)
└── streaming/
    ├── llm_callback.py       # LLM 回调 (修改)
    └── sse_manager.py        # SSE 管理器 (修改)
```

**Structure Decision**: 单体后端服务，所有变更在现有 `src/` 目录结构内完成。

## Complexity Tracking

> 无宪法违规，无需复杂性追踪。
