"""
标注路由
"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

annotation_bp = Blueprint('annotation', __name__)


@annotation_bp.route('/pending', methods=['GET'])
@jwt_required()
def get_pending():
    """
    获取待标注样本

    Query Params:
        limit: 返回数量 (默认100)
        offset: 偏移量 (默认0)

    Response:
        {
            "code": 200,
            "message": "success",
            "data": {
                "samples": [...],
                "total": 10
            }
        }
    """
    try:
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)

        samples = current_app.sample_dao.get_pending_samples(limit=limit, offset=offset)

        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'samples': samples,
                'total': len(samples)
            }
        })

    except Exception as e:
        logger.error(f"获取待标注样本异常: {e}")
        return jsonify({
            'code': 500,
            'message': '服务器错误'
        }), 500


@annotation_bp.route('/submit', methods=['POST'])
@jwt_required()
def submit():
    """
    提交标注结果

    Request:
        {
            "sample_id": 1,
            "label": 0,
            "defect_type": "划痕",
            "notes": "备注"
        }

    Response:
        {
            "code": 200,
            "message": "success"
        }
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        sample_id = data.get('sample_id')
        label = data.get('label')
        defect_type = data.get('defect_type')
        notes = data.get('notes')

        if sample_id is None or label is None:
            return jsonify({
                'code': 400,
                'message': '样本ID和标签不能为空'
            }), 400

        # 获取用户信息
        user = current_app.user_dao.get_by_id(user_id)
        operator = user['username'] if user else 'unknown'

        # 创建标注记录
        annotation_id = current_app.annotation_dao.create(
            sample_id=sample_id,
            label=label,
            operator=operator,
            defect_type=defect_type,
            notes=notes
        )

        logger.info(f"标注提交成功: 样本{sample_id}, 标签{label}, 操作员{operator}")

        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {'annotation_id': annotation_id}
        })

    except Exception as e:
        logger.error(f"提交标注异常: {e}")
        return jsonify({
            'code': 500,
            'message': '服务器错误'
        }), 500


@annotation_bp.route('/history', methods=['GET'])
@jwt_required()
def get_history():
    """
    获取标注历史

    Query Params:
        limit: 返回数量 (默认100)
        product_model_id: 产品型号ID (可选)

    Response:
        {
            "code": 200,
            "message": "success",
            "data": {
                "annotations": [...]
            }
        }
    """
    try:
        limit = request.args.get('limit', 100, type=int)
        product_model_id = request.args.get('product_model_id', None, type=int)

        annotations = current_app.annotation_dao.get_by_operator(
            operator=current_app.user_dao.get_by_id(get_jwt_identity())['username'],
            limit=limit
        )

        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'annotations': annotations
            }
        })

    except Exception as e:
        logger.error(f"获取标注历史异常: {e}")
        return jsonify({
            'code': 500,
            'message': '服务器错误'
        }), 500


@annotation_bp.route('/<int:annotation_id>', methods=['GET'])
@jwt_required()
def get_detail(annotation_id):
    """
    获取标注详情
    """
    try:
        annotation = current_app.annotation_dao.get_by_id(annotation_id)

        if not annotation:
            return jsonify({
                'code': 404,
                'message': '标注不存在'
            }), 404

        return jsonify({
            'code': 200,
            'message': 'success',
            'data': annotation
        })

    except Exception as e:
        logger.error(f"获取标注详情异常: {e}")
        return jsonify({
            'code': 500,
            'message': '服务器错误'
        }), 500
