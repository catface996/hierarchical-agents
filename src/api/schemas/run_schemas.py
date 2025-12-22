"""
Run Schemas - 运行记录请求/响应模型
"""

from typing import Optional, List, Any
from pydantic import BaseModel, Field

from .common import PaginationRequest


class RunStartRequest(BaseModel):
    """启动运行请求"""
    hierarchy_id: str = Field(..., description="层级团队 ID")
    task: str = Field(..., min_length=1, description="任务描述")


class RunListRequest(PaginationRequest):
    """运行记录列表请求"""
    hierarchy_id: Optional[str] = Field(default=None, description="过滤层级团队")
    status: Optional[str] = Field(default=None, description="过滤状态")


class RunStreamRequest(BaseModel):
    """流式获取运行事件请求"""
    id: str = Field(..., description="运行 ID")


class RunCancelRequest(BaseModel):
    """取消运行请求"""
    id: str = Field(..., description="运行 ID")


class EventResponse(BaseModel):
    """事件响应"""
    id: str
    event_type: str
    timestamp: Optional[str]
    data: Optional[Any]
    team_name: Optional[str]
    worker_name: Optional[str]

    class Config:
        from_attributes = True


class RunResponse(BaseModel):
    """运行记录响应"""
    id: str
    hierarchy_id: str
    task: str
    status: str
    result: Optional[str]
    error: Optional[str]
    statistics: Optional[Any]
    started_at: Optional[str]
    completed_at: Optional[str]
    created_at: Optional[str]

    class Config:
        from_attributes = True


class RunDetailResponse(RunResponse):
    """运行详情响应（含事件）"""
    events: List[EventResponse] = []
    topology_snapshot: Optional[Any] = None


class RunStartResponse(BaseModel):
    """启动运行响应"""
    id: str
    hierarchy_id: str
    task: str
    status: str
    stream_url: str
    created_at: Optional[str]
