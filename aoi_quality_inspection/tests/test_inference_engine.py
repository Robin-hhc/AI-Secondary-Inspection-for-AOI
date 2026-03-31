"""
推理引擎模块单元测试
"""
import pytest
import numpy as np
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from inference_engine.anomaly_detector import AnomalyDetector
from inference_engine.faiss_searcher import FaissSearcher


def test_anomaly_detector():
    """测试异常检测器"""
    detector = AnomalyDetector(threshold=0.5, uncertainty_margin=0.1)

    # 测试异常分数计算
    score = detector.compute_score(0.3)
    assert 0 <= score <= 1

    # 测试判定
    label, confidence, is_uncertain = detector.judge(0.5)
    assert is_uncertain == True  # 分数等于阈值,应该不确定

    label, confidence, is_uncertain = detector.judge(0.8)
    assert label == 1  # 分数大于阈值,应该判定为异常
    assert is_uncertain == False

    label, confidence, is_uncertain = detector.judge(0.2)
    assert label == 0  # 分数小于阈值,应该判定为正常
    assert is_uncertain == False

    # 测试批量判定
    scores = np.array([0.2, 0.5, 0.8])
    labels, confidences, uncertainties = detector.batch_judge(scores)
    assert len(labels) == 3
    assert labels[0] == 0
    assert labels[1] == -1
    assert labels[2] == 1


def test_faiss_searcher():
    """测试FAISS搜索器"""
    dim = 128
    searcher = FaissSearcher(dim=dim, index_type='Flat')

    # 生成测试数据
    n_samples = 100
    features = np.random.randn(n_samples, dim).astype('float32')

    # 构建索引
    searcher.build_index(features)
    assert searcher.get_index_size() == n_samples

    # 搜索
    query = np.random.randn(1, dim).astype('float32')
    distances, indices = searcher.search(query, k=5)
    assert distances.shape == (1, 5)
    assert indices.shape == (1, 5)

    # 添加特征
    new_features = np.random.randn(10, dim).astype('float32')
    searcher.add_features(new_features)
    assert searcher.get_index_size() == n_samples + 10


def test_faiss_searcher_save_load():
    """测试FAISS索引保存和加载"""
    import tempfile
    import os

    dim = 64
    searcher = FaissSearcher(dim=dim, index_type='Flat')

    # 构建索引
    features = np.random.randn(50, dim).astype('float32')
    searcher.build_index(features)

    # 保存索引
    with tempfile.NamedTemporaryFile(suffix='.index', delete=False) as f:
        index_path = f.name

    try:
        searcher.save_index(index_path)
        assert os.path.exists(index_path)

        # 加载索引
        new_searcher = FaissSearcher(dim=dim)
        new_searcher.load_index(index_path)
        assert new_searcher.get_index_size() == 50

    finally:
        os.unlink(index_path)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
