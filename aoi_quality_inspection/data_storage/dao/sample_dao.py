"""
样本数据访问对象
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from ..database import DatabaseManager
import logging

logger = logging.getLogger(__name__)


class SampleDAO:
    """样本数据访问对象"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def create(self, product_model_id: int, image_path: str, timestamp: datetime,
               aoi_result: int = None, ai_score: float = None,
               ai_label: int = None, confidence: float = None,
               is_uncertain: bool = False) -> int:
        """
        创建样本记录

        Args:
            product_model_id: 产品型号ID
            image_path: 图像路径
            timestamp: 时间戳
            aoi_result: AOI原始判定
            ai_score: AI异常分数
            ai_label: AI判定标签
            confidence: 置信度
            is_uncertain: 是否不确定样本

        Returns:
            int: 创建的记录ID
        """
        data = {
            'product_model_id': product_model_id,
            'image_path': image_path,
            'timestamp': timestamp.isoformat() if isinstance(timestamp, datetime) else timestamp,
            'aoi_result': aoi_result,
            'ai_score': ai_score,
            'ai_label': ai_label,
            'confidence': confidence,
            'is_uncertain': 1 if is_uncertain else 0
        }
        return self.db.insert('samples', data)

    def get_by_id(self, sample_id: int) -> Optional[Dict[str, Any]]:
        """按ID查询样本"""
        sql = "SELECT * FROM samples WHERE id = ?"
        return self.db.fetch_one(sql, (sample_id,))

    def get_pending_samples(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        获取待标注样本（不确定样本且未标注）

        Args:
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            List[Dict]: 待标注样本列表
        """
        sql = """
        SELECT s.*, pm.code as product_code, pm.name as product_name
        FROM samples s
        LEFT JOIN product_models pm ON s.product_model_id = pm.id
        LEFT JOIN annotations a ON s.id = a.sample_id
        WHERE s.is_uncertain = 1 AND a.id IS NULL
        ORDER BY s.timestamp DESC
        LIMIT ? OFFSET ?
        """
        return self.db.fetch_all(sql, (limit, offset))

    def get_labeled_samples(self, product_model_id: int = None,
                            start_time: datetime = None,
                            end_time: datetime = None,
                            limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取已标注样本

        Args:
            product_model_id: 产品型号ID（可选）
            start_time: 开始时间（可选）
            end_time: 结束时间（可选）
            limit: 返回数量限制

        Returns:
            List[Dict]: 已标注样本列表
        """
        sql = """
        SELECT s.*, a.label, a.defect_type, a.operator, a.annotated_at
        FROM samples s
        INNER JOIN annotations a ON s.id = a.sample_id
        WHERE 1=1
        """
        params = []

        if product_model_id:
            sql += " AND s.product_model_id = ?"
            params.append(product_model_id)

        if start_time:
            sql += " AND s.timestamp >= ?"
            params.append(start_time.isoformat())

        if end_time:
            sql += " AND s.timestamp <= ?"
            params.append(end_time.isoformat())

        sql += " ORDER BY a.annotated_at DESC LIMIT ?"
        params.append(limit)

        return self.db.fetch_all(sql, tuple(params))

    def list_by_status(self, ai_label: int = None, is_uncertain: bool = None,
                       product_model_id: int = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        按状态筛选样本

        Args:
            ai_label: AI判定标签（可选）
            is_uncertain: 是否不确定（可选）
            product_model_id: 产品型号ID（可选）
            limit: 返回数量限制

        Returns:
            List[Dict]: 样本列表
        """
        sql = "SELECT * FROM samples WHERE 1=1"
        params = []

        if ai_label is not None:
            sql += " AND ai_label = ?"
            params.append(ai_label)

        if is_uncertain is not None:
            sql += " AND is_uncertain = ?"
            params.append(1 if is_uncertain else 0)

        if product_model_id:
            sql += " AND product_model_id = ?"
            params.append(product_model_id)

        sql += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        return self.db.fetch_all(sql, tuple(params))

    def update_ai_result(self, sample_id: int, ai_score: float,
                         ai_label: int, confidence: float,
                         is_uncertain: bool) -> int:
        """
        更新AI推理结果

        Args:
            sample_id: 样本ID
            ai_score: AI异常分数
            ai_label: AI判定标签
            confidence: 置信度
            is_uncertain: 是否不确定

        Returns:
            int: 影响的行数
        """
        data = {
            'ai_score': ai_score,
            'ai_label': ai_label,
            'confidence': confidence,
            'is_uncertain': 1 if is_uncertain else 0
        }
        return self.db.update('samples', data, 'id = ?', (sample_id,))

    def count_by_label(self, product_model_id: int = None) -> Dict[str, int]:
        """
        统计各标签数量

        Args:
            product_model_id: 产品型号ID（可选）

        Returns:
            Dict: 各标签数量统计
        """
        sql = """
        SELECT
            COUNT(CASE WHEN ai_label = 0 THEN 1 END) as normal_count,
            COUNT(CASE WHEN ai_label = 1 THEN 1 END) as defect_count,
            COUNT(CASE WHEN is_uncertain = 1 THEN 1 END) as uncertain_count
        FROM samples
        WHERE 1=1
        """
        params = []

        if product_model_id:
            sql += " AND product_model_id = ?"
            params.append(product_model_id)

        result = self.db.fetch_one(sql, tuple(params) if params else None)
        return result if result else {'normal_count': 0, 'defect_count': 0, 'uncertain_count': 0}

    def delete_old_samples(self, days: int = 90) -> int:
        """
        删除旧样本

        Args:
            days: 保留天数

        Returns:
            int: 删除的行数
        """
        sql = """
        DELETE FROM samples
        WHERE datetime(timestamp) < datetime('now', ?)
        """
        return self.db.execute(sql, (f'-{days} days',))
