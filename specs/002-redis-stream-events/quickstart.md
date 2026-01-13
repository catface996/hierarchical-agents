# Quickstart: Redis Stream 事件存储

**Feature**: 002-redis-stream-events
**Date**: 2025-01-01

## 1. 环境准备

### 1.1 启动 Redis (Docker)

```bash
# 创建并启动 Redis 容器
docker run -d \
  --name op-stack-redis \
  -p 6379:6379 \
  -v redis_data:/data \
  redis:7-alpine \
  redis-server --appendonly yes

# 验证 Redis 运行状态
docker exec op-stack-redis redis-cli ping
# 应返回: PONG
```

### 1.2 环境变量配置

在 `.env` 文件中添加：

```bash
# Redis 配置
REDIS_URL=redis://localhost:6379/0
```

### 1.3 安装依赖

```bash
pip install redis>=5.0.0
```

或更新 `requirements.txt`：

```
redis>=5.0.0
```

## 2. 快速验证

### 2.1 Python 连接测试

```python
import redis

r = redis.from_url('redis://localhost:6379/0')
print(r.ping())  # True
```

### 2.2 Stream 基本操作

```python
import redis
import json

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

# 写入事件
stream_key = 'run:1:events'
event_data = {
    'timestamp': '2025-01-01T12:00:00.000Z',
    'sequence': '1',
    'event_category': 'lifecycle',
    'event_action': 'started',
    'data': json.dumps({'task': '测试任务'})
}
msg_id = r.xadd(stream_key, event_data, maxlen=10000)
print(f"写入消息 ID: {msg_id}")

# 读取事件
events = r.xrange(stream_key, '-', '+')
for event_id, fields in events:
    print(f"ID: {event_id}, 数据: {fields}")

# 设置过期时间
r.expire(stream_key, 86400)

# 清理测试数据
r.delete(stream_key)
```

## 3. 使用 EventStore

### 3.1 基本用法

```python
from src.streaming.event_store import EventStore

# 创建实例
store = EventStore()

# 写入事件
event_id = store.add(
    run_id=1,
    event_category='lifecycle',
    event_action='started',
    data={'task': '分析数据'},
    source=None
)
print(f"事件 ID: {event_id}")

# 读取所有事件
events = store.get_events(run_id=1)
for event in events:
    print(f"{event.id}: {event.event}")

# 读取指定 ID 之后的事件（断线重连）
events = store.get_events_after(run_id=1, last_id='1704067200000-0')

# 运行结束时设置过期
store.set_expire(run_id=1, ttl_seconds=86400)
```

### 3.2 实时订阅

```python
from src.streaming.event_store import EventStore

store = EventStore()

# 阻塞等待新事件
while True:
    events = store.subscribe(run_id=1, block_ms=5000)
    if events:
        for event in events:
            print(f"新事件: {event}")
    else:
        print("超时，继续等待...")
```

## 4. SSE 客户端示例

### 4.1 JavaScript (浏览器)

```javascript
const runId = 123;
let lastEventId = null;

function connectSSE() {
  const url = `http://localhost:8082/runs/${runId}/events/stream`;
  const eventSource = new EventSource(url);

  // 监听所有事件类型
  eventSource.onmessage = (e) => {
    lastEventId = e.lastEventId;
    const event = JSON.parse(e.data);
    console.log(`[${event.event.category}.${event.event.action}]`, event.data);
  };

  // 监听特定事件类型
  eventSource.addEventListener('lifecycle.started', (e) => {
    console.log('运行开始:', JSON.parse(e.data));
  });

  eventSource.addEventListener('llm.stream', (e) => {
    const event = JSON.parse(e.data);
    process.stdout.write(event.data.content || '');
  });

  eventSource.addEventListener('lifecycle.completed', (e) => {
    console.log('运行完成:', JSON.parse(e.data));
    eventSource.close();
  });

  // 错误处理和重连
  eventSource.onerror = (e) => {
    console.error('SSE 连接错误');
    eventSource.close();
    // 3秒后重连，携带 Last-Event-ID
    setTimeout(() => reconnect(lastEventId), 3000);
  };
}

function reconnect(lastId) {
  const url = `http://localhost:8082/runs/${runId}/events/stream`;
  const eventSource = new EventSource(url, {
    headers: { 'Last-Event-ID': lastId }
  });
  // ... 同上
}

connectSSE();
```

### 4.2 Python 客户端

```python
import requests
import json

def subscribe_events(run_id: int, last_event_id: str = None):
    url = f'http://localhost:8082/runs/{run_id}/events/stream'
    headers = {'Accept': 'text/event-stream'}
    if last_event_id:
        headers['Last-Event-ID'] = last_event_id

    with requests.get(url, headers=headers, stream=True) as response:
        for line in response.iter_lines(decode_unicode=True):
            if line.startswith('data:'):
                data = json.loads(line[5:].strip())
                yield data
            elif line.startswith('id:'):
                last_event_id = line[3:].strip()

# 使用
for event in subscribe_events(run_id=1):
    print(f"[{event['event']['category']}.{event['event']['action']}]")
    print(f"  数据: {event['data']}")
```

## 5. 常见问题

### Q1: Redis 连接失败

```
redis.exceptions.ConnectionError: Error 111 connecting to localhost:6379
```

**解决**: 检查 Redis 容器是否运行

```bash
docker ps | grep redis
docker start op-stack-redis
```

### Q2: 断线重连后没有收到历史事件

检查:
1. 客户端是否正确发送 `Last-Event-ID` 头
2. 服务端是否实现了历史事件恢复逻辑
3. 事件是否已过期（24 小时后自动删除）

### Q3: 事件顺序不正确

Redis Stream 消息 ID 保证顺序，如果客户端显示乱序：
1. 检查是否按 `sequence` 字段排序
2. 检查是否有并发写入问题

## 6. 开发调试

### 6.1 Redis CLI 查看事件

```bash
# 进入 Redis CLI
docker exec -it op-stack-redis redis-cli

# 查看所有 Stream
KEYS run:*:events

# 查看 Stream 信息
XINFO STREAM run:1:events

# 读取所有事件
XRANGE run:1:events - +

# 读取最近 10 个事件
XREVRANGE run:1:events + - COUNT 10

# 查看 Stream 长度
XLEN run:1:events

# 查看 TTL
TTL run:1:events
```

### 6.2 清理测试数据

```bash
# 删除单个 Stream
DEL run:1:events

# 删除所有事件 Stream
redis-cli KEYS "run:*:events" | xargs redis-cli DEL
```
