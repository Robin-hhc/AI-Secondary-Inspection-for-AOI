"""
FAISS向量搜索器
使用FAISS进行高效的最近邻搜索
"""
import faiss
import numpy as np
from pathlib import Path
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class FaissSearcher:
    """FAISS搜索器"""

    def __init__(self, dim: int, index_type: str = 'IVF',
                 nlist: int = 100, nprobe: int = 10,
                 use_gpu: bool = False):
        """
        初始化FAISS搜索器

        Args:
            dim: 特征维度
            index_type: 索引类型 ('Flat', 'IVF', 'IVFPQ')
            nlist: 聚类中心数量
            nprobe: 搜索时探测的聚类数量
            use_gpu: 是否使用GPU
        """
        self.dim = dim
        self.index_type = index_type
        self.nlist = nlist
        self.nprobe = nprobe
        self.use_gpu = use_gpu

        self.index = None
        self.is_trained = False

        logger.info(f"FAISS搜索器初始化: dim={dim}, type={index_type}, GPU={use_gpu}")

    def build_index(self, features: np.ndarray):
        """
        构建索引

        Args:
            features: 特征矩阵 (N, D)
        """
        n_samples, dim = features.shape
        assert dim == self.dim, f"特征维度不匹配: {dim} != {self.dim}"

        # 归一化特征
        faiss.normalize_L2(features)

        if self.index_type == 'Flat':
            # 暴力搜索
            self.index = faiss.IndexFlatL2(self.dim)

        elif self.index_type == 'IVF':
            # 倒排索引
            quantizer = faiss.IndexFlatL2(self.dim)
            self.index = faiss.IndexIVFFlat(quantizer, self.dim, self.nlist)

            # 训练
            logger.info(f"训练IVF索引, 样本数: {n_samples}")
            self.index.train(features)
            self.is_trained = True

        elif self.index_type == 'IVFPQ':
            # 乘积量化
            m = 8  # 子向量数量
            quantizer = faiss.IndexFlatL2(self.dim)
            self.index = faiss.IndexIVFPQ(quantizer, self.dim, self.nlist, m, 8)

            logger.info(f"训练IVFPQ索引, 样本数: {n_samples}")
            self.index.train(features)
            self.is_trained = True

        else:
            raise ValueError(f"不支持的索引类型: {self.index_type}")

        # 添加特征
        self.index.add(features)
        logger.info(f"索引构建完成, 总特征数: {self.index.ntotal}")

        # 设置搜索参数
        if hasattr(self.index, 'nprobe'):
            self.index.nprobe = self.nprobe

    def add_features(self, features: np.ndarray):
        """
        添加特征到索引

        Args:
            features: 特征矩阵 (N, D)
        """
        if self.index is None:
            raise RuntimeError("索引未初始化")

        faiss.normalize_L2(features)
        self.index.add(features)
        logger.info(f"添加 {features.shape[0]} 个特征, 总数: {self.index.ntotal}")

    def search(self, query: np.ndarray, k: int = 1) -> Tuple[np.ndarray, np.ndarray]:
        """
        搜索最近邻

        Args:
            query: 查询向量 (N, D) 或 (D,)
            k: 返回最近邻数量

        Returns:
            Tuple[np.ndarray, np.ndarray]: (距离, 索引)
        """
        if self.index is None:
            raise RuntimeError("索引未初始化")

        # 确保query是2D
        if query.ndim == 1:
            query = query.reshape(1, -1)

        # 归一化
        faiss.normalize_L2(query)

        # 搜索
        distances, indices = self.index.search(query, k)

        return distances, indices

    def save_index(self, path: str):
        """
        保存索引

        Args:
            path: 保存路径
        """
        if self.index is None:
            raise RuntimeError("索引未初始化")

        Path(path).parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, path)
        logger.info(f"索引已保存: {path}")

    def load_index(self, path: str):
        """
        加载索引

        Args:
            path: 索引路径
        """
        self.index = faiss.read_index(path)
        self.is_trained = True
        logger.info(f"索引已加载: {path}, 特征数: {self.index.ntotal}")

    def get_index_size(self) -> int:
        """
        获取索引大小

        Returns:
            int: 索引中的特征数量
        """
        return self.index.ntotal if self.index else 0

    def clear(self):
        """清空索引"""
        self.index = None
        self.is_trained = False
        logger.info("索引已清空")
