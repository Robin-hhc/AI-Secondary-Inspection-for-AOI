"""
用户数据访问对象
"""
from typing import Optional, Dict, Any
from datetime import datetime
from ..database import DatabaseManager
import logging
import hashlib

logger = logging.getLogger(__name__)


class UserDAO:
    """用户数据访问对象"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def _hash_password(self, password: str) -> str:
        """
        密码哈希

        Args:
            password: 明文密码

        Returns:
            str: 哈希后的密码
        """
        return hashlib.sha256(password.encode()).hexdigest()

    def create(self, username: str, password: str, role: str = 'operator') -> int:
        """
        创建用户

        Args:
            username: 用户名
            password: 密码
            role: 角色（admin/operator）

        Returns:
            int: 创建的记录ID
        """
        password_hash = self._hash_password(password)
        data = {
            'username': username,
            'password_hash': password_hash,
            'role': role,
            'is_active': 1
        }
        return self.db.insert('users', data)

    def get_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """按ID查询用户"""
        sql = "SELECT id, username, role, is_active, created_at, last_login FROM users WHERE id = ?"
        return self.db.fetch_one(sql, (user_id,))

    def get_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """按用户名查询用户"""
        sql = "SELECT * FROM users WHERE username = ?"
        return self.db.fetch_one(sql, (username,))

    def authenticate(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        用户认证

        Args:
            username: 用户名
            password: 密码

        Returns:
            Optional[Dict]: 认证成功返回用户信息，失败返回None
        """
        password_hash = self._hash_password(password)
        sql = """
        SELECT id, username, role, is_active
        FROM users
        WHERE username = ? AND password_hash = ? AND is_active = 1
        """
        user = self.db.fetch_one(sql, (username, password_hash))

        if user:
            # 更新最后登录时间
            self.db.execute(
                "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
                (user['id'],)
            )
            return user

        return None

    def update_password(self, user_id: int, new_password: str) -> int:
        """
        更新密码

        Args:
            user_id: 用户ID
            new_password: 新密码

        Returns:
            int: 影响的行数
        """
        password_hash = self._hash_password(new_password)
        data = {'password_hash': password_hash}
        return self.db.update('users', data, 'id = ?', (user_id,))

    def update_role(self, user_id: int, role: str) -> int:
        """
        更新角色

        Args:
            user_id: 用户ID
            role: 新角色

        Returns:
            int: 影响的行数
        """
        data = {'role': role}
        return self.db.update('users', data, 'id = ?', (user_id,))

    def set_active(self, user_id: int, is_active: bool) -> int:
        """
        设置用户状态

        Args:
            user_id: 用户ID
            is_active: 是否激活

        Returns:
            int: 影响的行数
        """
        data = {'is_active': 1 if is_active else 0}
        return self.db.update('users', data, 'id = ?', (user_id,))

    def delete(self, user_id: int) -> int:
        """删除用户"""
        return self.db.delete('users', 'id = ?', (user_id,))

    def list_all(self) -> list:
        """列出所有用户"""
        sql = "SELECT id, username, role, is_active, created_at, last_login FROM users ORDER BY created_at DESC"
        return self.db.fetch_all(sql)

    def count(self) -> int:
        """统计用户数量"""
        return self.db.count('users')
