"""
模型版本数据访问对象
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from ..database import DatabaseManager
import logging

logger = logging.getLogger(__name__)


class ModelVersionDAO:
    """模型版本数据访问对象"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def create(self, product_model_id: int, version: str,
               feature_lib_path: str, num_samples: int = 0,
               accuracy: float = None) -> int:
        """
        创建模型版本记录

        Args:
            product_model_id: 产品型号ID
            version: 版本号
            feature_lib_path: 特征库路径
            num_samples: 样本数量
            accuracy: 准确率

        Returns:
            int: 创建的记录ID
        """
        data = {
            'product_model_id': product_model_id,
            'version': version,
            'feature_lib_path': feature_lib_path,
            'num_samples': num_samples,
            'accuracy': accuracy,
            'is_active': 0
        }
        return self.db.insert('model_versions', data)

    def get_by_id(self, version_id: int) -> Optional[Dict[str, Any]]:
        """按ID查询版本"""
        sql = "SELECT * FROM model_versions WHERE id = ?"
        return self.db.fetch_one(sql, (version_id,))

    def get_active(self, product_model_id: int) -> Optional[Dict[str, Any]]:
        """
        获取产品型号的当前活跃版本

        Args:
            product_model_id: 产品型号ID

        Returns:
            Optional[Dict]: 活跃版本信息
        """
        sql = """
        SELECT * FROM model_versions
        WHERE product_model_id = ? AND is_active = 1
        LIMIT 1
        """
        return self.db.fetch_one(sql, (product_model_id,))

    def list_all(self, product_model_id: int = None, limit: int = 20) -> List[Dict[str, Any]]:
        """
        列出所有版本

        Args:
            product_model_id: 产品型号ID（可选）
            limit: 返回数量限制

        Returns:
            List[Dict]: 版本列表
        """
        sql = "SELECT * FROM model_versions"
        params = []

        if product_model_id:
            sql += " WHERE product_model_id = ?"
            params.append(product_model_id)

        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        return self.db.fetch_all(sql, tuple(params))

    def set_active(self, version_id: int) -> int:
        """
        设置活跃版本（同时取消该产品其他版本的活跃状态）

        Args:
            version_id: 版本ID

        Returns:
            int: 影响的行数
        """
        # 先获取版本信息
        version = self.get_by_id(version_id)
        if not version:
            return 0

        product_model_id = version['product_model_id']

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            # 取消该产品所有版本的活跃状态
            cursor.execute(
                "UPDATE model_versions SET is_active = 0 WHERE product_model_id = ?",
                (product_model_id,)
            )
            # 设置指定版本为活跃
            cursor.execute(
                "UPDATE model_versions SET is_active = 1 WHERE id = ?",
                (version_id,)
            )
            conn.commit()
            return cursor.rowcount

    def update_accuracy(self, version_id: int, accuracy: float) -> int:
        """
        更新版本准确率

        Args:
            version_id: 版本ID
            accuracy: 准确率

        Returns:
            int: 影响的行数
        """
        data = {'accuracy': accuracy}
        return self.db.update('model_versions', data, 'id = ?', (version_id,))

    def update_num_samples(self, version_id: int, num_samples: int) -> int:
        """
        更新样本数量

        Args:
            version_id: 版本ID
            num_samples: 样本数量

        Returns:
            int: 影响的行数
        """
        data = {'num_samples': num_samples}
        return self.db.update('model_versions', data, 'id = ?', (version_id,))

    def delete(self, version_id: int) -> int:
        """删除版本"""
        return self.db.delete('model_versions', 'id = ?', (version_id,))

    def delete_old_versions(self, product_model_id: int, keep_count: int = 10) -> int:
        """
        删除旧版本，保留最近的N个版本

        Args:
            product_model_id: 产品型号ID
            keep_count: 保留数量

        Returns:
            int: 删除的行数
        """
        sql = """
        DELETE FROM model_versions
        WHERE product_model_id = ?
        AND id NOT IN (
            SELECT id FROM model_versions
            WHERE product_model_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        )
        """
        return self.db.execute(sql, (product_model_id, product_model_id, keep_count))

    def count(self, product_model_id: int = None) -> int:
        """
        统计版本数量

        Args:
            product_model_id: 产品型号ID（可选）

        Returns:
            int: 版本数量
        """
        if product_model_id:
            return self.db.count('model_versions', 'product_model_id = ?', (product_model_id,))
        else:
            return self.db.count('model_versions')
