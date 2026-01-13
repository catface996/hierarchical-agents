# Quickstart: Add Agent ID Feature

**Feature**: 001-add-agent-id
**Date**: 2025-12-30

## Overview

本功能为 Hierarchy API 和 Stream Event 添加 `agent_id` 字段，使前端能够识别 LLM 输出的具体来源。

## Prerequisites

- Python 3.11+
- MySQL 或 PostgreSQL 数据库
- 已启动的 op-stack-executor 服务

## Quick Test

### 1. 创建带 agent_id 的 Hierarchy

```bash
curl -X POST http://localhost:8082/api/executor/v1/hierarchies/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试研究团队",
    "global_supervisor_agent": {
      "agent_id": "gs-test-001",
      "prompt": "你是首席科学家，负责协调研究工作。"
    },
    "execution_mode": "sequential",
    "teams": [
      {
        "name": "分析组",
        "team_supervisor_agent": {
          "agent_id": "ts-analysis-001",
          "prompt": "你是分析组负责人。"
        },
        "workers": [
          {
            "agent_id": "w-analyst-001",
            "name": "数据分析师",
            "role": "分析研究员",
            "system_prompt": "你是数据分析专家。"
          }
        ]
      }
    ]
  }'
```

**预期响应**:
```json
{
  "success": true,
  "data": {
    "id": "xxx-xxx-xxx",
    "name": "测试研究团队",
    "global_supervisor_agent": {
      "agent_id": "gs-test-001",
      "prompt": "你是首席科学家..."
    },
    "teams": [...]
  }
}
```

### 2. 启动执行并监听 Stream Event

```bash
# 启动执行
curl -X POST http://localhost:8082/api/executor/v1/runs/start \
  -H "Content-Type: application/json" \
  -d '{
    "hierarchy_id": "YOUR_HIERARCHY_ID",
    "task": "分析今天的天气情况"
  }'

# 获取 run_id 后，监听 stream
curl -N http://localhost:8082/api/executor/v1/runs/stream?run_id=YOUR_RUN_ID
```

**预期 Stream Event 格式**:
```
event: llm_stream
data: {"content":"分析","agent_id":"w-analyst-001","timestamp":"2025-12-30T10:30:00.123Z","run_id":"xxx"}

event: llm_stream
data: {"content":"结果","agent_id":"w-analyst-001","timestamp":"2025-12-30T10:30:00.456Z","run_id":"xxx"}
```

### 3. 验证 agent_id Hierarchy 内唯一性

```bash
# 尝试在同一个 Hierarchy 内创建重复 agent_id
curl -X POST http://localhost:8082/api/executor/v1/hierarchies/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试重复团队",
    "global_supervisor_agent": {
      "agent_id": "duplicate-001"
    },
    "teams": [
      {
        "name": "分析组",
        "team_supervisor_agent": {
          "agent_id": "duplicate-001"
        },
        "workers": []
      }
    ]
  }'
```

**预期响应（400 错误）**:
```json
{
  "success": false,
  "error": "agent_id 'duplicate-001' is duplicated within this hierarchy",
  "code": 400001
}
```

**注意**: 不同 Hierarchy 之间可以使用相同的 agent_id，以下操作是允许的：

```bash
# 在另一个 Hierarchy 中使用相同的 agent_id（允许）
curl -X POST http://localhost:8082/api/executor/v1/hierarchies/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "另一个团队",
    "global_supervisor_agent": {
      "agent_id": "gs-test-001"
    },
    "teams": []
  }'
# 这是允许的，因为不同 Hierarchy 可以有相同的 agent_id
```

### 4. 向后兼容测试

使用旧格式创建 Hierarchy（不含 agent_id）:

```bash
curl -X POST http://localhost:8082/api/executor/v1/hierarchies/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "旧格式团队",
    "global_prompt": "你是负责人。",
    "teams": [
      {
        "name": "执行组",
        "supervisor_prompt": "你是执行组负责人。",
        "workers": [
          {
            "name": "执行者",
            "role": "执行研究员",
            "system_prompt": "你是执行专家。"
          }
        ]
      }
    ]
  }'
```

**预期**: 系统自动为所有 Agent 生成 UUID 格式的 `agent_id`。

## Key Changes Summary

| Component | Change |
|-----------|--------|
| API 请求体 | 新增 `global_supervisor_agent`、`team_supervisor_agent` 对象 |
| Worker | 新增 `agent_id` 字段 |
| Stream Event | 简化为 `agent_id` + `content` + `timestamp` + `run_id` |
| 唯一性 | `agent_id` 在同一 Hierarchy 内唯一，不同 Hierarchy 可重复 |
| Timestamp | 精确到毫秒 (`2025-12-30T10:30:00.123Z`) |

## Troubleshooting

### agent_id 冲突
- 错误: `agent_id 'xxx' is duplicated within this hierarchy`
- 解决: 在同一个 Hierarchy 内使用不同的 agent_id
- 注意: 不同 Hierarchy 之间可以使用相同的 agent_id

### 旧版客户端
- 旧版请求（无 agent_id）仍然支持
- 系统自动生成 UUID 格式的 agent_id

### Stream Event 字段变化
- 移除: `_is_global_supervisor`, `_team_name`, `_is_team_supervisor`, `_worker_name`
- 新增: `agent_id`
- 前端需要从 `topology_created` 事件或 `hierarchies/get` 接口获取 Agent 详细信息
