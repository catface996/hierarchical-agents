"""
SSE Manager - Server-Sent Events 管理器
"""

import json
import threading
from queue import Queue, Empty
from datetime import datetime
from typing import Generator, Optional, Dict
from flask import Response


class SSEManager:
    """
    SSE 管理器 - 管理服务器发送事件
    """

    def __init__(self, run_id: str):
        self.run_id = run_id
        self.event_queue: Queue = Queue()
        self.is_active = True
        self._lock = threading.Lock()

    def emit(self, event_type: str, data: dict):
        """
        发射事件到队列

        Args:
            event_type: 事件类型
            data: 事件数据
        """
        if not self.is_active:
            return

        event = {
            'event': event_type,
            'data': {
                **data,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'run_id': self.run_id
            }
        }
        self.event_queue.put(event)

    def close(self):
        """关闭 SSE 连接"""
        with self._lock:
            self.is_active = False
            # 发送结束事件
            self.event_queue.put({'event': 'close', 'data': {}})

    def generate_events(self, timeout: float = 30.0) -> Generator[str, None, None]:
        """
        生成 SSE 事件流

        Args:
            timeout: 队列等待超时时间

        Yields:
            格式化的 SSE 事件字符串
        """
        heartbeat_interval = 15  # 心跳间隔秒数
        last_heartbeat = datetime.utcnow()

        while self.is_active or not self.event_queue.empty():
            try:
                event = self.event_queue.get(timeout=1.0)

                if event['event'] == 'close':
                    # 发送关闭事件
                    yield f"event: close\ndata: {json.dumps({'message': 'Stream closed'}, ensure_ascii=False)}\n\n"
                    break

                # 格式化 SSE 事件
                yield f"event: {event['event']}\n"
                yield f"data: {json.dumps(event['data'], ensure_ascii=False)}\n\n"

            except Empty:
                # 发送心跳保持连接
                now = datetime.utcnow()
                if (now - last_heartbeat).seconds >= heartbeat_interval:
                    yield f": heartbeat {now.isoformat()}Z\n\n"
                    last_heartbeat = now

    def create_response(self) -> Response:
        """创建 Flask SSE 响应"""
        return Response(
            self.generate_events(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no',  # 禁用 nginx 缓冲
                'Access-Control-Allow-Origin': '*',
            }
        )


class SSERegistry:
    """
    SSE 管理器注册表 - 单例模式
    """

    _instance: Optional['SSERegistry'] = None
    _managers: Dict[str, SSEManager] = {}
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._managers = {}
        return cls._instance

    @classmethod
    def get_instance(cls) -> 'SSERegistry':
        """获取单例实例"""
        return cls()

    def register(self, run_id: str) -> SSEManager:
        """注册新的 SSE 管理器"""
        with self._lock:
            if run_id in self._managers:
                # 关闭旧的管理器
                self._managers[run_id].close()

            manager = SSEManager(run_id)
            self._managers[run_id] = manager
            return manager

    def get(self, run_id: str) -> Optional[SSEManager]:
        """获取 SSE 管理器"""
        return self._managers.get(run_id)

    def remove(self, run_id: str):
        """移除 SSE 管理器"""
        with self._lock:
            if run_id in self._managers:
                self._managers[run_id].close()
                del self._managers[run_id]

    def get_all_run_ids(self) -> list:
        """获取所有活跃的运行 ID"""
        return list(self._managers.keys())
