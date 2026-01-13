# Data Model: Add Agent ID

**Date**: 2025-12-30
**Feature**: 001-add-agent-id

## Entity Changes

### 1. HierarchyTeam (hierarchy_team)

**New Field:**

| Field | Type | Nullable | Default | Constraint | Description |
|-------|------|----------|---------|------------|-------------|
| `global_supervisor_agent_id` | String(100) | Yes | NULL | - | Global Supervisor 的 agent_id |

**Validation Rules:**
- 非空时，最大长度 100 字符
- 在同一 Hierarchy 内唯一（应用层校验）
- 为空时，创建时自动生成 UUID

---

### 2. Team (team)

**New Field:**

| Field | Type | Nullable | Default | Constraint | Description |
|-------|------|----------|---------|------------|-------------|
| `supervisor_agent_id` | String(100) | Yes | NULL | - | Team Supervisor 的 agent_id |

**Validation Rules:**
- 非空时，最大长度 100 字符
- 在同一 Hierarchy 内唯一（应用层校验）
- 为空时，创建时自动生成 UUID

---

### 3. Worker (worker)

**New Field:**

| Field | Type | Nullable | Default | Constraint | Description |
|-------|------|----------|---------|------------|-------------|
| `agent_id` | String(100) | Yes | NULL | - | Worker 的 agent_id |

**Validation Rules:**
- 非空时，最大长度 100 字符
- 在同一 Hierarchy 内唯一（应用层校验）
- 为空时，创建时自动生成 UUID

---

### 4. ExecutionEvent (execution_event)

**New Field:**

| Field | Type | Nullable | Default | Constraint | Description |
|-------|------|----------|---------|------------|-------------|
| `agent_id` | String(100) | Yes | NULL | - | 事件来源 Agent 的 agent_id |

**Deprecated Fields (保留但不再写入新数据):**
- `is_global_supervisor` → 由 `agent_id` 查 topology 判断
- `team_name` → 由 `agent_id` 查 topology 获取
- `is_team_supervisor` → 由 `agent_id` 查 topology 判断
- `worker_name` → 由 `agent_id` 查 topology 获取

---

## Hierarchy 内唯一性约束

`agent_id` 仅需在单个 Hierarchy Team 内唯一，不同 Hierarchy 之间可以使用相同的 `agent_id`。

**Implementation Strategy:**

在创建/更新 Hierarchy 时，收集所有 agent_id 并检查是否有重复：

```python
def check_agent_ids_unique_in_hierarchy(
    global_agent_id: str,
    teams: List[dict]
) -> Tuple[bool, Optional[str]]:
    """检查 agent_id 在 Hierarchy 内是否唯一"""
    all_agent_ids = []

    # 收集 Global Supervisor agent_id
    if global_agent_id:
        all_agent_ids.append(global_agent_id)

    # 收集所有 Team Supervisor 和 Worker 的 agent_id
    for team in teams:
        if team.get('supervisor_agent_id'):
            all_agent_ids.append(team['supervisor_agent_id'])
        for worker in team.get('workers', []):
            if worker.get('agent_id'):
                all_agent_ids.append(worker['agent_id'])

    # 检查是否有重复
    seen = set()
    for agent_id in all_agent_ids:
        if agent_id in seen:
            return False, agent_id  # 返回重复的 agent_id
        seen.add(agent_id)

    return True, None
```

---

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        HierarchyTeam                             │
├─────────────────────────────────────────────────────────────────┤
│ id: String(36) [PK]                                              │
│ name: String(100)                                                │
│ global_prompt: Text                                              │
│ global_supervisor_agent_id: String(100) [NEW]                   │
│ ...                                                              │
└─────────────────────────────────────────────────────────────────┘
                              │ 1:N
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                            Team                                  │
├─────────────────────────────────────────────────────────────────┤
│ id: String(36) [PK]                                              │
│ hierarchy_id: String(36) [FK]                                    │
│ name: String(100)                                                │
│ supervisor_prompt: Text                                          │
│ supervisor_agent_id: String(100) [NEW]                          │
│ ...                                                              │
└─────────────────────────────────────────────────────────────────┘
                              │ 1:N
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                           Worker                                 │
├─────────────────────────────────────────────────────────────────┤
│ id: String(36) [PK]                                              │
│ team_id: String(36) [FK]                                         │
│ name: String(100)                                                │
│ agent_id: String(100) [NEW]                                     │
│ ...                                                              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                       ExecutionEvent                             │
├─────────────────────────────────────────────────────────────────┤
│ id: String(36) [PK]                                              │
│ run_id: String(36) [FK]                                          │
│ event_type: String(50)                                           │
│ agent_id: String(100) [NEW]                                     │
│ timestamp: DateTime                                              │
│ data: JSON                                                       │
│ ...                                                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Migration Notes

1. **新增字段**: 所有新字段均为 nullable，不影响现有数据
2. **无唯一约束**: `agent_id` 唯一性通过应用层校验，无需数据库唯一索引
3. **向后兼容**: 旧数据 `agent_id` 为 NULL，查询时需处理
