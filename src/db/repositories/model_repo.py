"""
Model Repository - AI 模型数据访问层
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from ..models import AIModel


class ModelRepository:
    """AI 模型仓库"""

    def __init__(self, session: Session):
        self.session = session

    def create(self, data: dict) -> AIModel:
        """创建模型"""
        model = AIModel(**data)
        self.session.add(model)
        self.session.commit()
        self.session.refresh(model)
        return model

    def get_by_id(self, model_id: str) -> Optional[AIModel]:
        """根据 ID 获取模型"""
        return self.session.query(AIModel).filter(AIModel.id == model_id).first()

    def get_by_name(self, name: str) -> Optional[AIModel]:
        """根据名称获取模型"""
        return self.session.query(AIModel).filter(AIModel.name == name).first()

    def list(
        self,
        page: int = 1,
        size: int = 20,
        is_active: Optional[bool] = None
    ) -> tuple[List[AIModel], int]:
        """
        获取模型列表

        Returns:
            (模型列表, 总数)
        """
        query = self.session.query(AIModel)

        if is_active is not None:
            query = query.filter(AIModel.is_active == is_active)

        total = query.count()
        models = query.order_by(AIModel.created_at.desc()) \
                     .offset((page - 1) * size) \
                     .limit(size) \
                     .all()

        return models, total

    def update(self, model_id: str, data: dict) -> Optional[AIModel]:
        """更新模型"""
        model = self.get_by_id(model_id)
        if not model:
            return None

        for key, value in data.items():
            if hasattr(model, key) and key not in ('id', 'created_at'):
                setattr(model, key, value)

        self.session.commit()
        self.session.refresh(model)
        return model

    def delete(self, model_id: str) -> bool:
        """删除模型"""
        model = self.get_by_id(model_id)
        if not model:
            return False

        self.session.delete(model)
        self.session.commit()
        return True

    def exists(self, model_id: str) -> bool:
        """检查模型是否存在"""
        return self.session.query(AIModel).filter(AIModel.id == model_id).count() > 0
