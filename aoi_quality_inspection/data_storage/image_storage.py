"""
图像存储管理模块
"""
import os
import shutil
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ImageStorageManager:
    """图像存储管理器"""

    def __init__(self, root_path: str = "./data/images"):
        """
        初始化图像存储管理器

        Args:
            root_path: 图像存储根目录
        """
        self.root_path = Path(root_path)
        self._ensure_root_dir()

    def _ensure_root_dir(self):
        """确保根目录存在"""
        self.root_path.mkdir(parents=True, exist_ok=True)

    def save_image(self, image_data: bytes, product_model: str,
                   filename: str = None, timestamp: datetime = None) -> str:
        """
        保存图像

        Args:
            image_data: 图像二进制数据
            product_model: 产品型号
            filename: 文件名（可选，自动生成）
            timestamp: 时间戳（可选，使用当前时间）

        Returns:
            str: 保存的图像路径
        """
        if timestamp is None:
            timestamp = datetime.now()

        # 按日期组织目录
        date_dir = timestamp.strftime("%Y%m%d")
        model_dir = product_model.replace(" ", "_")

        # 创建目录
        save_dir = self.root_path / date_dir / model_dir
        save_dir.mkdir(parents=True, exist_ok=True)

        # 生成文件名
        if filename is None:
            timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S_%f")
            filename = f"{timestamp_str}.jpg"

        # 保存文件
        save_path = save_dir / filename
        with open(save_path, 'wb') as f:
            f.write(image_data)

        logger.debug(f"图像已保存: {save_path}")
        return str(save_path)

    def get_image_path(self, relative_path: str) -> Path:
        """
        获取图像完整路径

        Args:
            relative_path: 相对路径

        Returns:
            Path: 完整路径
        """
        return self.root_path / relative_path

    def read_image(self, image_path: str) -> Optional[bytes]:
        """
        读取图像

        Args:
            image_path: 图像路径

        Returns:
            Optional[bytes]: 图像数据，不存在返回None
        """
        path = Path(image_path)
        if not path.is_absolute():
            path = self.root_path / image_path

        if path.exists():
            with open(path, 'rb') as f:
                return f.read()

        return None

    def delete_image(self, image_path: str) -> bool:
        """
        删除图像

        Args:
            image_path: 图像路径

        Returns:
            bool: 是否成功
        """
        path = Path(image_path)
        if not path.is_absolute():
            path = self.root_path / image_path

        if path.exists():
            path.unlink()
            logger.debug(f"图像已删除: {path}")
            return True

        return False

    def organize_by_date(self, source_dir: str) -> int:
        """
        按日期组织图像

        Args:
            source_dir: 源目录

        Returns:
            int: 移动的文件数量
        """
        source_path = Path(source_dir)
        if not source_path.exists():
            return 0

        count = 0
        for file_path in source_path.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                # 获取文件修改时间
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                date_dir = mtime.strftime("%Y%m%d")

                # 创建目标目录
                target_dir = self.root_path / date_dir
                target_dir.mkdir(parents=True, exist_ok=True)

                # 移动文件
                target_path = target_dir / file_path.name
                if not target_path.exists():
                    shutil.move(str(file_path), str(target_path))
                    count += 1

        logger.info(f"已组织 {count} 个图像文件")
        return count

    def check_storage_space(self) -> Tuple[int, int, float]:
        """
        检查存储空间

        Returns:
            Tuple[int, int, float]: (已用空间MB, 总空间MB, 使用率)
        """
        total_size = 0
        for file_path in self.root_path.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size

        # 获取磁盘总空间
        disk_usage = shutil.disk_usage(self.root_path)
        total_space = disk_usage.total
        used_space = disk_usage.used

        # 转换为MB
        total_size_mb = total_size / (1024 * 1024)
        total_space_mb = total_space / (1024 * 1024)

        usage_rate = total_size / total_space if total_space > 0 else 0

        return int(total_size_mb), int(total_space_mb), usage_rate

    def cleanup_old_images(self, days: int = 90, dry_run: bool = False) -> int:
        """
        清理旧图像

        Args:
            days: 保留天数
            dry_run: 是否仅模拟运行

        Returns:
            int: 删除的文件数量
        """
        cutoff_time = datetime.now().timestamp() - days * 24 * 3600
        count = 0

        for file_path in self.root_path.rglob("*"):
            if file_path.is_file():
                if file_path.stat().st_mtime < cutoff_time:
                    if not dry_run:
                        file_path.unlink()
                    count += 1

        logger.info(f"{'模拟: ' if dry_run else ''}清理了 {count} 个旧图像文件")
        return count

    def get_statistics(self) -> dict:
        """
        获取存储统计信息

        Returns:
            dict: 统计信息
        """
        total_files = 0
        total_size = 0
        by_date = {}
        by_model = {}

        for file_path in self.root_path.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                total_files += 1
                file_size = file_path.stat().st_size
                total_size += file_size

                # 按日期统计
                parts = file_path.relative_to(self.root_path).parts
                if len(parts) > 0:
                    date_str = parts[0]
                    by_date[date_str] = by_date.get(date_str, 0) + 1

                # 按型号统计
                if len(parts) > 1:
                    model = parts[1]
                    by_model[model] = by_model.get(model, 0) + 1

        return {
            'total_files': total_files,
            'total_size_mb': total_size / (1024 * 1024),
            'by_date': by_date,
            'by_model': by_model
        }
