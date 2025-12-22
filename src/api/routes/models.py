"""
Models Routes - AI 模型管理路由
"""

import math
from flask import Blueprint, request, jsonify
from flasgger import swag_from
from pydantic import ValidationError

from ..schemas.model_schemas import (
    ModelCreateRequest, ModelUpdateRequest, ModelListRequest
)
from ..schemas.common import IdRequest
from ...db.database import get_db_session
from ...db.repositories import ModelRepository

models_bp = Blueprint('models', __name__)


def get_repo():
    """获取模型仓库"""
    return ModelRepository(get_db_session())


@models_bp.route('/list', methods=['POST'])
@swag_from({
    'tags': ['Models'],
    'summary': '获取模型列表',
    'description': '分页获取 AI 模型配置列表',
    'parameters': [{
        'name': 'body',
        'in': 'body',
        'required': True,
        'schema': {
            'type': 'object',
            'properties': {
                'page': {'type': 'integer', 'default': 1},
                'size': {'type': 'integer', 'default': 20},
                'is_active': {'type': 'boolean'}
            }
        }
    }],
    'responses': {
        200: {'description': '模型列表'}
    }
})
def list_models():
    """获取模型列表"""
    try:
        data = request.get_json() or {}
        req = ModelListRequest(**data)

        repo = get_repo()
        models, total = repo.list(
            page=req.page,
            size=req.size,
            is_active=req.is_active
        )

        return jsonify({
            'success': True,
            'data': {
                'items': [m.to_dict() for m in models],
                'total': total,
                'page': req.page,
                'size': req.size,
                'pages': math.ceil(total / req.size) if req.size > 0 else 0
            }
        })
    except ValidationError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@models_bp.route('/get', methods=['POST'])
@swag_from({
    'tags': ['Models'],
    'summary': '获取模型详情',
    'parameters': [{
        'name': 'body',
        'in': 'body',
        'required': True,
        'schema': {
            'type': 'object',
            'required': ['id'],
            'properties': {
                'id': {'type': 'string'}
            }
        }
    }],
    'responses': {
        200: {'description': '模型详情'},
        404: {'description': '模型不存在'}
    }
})
def get_model():
    """获取模型详情"""
    try:
        data = request.get_json() or {}
        req = IdRequest(**data)

        repo = get_repo()
        model = repo.get_by_id(req.id)

        if not model:
            return jsonify({'success': False, 'error': '模型不存在'}), 404

        return jsonify({
            'success': True,
            'data': model.to_dict()
        })
    except ValidationError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@models_bp.route('/create', methods=['POST'])
@swag_from({
    'tags': ['Models'],
    'summary': '创建模型',
    'parameters': [{
        'name': 'body',
        'in': 'body',
        'required': True,
        'schema': {
            'type': 'object',
            'required': ['name', 'model_id'],
            'properties': {
                'name': {'type': 'string'},
                'model_id': {'type': 'string'},
                'region': {'type': 'string', 'default': 'us-east-1'},
                'temperature': {'type': 'number', 'default': 0.7},
                'max_tokens': {'type': 'integer', 'default': 2048},
                'top_p': {'type': 'number', 'default': 0.9},
                'description': {'type': 'string'},
                'is_active': {'type': 'boolean', 'default': True}
            }
        }
    }],
    'responses': {
        200: {'description': '创建成功'},
        400: {'description': '请求无效'}
    }
})
def create_model():
    """创建模型"""
    try:
        data = request.get_json() or {}
        req = ModelCreateRequest(**data)

        repo = get_repo()

        # 检查名称是否重复
        if repo.get_by_name(req.name):
            return jsonify({'success': False, 'error': f'模型名称 "{req.name}" 已存在'}), 400

        model = repo.create(req.model_dump())

        return jsonify({
            'success': True,
            'message': '模型创建成功',
            'data': model.to_dict()
        })
    except ValidationError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@models_bp.route('/update', methods=['POST'])
@swag_from({
    'tags': ['Models'],
    'summary': '更新模型',
    'parameters': [{
        'name': 'body',
        'in': 'body',
        'required': True,
        'schema': {
            'type': 'object',
            'required': ['id'],
            'properties': {
                'id': {'type': 'string'},
                'name': {'type': 'string'},
                'model_id': {'type': 'string'},
                'region': {'type': 'string'},
                'temperature': {'type': 'number'},
                'max_tokens': {'type': 'integer'},
                'top_p': {'type': 'number'},
                'description': {'type': 'string'},
                'is_active': {'type': 'boolean'}
            }
        }
    }],
    'responses': {
        200: {'description': '更新成功'},
        404: {'description': '模型不存在'}
    }
})
def update_model():
    """更新模型"""
    try:
        data = request.get_json() or {}
        req = ModelUpdateRequest(**data)

        repo = get_repo()

        # 过滤掉 None 值
        update_data = {k: v for k, v in req.model_dump().items() if v is not None and k != 'id'}

        # 检查名称是否与其他模型重复
        if 'name' in update_data:
            existing = repo.get_by_name(update_data['name'])
            if existing and existing.id != req.id:
                return jsonify({'success': False, 'error': f'模型名称 "{update_data["name"]}" 已存在'}), 400

        model = repo.update(req.id, update_data)

        if not model:
            return jsonify({'success': False, 'error': '模型不存在'}), 404

        return jsonify({
            'success': True,
            'message': '模型更新成功',
            'data': model.to_dict()
        })
    except ValidationError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@models_bp.route('/delete', methods=['POST'])
@swag_from({
    'tags': ['Models'],
    'summary': '删除模型',
    'parameters': [{
        'name': 'body',
        'in': 'body',
        'required': True,
        'schema': {
            'type': 'object',
            'required': ['id'],
            'properties': {
                'id': {'type': 'string'}
            }
        }
    }],
    'responses': {
        200: {'description': '删除成功'},
        404: {'description': '模型不存在'}
    }
})
def delete_model():
    """删除模型"""
    try:
        data = request.get_json() or {}
        req = IdRequest(**data)

        repo = get_repo()
        success = repo.delete(req.id)

        if not success:
            return jsonify({'success': False, 'error': '模型不存在'}), 404

        return jsonify({
            'success': True,
            'message': '模型删除成功'
        })
    except ValidationError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
