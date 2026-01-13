# API Contract: Event Stream

**Feature**: 002-redis-stream-events
**Date**: 2025-01-01

## 1. SSE 事件流端点

### GET /runs/{run_id}/events/stream

实时订阅运行的事件流。

#### 请求

```http
GET /runs/123/events/stream HTTP/1.1
Accept: text/event-stream
Last-Event-ID: 1704067200000-5    # 可选，断线重连时使用
```

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `run_id` | path | integer | 是 | 运行 ID |
| `Last-Event-ID` | header | string | 否 | 上次接收的事件 ID，用于断线重连 |

#### 响应

```http
HTTP/1.1 200 OK
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
X-Accel-Buffering: no

id: 1704067200000-0
event: lifecycle.started
data: {"run_id":123,"timestamp":"2025-01-01T12:00:00.000Z","sequence":1,"source":null,"event":{"category":"lifecycle","action":"started"},"data":{"task":"分析数据"}}

id: 1704067200001-0
event: llm.stream
data: {"run_id":123,"timestamp":"2025-01-01T12:00:00.001Z","sequence":2,"source":{"agent_id":"researcher","agent_type":"worker","agent_name":"研究员","team_name":"research"},"event":{"category":"llm","action":"stream"},"data":{"content":"正在分析..."}}

: heartbeat 2025-01-01T12:00:15.000Z

id: 1704067200100-0
event: lifecycle.completed
data: {"run_id":123,"timestamp":"2025-01-01T12:00:00.100Z","sequence":50,"source":null,"event":{"category":"lifecycle","action":"completed"},"data":{"result":"分析完成","statistics":{}}}

event: close
data: {"message":"Stream closed"}
```

#### SSE 消息格式

| 字段 | 说明 |
|------|------|
| `id` | Redis Stream 消息 ID，客户端用于断线重连 |
| `event` | 事件类型，格式为 `{category}.{action}` |
| `data` | JSON 格式的完整事件数据 |

#### 错误响应

```http
HTTP/1.1 404 Not Found
Content-Type: application/json

{"code": "RUN_NOT_FOUND", "message": "运行不存在: 123"}
```

```http
HTTP/1.1 410 Gone
Content-Type: application/json

{"code": "RUN_EXPIRED", "message": "运行事件已过期"}
```

---

## 2. 历史事件查询端点

### GET /runs/{run_id}/events

获取运行的历史事件列表。

#### 请求

```http
GET /runs/123/events?start_id=-&end_id=+&limit=100 HTTP/1.1
Accept: application/json
```

| 参数 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|------|--------|------|
| `run_id` | path | integer | 是 | - | 运行 ID |
| `start_id` | query | string | 否 | `-` | 起始 ID，`-` 表示最早 |
| `end_id` | query | string | 否 | `+` | 结束 ID，`+` 表示最新 |
| `limit` | query | integer | 否 | `1000` | 最大返回数量 |

#### 成功响应

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "run_id": 123,
  "events": [
    {
      "id": "1704067200000-0",
      "run_id": 123,
      "timestamp": "2025-01-01T12:00:00.000Z",
      "sequence": 1,
      "source": null,
      "event": {
        "category": "lifecycle",
        "action": "started"
      },
      "data": {
        "task": "分析数据"
      }
    },
    {
      "id": "1704067200001-0",
      "run_id": 123,
      "timestamp": "2025-01-01T12:00:00.001Z",
      "sequence": 2,
      "source": {
        "agent_id": "researcher",
        "agent_type": "worker",
        "agent_name": "研究员",
        "team_name": "research"
      },
      "event": {
        "category": "llm",
        "action": "stream"
      },
      "data": {
        "content": "正在分析..."
      }
    }
  ],
  "count": 2,
  "has_more": false,
  "next_id": null
}
```

#### 响应字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `run_id` | integer | 运行 ID |
| `events` | array | 事件列表 |
| `count` | integer | 返回的事件数量 |
| `has_more` | boolean | 是否还有更多事件 |
| `next_id` | string | 下一页起始 ID（分页用） |

#### 错误响应

```http
HTTP/1.1 404 Not Found
Content-Type: application/json

{"code": "RUN_NOT_FOUND", "message": "运行不存在: 123"}
```

---

## 3. 事件数据结构

### StreamEvent

```typescript
interface StreamEvent {
  id: string;           // Redis Stream 消息 ID
  run_id: number;       // 运行 ID
  timestamp: string;    // ISO 8601 时间戳
  sequence: number;     // 运行内序列号
  source: EventSource | null;  // 事件来源
  event: EventType;     // 事件类型
  data: Record<string, any>;   // 事件数据
}

interface EventSource {
  agent_id: string;
  agent_type: 'global_supervisor' | 'team_supervisor' | 'worker';
  agent_name: string;
  team_name: string;
}

interface EventType {
  category: 'lifecycle' | 'llm' | 'dispatch' | 'system';
  action: string;
}
```

---

## 4. 断线重连流程

### 客户端实现

```javascript
let lastEventId = null;

function connect() {
  const url = `/runs/${runId}/events/stream`;
  const options = lastEventId
    ? { headers: { 'Last-Event-ID': lastEventId } }
    : {};

  const eventSource = new EventSource(url, options);

  eventSource.onmessage = (event) => {
    lastEventId = event.lastEventId;
    handleEvent(JSON.parse(event.data));
  };

  eventSource.onerror = () => {
    eventSource.close();
    setTimeout(connect, 3000);  // 3秒后重连
  };
}
```

### 服务端行为

1. 检查 `Last-Event-ID` 请求头
2. 如果有 `Last-Event-ID`:
   - 从 Redis Stream 读取该 ID 之后的所有事件
   - 先发送历史事件
   - 然后切换到实时订阅模式
3. 如果没有 `Last-Event-ID`:
   - 直接进入实时订阅模式

---

## 5. 心跳机制

服务端每 15 秒发送一次心跳，格式：

```
: heartbeat 2025-01-01T12:00:15.000Z

```

心跳用于：
- 保持 HTTP 连接存活
- 检测客户端断线

---

## 6. 错误码

| 错误码 | HTTP 状态码 | 说明 |
|--------|-------------|------|
| `RUN_NOT_FOUND` | 404 | 运行不存在 |
| `RUN_EXPIRED` | 410 | 运行事件已过期（超过 24 小时） |
| `REDIS_UNAVAILABLE` | 503 | Redis 服务不可用 |
| `INVALID_EVENT_ID` | 400 | 无效的事件 ID 格式 |
