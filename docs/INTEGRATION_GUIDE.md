# Op-Stack Executor 接入指南

本文档指导其他系统如何接入 Op-Stack Executor 的流式事件 API。

## 目录

- [快速开始](#快速开始)
- [API 端点](#api-端点)
- [事件格式](#事件格式)
- [事件类型详解](#事件类型详解)
- [代码示例](#代码示例)
- [最佳实践](#最佳实践)

---

## 快速开始

### 1. 创建层级团队

```bash
curl -X POST http://localhost:8082/api/executor/v1/hierarchies/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "研究团队",
    "global_supervisor_agent": {
      "agent_id": "gs-001",
      "system_prompt": "你是首席科学家，负责协调研究团队。"
    },
    "teams": [{
      "name": "分析组",
      "team_supervisor_agent": {
        "agent_id": "ts-001",
        "system_prompt": "你是分析组主管。"
      },
      "workers": [{
        "agent_id": "w-001",
        "name": "分析师",
        "role": "数据分析",
        "system_prompt": "你是数据分析师。"
      }]
    }]
  }'
```

### 2. 启动任务

```bash
curl -X POST http://localhost:8082/api/executor/v1/runs/start \
  -H "Content-Type: application/json" \
  -d '{
    "hierarchy_id": "<hierarchy_id>",
    "task": "请分析这个问题"
  }'
```

### 3. 监听 SSE 事件流

```bash
curl -X POST http://localhost:8082/api/executor/v1/runs/stream \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"id": "<run_id>"}'
```

---

## API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/executor/v1/hierarchies/create` | POST | 创建层级团队 |
| `/api/executor/v1/hierarchies/list` | POST | 获取层级团队列表 |
| `/api/executor/v1/hierarchies/get` | POST | 获取层级团队详情 |
| `/api/executor/v1/runs/start` | POST | 启动任务运行 |
| `/api/executor/v1/runs/stream` | POST | SSE 流式事件 |
| `/api/executor/v1/runs/events` | POST | 获取历史事件列表 |
| `/api/executor/v1/runs/cancel` | POST | 取消运行 |
| `/swagger-ui.html` | GET | Swagger UI |
| `/v3/api-docs` | GET | OpenAPI 3.0 JSON |

---

## 事件格式

### SSE 事件结构

每个 SSE 事件格式如下：

```
event: {category}.{action}
data: {"run_id": "...", "timestamp": "...", "sequence": 123, "source": {...}, "event": {...}, "data": {...}}
```

### 完整事件 JSON 结构

```json
{
  "run_id": "abc-123-def",
  "timestamp": "2025-01-01T12:00:00.123Z",
  "sequence": 1,
  "source": {
    "agent_id": "gs-001",
    "agent_type": "global_supervisor",
    "agent_name": "Global Supervisor",
    "team_name": null
  },
  "event": {
    "category": "llm",
    "action": "stream"
  },
  "data": {
    "content": "正在分析任务..."
  }
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `run_id` | string | 运行唯一标识 |
| `timestamp` | string | ISO 8601 时间戳（毫秒精度） |
| `sequence` | integer | 事件序列号（用于排序） |
| `source` | object | 事件来源（可为 null） |
| `event` | object | 事件类型 |
| `data` | object | 事件数据 |

### Source 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `agent_id` | string | Agent 唯一标识 |
| `agent_type` | string | Agent 类型 |
| `agent_name` | string | Agent 名称 |
| `team_name` | string | 所属团队（Worker/TeamSupervisor 有值） |

### Agent 类型 (agent_type)

| 值 | 说明 |
|----|------|
| `global_supervisor` | 全局主管，负责协调所有团队 |
| `team_supervisor` | 团队主管，负责协调团队内 Worker |
| `worker` | 工作者，执行具体任务 |

---

## 事件类型详解

### 事件类别 (category)

| category | 说明 |
|----------|------|
| `lifecycle` | 生命周期事件 |
| `llm` | LLM 相关事件 |
| `dispatch` | 调度事件 |
| `system` | 系统事件 |

### 事件动作 (action)

#### lifecycle 类别

| action | 说明 | source | data |
|--------|------|--------|------|
| `started` | 运行开始 | null | `{task: "..."}` |
| `completed` | 运行完成 | null | `{result: "...", statistics: {...}}` |
| `failed` | 运行失败 | null | `{error: "..."}` |
| `cancelled` | 运行取消 | null | `{}` |

#### llm 类别

| action | 说明 | source | data |
|--------|------|--------|------|
| `stream` | LLM 流式输出 | Agent 来源 | `{content: "..."}` |
| `reasoning` | LLM 推理过程 | Agent 来源 | `{content: "..."}` |
| `tool_call` | 工具调用 | Agent 来源 | `{tool_name: "...", arguments: {...}}` |
| `tool_result` | 工具结果 | Agent 来源 | `{tool_name: "...", result: "..."}` |

#### dispatch 类别

| action | 说明 | source | data |
|--------|------|--------|------|
| `team` | 调度团队 | Global Supervisor | `{name: "团队名", task: "..."}` |
| `worker` | 调度 Worker | Team Supervisor | `{name: "Worker名", task: "..."}` |

#### system 类别

| action | 说明 | source | data |
|--------|------|--------|------|
| `topology` | 拓扑结构 | null | `{topology: {...}}` |
| `warning` | 警告信息 | 视情况 | `{message: "..."}` |
| `error` | 错误信息 | 视情况 | `{error: "...", details: "..."}` |

---

## 代码示例

### Python 客户端

```python
import json
import requests
import sseclient

BASE_URL = "http://localhost:8082"

def start_and_stream(hierarchy_id: str, task: str):
    # 1. 启动任务
    resp = requests.post(
        f"{BASE_URL}/api/executor/v1/runs/start",
        json={"hierarchy_id": hierarchy_id, "task": task}
    )
    run_id = resp.json()["data"]["id"]
    print(f"Run ID: {run_id}")

    # 2. 监听事件流
    stream_resp = requests.post(
        f"{BASE_URL}/api/executor/v1/runs/stream",
        json={"id": run_id},
        stream=True
    )

    client = sseclient.SSEClient(stream_resp)
    for event in client.events():
        if event.event == "close":
            print("Stream closed")
            break

        data = json.loads(event.data)
        handle_event(event.event, data)

def handle_event(event_type: str, data: dict):
    """处理事件"""
    source = data.get("source")
    event_data = data.get("data", {})

    # 根据事件类型处理
    if event_type == "lifecycle.started":
        print(f"任务开始: {event_data.get('task')}")

    elif event_type == "llm.stream":
        content = event_data.get("content", "")
        agent_type = source.get("agent_type") if source else "system"
        print(f"[{agent_type}] {content}", end="")

    elif event_type == "dispatch.team":
        print(f"\n调度团队: {event_data.get('name')}")

    elif event_type == "lifecycle.completed":
        print(f"\n任务完成")

    elif event_type == "lifecycle.failed":
        print(f"\n任务失败: {event_data.get('error')}")
```

### JavaScript 客户端

```javascript
async function startAndStream(hierarchyId, task) {
  // 1. 启动任务
  const startResp = await fetch(`${BASE_URL}/api/executor/v1/runs/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ hierarchy_id: hierarchyId, task })
  });
  const { data: { id: runId } } = await startResp.json();

  // 2. 监听事件流
  const streamResp = await fetch(`${BASE_URL}/api/executor/v1/runs/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id: runId })
  });

  const reader = streamResp.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const text = decoder.decode(value);
    const lines = text.split('\n');

    for (const line of lines) {
      if (line.startsWith('event:')) {
        const eventType = line.slice(7).trim();
      } else if (line.startsWith('data:')) {
        const data = JSON.parse(line.slice(5));
        handleEvent(eventType, data);
      }
    }
  }
}

function handleEvent(eventType, data) {
  const { source, data: eventData } = data;

  switch (eventType) {
    case 'llm.stream':
      const agentType = source?.agent_type || 'system';
      console.log(`[${agentType}]`, eventData.content);
      break;
    case 'lifecycle.completed':
      console.log('任务完成');
      break;
    case 'lifecycle.failed':
      console.error('任务失败:', eventData.error);
      break;
  }
}
```

---

## 最佳实践

### 1. 事件处理

- **按 sequence 排序**: 同一秒内可能有多个事件，使用 `sequence` 字段保证顺序
- **处理 source 为 null**: 系统级事件（如 lifecycle）的 source 为 null
- **流式内容拼接**: `llm.stream` 事件的 content 需要累积拼接显示

### 2. 错误处理

- 监听 `lifecycle.failed` 和 `system.error` 事件
- 实现重连机制，SSE 连接可能因网络问题断开
- 使用 `runs/events` 端点获取历史事件作为备份

### 3. UI 展示建议

```
┌─────────────────────────────────────────┐
│ 🎯 Global Supervisor                    │
│ ├── 正在分析任务...                      │
│ └── 📤 调度: 研究组                      │
│                                         │
│ 👔 研究组 Supervisor                     │
│ ├── 协调团队成员...                      │
│ └── 📤 调度: 分析师                      │
│                                         │
│ 👷 分析师 (研究组)                       │
│ └── 分析结果: ...                        │
│                                         │
│ ✅ 任务完成                              │
└─────────────────────────────────────────┘
```

### 4. Agent 类型图标建议

| agent_type | 建议图标 | 颜色 |
|------------|---------|------|
| `global_supervisor` | 🎯 | 紫色 |
| `team_supervisor` | 👔 | 蓝色 |
| `worker` | 👷 | 绿色 |

---

## 附录：完整事件流示例

```
event: lifecycle.started
data: {"run_id":"abc","timestamp":"2025-01-01T12:00:00.001Z","sequence":1,"source":null,"event":{"category":"lifecycle","action":"started"},"data":{"task":"解释AI"}}

event: llm.stream
data: {"run_id":"abc","timestamp":"2025-01-01T12:00:00.100Z","sequence":2,"source":{"agent_id":"gs-001","agent_type":"global_supervisor","agent_name":"Global Supervisor","team_name":null},"event":{"category":"llm","action":"stream"},"data":{"content":"分析任务..."}}

event: dispatch.team
data: {"run_id":"abc","timestamp":"2025-01-01T12:00:01.000Z","sequence":10,"source":{"agent_id":"gs-001","agent_type":"global_supervisor","agent_name":"Global Supervisor","team_name":null},"event":{"category":"dispatch","action":"team"},"data":{"name":"研究组","task":"解释AI"}}

event: llm.stream
data: {"run_id":"abc","timestamp":"2025-01-01T12:00:02.000Z","sequence":20,"source":{"agent_id":"ts-001","agent_type":"team_supervisor","agent_name":"研究组主管","team_name":"研究组"},"event":{"category":"llm","action":"stream"},"data":{"content":"协调研究..."}}

event: llm.stream
data: {"run_id":"abc","timestamp":"2025-01-01T12:00:05.000Z","sequence":50,"source":{"agent_id":"w-001","agent_type":"worker","agent_name":"分析师","team_name":"研究组"},"event":{"category":"llm","action":"stream"},"data":{"content":"AI是..."}}

event: lifecycle.completed
data: {"run_id":"abc","timestamp":"2025-01-01T12:00:10.000Z","sequence":100,"source":null,"event":{"category":"lifecycle","action":"completed"},"data":{"result":"AI是通过计算机模拟人类智能的技术"}}

event: close
data: {"message":"Stream closed"}
```
