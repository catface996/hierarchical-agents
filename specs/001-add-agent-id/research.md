# Research: Add Agent ID to Hierarchy API and Stream Events

**Date**: 2025-12-30
**Feature**: 001-add-agent-id

## Research Summary

本功能基于现有代码库扩展，无需外部技术研究。以下是对现有实现的分析和设计决策。

---

## 1. Hierarchy 内唯一性校验方案

### Decision
使用应用层校验，在创建/更新 Hierarchy 时检查 agent_id 是否在该 Hierarchy 内重复

### Rationale
- `agent_id` 仅需在单个 Hierarchy Team 内唯一，不需要跨 Hierarchy 全局唯一
- 不同 Hierarchy 可以使用相同的 `agent_id`（如 "analyst-001"）
- 应用层校验足够，无需数据库唯一约束（因为唯一性范围是 Hierarchy 内）

### Alternatives Considered
1. **数据库复合唯一约束**: 复杂度高，需要在多表间协调
2. **全局唯一**: 限制过严，不同项目无法复用相同的 agent_id 命名
3. **不校验**: 可能导致同一 Hierarchy 内有重复 agent_id，stream event 无法区分来源

### Implementation Notes
- 创建 Hierarchy 时，收集所有 agent_id（global + team supervisors + workers）
- 检查是否有重复，如有则返回 400 错误
- 更新 Hierarchy 时同样检查

---

## 2. API 请求体结构重构

### Decision
采用嵌套 Agent 对象结构，保持向后兼容

### Rationale
- 将 Agent 配置（prompt, model_id, temperature 等）封装在独立对象中
- 现有字段 `global_prompt` 映射到 `global_supervisor_agent.prompt`
- 支持同时接收旧格式（global_prompt）和新格式（global_supervisor_agent）

### Alternatives Considered
1. **扁平化结构**: 字段过多，不利于扩展
2. **完全替换旧字段**: 破坏向后兼容性
3. **新版本 API (v2)**: 维护成本高，当前变更不需要

### Backward Compatibility Strategy
```python
# 兼容逻辑伪代码
if request.global_supervisor_agent:
    global_prompt = request.global_supervisor_agent.prompt
    global_agent_id = request.global_supervisor_agent.agent_id or generate_uuid()
elif request.global_prompt:
    global_prompt = request.global_prompt
    global_agent_id = generate_uuid()  # 旧版请求自动生成
```

---

## 3. Stream Event 简化

### Decision
移除冗余字段，仅保留 `agent_id`、`content`、`timestamp`、`run_id`

### Rationale
- `agent_id` 全局唯一，可直接定位到具体 Agent
- 前端从 `topology_created` 事件或 `hierarchies/get` 接口获取 Agent 详细信息
- 减少网络传输量和事件处理复杂度

### Fields to Remove
- `_is_global_supervisor`
- `_team_name`
- `_is_team_supervisor`
- `_worker_name`

### Migration Impact
- **数据库**: `execution_event` 表仍保留这些字段用于历史数据查询
- **实时事件**: 新事件不再包含这些字段
- **前端**: 需要更新事件处理逻辑

---

## 4. Timestamp 毫秒精度

### Decision
使用 ISO 8601 格式，精确到毫秒：`2025-12-30T10:30:00.123Z`

### Rationale
- 毫秒精度足够区分快速连续的事件
- ISO 8601 是标准格式，前端解析方便
- Python `datetime.isoformat()` 默认支持微秒，截取到毫秒即可

### Implementation
```python
from datetime import datetime
timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.') + f'{datetime.utcnow().microsecond // 1000:03d}Z'
```

---

## 5. CallerContext 重构

### Decision
在 `CallerContext` 中添加 `agent_id` 字段

### Rationale
- `CallerContext` 已用于追踪 LLM 调用来源
- 添加 `agent_id` 字段可无缝集成到现有事件发射流程
- 移除 `to_event_fields()` 中的旧字段，仅返回 `agent_id`

### Current Structure
```python
@dataclass
class CallerContext:
    is_global_supervisor: bool = False
    team_name: Optional[str] = None
    is_team_supervisor: bool = False
    worker_name: Optional[str] = None
```

### New Structure
```python
@dataclass
class CallerContext:
    agent_id: str  # 必填，全局唯一
    # 内部使用（不发送到事件）
    _is_global_supervisor: bool = False
    _team_name: Optional[str] = None
    _is_team_supervisor: bool = False
    _worker_name: Optional[str] = None
```

---

## Conclusion

所有技术决策已明确，无需外部研究。可直接进入 Phase 1 设计阶段。
