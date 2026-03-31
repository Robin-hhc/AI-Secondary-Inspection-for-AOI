"""
推理引擎核心
集成特征提取、向量搜索和异常检测
"""
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
import logging
import time

from .feature_extractor import FeatureExtractor
from .faiss_searcher import FaissSearcher
from .anomaly_detector import AnomalyDetector

logger = logging.getLogger(__name__)


class InferenceEngine:
    """推理引擎"""

    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化推理引擎

        Args:
            config: 配置字典
        """
        self.config = config or {}

        # 初始化组件
        self.feature_extractor = None
        self.faiss_searcher = None
        self.anomaly_detector = None

        # 状态
        self.is_initialized = False
        self.current_model = None

        logger.info("推理引擎创建")

    def initialize(self, backbone: str = 'wide_resnet50',
                   feature_dim: int = 512,
                   threshold: float = 0.5,
                   device: str = 'cuda'):
        """
        初始化推理引擎

        Args:
            backbone: 骨干网络
            feature_dim: 特征维度
            threshold: 异常阈值
            device: 计算设备
        """
        # 初始化特征提取器
        self.feature_extractor = FeatureExtractor(
            backbone=backbone,
            device=device
        )

        # 初始化FAISS搜索器
        self.faiss_searcher = FaissSearcher(
            dim=feature_dim,
            index_type='IVF',
            use_gpu=(device == 'cuda')
        )

        # 初始化异常检测器
        self.anomaly_detector = AnomalyDetector(threshold=threshold)

        self.is_initialized = True
        logger.info("推理引擎初始化完成")

    def load_feature_lib(self, lib_path: str):
        """
        加载特征库

        Args:
            lib_path: 特征库路径
        """
        if not self.is_initialized:
            raise RuntimeError("推理引擎未初始化")

        self.faiss_searcher.load_index(lib_path)
        self.current_model = lib_path
        logger.info(f"特征库已加载: {lib_path}")

    def infer(self, image: np.ndarray) -> Dict[str, Any]:
        """
        执行推理

        Args:
            image: 输入图像 (C, H, W)

        Returns:
            Dict: 推理结果
        """
        if not self.is_initialized:
            raise RuntimeError("推理引擎未初始化")

        start_time = time.time()

        # 提取特征
        features = self.feature_extractor.extract(image)

        # 搜索最近邻
        distances, indices = self.faiss_searcher.search(features, k=1)
        min_distance = float(distances[0][0])

        # 计算异常分数
        score = self.anomaly_detector.compute_score(min_distance)

        # 判定
        label, confidence, is_uncertain = self.anomaly_detector.judge(score)

        # 推理耗时
        elapsed = (time.time() - start_time) * 1000

        result = {
            'score': score,
            'label': label,
            'confidence': confidence,
            'is_uncertain': is_uncertain,
            'distance': min_distance,
            'elapsed_ms': elapsed
        }

        logger.debug(f"推理完成: score={score:.4f}, label={label}, 耗时={elapsed:.2f}ms")
        return result

    def batch_infer(self, images: np.ndarray) -> list:
        """
        批量推理

        Args:
            images: 图像批次 (N, C, H, W)

        Returns:
            list: 推理结果列表
        """
        if not self.is_initialized:
            raise RuntimeError("推理引擎未初始化")

        start_time = time.time()

        # 批量提取特征
        features = self.feature_extractor.extract_batch(images)

        # 批量搜索
        distances, indices = self.faiss_searcher.search(features, k=1)
        min_distances = distances[:, 0]

        # 批量计算分数
        scores = [self.anomaly_detector.compute_score(d) for d in min_distances]

        # 批量判定
        labels, confidences, uncertainties = self.anomaly_detector.batch_judge(np.array(scores))

        elapsed = (time.time() - start_time) * 1000

        results = []
        for i in range(len(images)):
            results.append({
                'score': scores[i],
                'label': int(labels[i]),
                'confidence': float(confidences[i]),
                'is_uncertain': bool(uncertainties[i]),
                'distance': float(min_distances[i]),
                'elapsed_ms': elapsed / len(images)
            })

        logger.info(f"批量推理完成: {len(images)}张, 总耗时={elapsed:.2f}ms")
        return results

    def switch_model(self, lib_path: str):
        """
        切换模型

        Args:
            lib_path: 新特征库路径
        """
        self.load_feature_lib(lib_path)
        logger.info(f"模型已切换: {lib_path}")

    def get_status(self) -> Dict[str, Any]:
        """
        获取引擎状态

        Returns:
            Dict: 状态信息
        """
        return {
            'is_initialized': self.is_initialized,
            'current_model': self.current_model,
            'feature_lib_size': self.faiss_searcher.get_index_size() if self.faiss_searcher else 0,
            'threshold': self.anomaly_detector.threshold if self.anomaly_detector else None
        }

    def update_threshold(self, threshold: float):
        """
        更新异常阈值

        Args:
            threshold: 新阈值
        """
        if self.anomaly_detector:
            self.anomaly_detector.update_threshold(threshold)
