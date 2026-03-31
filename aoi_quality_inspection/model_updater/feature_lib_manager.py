"""
特征库管理器
管理产品特征库的创建、更新和版本控制
"""
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import shutil
import logging

logger = logging.getLogger(__name__)


class FeatureLibManager:
    """特征库管理器"""

    def __init__(self, lib_root: str = "./data/feature_libs"):
        """
        初始化特征库管理器

        Args:
            lib_root: 特征库根目录
        """
        self.lib_root = Path(lib_root)
        self.lib_root.mkdir(parents=True, exist_ok=True)

        logger.info(f"特征库管理器初始化: {lib_root}")

    def create_lib(self, product_code: str, features: np.ndarray,
                   version: str = None) -> str:
        """
        创建特征库

        Args:
            product_code: 产品编码
            features: 特征矩阵 (N, D)
            version: 版本号

        Returns:
            str: 特征库路径
        """
        if version is None:
            version = datetime.now().strftime("v%Y%m%d_%H%M%S")

        # 创建产品目录
        product_dir = self.lib_root / product_code
        product_dir.mkdir(parents=True, exist_ok=True)

        # 特征库文件路径
        lib_path = product_dir / f"{version}.npy"

        # 保存特征
        np.save(str(lib_path), features)

        logger.info(f"特征库创建成功: {lib_path}, 特征数={len(features)}")
        return str(lib_path)

    def load_lib(self, lib_path: str) -> np.ndarray:
        """
        加载特征库

        Args:
            lib_path: 特征库路径

        Returns:
            np.ndarray: 特征矩阵
        """
        path = Path(lib_path)
        if not path.exists():
            raise FileNotFoundError(f"特征库不存在: {lib_path}")

        features = np.load(str(path))
        logger.debug(f"特征库加载成功: {lib_path}, 特征数={len(features)}")

        return features

    def add_features(self, lib_path: str, new_features: np.ndarray) -> str:
        """
        添加特征到现有特征库

        Args:
            lib_path: 现有特征库路径
            new_features: 新特征矩阵

        Returns:
            str: 新特征库路径
        """
        # 加载现有特征
        existing_features = self.load_lib(lib_path)

        # 合并特征
        combined_features = np.vstack([existing_features, new_features])

        # 生成新版本
        path = Path(lib_path)
        product_dir = path.parent
        new_version = datetime.now().strftime("v%Y%m%d_%H%M%S")
        new_lib_path = product_dir / f"{new_version}.npy"

        # 保存
        np.save(str(new_lib_path), combined_features)

        logger.info(f"特征添加成功: {new_lib_path}, 总特征数={len(combined_features)}")
        return str(new_lib_path)

    def rebuild_lib(self, product_code: str, features: np.ndarray,
                    version: str = None) -> str:
        """
        重建特征库

        Args:
            product_code: 产品编码
            features: 特征矩阵
            version: 版本号

        Returns:
            str: 新特征库路径
        """
        return self.create_lib(product_code, features, version)

    def get_lib_info(self, lib_path: str) -> Dict[str, Any]:
        """
        获取特征库信息

        Args:
            lib_path: 特征库路径

        Returns:
            Dict: 特征库信息
        """
        path = Path(lib_path)
        if not path.exists():
            return {}

        features = self.load_lib(lib_path)
        stat = path.stat()

        return {
            'path': str(lib_path),
            'version': path.stem,
            'num_features': len(features),
            'feature_dim': features.shape[1] if len(features) > 0 else 0,
            'file_size_mb': stat.st_size / (1024 * 1024),
            'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'modified_at': datetime.fromtimestamp(stat.st_mtime).isoformat()
        }

    def list_versions(self, product_code: str) -> List[Dict[str, Any]]:
        """
        列出产品的所有版本

        Args:
            product_code: 产品编码

        Returns:
            List[Dict]: 版本列表
        """
        product_dir = self.lib_root / product_code
        if not product_dir.exists():
            return []

        versions = []
        for lib_file in product_dir.glob("*.npy"):
            info = self.get_lib_info(str(lib_file))
            versions.append(info)

        # 按修改时间降序排列
        versions.sort(key=lambda x: x['modified_at'], reverse=True)

        return versions

    def delete_version(self, lib_path: str) -> bool:
        """
        删除特征库版本

        Args:
            lib_path: 特征库路径

        Returns:
            bool: 是否成功
        """
        path = Path(lib_path)
        if path.exists():
            path.unlink()
            logger.info(f"特征库已删除: {lib_path}")
            return True

        return False

    def cleanup_old_versions(self, product_code: str, keep_count: int = 10) -> int:
        """
        清理旧版本,保留最近的N个版本

        Args:
            product_code: 产品编码
            keep_count: 保留数量

        Returns:
            int: 删除的数量
        """
        versions = self.list_versions(product_code)

        if len(versions) <= keep_count:
            return 0

        # 删除旧版本
        delete_count = 0
        for version in versions[keep_count:]:
            if self.delete_version(version['path']):
                delete_count += 1

        logger.info(f"清理旧版本: 产品{product_code}, 删除{delete_count}个")
        return delete_count

    def get_active_version(self, product_code: str) -> Optional[str]:
        """
        获取产品的活跃版本(最新的)

        Args:
            product_code: 产品编码

        Returns:
            Optional[str]: 活跃版本路径
        """
        versions = self.list_versions(product_code)
        if versions:
            return versions[0]['path']

        return None

    def backup_lib(self, lib_path: str, backup_dir: str = None) -> str:
        """
        备份特征库

        Args:
            lib_path: 特征库路径
            backup_dir: 备份目录

        Returns:
            str: 备份路径
        """
        if backup_dir is None:
            backup_dir = self.lib_root / "backups"

        backup_path = Path(backup_dir)
        backup_path.mkdir(parents=True, exist_ok=True)

        src_path = Path(lib_path)
        backup_file = backup_path / f"{src_path.stem}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.npy"

        shutil.copy(str(src_path), str(backup_file))

        logger.info(f"特征库备份成功: {backup_file}")
        return str(backup_file)
