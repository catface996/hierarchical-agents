# Implementation Plan: Redis Stream 事件存储

**Branch**: `002-redis-stream-events` | **Date**: 2025-01-01 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-redis-stream-events/spec.md`

## Summary

将执行事件从 MySQL 存储迁移到 Redis Stream，以提升实时事件处理性能。Redis Stream 原生支持消费者断线重连（通过消息 ID 恢复）和多客户端订阅。本地开发环境使用 Docker 部署 Redis。

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: Flask 3.0+, redis-py 5.0+, SQLAlchemy 2.0+ (保留用于 ExecutionRun)
**Storage**: Redis Stream (事件存储) + MySQL (运行记录存储)
**Testing**: pytest
**Target Platform**: Linux server / macOS (本地开发)
**Project Type**: single
**Performance Goals**:
- 事件写入延迟 < 10ms
- 事件推送延迟 < 100ms (P95)
- 单运行支持 10000+ 事件
**Constraints**:
- 事件保留期 24 小时
- 单事件大小 < 1MB
- 向后兼容现有 SSE 接口
**Scale/Scope**: 100+ 并发订阅客户端

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| Database Type: MySQL | ✅ PASS | 运行记录继续使用 MySQL，仅事件数据迁移到 Redis |
| V2 Event Format | ✅ PASS | 保持现有事件结构不变 |
| Local Development | ✅ PASS | Redis 使用 Docker 部署，服务本身直接运行 |

## Project Structure

### Documentation (this feature)

```text
specs/002-redis-stream-events/
├── plan.md              # This file
├── research.md          # Phase 0: Redis Stream 技术研究
├── data-model.md        # Phase 1: 数据模型设计
├── quickstart.md        # Phase 1: 快速开始指南
├── contracts/           # Phase 1: 接口契约
│   └── event-stream-api.md
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/
├── core/
│   └── api_models.py        # 现有事件类型定义
├── db/
│   ├── models.py            # 保留 ExecutionRun，移除 ExecutionEvent
│   └── repositories/
│       └── run_repo.py      # 移除事件相关方法，保留运行记录方法
├── streaming/
│   ├── sse_manager.py       # 改为从 Redis Stream 读取事件
│   ├── event_store.py       # 新增: Redis Stream 事件存储
│   └── llm_callback.py      # 改为调用 event_store
└── runner/
    └── run_manager.py       # 改为使用 event_store 写入事件

tests/
├── integration/
│   └── test_event_stream.py # 新增: 事件流集成测试
└── unit/
    └── test_event_store.py  # 新增: 事件存储单元测试
```

**Structure Decision**: 采用 Single project 结构。新增 `src/streaming/event_store.py` 封装 Redis Stream 操作，修改现有组件使用新的事件存储。

## Complexity Tracking

> **No constitution violations detected.**

---

## Phase 0: Research

### Redis Stream 核心概念

Redis Stream 是 Redis 5.0 引入的数据结构，专为消息队列和事件日志设计：

1. **消息 ID**: 格式为 `<timestamp>-<sequence>`，天然有序且唯一
2. **XADD**: 追加消息到 Stream，支持自动生成 ID 或指定 ID
3. **XRANGE**: 范围读取，支持从指定 ID 开始
4. **XREAD BLOCK**: 阻塞读取新消息，用于实时订阅
5. **MAXLEN**: 自动修剪，保持 Stream 长度

### 关键操作

```python
# 写入事件
XADD run:{run_id}:events MAXLEN ~ 10000 * field1 value1 field2 value2

# 读取历史事件
XRANGE run:{run_id}:events - +

# 从指定位置读取（断线重连）
XRANGE run:{run_id}:events {last_id} +

# 实时订阅新事件
XREAD BLOCK 0 STREAMS run:{run_id}:events $

# 设置过期时间（运行结束后）
EXPIRE run:{run_id}:events 86400
```

### 与现有实现的对比

| 特性 | MySQL (当前) | Redis Stream (目标) |
|------|-------------|---------------------|
| 写入延迟 | 10-50ms | < 5ms |
| 实时订阅 | 轮询 | 原生阻塞读取 |
| 断线重连 | 需自实现 | 消息 ID 天然支持 |
| 多客户端 | 需自实现 | 原生支持 |
| 数据持久化 | 强一致 | AOF/RDB 可配置 |
| 自动过期 | 需定时任务 | TTL 原生支持 |

### 风险评估

1. **Redis 不可用**: 需要错误处理和降级策略
2. **数据丢失**: 配置适当的 AOF 策略
3. **内存限制**: 使用 MAXLEN 控制 Stream 大小

---

## Phase 1: Design Artifacts

### 数据模型 (data-model.md)

见 `specs/002-redis-stream-events/data-model.md`

### 接口契约 (contracts/)

见 `specs/002-redis-stream-events/contracts/event-stream-api.md`

### 快速开始 (quickstart.md)

见 `specs/002-redis-stream-events/quickstart.md`
