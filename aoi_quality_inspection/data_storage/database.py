"""
数据库管理模块
提供数据库连接、初始化和基础操作功能
"""
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """数据库管理器"""

    def __init__(self, db_path: str = "./data/aoi_system.db"):
        """
        初始化数据库管理器

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._ensure_db_dir()

    def _ensure_db_dir(self):
        """确保数据库目录存在"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

    def init_db(self, schema_path: str = None):
        """
        初始化数据库，创建所有表

        Args:
            schema_path: SQL脚本路径，默认使用内置schema.sql
        """
        if schema_path is None:
            schema_path = Path(__file__).parent / "schema.sql"

        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()

        with self.get_connection() as conn:
            conn.executescript(schema_sql)
            conn.commit()
            logger.info(f"数据库初始化完成: {self.db_path}")

    @contextmanager
    def get_connection(self):
        """
        获取数据库连接（上下文管理器）

        Yields:
            sqlite3.Connection: 数据库连接对象
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 支持字典式访问
        try:
            yield conn
        except Exception as e:
            conn.rollback()
            logger.error(f"数据库操作异常: {e}")
            raise
        finally:
            conn.close()

    def execute(self, sql: str, params: tuple = None) -> int:
        """
        执行SQL语句

        Args:
            sql: SQL语句
            params: 参数元组

        Returns:
            int: 影响的行数
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            conn.commit()
            return cursor.rowcount

    def fetch_one(self, sql: str, params: tuple = None) -> Optional[Dict[str, Any]]:
        """
        查询单条记录

        Args:
            sql: SQL语句
            params: 参数元组

        Returns:
            Optional[Dict]: 查询结果字典，无结果返回None
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            row = cursor.fetchone()
            return dict(row) if row else None

    def fetch_all(self, sql: str, params: tuple = None) -> List[Dict[str, Any]]:
        """
        查询多条记录

        Args:
            sql: SQL语句
            params: 参数元组

        Returns:
            List[Dict]: 查询结果列表
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def insert(self, table: str, data: Dict[str, Any]) -> int:
        """
        插入记录

        Args:
            table: 表名
            data: 数据字典

        Returns:
            int: 插入记录的ID
        """
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, tuple(data.values()))
            conn.commit()
            return cursor.lastrowid

    def update(self, table: str, data: Dict[str, Any], where: str, where_params: tuple = None) -> int:
        """
        更新记录

        Args:
            table: 表名
            data: 更新数据字典
            where: WHERE条件语句
            where_params: WHERE条件参数

        Returns:
            int: 影响的行数
        """
        set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
        sql = f"UPDATE {table} SET {set_clause} WHERE {where}"
        params = tuple(data.values()) + (where_params if where_params else ())

        return self.execute(sql, params)

    def delete(self, table: str, where: str, params: tuple = None) -> int:
        """
        删除记录

        Args:
            table: 表名
            where: WHERE条件语句
            params: WHERE条件参数

        Returns:
            int: 影响的行数
        """
        sql = f"DELETE FROM {table} WHERE {where}"
        return self.execute(sql, params)

    def count(self, table: str, where: str = None, params: tuple = None) -> int:
        """
        统计记录数

        Args:
            table: 表名
            where: WHERE条件语句
            params: WHERE条件参数

        Returns:
            int: 记录数
        """
        sql = f"SELECT COUNT(*) as count FROM {table}"
        if where:
            sql += f" WHERE {where}"

        result = self.fetch_one(sql, params)
        return result['count'] if result else 0

    def table_exists(self, table_name: str) -> bool:
        """
        检查表是否存在

        Args:
            table_name: 表名

        Returns:
            bool: 表是否存在
        """
        sql = """
        SELECT name FROM sqlite_master
        WHERE type='table' AND name=?
        """
        result = self.fetch_one(sql, (table_name,))
        return result is not None
