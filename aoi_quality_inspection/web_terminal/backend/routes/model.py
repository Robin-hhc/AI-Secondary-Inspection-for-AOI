"""
模型管理路由
"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

logger = logging.getLogger(__name__)

model_bp = Blueprint('model', __name__)


@model_bp.route('/list', methods=['GET'])
@jwt_required()
def list_models():
    """
    获取产品型号列表

    Response:
        {
            "code": 200,
            "message": "success",
            "data": {
                "models": [...]
            }
        }
    """
    try:
        models = current_app.product_dao.list_all()

        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'models': models
            }
        })

    except Exception as e:
        logger.error(f"获取产品型号列表异常: {e}")
        return jsonify({
            'code': 500,
            'message': '服务器错误'
        }), 500


@model_bp.route('/switch', methods=['POST'])
@jwt_required()
def switch_model():
    """
    切换产品型号

    Request:
        {
            "model_id": 1
        }

    Response:
        {
            "code": 200,
            "message": "success"
        }
    """
    try:
        data = request.get_json()
        model_id = data.get('model_id')

        if not model_id:
            return jsonify({
                'code': 400,
                'message': '型号ID不能为空'
            }), 400

        # 设置活跃型号
        current_app.product_dao.set_active(model_id)

        logger.info(f"产品型号切换: {model_id}")

        return jsonify({
            'code': 200,
            'message': 'success'
        })

    except Exception as e:
        logger.error(f"切换产品型号异常: {e}")
        return jsonify({
            'code': 500,
            'message': '服务器错误'
        }), 500


@model_bp.route('/add', methods=['POST'])
@jwt_required()
def add_model():
    """
    添加产品型号

    Request:
        {
            "code": "product_a",
            "name": "产品A",
            "description": "描述",
            "threshold": 0.5
        }
    """
    try:
        data = request.get_json()

        code = data.get('code')
        name = data.get('name')
        description = data.get('description')
        threshold = data.get('threshold', 0.5)

        if not code or not name:
            return jsonify({
                'code': 400,
                'message': '编码和名称不能为空'
            }), 400

        model_id = current_app.product_dao.create(
            code=code,
            name=name,
            description=description,
            threshold=threshold
        )

        logger.info(f"产品型号添加: {code}")

        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {'model_id': model_id}
        })

    except Exception as e:
        logger.error(f"添加产品型号异常: {e}")
        return jsonify({
            'code': 500,
            'message': '服务器错误'
        }), 500


@model_bp.route('/active', methods=['GET'])
@jwt_required()
def get_active():
    """
    获取当前活跃的产品型号
    """
    try:
        model = current_app.product_dao.get_active()

        return jsonify({
            'code': 200,
            'message': 'success',
            'data': model
        })

    except Exception as e:
        logger.error(f"获取活跃型号异常: {e}")
        return jsonify({
            'code': 500,
            'message': '服务器错误'
        }), 500
