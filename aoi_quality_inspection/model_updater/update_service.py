"""
模型更新服务
实现特征库的增量更新和全量重建
"""
import time
import threading
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np
import logging

from .feature_lib_manager import FeatureLibManager

logger = logging.getLogger(__name__)


class ModelUpdateService:
    """模型更新服务"""

    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化模型更新服务

        Args:
            config: 配置字典
        """
        self.config = config or {}

        # 特征库管理器
        self.lib_manager = FeatureLibManager(
            lib_root=self.config.get('lib_root', './data/feature_libs')
        )

        # 更新触发条件
        self.min_samples = self.config.get('min_samples', 50)
        self.time_interval = self.config.get('time_interval', 86400)  # 24小时
        self.accuracy_drop = self.config.get('accuracy_drop', 0.05)

        # 更新策略
        self.update_strategy = self.config.get('strategy', 'incremental')
        self.rebuild_threshold = self.config.get('rebuild_threshold', 1000)

        # 服务状态
        self.is_running = False
        self.update_thread = None
        self.last_update_time = datetime.now()

        # 待更新样本缓存
        self.pending_samples: List[Dict[str, Any]] = []

        logger.info("模型更新服务初始化完成")

    def start(self):
        """启动服务"""
        if self.is_running:
            logger.warning("模型更新服务已在运行")
            return

        self.is_running = True
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()

        logger.info("模型更新服务已启动")

    def stop(self):
        """停止服务"""
        if not self.is_running:
            return

        self.is_running = False
        if self.update_thread:
            self.update_thread.join(timeout=5)

        logger.info("模型更新服务已停止")

    def _update_loop(self):
        """更新循环"""
        while self.is_running:
            try:
                # 检查更新条件
                if self._check_update_condition():
                    logger.info("触发自动更新")
                    self.trigger_update()

                # 等待下一次检查
                time.sleep(3600)  # 每小时检查一次

            except Exception as e:
                logger.error(f"更新循环异常: {e}")
                time.sleep(600)

    def _check_update_condition(self) -> bool:
        """
        检查更新条件

        Returns:
            bool: 是否满足更新条件
        """
        # 检查样本数量
        if len(self.pending_samples) >= self.min_samples:
            logger.info(f"样本数量达到阈值: {len(self.pending_samples)} >= {self.min_samples}")
            return True

        # 检查时间间隔
        elapsed = (datetime.now() - self.last_update_time).total_seconds()
        if elapsed >= self.time_interval and len(self.pending_samples) > 0:
            logger.info(f"时间间隔达到阈值: {elapsed:.0f}s >= {self.time_interval}s")
            return True

        return False

    def trigger_update(self, product_code: str = None,
                      force: bool = False) -> Dict[str, Any]:
        """
        触发模型更新

        Args:
            product_code: 产品编码
            force: 是否强制更新

        Returns:
            Dict: 更新结果
        """
        if not self.pending_samples and not force:
            logger.warning("没有待更新样本")
            return {'success': False, 'message': '没有待更新样本'}

        try:
            start_time = time.time()

            # 获取正常样本的特征
            normal_features = self._extract_normal_features()

            if len(normal_features) == 0:
                return {'success': False, 'message': '没有正常样本特征'}

            # 执行更新
            if self.update_strategy == 'incremental':
                lib_path = self._incremental_update(product_code, normal_features)
            else:
                lib_path = self._full_rebuild(product_code, normal_features)

            # 清空待更新样本
            self.pending_samples.clear()
            self.last_update_time = datetime.now()

            elapsed = time.time() - start_time

            result = {
                'success': True,
                'lib_path': lib_path,
                'num_features': len(normal_features),
                'elapsed_seconds': elapsed,
                'timestamp': self.last_update_time.isoformat()
            }

            logger.info(f"模型更新完成: {result}")
            return result

        except Exception as e:
            logger.error(f"模型更新失败: {e}")
            return {'success': False, 'message': str(e)}

    def _extract_normal_features(self) -> np.ndarray:
        """
        提取正常样本特征

        Returns:
            np.ndarray: 特征矩阵
        """
        # 筛选正常样本
        normal_samples = [
            s for s in self.pending_samples
            if s.get('label') == 0  # 0表示正常
        ]

        if not normal_samples:
            return np.array([])

        # 提取特征
        features = []
        for sample in normal_samples:
            if 'features' in sample:
                features.append(sample['features'])

        if features:
            return np.vstack(features)

        return np.array([])

    def _incremental_update(self, product_code: str,
                           new_features: np.ndarray) -> str:
        """
        增量更新

        Args:
            product_code: 产品编码
            new_features: 新特征

        Returns:
            str: 新特征库路径
        """
        # 获取当前活跃版本
        current_lib = self.lib_manager.get_active_version(product_code)

        if current_lib:
            # 添加到现有特征库
            new_lib = self.lib_manager.add_features(current_lib, new_features)
        else:
            # 创建新特征库
            new_lib = self.lib_manager.create_lib(product_code, new_features)

        logger.info(f"增量更新完成: {new_lib}")
        return new_lib

    def _full_rebuild(self, product_code: str,
                     features: np.ndarray) -> str:
        """
        全量重建

        Args:
            product_code: 产品编码
            features: 特征

        Returns:
            str: 新特征库路径
        """
        # 重建特征库
        new_lib = self.lib_manager.rebuild_lib(product_code, features)

        logger.info(f"全量重建完成: {new_lib}")
        return new_lib

    def add_sample(self, sample: Dict[str, Any]):
        """
        添加样本到待更新队列

        Args:
            sample: 样本信息
        """
        self.pending_samples.append(sample)
        logger.debug(f"添加待更新样本: {sample.get('id')}")

    def add_samples(self, samples: List[Dict[str, Any]]):
        """
        批量添加样本

        Args:
            samples: 样本列表
        """
        self.pending_samples.extend(samples)
        logger.info(f"批量添加{len(samples)}个待更新样本")

    def get_status(self) -> Dict[str, Any]:
        """
        获取服务状态

        Returns:
            Dict: 状态信息
        """
        return {
            'is_running': self.is_running,
            'pending_samples': len(self.pending_samples),
            'last_update_time': self.last_update_time.isoformat(),
            'update_strategy': self.update_strategy,
            'min_samples': self.min_samples
        }

    def set_strategy(self, strategy: str):
        """
        设置更新策略

        Args:
            strategy: 策略类型 ('incremental', 'full')
        """
        self.update_strategy = strategy
        logger.info(f"更新策略已设置: {strategy}")
