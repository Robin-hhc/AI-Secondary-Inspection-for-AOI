"""
主动学习模块单元测试
"""
import pytest
import numpy as np
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from active_learning.uncertainty_sampler import UncertaintySampler
from active_learning.performance_monitor import PerformanceMonitor


def test_uncertainty_sampler():
    """测试不确定性采样器"""
    sampler = UncertaintySampler(threshold=0.5, margin=0.1)

    # 测试不确定性计算
    uncertainty = sampler.compute_uncertainty(0.5)
    assert uncertainty == 0  # 分数等于阈值,不确定性为0

    uncertainty = sampler.compute_uncertainty(0.6)
    assert uncertainty == 0.1  # |0.6 - 0.5| = 0.1

    # 测试不确定判断
    assert sampler.is_uncertain(0.5) == True
    assert sampler.is_uncertain(0.55) == True
    assert sampler.is_uncertain(0.7) == False


def test_uncertainty_sampling():
    """测试不确定性采样"""
    sampler = UncertaintySampler(threshold=0.5, margin=0.1)

    # 创建测试样本
    samples = [
        {'id': 1, 'ai_score': 0.5},
        {'id': 2, 'ai_score': 0.52},
        {'id': 3, 'ai_score': 0.8},
        {'id': 4, 'ai_score': 0.2},
        {'id': 5, 'ai_score': 0.48}
    ]

    # 不确定性采样
    selected = sampler.select_samples(samples, max_samples=3, strategy='uncertainty')
    assert len(selected) == 3
    # 应该选择最不确定的样本(分数接近0.5)
    assert selected[0]['id'] in [1, 2, 5]


def test_performance_monitor():
    """测试性能监控器"""
    monitor = PerformanceMonitor(window_size=10)

    # 记录指标
    monitor.record('accuracy', 0.9)
    monitor.record('accuracy', 0.92)
    monitor.record('inference_latency', 120.5)

    # 获取趋势
    trend = monitor.get_trend('accuracy')
    assert trend['current'] == 0.92
    assert trend['mean'] == 0.91

    # 记录推理结果
    monitor.record_inference(100.0, is_correct=True)
    monitor.record_inference(150.0, is_correct=False)

    summary = monitor.get_summary()
    assert summary['total_inferences'] == 3  # 包括之前的记录
    assert summary['total_labelings'] == 2


def test_performance_metrics():
    """测试性能指标计算"""
    monitor = PerformanceMonitor()

    # 计算评估指标
    true_labels = [0, 0, 1, 1, 0, 1]
    pred_labels = [0, 1, 1, 1, 0, 0]

    metrics = monitor.compute_metrics(true_labels, pred_labels)

    assert 'accuracy' in metrics
    assert 'precision' in metrics
    assert 'recall' in metrics
    assert 'f1' in metrics

    # 验证准确率
    # 正确预测: 0, 1, 1, 0 (4个)
    # 总数: 6
    assert metrics['accuracy'] == pytest.approx(4/6, rel=1e-2)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
