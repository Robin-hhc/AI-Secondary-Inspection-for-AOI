"""
产品型号数据访问对象
"""
from typing import Optional, List, Dict, Any
from ..database import DatabaseManager
import logging

logger = logging.getLogger(__name__)


class ProductModelDAO:
    """产品型号数据访问对象"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def create(self, code: str, name: str, description: str = None,
               feature_lib_path: str = None, threshold: float = 0.5) -> int:
        """
        创建产品型号

        Args:
            code: 产品编码
            name: 产品名称
            description: 描述
            feature_lib_path: 特征库路径
            threshold: 判定阈值

        Returns:
            int: 创建的记录ID
        """
        data = {
            'code': code,
            'name': name,
            'description': description,
            'feature_lib_path': feature_lib_path,
            'threshold': threshold,
            'is_active': 0
        }
        return self.db.insert('product_models', data)

    def get_by_id(self, model_id: int) -> Optional[Dict[str, Any]]:
        """按ID查询产品型号"""
        sql = "SELECT * FROM product_models WHERE id = ?"
        return self.db.fetch_one(sql, (model_id,))

    def get_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """按编码查询产品型号"""
        sql = "SELECT * FROM product_models WHERE code = ?"
        return self.db.fetch_one(sql, (code,))

    def get_active(self) -> Optional[Dict[str, Any]]:
        """获取当前活跃的产品型号"""
        sql = "SELECT * FROM product_models WHERE is_active = 1 LIMIT 1"
        return self.db.fetch_one(sql)

    def list_all(self) -> List[Dict[str, Any]]:
        """列出所有产品型号"""
        sql = "SELECT * FROM product_models ORDER BY created_at DESC"
        return self.db.fetch_all(sql)

    def update(self, model_id: int, **kwargs) -> int:
        """
        更新产品型号

        Args:
            model_id: 产品型号ID
            **kwargs: 要更新的字段

        Returns:
            int: 影响的行数
        """
        if not kwargs:
            return 0

        # 添加更新时间
        kwargs['updated_at'] = 'CURRENT_TIMESTAMP'
        return self.db.update('product_models', kwargs, 'id = ?', (model_id,))

    def set_active(self, model_id: int) -> int:
        """
        设置活跃产品型号（同时取消其他型号的活跃状态）

        Args:
            model_id: 产品型号ID

        Returns:
            int: 影响的行数
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            # 先取消所有活跃状态
            cursor.execute("UPDATE product_models SET is_active = 0")
            # 设置指定型号为活跃
            cursor.execute("UPDATE product_models SET is_active = 1 WHERE id = ?", (model_id,))
            conn.commit()
            return cursor.rowcount

    def delete(self, model_id: int) -> int:
        """删除产品型号"""
        return self.db.delete('product_models', 'id = ?', (model_id,))

    def count(self) -> int:
        """统计产品型号数量"""
        return self.db.count('product_models')
