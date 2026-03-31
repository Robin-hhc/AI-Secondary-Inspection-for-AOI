"""
性能监控器
监控和记录系统性能指标
"""
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import deque
import logging

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self, window_size: int = 100):
        """
        初始化性能监控器

        Args:
            window_size: 滑动窗口大小
        """
        self.window_size = window_size

        # 性能指标历史
        self.accuracy_history: deque = deque(maxlen=window_size)
        self.precision_history: deque = deque(maxlen=window_size)
        self.recall_history: deque = deque(maxlen=window_size)
        self.f1_history: deque = deque(maxlen=window_size)

        # 推理延迟历史
        self.inference_latency_history: deque = deque(maxlen=window_size)

        # 标注统计
        self.labeling_count = 0
        self.correct_count = 0

        logger.info(f"性能监控器初始化: 窗口大小={window_size}")

    def record(self, metric_type: str, value: float, timestamp: datetime = None):
        """
        记录性能指标

        Args:
            metric_type: 指标类型
            value: 指标值
            timestamp: 时间戳
        """
        if timestamp is None:
            timestamp = datetime.now()

        if metric_type == 'accuracy':
            self.accuracy_history.append(value)
        elif metric_type == 'precision':
            self.precision_history.append(value)
        elif metric_type == 'recall':
            self.recall_history.append(value)
        elif metric_type == 'f1':
            self.f1_history.append(value)
        elif metric_type == 'inference_latency':
            self.inference_latency_history.append(value)

        logger.debug(f"记录指标: {metric_type}={value}")

    def record_inference(self, latency_ms: float, is_correct: bool = None):
        """
        记录推理结果

        Args:
            latency_ms: 推理延迟(毫秒)
            is_correct: 是否正确(可选)
        """
        self.inference_latency_history.append(latency_ms)

        if is_correct is not None:
            self.labeling_count += 1
            if is_correct:
                self.correct_count += 1

    def compute_metrics(self, true_labels: List[int],
                       pred_labels: List[int]) -> Dict[str, float]:
        """
        计算评估指标

        Args:
            true_labels: 真实标签
            pred_labels: 预测标签

        Returns:
            Dict: 评估指标
        """
        true_labels = np.array(true_labels)
        pred_labels = np.array(pred_labels)

        # 准确率
        accuracy = np.mean(true_labels == pred_labels)

        # 精确率 (针对异常类)
        true_positives = np.sum((true_labels == 1) & (pred_labels == 1))
        false_positives = np.sum((true_labels == 0) & (pred_labels == 1))
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0

        # 召回率
        false_negatives = np.sum((true_labels == 1) & (pred_labels == 0))
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0

        # F1分数
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        metrics = {
            'accuracy': float(accuracy),
            'precision': float(precision),
            'recall': float(recall),
            'f1': float(f1)
        }

        # 记录到历史
        self.record('accuracy', accuracy)
        self.record('precision', precision)
        self.record('recall', recall)
        self.record('f1', f1)

        return metrics

    def get_trend(self, metric_type: str = 'accuracy',
                  window: int = None) -> Dict[str, Any]:
        """
        获取性能趋势

        Args:
            metric_type: 指标类型
            window: 窗口大小

        Returns:
            Dict: 趋势信息
        """
        if metric_type == 'accuracy':
            history = list(self.accuracy_history)
        elif metric_type == 'precision':
            history = list(self.precision_history)
        elif metric_type == 'recall':
            history = list(self.recall_history)
        elif metric_type == 'f1':
            history = list(self.f1_history)
        elif metric_type == 'inference_latency':
            history = list(self.inference_latency_history)
        else:
            return {}

        if not history:
            return {}

        if window:
            history = history[-window:]

        return {
            'metric_type': metric_type,
            'current': float(history[-1]) if history else 0,
            'mean': float(np.mean(history)),
            'std': float(np.std(history)),
            'min': float(np.min(history)),
            'max': float(np.max(history)),
            'trend': 'improving' if len(history) > 1 and history[-1] > history[-2] else 'declining',
            'history': history
        }

    def check_alert(self, threshold: float = 0.85) -> Dict[str, Any]:
        """
        检查告警条件

        Args:
            threshold: 告警阈值

        Returns:
            Dict: 告警信息
        """
        alerts = []

        # 检查准确率
        if self.accuracy_history:
            recent_accuracy = np.mean(list(self.accuracy_history)[-10:])
            if recent_accuracy < threshold:
                alerts.append({
                    'type': 'accuracy_low',
                    'message': f'准确率低于阈值: {recent_accuracy:.3f} < {threshold}',
                    'severity': 'warning'
                })

        # 检查推理延迟
        if self.inference_latency_history:
            recent_latency = np.mean(list(self.inference_latency_history)[-10:])
            if recent_latency > 500:  # 超过500ms
                alerts.append({
                    'type': 'latency_high',
                    'message': f'推理延迟过高: {recent_latency:.2f}ms',
                    'severity': 'warning'
                })

        return {
            'has_alert': len(alerts) > 0,
            'alerts': alerts,
            'timestamp': datetime.now().isoformat()
        }

    def get_summary(self) -> Dict[str, Any]:
        """
        获取性能摘要

        Returns:
            Dict: 性能摘要
        """
        summary = {
            'total_inferences': len(self.inference_latency_history),
            'total_labelings': self.labeling_count,
            'overall_accuracy': self.correct_count / self.labeling_count if self.labeling_count > 0 else 0
        }

        # 添加各指标趋势
        for metric in ['accuracy', 'precision', 'recall', 'f1', 'inference_latency']:
            trend = self.get_trend(metric)
            if trend:
                summary[f'{metric}_trend'] = trend

        return summary

    def reset(self):
        """重置监控器"""
        self.accuracy_history.clear()
        self.precision_history.clear()
        self.recall_history.clear()
        self.f1_history.clear()
        self.inference_latency_history.clear()
        self.labeling_count = 0
        self.correct_count = 0

        logger.info("性能监控器已重置")
