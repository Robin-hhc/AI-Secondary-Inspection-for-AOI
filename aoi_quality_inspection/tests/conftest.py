"""
测试配置文件
"""
import pytest
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope='session')
def test_data_dir():
    """测试数据目录"""
    data_dir = Path(__file__).parent / 'test_data'
    data_dir.mkdir(exist_ok=True)
    return data_dir


@pytest.fixture
def sample_image():
    """创建测试图像"""
    import numpy as np
    import cv2

    # 创建随机图像
    image = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
    return image
