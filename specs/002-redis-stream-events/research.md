# Research: Redis Stream 事件存储

**Feature**: 002-redis-stream-events
**Date**: 2025-01-01

## 1. Redis Stream 技术概述

### 1.1 什么是 Redis Stream

Redis Stream 是 Redis 5.0 (2018) 引入的数据结构，设计目标是提供：
- 高性能的追加日志（Append-only log）
- 消息队列功能
- 消费者组支持
- 消息持久化和回放

### 1.2 核心特性

| 特性 | 描述 |
|------|------|
| 消息 ID | 格式 `<millisecondsTime>-<sequenceNumber>`，自动生成，保证唯一且有序 |
| 范围查询 | 支持按 ID 范围高效读取 |
| 阻塞读取 | `XREAD BLOCK` 支持实时订阅 |
| 消费者组 | 支持多消费者协作消费（本特性不需要） |
| 自动修剪 | `MAXLEN` 参数控制 Stream 长度 |
| TTL | 可设置整个 Stream 的过期时间 |

### 1.3 与其他 Redis 数据结构对比

| 数据结构 | 适用场景 | 优势 | 劣势 |
|----------|----------|------|------|
| List | 简单队列 | 简单 | 无 ID，无范围查询 |
| Pub/Sub | 实时广播 | 低延迟 | 不持久化，断线丢失 |
| Sorted Set | 有序数据 | 灵活排序 | 无阻塞读取 |
| **Stream** | 事件日志 | ID+持久化+阻塞读取 | 相对复杂 |

**结论**: Redis Stream 是执行事件存储的最佳选择。

## 2. Python redis-py 库

### 2.1 版本选择

```
redis>=5.0.0
```

redis-py 5.0+ 提供完整的 Stream 支持和异步接口。

### 2.2 核心 API

```python
import redis

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

# 写入消息
message_id = r.xadd(
    'mystream',
    {'field1': 'value1', 'field2': 'value2'},
    maxlen=10000,      # 最大长度
    approximate=True    # 近似修剪（性能更好）
)
# 返回: '1704067200000-0'

# 读取所有消息
messages = r.xrange('mystream', '-', '+')
# 返回: [('1704067200000-0', {'field1': 'value1', 'field2': 'value2'}), ...]

# 从指定 ID 之后读取（断线重连）
messages = r.xrange('mystream', '1704067200000-0', '+', count=100)

# 阻塞读取新消息
messages = r.xread({'mystream': '$'}, block=5000)  # 阻塞 5 秒
# 返回: [['mystream', [('1704067200001-0', {...})]]]

# 设置过期时间
r.expire('mystream', 86400)  # 24 小时
```

## 3. 数据结构设计

### 3.1 Stream Key 命名

```
run:{run_id}:events
```

示例: `run:123:events`

### 3.2 消息字段

```json
{
  "timestamp": "2025-01-01T12:00:00.000Z",
  "sequence": "1",
  "source_agent_id": "agent-001",
  "source_agent_type": "worker",
  "source_agent_name": "researcher",
  "source_team_name": "research_team",
  "event_category": "llm",
  "event_action": "stream",
  "data": "{\"content\": \"...\"}"
}
```

**注意**: Redis Stream 字段值只能是字符串，JSON 对象需要序列化。

### 3.3 消息 ID 使用

- 使用 Redis 自动生成的 ID（`*`）
- 格式: `<timestamp_ms>-<seq>`
- 天然有序，可用于断线重连
- SSE 客户端发送 `Last-Event-ID` 时，直接使用 Redis Stream 消息 ID

## 4. 实现架构

### 4.1 组件关系

```
┌─────────────────────────────────────────────────────────────┐
│                       RunManager                             │
│                                                              │
│  ┌──────────────────┐     ┌──────────────────────────────┐  │
│  │ execute_hierarchy│────▶│ event_callback               │  │
│  └──────────────────┘     │                              │  │
│                           │  ┌────────────────────────┐  │  │
│                           │  │ EventStore.add()       │──┼──┼──▶ Redis Stream
│                           │  └────────────────────────┘  │  │
│                           │  ┌────────────────────────┐  │  │
│                           │  │ SSEManager.emit()      │──┼──┼──▶ Queue (in-memory)
│                           │  └────────────────────────┘  │  │
│                           └──────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                       SSE Endpoint                           │
│                                                              │
│  GET /runs/{id}/events/stream                                │
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  1. 检查 Last-Event-ID header                           ││
│  │  2. 如有 last_id: EventStore.get_events_from(last_id)   ││
│  │  3. 实时订阅: SSEManager.generate_events() 或           ││
│  │              EventStore.subscribe()                      ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### 4.2 双写策略

**方案一**: 同时写入 Redis 和内存队列（推荐）
- 优点: SSE 响应延迟最低，断线重连有 Redis 兜底
- 缺点: 两个数据源，需保证一致性

**方案二**: 只写入 Redis，SSE 从 Redis 读取
- 优点: 单一数据源
- 缺点: SSE 需要轮询或使用 XREAD BLOCK

**结论**: 采用方案一，保持现有 SSE 的低延迟特性。

## 5. 错误处理和降级

### 5.1 Redis 不可用

```python
class EventStore:
    def add(self, run_id, event_data):
        try:
            return self.redis.xadd(...)
        except redis.RedisError as e:
            logger.error(f"Redis write failed: {e}")
            # 不阻塞主流程，仅记录日志
            return None
```

### 5.2 重连机制

redis-py 自带连接池和自动重连：

```python
r = redis.Redis(
    host='localhost',
    port=6379,
    socket_connect_timeout=5,
    socket_keepalive=True,
    retry_on_timeout=True
)
```

## 6. 性能考量

### 6.1 写入性能

- Redis XADD: ~100,000 ops/sec (单实例)
- 完全满足 "事件写入延迟 < 10ms" 要求

### 6.2 读取性能

- XRANGE: O(log(N) + M) 其中 M 是返回的消息数
- XREAD BLOCK: 无轮询开销

### 6.3 内存优化

```python
# 近似修剪（性能更好）
XADD stream MAXLEN ~ 10000 * field value

# 运行结束后设置 TTL
EXPIRE stream 86400
```

## 7. 本地开发环境

### 7.1 Docker Compose

```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

volumes:
  redis_data:
```

### 7.2 环境变量

```bash
REDIS_URL=redis://localhost:6379/0
```

## 8. 与现有代码的集成点

### 8.1 需要修改的文件

| 文件 | 修改内容 |
|------|----------|
| `requirements.txt` | 添加 `redis>=5.0.0` |
| `src/streaming/event_store.py` | 新增：Redis Stream 事件存储 |
| `src/runner/run_manager.py` | 修改：使用 EventStore 写入事件 |
| `src/streaming/sse_manager.py` | 修改：支持断线重连读取历史事件 |
| `src/api/routes/runs.py` | 修改：SSE 端点支持 Last-Event-ID |
| `src/db/models.py` | 可选：移除 ExecutionEvent 模型 |
| `src/db/repositories/run_repo.py` | 修改：移除事件相关方法 |

### 8.2 保持不变

- `src/core/api_models.py` - 事件类型定义不变
- `src/streaming/llm_callback.py` - 回调机制不变
- V2 事件格式不变

## 9. 测试策略

### 9.1 单元测试

- `test_event_store.py`: Mock Redis，测试 EventStore 逻辑

### 9.2 集成测试

- `test_event_stream.py`: 使用真实 Redis，测试端到端流程
- 测试断线重连场景
- 测试多客户端订阅

### 9.3 性能测试

- 写入 10000 个事件的耗时
- 断线重连恢复 1000 个事件的耗时

## 10. 结论

Redis Stream 是本特性的最佳选择：
1. 原生支持消息 ID 和范围查询，完美支持断线重连
2. XREAD BLOCK 支持实时订阅
3. MAXLEN + TTL 支持自动清理
4. 高性能，满足延迟要求
5. redis-py 提供完整支持

**建议**: 采用 "双写" 策略，同时写入 Redis（持久化+断线恢复）和内存队列（低延迟 SSE）。
