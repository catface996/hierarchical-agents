"""
Hierarchies Routes - 层级团队管理路由
"""

import math
from flask import Blueprint, request, jsonify
from flasgger import swag_from
from pydantic import ValidationError

from ..schemas.hierarchy_schemas import (
    HierarchyCreateRequest, HierarchyUpdateRequest, HierarchyListRequest
)
from ..schemas.common import IdRequest
from ...db.database import get_db_session
from ...db.repositories import HierarchyRepository

hierarchies_bp = Blueprint('hierarchies', __name__)


def get_repo():
    """获取层级团队仓库"""
    return HierarchyRepository(get_db_session())


@hierarchies_bp.route('/list', methods=['POST'])
@swag_from({
    'tags': ['Hierarchies'],
    'summary': '获取层级团队列表',
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
        200: {'description': '层级团队列表'}
    }
})
def list_hierarchies():
    """获取层级团队列表"""
    try:
        data = request.get_json() or {}
        req = HierarchyListRequest(**data)

        repo = get_repo()
        hierarchies, total = repo.list(
            page=req.page,
            size=req.size,
            is_active=req.is_active
        )

        # 返回简化的列表项（不含完整配置）
        items = []
        for h in hierarchies:
            item = h.to_dict(include_teams=False)
            item['team_count'] = len(h.teams)
            items.append(item)

        return jsonify({
            'success': True,
            'data': {
                'items': items,
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


@hierarchies_bp.route('/get', methods=['POST'])
@swag_from({
    'tags': ['Hierarchies'],
    'summary': '获取层级团队详情',
    'description': '获取完整的层级团队配置，包含所有团队和 Worker',
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
        200: {'description': '层级团队详情'},
        404: {'description': '层级团队不存在'}
    }
})
def get_hierarchy():
    """获取层级团队详情"""
    try:
        data = request.get_json() or {}
        req = IdRequest(**data)

        repo = get_repo()
        hierarchy = repo.get_by_id(req.id)

        if not hierarchy:
            return jsonify({'success': False, 'error': '层级团队不存在'}), 404

        return jsonify({
            'success': True,
            'data': hierarchy.to_dict()
        })
    except ValidationError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@hierarchies_bp.route('/create', methods=['POST'])
@swag_from({
    'tags': ['Hierarchies'],
    'summary': '创建层级团队',
    'parameters': [{
        'name': 'body',
        'in': 'body',
        'required': True,
        'schema': {
            'type': 'object',
            'required': ['name', 'global_prompt', 'teams'],
            'properties': {
                'name': {'type': 'string'},
                'description': {'type': 'string'},
                'global_prompt': {'type': 'string'},
                'execution_mode': {'type': 'string', 'enum': ['sequential', 'parallel']},
                'enable_context_sharing': {'type': 'boolean'},
                'global_model_id': {'type': 'string'},
                'teams': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'required': ['name', 'supervisor_prompt', 'workers'],
                        'properties': {
                            'name': {'type': 'string'},
                            'supervisor_prompt': {'type': 'string'},
                            'prevent_duplicate': {'type': 'boolean'},
                            'share_context': {'type': 'boolean'},
                            'model_id': {'type': 'string'},
                            'workers': {
                                'type': 'array',
                                'items': {
                                    'type': 'object',
                                    'required': ['name', 'role', 'system_prompt'],
                                    'properties': {
                                        'name': {'type': 'string'},
                                        'role': {'type': 'string'},
                                        'system_prompt': {'type': 'string'},
                                        'tools': {'type': 'array', 'items': {'type': 'string'}},
                                        'temperature': {'type': 'number'},
                                        'max_tokens': {'type': 'integer'},
                                        'model_id': {'type': 'string'}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }],
    'responses': {
        200: {'description': '创建成功'},
        400: {'description': '请求无效'}
    }
})
def create_hierarchy():
    """创建层级团队"""
    try:
        data = request.get_json() or {}
        req = HierarchyCreateRequest(**data)

        repo = get_repo()

        # 检查名称是否重复
        if repo.get_by_name(req.name):
            return jsonify({'success': False, 'error': f'层级团队名称 "{req.name}" 已存在'}), 400

        # 转换为字典并创建
        create_data = req.model_dump()
        # 转换 teams 中的 workers
        for team in create_data['teams']:
            team['workers'] = [w for w in team['workers']]

        hierarchy = repo.create(create_data)

        return jsonify({
            'success': True,
            'message': '层级团队创建成功',
            'data': hierarchy.to_dict()
        })
    except ValidationError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@hierarchies_bp.route('/update', methods=['POST'])
@swag_from({
    'tags': ['Hierarchies'],
    'summary': '更新层级团队',
    'description': '更新层级团队配置。如果提供 teams 字段，将完整替换团队配置',
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
                'description': {'type': 'string'},
                'global_prompt': {'type': 'string'},
                'execution_mode': {'type': 'string'},
                'enable_context_sharing': {'type': 'boolean'},
                'global_model_id': {'type': 'string'},
                'is_active': {'type': 'boolean'},
                'teams': {'type': 'array', 'description': '提供时将完整替换'}
            }
        }
    }],
    'responses': {
        200: {'description': '更新成功'},
        404: {'description': '层级团队不存在'}
    }
})
def update_hierarchy():
    """更新层级团队"""
    try:
        data = request.get_json() or {}
        req = HierarchyUpdateRequest(**data)

        repo = get_repo()

        # 过滤掉 None 值
        update_data = {k: v for k, v in req.model_dump().items() if v is not None and k != 'id'}

        # 检查名称是否与其他层级重复
        if 'name' in update_data:
            existing = repo.get_by_name(update_data['name'])
            if existing and existing.id != req.id:
                return jsonify({'success': False, 'error': f'层级团队名称 "{update_data["name"]}" 已存在'}), 400

        # 转换 teams 数据
        if 'teams' in update_data and update_data['teams'] is not None:
            for team in update_data['teams']:
                if isinstance(team, dict) and 'workers' in team:
                    team['workers'] = [w if isinstance(w, dict) else w.model_dump() for w in team['workers']]

        hierarchy = repo.update(req.id, update_data)

        if not hierarchy:
            return jsonify({'success': False, 'error': '层级团队不存在'}), 404

        return jsonify({
            'success': True,
            'message': '层级团队更新成功',
            'data': hierarchy.to_dict()
        })
    except ValidationError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@hierarchies_bp.route('/delete', methods=['POST'])
@swag_from({
    'tags': ['Hierarchies'],
    'summary': '删除层级团队',
    'description': '删除层级团队及其所有团队和 Worker 配置',
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
        404: {'description': '层级团队不存在'}
    }
})
def delete_hierarchy():
    """删除层级团队"""
    try:
        data = request.get_json() or {}
        req = IdRequest(**data)

        repo = get_repo()
        success = repo.delete(req.id)

        if not success:
            return jsonify({'success': False, 'error': '层级团队不存在'}), 404

        return jsonify({
            'success': True,
            'message': '层级团队删除成功'
        })
    except ValidationError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
