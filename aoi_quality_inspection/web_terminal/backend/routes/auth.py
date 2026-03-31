"""
认证路由
"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    用户登录

    Request:
        {
            "username": "admin",
            "password": "password"
        }

    Response:
        {
            "code": 200,
            "message": "success",
            "data": {
                "access_token": "...",
                "user": {...}
            }
        }
    """
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({
                'code': 400,
                'message': '用户名和密码不能为空'
            }), 400

        # 认证用户
        user = current_app.user_dao.authenticate(username, password)

        if not user:
            return jsonify({
                'code': 401,
                'message': '用户名或密码错误'
            }), 401

        # 生成访问令牌
        access_token = create_access_token(identity=user['id'])

        logger.info(f"用户登录成功: {username}")

        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'access_token': access_token,
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'role': user['role']
                }
            }
        })

    except Exception as e:
        logger.error(f"登录异常: {e}")
        return jsonify({
            'code': 500,
            'message': '服务器错误'
        }), 500


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    用户登出
    """
    try:
        user_id = get_jwt_identity()
        logger.info(f"用户登出: {user_id}")

        return jsonify({
            'code': 200,
            'message': 'success'
        })

    except Exception as e:
        logger.error(f"登出异常: {e}")
        return jsonify({
            'code': 500,
            'message': '服务器错误'
        }), 500


@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """
    获取用户信息
    """
    try:
        user_id = get_jwt_identity()
        user = current_app.user_dao.get_by_id(user_id)

        if not user:
            return jsonify({
                'code': 404,
                'message': '用户不存在'
            }), 404

        return jsonify({
            'code': 200,
            'message': 'success',
            'data': user
        })

    except Exception as e:
        logger.error(f"获取用户信息异常: {e}")
        return jsonify({
            'code': 500,
            'message': '服务器错误'
        }), 500
