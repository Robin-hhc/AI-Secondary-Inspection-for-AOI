"""
统计路由
"""
from flask import Blueprint, jsonify, current_app
from flask_jwt_extended import jwt_required
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

statistics_bp = Blueprint('statistics', __name__)


@statistics_bp.route('/overview', methods=['GET'])
@jwt_required()
def get_overview():
    """
    获取统计概览

    Response:
        {
            "code": 200,
            "message": "success",
            "data": {
                "total_samples": 1000,
                "total_annotations": 500,
                "normal_count": 400,
                "defect_count": 100
            }
        }
    """
    try:
        # 样本统计
        total_samples = current_app.sample_dao.count()
        sample_stats = current_app.sample_dao.count_by_label()

        # 标注统计
        annotation_stats = current_app.annotation_dao.count_by_label()

        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'total_samples': total_samples,
                'total_annotations': annotation_stats.get('total_count', 0),
                'normal_count': annotation_stats.get('normal_count', 0),
                'defect_count': annotation_stats.get('defect_count', 0),
                'uncertain_count': sample_stats.get('uncertain_count', 0)
            }
        })

    except Exception as e:
        logger.error(f"获取统计概览异常: {e}")
        return jsonify({
            'code': 500,
            'message': '服务器错误'
        }), 500


@statistics_bp.route('/performance', methods=['GET'])
@jwt_required()
def get_performance():
    """
    获取性能趋势

    Query Params:
        days: 统计天数 (默认7)
    """
    try:
        days = request.args.get('days', 7, type=int)
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)

        # 获取标注统计
        stats = current_app.annotation_dao.get_statistics()

        return jsonify({
            'code': 200,
            'message': 'success',
            'data': stats
        })

    except Exception as e:
        logger.error(f"获取性能趋势异常: {e}")
        return jsonify({
            'code': 500,
            'message': '服务器错误'
        }), 500


@statistics_bp.route('/labeling', methods=['GET'])
@jwt_required()
def get_labeling_stats():
    """
    获取标注统计

    Query Params:
        product_model_id: 产品型号ID (可选)
    """
    try:
        product_model_id = request.args.get('product_model_id', None, type=int)

        stats = current_app.annotation_dao.get_statistics(product_model_id)

        return jsonify({
            'code': 200,
            'message': 'success',
            'data': stats
        })

    except Exception as e:
        logger.error(f"获取标注统计异常: {e}")
        return jsonify({
            'code': 500,
            'message': '服务器错误'
        }), 500
