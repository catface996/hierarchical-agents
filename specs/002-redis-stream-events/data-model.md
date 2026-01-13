# Data Model: Redis Stream 事件存储

**Feature**: 002-redis-stream-events
**Date**: 2025-01-01

## 1. Redis Stream 数据结构

### 1.1 Stream Key 命名规范

```
run:{run_id}:events
```

| 示例 | 说明 |
|------|------|
| `run:1:events` | 运行 ID 为 1 的事件流 |
| `run:123:events` | 运行 ID 为 123 的事件流 |

### 1.2 消息 ID

使用 Redis 自动生成的 ID，格式：`<timestamp_ms>-<sequence>`

```
1704067200000-0    # 第一条消息
1704067200000-1    # 同一毫秒内的第二条消息
1704067200001-0    # 下一毫秒的消息
```

**用途**:
- 保证消息顺序
- 支持断线重连（从指定 ID 继续读取）
- 作为 SSE 的 `Last-Event-ID`

## 2. 事件消息字段

### 2.1 字段定义

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `timestamp` | string | 是 | ISO 8601 时间戳，毫秒精度 |
| `sequence` | string | 是 | 运行内序列号（自增） |
| `source_agent_id` | string | 否 | Agent ID |
| `source_agent_type` | string | 否 | Agent 类型 |
| `source_agent_name` | string | 否 | Agent 名称 |
| `source_team_name` | string | 否 | 所属团队名称 |
| `event_category` | string | 是 | 事件类别 |
| `event_action` | string | 是 | 事件动作 |
| `data` | string | 是 | JSON 序列化的事件数据 |

### 2.2 示例消息

```python
# Redis Stream 存储格式
{
    "timestamp": "2025-01-01T12:00:00.123Z",
    "sequence": "1",
    "source_agent_id": "global_supervisor",
    "source_agent_type": "global_supervisor",
    "source_agent_name": "全局协调者",
    "source_team_name": "",
    "event_category": "lifecycle",
    "event_action": "started",
    "data": "{\"task\": \"分析市场数据\"}"
}
```

### 2.3 完整事件格式（应用层）

转换为应用层格式后：

```json
{
    "id": "1704067200123-0",
    "run_id": 1,
    "timestamp": "2025-01-01T12:00:00.123Z",
    "sequence": 1,
    "source": {
        "agent_id": "global_supervisor",
        "agent_type": "global_supervisor",
        "agent_name": "全局协调者",
        "team_name": ""
    },
    "event": {
        "category": "lifecycle",
        "action": "started"
    },
    "data": {
        "task": "分析市场数据"
    }
}
```

## 3. 事件类型定义

### 3.1 事件类别 (category)

| 类别 | 说明 | 典型场景 |
|------|------|----------|
| `lifecycle` | 生命周期事件 | 运行开始/完成/失败 |
| `llm` | LLM 相关事件 | 流式输出、完成响应 |
| `dispatch` | 任务分发事件 | Agent 接收/完成任务 |
| `system` | 系统事件 | 连接关闭、错误 |

### 3.2 事件动作 (action)

| 动作 | 说明 | 使用场景 |
|------|------|----------|
| `started` | 开始 | 运行/任务开始 |
| `completed` | 完成 | 运行/任务完成 |
| `failed` | 失败 | 运行/任务失败 |
| `cancelled` | 取消 | 运行被取消 |
| `stream` | 流式输出 | LLM 流式响应 |
| `assigned` | 任务分配 | 任务分发给 Agent |
| `close` | 关闭 | SSE 连接关闭 |

## 4. Stream 配置

### 4.1 长度限制

```python
MAXLEN = 10000  # 单个运行最多保留 10000 条事件
APPROXIMATE = True  # 使用近似修剪提升性能
```

### 4.2 过期策略

```python
TTL_SECONDS = 86400  # 24 小时后自动删除
```

设置时机：运行结束时调用 `EXPIRE run:{run_id}:events 86400`

## 5. Python 数据类

### 5.1 EventStore 接口

```python
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime

@dataclass
class StreamEvent:
    """Redis Stream 事件"""
    id: str                          # Redis 消息 ID
    run_id: int                      # 运行 ID
    timestamp: str                   # ISO 8601 时间戳
    sequence: int                    # 序列号
    source: Optional[Dict[str, str]] # 来源信息
    event: Dict[str, str]           # 事件类型
    data: Dict[str, Any]            # 事件数据


class EventStore:
    """事件存储接口"""

    def add(
        self,
        run_id: int,
        event_category: str,
        event_action: str,
        data: dict = None,
        source: dict = None
    ) -> Optional[str]:
        """
        添加事件到 Stream

        Returns:
            消息 ID 或 None（失败时）
        """
        pass

    def get_events(
        self,
        run_id: int,
        start_id: str = '-',
        end_id: str = '+',
        count: int = None
    ) -> List[StreamEvent]:
        """
        获取事件列表

        Args:
            run_id: 运行 ID
            start_id: 起始 ID（包含），'-' 表示最早
            end_id: 结束 ID（包含），'+' 表示最新
            count: 最大返回数量
        """
        pass

    def get_events_after(
        self,
        run_id: int,
        last_id: str,
        count: int = None
    ) -> List[StreamEvent]:
        """
        获取指定 ID 之后的事件（不包含 last_id）

        用于断线重连场景
        """
        pass

    def subscribe(
        self,
        run_id: int,
        last_id: str = '$',
        block_ms: int = 5000
    ) -> List[StreamEvent]:
        """
        订阅新事件（阻塞读取）

        Args:
            run_id: 运行 ID
            last_id: 从此 ID 之后开始读取，'$' 表示只读新消息
            block_ms: 阻塞等待时间（毫秒）
        """
        pass

    def set_expire(self, run_id: int, ttl_seconds: int = 86400) -> bool:
        """设置 Stream 过期时间"""
        pass

    def delete(self, run_id: int) -> bool:
        """删除 Stream"""
        pass
```

## 6. 与现有模型的关系

### 6.1 保留的 MySQL 模型

**ExecutionRun** - 继续存储在 MySQL：
- 运行记录元数据（id, hierarchy_id, task, status）
- 执行结果（result, error, statistics）
- 时间戳（created_at, started_at, completed_at）
- 拓扑快照（topology_snapshot）

### 6.2 迁移到 Redis 的数据

**ExecutionEvent** - 从 MySQL 迁移到 Redis Stream：
- 所有事件数据通过 Redis Stream 存储
- MySQL 中的 `execution_event` 表将不再使用
- 可选：保留表结构作为备份机制

## 7. 数据流图

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   RunManager    │     │   EventStore    │     │  Redis Stream   │
│                 │     │                 │     │                 │
│ event_callback()├────▶│ add()           ├────▶│ XADD            │
│                 │     │                 │     │ run:1:events    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   SSE Client    │◀────│   SSE Endpoint  │◀────│ XRANGE/XREAD    │
│                 │     │                 │     │                 │
│ (断线重连)      │────▶│ Last-Event-ID   │────▶│ get_events_after│
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## 8. 索引和查询优化

Redis Stream 自带基于消息 ID 的索引，支持：
- O(log N) 的 ID 查找
- O(log N + M) 的范围查询（M 为返回数量）

无需额外索引配置。
