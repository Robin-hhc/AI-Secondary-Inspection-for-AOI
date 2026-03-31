"""
标注数据访问对象
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from ..database import DatabaseManager
import logging

logger = logging.getLogger(__name__)


class AnnotationDAO:
    """标注数据访问对象"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def create(self, sample_id: int, label: int, operator: str,
               defect_type: str = None, notes: str = None) -> int:
        """
        创建标注记录

        Args:
            sample_id: 样本ID
            label: 标注标签（0=正常，1=缺陷）
            operator: 操作员
            defect_type: 缺陷类型
            notes: 备注

        Returns:
            int: 创建的记录ID
        """
        data = {
            'sample_id': sample_id,
            'label': label,
            'defect_type': defect_type,
            'operator': operator,
            'notes': notes
        }
        return self.db.insert('annotations', data)

    def get_by_id(self, annotation_id: int) -> Optional[Dict[str, Any]]:
        """按ID查询标注"""
        sql = "SELECT * FROM annotations WHERE id = ?"
        return self.db.fetch_one(sql, (annotation_id,))

    def get_by_sample(self, sample_id: int) -> Optional[Dict[str, Any]]:
        """按样本ID查询标注"""
        sql = "SELECT * FROM annotations WHERE sample_id = ?"
        return self.db.fetch_one(sql, (sample_id,))

    def get_by_operator(self, operator: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        按操作员查询标注历史

        Args:
            operator: 操作员
            limit: 返回数量限制

        Returns:
            List[Dict]: 标注列表
        """
        sql = """
        SELECT a.*, s.image_path, s.timestamp, pm.code as product_code
        FROM annotations a
        INNER JOIN samples s ON a.sample_id = s.id
        INNER JOIN product_models pm ON s.product_model_id = pm.id
        WHERE a.operator = ?
        ORDER BY a.annotated_at DESC
        LIMIT ?
        """
        return self.db.fetch_all(sql, (operator, limit))

    def list_by_time_range(self, start_time: datetime, end_time: datetime,
                           product_model_id: int = None) -> List[Dict[str, Any]]:
        """
        按时间范围查询标注

        Args:
            start_time: 开始时间
            end_time: 结束时间
            product_model_id: 产品型号ID（可选）

        Returns:
            List[Dict]: 标注列表
        """
        sql = """
        SELECT a.*, s.image_path, s.product_model_id
        FROM annotations a
        INNER JOIN samples s ON a.sample_id = s.id
        WHERE a.annotated_at >= ? AND a.annotated_at <= ?
        """
        params = [start_time.isoformat(), end_time.isoformat()]

        if product_model_id:
            sql += " AND s.product_model_id = ?"
            params.append(product_model_id)

        sql += " ORDER BY a.annotated_at DESC"
        return self.db.fetch_all(sql, tuple(params))

    def update(self, annotation_id: int, label: int = None,
               defect_type: str = None, notes: str = None) -> int:
        """
        更新标注

        Args:
            annotation_id: 标注ID
            label: 标注标签
            defect_type: 缺陷类型
            notes: 备注

        Returns:
            int: 影响的行数
        """
        data = {}
        if label is not None:
            data['label'] = label
        if defect_type is not None:
            data['defect_type'] = defect_type
        if notes is not None:
            data['notes'] = notes

        if not data:
            return 0

        return self.db.update('annotations', data, 'id = ?', (annotation_id,))

    def delete(self, annotation_id: int) -> int:
        """删除标注"""
        return self.db.delete('annotations', 'id = ?', (annotation_id,))

    def count_by_label(self, product_model_id: int = None,
                       start_time: datetime = None,
                       end_time: datetime = None) -> Dict[str, int]:
        """
        统计各标签标注数量

        Args:
            product_model_id: 产品型号ID（可选）
            start_time: 开始时间（可选）
            end_time: 结束时间（可选）

        Returns:
            Dict: 各标签数量统计
        """
        sql = """
        SELECT
            COUNT(CASE WHEN a.label = 0 THEN 1 END) as normal_count,
            COUNT(CASE WHEN a.label = 1 THEN 1 END) as defect_count,
            COUNT(*) as total_count
        FROM annotations a
        INNER JOIN samples s ON a.sample_id = s.id
        WHERE 1=1
        """
        params = []

        if product_model_id:
            sql += " AND s.product_model_id = ?"
            params.append(product_model_id)

        if start_time:
            sql += " AND a.annotated_at >= ?"
            params.append(start_time.isoformat())

        if end_time:
            sql += " AND a.annotated_at <= ?"
            params.append(end_time.isoformat())

        result = self.db.fetch_one(sql, tuple(params) if params else None)
        return result if result else {'normal_count': 0, 'defect_count': 0, 'total_count': 0}

    def get_statistics(self, product_model_id: int = None) -> Dict[str, Any]:
        """
        获取标注统计信息

        Args:
            product_model_id: 产品型号ID（可选）

        Returns:
            Dict: 统计信息
        """
        # 总体统计
        counts = self.count_by_label(product_model_id)

        # 操作员统计
        sql = """
        SELECT operator, COUNT(*) as count
        FROM annotations a
        INNER JOIN samples s ON a.sample_id = s.id
        WHERE 1=1
        """
        params = []

        if product_model_id:
            sql += " AND s.product_model_id = ?"
            params.append(product_model_id)

        sql += " GROUP BY operator ORDER BY count DESC LIMIT 10"
        operator_stats = self.db.fetch_all(sql, tuple(params) if params else None)

        # 缺陷类型统计
        sql = """
        SELECT defect_type, COUNT(*) as count
        FROM annotations a
        INNER JOIN samples s ON a.sample_id = s.id
        WHERE a.label = 1
        """
        params = []

        if product_model_id:
            sql += " AND s.product_model_id = ?"
            params.append(product_model_id)

        sql += " GROUP BY defect_type ORDER BY count DESC"
        defect_stats = self.db.fetch_all(sql, tuple(params) if params else None)

        return {
            'total': counts,
            'by_operator': operator_stats,
            'by_defect_type': defect_stats
        }
