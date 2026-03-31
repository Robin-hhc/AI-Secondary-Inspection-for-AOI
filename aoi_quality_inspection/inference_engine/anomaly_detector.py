"""
异常检测器
基于PatchCore的异常检测逻辑
"""
import numpy as np
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """异常检测器"""

    def __init__(self, threshold: float = 0.5,
                 uncertainty_margin: float = 0.1,
                 min_confidence: float = 0.7):
        """
        初始化异常检测器

        Args:
            threshold: 异常判定阈值
            uncertainty_margin: 不确定性边界
            min_confidence: 最小置信度
        """
        self.threshold = threshold
        self.uncertainty_margin = uncertainty_margin
        self.min_confidence = min_confidence

        logger.info(f"异常检测器初始化: 阈值={threshold}, 边界={uncertainty_margin}")

    def compute_score(self, distance: float,
                      max_distance: float = None) -> float:
        """
        计算异常分数

        Args:
            distance: 特征距离
            max_distance: 最大距离（用于归一化）

        Returns:
            float: 异常分数 [0, 1]
        """
        if max_distance is not None and max_distance > 0:
            score = distance / max_distance
        else:
            # 使用sigmoid归一化
            score = 1 / (1 + np.exp(-distance + 5))

        return float(np.clip(score, 0, 1))

    def judge(self, score: float) -> Tuple[int, float, bool]:
        """
        判定是否异常

        Args:
            score: 异常分数

        Returns:
            Tuple[int, float, bool]: (标签, 置信度, 是否不确定)
        """
        # 计算与阈值的距离
        distance_to_threshold = abs(score - self.threshold)

        # 计算置信度
        confidence = min(distance_to_threshold / self.uncertainty_margin, 1.0)

        # 判断是否不确定
        is_uncertain = distance_to_threshold < self.uncertainty_margin

        # 判定标签
        if is_uncertain:
            label = -1  # 不确定
        elif score >= self.threshold:
            label = 1  # 异常
        else:
            label = 0  # 正常

        return label, confidence, is_uncertain

    def compute_anomaly_map(self, patch_scores: np.ndarray,
                            image_size: Tuple[int, int]) -> np.ndarray:
        """
        计算异常热力图

        Args:
            patch_scores: 图像块分数 (H, W)
            image_size: 图像尺寸 (H, W)

        Returns:
            np.ndarray: 异常热力图
        """
        # 这里简化处理，实际PatchCore会进行上采样
        import cv2

        # 归一化到[0, 255]
        heatmap = (patch_scores * 255).astype(np.uint8)

        # 应用颜色映射
        heatmap = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)

        # 调整大小
        heatmap = cv2.resize(heatmap, image_size[::-1])

        return heatmap

    def batch_judge(self, scores: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        批量判定

        Args:
            scores: 异常分数数组

        Returns:
            Tuple: (标签数组, 置信度数组, 不确定标志数组)
        """
        labels = []
        confidences = []
        uncertainties = []

        for score in scores:
            label, conf, uncertain = self.judge(score)
            labels.append(label)
            confidences.append(conf)
            uncertainties.append(uncertain)

        return (
            np.array(labels),
            np.array(confidences),
            np.array(uncertainties)
        )

    def update_threshold(self, threshold: float):
        """
        更新阈值

        Args:
            threshold: 新阈值
        """
        self.threshold = threshold
        logger.info(f"阈值已更新: {threshold}")

    def get_statistics(self, scores: np.ndarray) -> dict:
        """
        获取分数统计信息

        Args:
            scores: 异常分数数组

        Returns:
            dict: 统计信息
        """
        return {
            'mean': float(np.mean(scores)),
            'std': float(np.std(scores)),
            'min': float(np.min(scores)),
            'max': float(np.max(scores)),
            'median': float(np.median(scores)),
            'q25': float(np.percentile(scores, 25)),
            'q75': float(np.percentile(scores, 75))
        }
