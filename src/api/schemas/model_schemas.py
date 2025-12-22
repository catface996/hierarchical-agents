"""
Model Schemas - AI 模型请求/响应模型
"""

from typing import Optional, List
from pydantic import BaseModel, Field

from .common import PaginationRequest


class ModelCreateRequest(BaseModel):
    """创建模型请求"""
    name: str = Field(..., min_length=1, max_length=100, description="模型名称")
    model_id: str = Field(..., min_length=1, max_length=200, description="AWS Bedrock 模型 ID")
    region: str = Field(default="us-east-1", description="AWS 区域")
    temperature: float = Field(default=0.7, ge=0, le=2, description="温度参数")
    max_tokens: int = Field(default=2048, ge=1, le=100000, description="最大 token 数")
    top_p: float = Field(default=0.9, ge=0, le=1, description="Top-P 参数")
    description: Optional[str] = Field(default=None, description="模型描述")
    is_active: bool = Field(default=True, description="是否激活")


class ModelUpdateRequest(BaseModel):
    """更新模型请求"""
    id: str = Field(..., description="模型 ID")
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    model_id: Optional[str] = Field(default=None, min_length=1, max_length=200)
    region: Optional[str] = None
    temperature: Optional[float] = Field(default=None, ge=0, le=2)
    max_tokens: Optional[int] = Field(default=None, ge=1, le=100000)
    top_p: Optional[float] = Field(default=None, ge=0, le=1)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ModelListRequest(PaginationRequest):
    """模型列表请求"""
    is_active: Optional[bool] = Field(default=None, description="过滤激活状态")


class ModelResponse(BaseModel):
    """模型响应"""
    id: str
    name: str
    model_id: str
    region: str
    temperature: float
    max_tokens: int
    top_p: float
    description: Optional[str]
    is_active: bool
    created_at: Optional[str]
    updated_at: Optional[str]

    class Config:
        from_attributes = True
