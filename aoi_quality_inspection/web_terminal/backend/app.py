"""
Flask Web应用主程序
"""
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import logging
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from data_storage import DatabaseManager
from data_storage.dao import UserDAO, ProductModelDAO, SampleDAO, AnnotationDAO

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app(config: dict = None) -> Flask:
    """
    应用工厂函数

    Args:
        config: 配置字典

    Returns:
        Flask: Flask应用实例
    """
    app = Flask(__name__)

    # 加载配置
    config = config or {}
    app.config['SECRET_KEY'] = config.get('secret_key', 'dev-secret-key')
    app.config['JWT_SECRET_KEY'] = config.get('jwt_secret_key', 'jwt-secret-key')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = config.get('jwt_expires', 3600)

    # CORS配置
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # JWT配置
    jwt = JWTManager(app)

    # 初始化数据库
    db_path = config.get('db_path', './data/aoi_system.db')
    app.db_manager = DatabaseManager(db_path)
    app.user_dao = UserDAO(app.db_manager)
    app.product_dao = ProductModelDAO(app.db_manager)
    app.sample_dao = SampleDAO(app.db_manager)
    app.annotation_dao = AnnotationDAO(app.db_manager)

    # 注册蓝图
    from .routes.auth import auth_bp
    from .routes.annotation import annotation_bp
    from .routes.model import model_bp
    from .routes.statistics import statistics_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(annotation_bp, url_prefix='/api/annotation')
    app.register_blueprint(model_bp, url_prefix='/api/model')
    app.register_blueprint(statistics_bp, url_prefix='/api/statistics')

    # 错误处理
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'code': 404, 'message': '资源不存在'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'code': 500, 'message': '服务器内部错误'}), 500

    # 健康检查
    @app.route('/health')
    def health():
        return jsonify({'status': 'ok'})

    logger.info("Flask应用初始化完成")

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
