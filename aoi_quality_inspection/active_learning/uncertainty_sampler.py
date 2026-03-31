"""
不确定性采样器
实现主动学习的不确定性采样策略
"""
import numpy as np
from typing import List, Dict, Any, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class UncertaintySampler:
    """不确定性采样器"""

    def __init__(self, threshold: float = 0.5,
                 margin: float = 0.1,
                 diversity_threshold: float = 0.3):
        """
        初始化不确定性采样器

        Args:
            threshold: 异常判定阈值
            margin: 不确定性边界
            diversity_threshold: 多样性阈值
        """
        self.threshold = threshold
        self.margin = margin
        self.diversity_threshold = diversity_threshold

        logger.info(f"不确定性采样器初始化: 阈值={threshold}, 边界={margin}")

    def compute_uncertainty(self, score: float) -> float:
        """
        计算不确定性分数

        Args:
            score: 异常分数

        Returns:
            float: 不确定性分数 (越小越不确定)
        """
        # 不确定性 = |异常分数 - 阈值|
        uncertainty = abs(score - self.threshold)
        return uncertainty

    def is_uncertain(self, score: float) -> bool:
        """
        判断是否为不确定样本

        Args:
            score: 异常分数

        Returns:
            bool: 是否不确定
        """
        uncertainty = self.compute_uncertainty(score)
        return uncertainty < self.margin

    def select_samples(self, samples: List[Dict[str, Any]],
                       max_samples: int = 100,
                       strategy: str = 'uncertainty') -> List[Dict[str, Any]]:
        """
        选择样本进行标注

        Args:
            samples: 样本列表,每个样本包含'score'字段
            max_samples: 最大选择数量
            strategy: 采样策略 ('uncertainty', 'diversity', 'hybrid')

        Returns:
            List[Dict]: 选中的样本列表
        """
        if not samples:
            return []

        # 计算每个样本的不确定性
        for sample in samples:
            score = sample.get('ai_score', 0.5)
            sample['uncertainty'] = self.compute_uncertainty(score)

        if strategy == 'uncertainty':
            # 纯不确定性采样:选择最不确定的样本
            selected = self._uncertainty_sampling(samples, max_samples)

        elif strategy == 'diversity':
            # 多样性采样:选择差异最大的样本
            selected = self._diversity_sampling(samples, max_samples)

        elif strategy == 'hybrid':
            # 混合策略:先不确定性,再多样性
            selected = self._hybrid_sampling(samples, max_samples)

        else:
            logger.warning(f"未知采样策略: {strategy}, 使用不确定性采样")
            selected = self._uncertainty_sampling(samples, max_samples)

        logger.info(f"采样完成: 策略={strategy}, 选中{len(selected)}个样本")
        return selected

    def _uncertainty_sampling(self, samples: List[Dict[str, Any]],
                              max_samples: int) -> List[Dict[str, Any]]:
        """
        不确定性采样

        Args:
            samples: 样本列表
            max_samples: 最大数量

        Returns:
            List[Dict]: 选中的样本
        """
        # 按不确定性升序排列(越小越不确定)
        sorted_samples = sorted(samples, key=lambda x: x['uncertainty'])

        # 选择前N个最不确定的样本
        selected = sorted_samples[:max_samples]

        return selected

    def _diversity_sampling(self, samples: List[Dict[str, Any]],
                            max_samples: int) -> List[Dict[str, Any]]:
        """
        多样性采样

        Args:
            samples: 样本列表
            max_samples: 最大数量

        Returns:
            List[Dict]: 选中的样本
        """
        if len(samples) <= max_samples:
            return samples

        selected = []

        # 随机选择第一个样本
        import random
        first_idx = random.randint(0, len(samples) - 1)
        selected.append(samples[first_idx])
        remaining = [s for i, s in enumerate(samples) if i != first_idx]

        # 贪心选择与已选样本差异最大的样本
        while len(selected) < max_samples and remaining:
            best_idx = 0
            max_diversity = -1

            for i, candidate in enumerate(remaining):
                # 计算与已选样本的最小差异
                min_diff = min(
                    abs(candidate['uncertainty'] - s['uncertainty'])
                    for s in selected
                )

                if min_diff > max_diversity:
                    max_diversity = min_diff
                    best_idx = i

            selected.append(remaining[best_idx])
            remaining.pop(best_idx)

        return selected

    def _hybrid_sampling(self, samples: List[Dict[str, Any]],
                         max_samples: int) -> List[Dict[str, Any]]:
        """
        混合采样:先不确定性,再多样性

        Args:
            samples: 样本列表
            max_samples: 最大数量

        Returns:
            List[Dict]: 选中的样本
        """
        # 先筛选不确定样本
        uncertain_samples = [s for s in samples if s['uncertainty'] < self.margin]

        if len(uncertain_samples) <= max_samples:
            return uncertain_samples

        # 再进行多样性采样
        return self._diversity_sampling(uncertain_samples, max_samples)

    def _is_diverse(self, candidate: Dict[str, Any],
                    selected: List[Dict[str, Any]]) -> bool:
        """
        检查样本是否与已选样本足够多样

        Args:
            candidate: 候选样本
            selected: 已选样本列表

        Returns:
            bool: 是否多样
        """
        if not selected:
            return True

        # 计算与已选样本的最小差异
        min_diff = min(
            abs(candidate['uncertainty'] - s['uncertainty'])
            for s in selected
        )

        return min_diff > self.diversity_threshold

    def get_sampling_statistics(self, samples: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        获取采样统计信息

        Args:
            samples: 样本列表

        Returns:
            Dict: 统计信息
        """
        if not samples:
            return {}

        uncertainties = [s.get('uncertainty', 0.5) for s in samples]

        return {
            'total_samples': len(samples),
            'uncertain_count': sum(1 for u in uncertainties if u < self.margin),
            'uncertain_ratio': sum(1 for u in uncertainties if u < self.margin) / len(samples),
            'mean_uncertainty': float(np.mean(uncertainties)),
            'std_uncertainty': float(np.std(uncertainties)),
            'min_uncertainty': float(np.min(uncertainties)),
            'max_uncertainty': float(np.max(uncertainties))
        }
