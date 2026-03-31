"""
数据存储模块单元测试
"""
import pytest
import tempfile
import os
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data_storage import DatabaseManager
from data_storage.dao import UserDAO, ProductModelDAO, SampleDAO


@pytest.fixture
def db_manager():
    """创建临时数据库"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name

    db = DatabaseManager(db_path)
    db.init_db()

    yield db

    # 清理
    os.unlink(db_path)


def test_database_init(db_manager):
    """测试数据库初始化"""
    assert db_manager.table_exists('product_models')
    assert db_manager.table_exists('samples')
    assert db_manager.table_exists('annotations')
    assert db_manager.table_exists('users')


def test_user_dao(db_manager):
    """测试用户DAO"""
    user_dao = UserDAO(db_manager)

    # 创建用户
    user_id = user_dao.create('test_user', 'password123', 'operator')
    assert user_id > 0

    # 查询用户
    user = user_dao.get_by_id(user_id)
    assert user is not None
    assert user['username'] == 'test_user'

    # 认证
    auth_user = user_dao.authenticate('test_user', 'password123')
    assert auth_user is not None

    # 错误密码
    auth_user = user_dao.authenticate('test_user', 'wrong_password')
    assert auth_user is None


def test_product_model_dao(db_manager):
    """测试产品型号DAO"""
    product_dao = ProductModelDAO(db_manager)

    # 创建产品型号
    model_id = product_dao.create(
        code='product_a',
        name='产品A',
        threshold=0.5
    )
    assert model_id > 0

    # 查询产品型号
    model = product_dao.get_by_id(model_id)
    assert model is not None
    assert model['code'] == 'product_a'

    # 设置活跃
    product_dao.set_active(model_id)
    active_model = product_dao.get_active()
    assert active_model is not None
    assert active_model['id'] == model_id


def test_sample_dao(db_manager):
    """测试样本DAO"""
    # 先创建产品型号
    product_dao = ProductModelDAO(db_manager)
    product_id = product_dao.create('product_a', '产品A')

    sample_dao = SampleDAO(db_manager)

    # 创建样本
    from datetime import datetime
    sample_id = sample_dao.create(
        product_model_id=product_id,
        image_path='/data/images/test.jpg',
        timestamp=datetime.now(),
        ai_score=0.6,
        ai_label=1,
        is_uncertain=False
    )
    assert sample_id > 0

    # 查询样本
    sample = sample_dao.get_by_id(sample_id)
    assert sample is not None
    assert sample['ai_score'] == 0.6

    # 统计
    stats = sample_dao.count_by_label()
    assert 'normal_count' in stats
    assert 'defect_count' in stats


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
