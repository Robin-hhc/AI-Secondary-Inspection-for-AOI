"""
数据库初始化脚本
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data_storage import DatabaseManager
from data_storage.dao import UserDAO, ProductModelDAO
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_database():
    """初始化数据库"""
    logger.info("开始初始化数据库...")

    # 创建数据库管理器
    db_manager = DatabaseManager("./data/aoi_system.db")

    # 初始化数据库表
    db_manager.init_db()
    logger.info("数据库表创建完成")

    # 创建默认管理员用户
    user_dao = UserDAO(db_manager)
    try:
        admin_id = user_dao.create("admin", "admin123", "admin")
        logger.info(f"管理员用户创建成功: ID={admin_id}")
    except Exception as e:
        logger.warning(f"管理员用户已存在或创建失败: {e}")

    # 创建默认产品型号
    product_dao = ProductModelDAO(db_manager)
    try:
        product_id = product_dao.create(
            code="product_a",
            name="产品A",
            description="默认产品型号",
            feature_lib_path="./data/feature_libs/product_a.bin",
            threshold=0.5
        )
        product_dao.set_active(product_id)
        logger.info(f"默认产品型号创建成功: ID={product_id}")
    except Exception as e:
        logger.warning(f"产品型号已存在或创建失败: {e}")

    logger.info("数据库初始化完成!")


if __name__ == "__main__":
    init_database()
