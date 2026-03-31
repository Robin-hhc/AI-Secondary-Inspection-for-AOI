"""
系统配置数据访问对象
"""
from typing import Optional, Any
from ..database import DatabaseManager
import logging
import json

logger = logging.getLogger(__name__)


class ConfigDAO:
    """系统配置数据访问对象"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键
            default: 默认值

        Returns:
            Any: 配置值
        """
        sql = "SELECT value FROM system_config WHERE key = ?"
        result = self.db.fetch_one(sql, (key,))

        if result:
            try:
                # 尝试解析JSON
                return json.loads(result['value'])
            except (json.JSONDecodeError, TypeError):
                return result['value']

        return default

    def set(self, key: str, value: Any, description: str = None) -> bool:
        """
        设置配置值

        Args:
            key: 配置键
            value: 配置值
            description: 描述

        Returns:
            bool: 是否成功
        """
        # 将值转换为JSON字符串
        if isinstance(value, (dict, list)):
            value_str = json.dumps(value)
        else:
            value_str = str(value)

        # 检查是否已存在
        existing = self.db.fetch_one(
            "SELECT key FROM system_config WHERE key = ?",
            (key,)
        )

        if existing:
            # 更新
            data = {'value': value_str, 'updated_at': 'CURRENT_TIMESTAMP'}
            if description:
                data['description'] = description
            self.db.update('system_config', data, 'key = ?', (key,))
        else:
            # 插入
            data = {
                'key': key,
                'value': value_str,
                'description': description
            }
            self.db.insert('system_config', data)

        return True

    def delete(self, key: str) -> int:
        """
        删除配置

        Args:
            key: 配置键

        Returns:
            int: 影响的行数
        """
        return self.db.delete('system_config', 'key = ?', (key,))

    def get_all(self) -> dict:
        """
        获取所有配置

        Returns:
            dict: 所有配置字典
        """
        sql = "SELECT key, value, description FROM system_config"
        rows = self.db.fetch_all(sql)

        config = {}
        for row in rows:
            try:
                config[row['key']] = json.loads(row['value'])
            except (json.JSONDecodeError, TypeError):
                config[row['key']] = row['value']

        return config

    def get_by_prefix(self, prefix: str) -> dict:
        """
        按前缀获取配置

        Args:
            prefix: 配置键前缀

        Returns:
            dict: 配置字典
        """
        sql = "SELECT key, value FROM system_config WHERE key LIKE ?"
        rows = self.db.fetch_all(sql, (f"{prefix}%",))

        config = {}
        for row in rows:
            # 移除前缀
            key = row['key'][len(prefix):]
            try:
                config[key] = json.loads(row['value'])
            except (json.JSONDecodeError, TypeError):
                config[key] = row['value']

        return config

    def batch_set(self, config_dict: dict) -> bool:
        """
        批量设置配置

        Args:
            config_dict: 配置字典

        Returns:
            bool: 是否成功
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            for key, value in config_dict.items():
                # 将值转换为JSON字符串
                if isinstance(value, (dict, list)):
                    value_str = json.dumps(value)
                else:
                    value_str = str(value)

                # 使用INSERT OR REPLACE
                cursor.execute(
                    "INSERT OR REPLACE INTO system_config (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
                    (key, value_str)
                )
            conn.commit()

        return True
