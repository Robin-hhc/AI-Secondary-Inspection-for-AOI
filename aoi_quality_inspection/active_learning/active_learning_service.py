"""
主动学习服务
集成不确定性采样和性能监控
"""
import time
import threading
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from .uncertainty_sampler import UncertaintySampler
from .performance_monitor import PerformanceMonitor

logger = logging.getLogger(__name__)


class ActiveLearningService:
    """主动学习服务"""

    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化主动学习服务

        Args:
            config: 配置字典
        """
        self.config = config or {}

        # 初始化组件
        self.sampler = UncertaintySampler(
            threshold=self.config.get('threshold', 0.5),
            margin=self.config.get('margin', 0.1)
        )

        self.monitor = PerformanceMonitor(
            window_size=self.config.get('metrics_window', 100)
        )

        # 待标注样本队列
        self.pending_samples: List[Dict[str, Any]] = []
        self.max_pending = self.config.get('max_pending', 1000)

        # 服务状态
        self.is_running = False
        self.sampling_thread = None
        self.sampling_interval = self.config.get('sampling_interval', 60)

        logger.info("主动学习服务初始化完成")

    def start(self):
        """启动服务"""
        if self.is_running:
            logger.warning("主动学习服务已在运行")
            return

        self.is_running = True
        self.sampling_thread = threading.Thread(target=self._sampling_loop, daemon=True)
        self.sampling_thread.start()

        logger.info("主动学习服务已启动")

    def stop(self):
        """停止服务"""
        if not self.is_running:
            return

        self.is_running = False
        if self.sampling_thread:
            self.sampling_thread.join(timeout=5)

        logger.info("主动学习服务已停止")

    def _sampling_loop(self):
        """采样循环"""
        while self.is_running:
            try:
                # 执行采样周期任务
                self._sampling_cycle()

                # 等待下一次采样
                time.sleep(self.sampling_interval)

            except Exception as e:
                logger.error(f"采样循环异常: {e}")
                time.sleep(10)

    def _sampling_cycle(self):
        """采样周期任务"""
        logger.debug("执行采样周期任务")

        # 检查告警
        alert_info = self.monitor.check_alert()
        if alert_info['has_alert']:
            for alert in alert_info['alerts']:
                logger.warning(f"性能告警: {alert['message']}")

    def add_sample(self, sample: Dict[str, Any]):
        """
        添加样本到待标注队列

        Args:
            sample: 样本信息
        """
        if len(self.pending_samples) >= self.max_pending:
            logger.warning(f"待标注队列已满,丢弃样本: {sample.get('id')}")
            return

        # 检查是否为不确定样本
        score = sample.get('ai_score', 0.5)
        if self.sampler.is_uncertain(score):
            sample['added_at'] = datetime.now()
            self.pending_samples.append(sample)
            logger.debug(f"添加不确定样本: {sample.get('id')}, 分数={score:.4f}")

    def get_pending_samples(self, limit: int = 100,
                           strategy: str = 'uncertainty') -> List[Dict[str, Any]]:
        """
        获取待标注样本

        Args:
            limit: 最大数量
            strategy: 采样策略

        Returns:
            List[Dict]: 待标注样本列表
        """
        if not self.pending_samples:
            return []

        # 使用采样器选择样本
        selected = self.sampler.select_samples(
            self.pending_samples,
            max_samples=limit,
            strategy=strategy
        )

        return selected

    def submit_label(self, sample_id: int, label: int,
                    operator: str, defect_type: str = None) -> bool:
        """
        提交标注结果

        Args:
            sample_id: 样本ID
            label: 标注标签
            operator: 操作员
            defect_type: 缺陷类型

        Returns:
            bool: 是否成功
        """
        # 从待标注队列移除
        self.pending_samples = [
            s for s in self.pending_samples
            if s.get('id') != sample_id
        ]

        # 记录标注统计
        self.monitor.labeling_count += 1

        logger.info(f"标注提交: 样本{sample_id}, 标签{label}, 操作员{operator}")
        return True

    def record_inference_result(self, sample_id: int, ai_score: float,
                               ai_label: int, latency_ms: float,
                               true_label: int = None):
        """
        记录推理结果

        Args:
            sample_id: 样本ID
            ai_score: AI异常分数
            ai_label: AI判定标签
            latency_ms: 推理延迟
            true_label: 真实标签(可选)
        """
        # 记录推理延迟
        self.monitor.record_inference(latency_ms)

        # 如果有真实标签,记录正确性
        if true_label is not None:
            is_correct = (ai_label == true_label)
            self.monitor.correct_count += 1 if is_correct else 0

        # 添加到待标注队列
        sample = {
            'id': sample_id,
            'ai_score': ai_score,
            'ai_label': ai_label,
            'latency_ms': latency_ms
        }
        self.add_sample(sample)

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            Dict: 统计信息
        """
        # 采样统计
        sampling_stats = self.sampler.get_sampling_statistics(self.pending_samples)

        # 性能摘要
        performance_summary = self.monitor.get_summary()

        return {
            'pending_samples': len(self.pending_samples),
            'max_pending': self.max_pending,
            'sampling': sampling_stats,
            'performance': performance_summary,
            'is_running': self.is_running
        }

    def update_threshold(self, threshold: float):
        """
        更新异常阈值

        Args:
            threshold: 新阈值
        """
        self.sampler.threshold = threshold
        logger.info(f"阈值已更新: {threshold}")

    def clear_pending(self):
        """清空待标注队列"""
        self.pending_samples.clear()
        logger.info("待标注队列已清空")
