"""
文件监控服务
监控指定目录的新增文件
"""
import time
from pathlib import Path
from typing import Callable, List, Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent
import logging

logger = logging.getLogger(__name__)


class ImageFileHandler(FileSystemEventHandler):
    """图像文件事件处理器"""

    def __init__(self, callback: Callable, file_patterns: List[str] = None):
        """
        初始化事件处理器

        Args:
            callback: 文件创建回调函数
            file_patterns: 文件模式列表（如['*.jpg', '*.png']）
        """
        super().__init__()
        self.callback = callback
        self.file_patterns = file_patterns or ['*.jpg', '*.jpeg', '*.png']
        self.processed_files: Set[str] = set()

    def on_created(self, event):
        """文件创建事件"""
        if isinstance(event, FileCreatedEvent) and not event.is_directory:
            file_path = Path(event.src_path)

            # 检查文件模式
            if self._match_pattern(file_path):
                # 避免重复处理
                if str(file_path) not in self.processed_files:
                    self.processed_files.add(str(file_path))
                    logger.info(f"检测到新文件: {file_path}")

                    try:
                        self.callback(file_path)
                    except Exception as e:
                        logger.error(f"处理文件失败 {file_path}: {e}")

    def _match_pattern(self, file_path: Path) -> bool:
        """检查文件是否匹配模式"""
        for pattern in self.file_patterns:
            if file_path.match(pattern):
                return True
        return False


class FileWatcher:
    """文件监控器"""

    def __init__(self, watch_paths: List[str], callback: Callable,
                 file_patterns: List[str] = None, check_interval: float = 1.0):
        """
        初始化文件监控器

        Args:
            watch_paths: 监控路径列表
            callback: 文件创建回调函数
            file_patterns: 文件模式列表
            check_interval: 检查间隔（秒）
        """
        self.watch_paths = [Path(p) for p in watch_paths]
        self.callback = callback
        self.file_patterns = file_patterns
        self.check_interval = check_interval

        self.observer = Observer()
        self.is_running = False

    def start(self):
        """启动监控"""
        if self.is_running:
            logger.warning("文件监控器已在运行")
            return

        # 创建事件处理器
        handler = ImageFileHandler(self.callback, self.file_patterns)

        # 为每个监控路径添加观察者
        for watch_path in self.watch_paths:
            if watch_path.exists():
                self.observer.schedule(handler, str(watch_path), recursive=True)
                logger.info(f"开始监控目录: {watch_path}")
            else:
                logger.warning(f"监控目录不存在: {watch_path}")

        # 启动观察者
        self.observer.start()
        self.is_running = True
        logger.info("文件监控器已启动")

    def stop(self):
        """停止监控"""
        if not self.is_running:
            return

        self.observer.stop()
        self.observer.join()
        self.is_running = False
        logger.info("文件监控器已停止")

    def __enter__(self):
        """上下文管理器入口"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.stop()


class SimpleFileWatcher:
    """简单文件监控器（轮询方式）"""

    def __init__(self, watch_paths: List[str], callback: Callable,
                 file_patterns: List[str] = None, check_interval: float = 1.0):
        """
        初始化简单文件监控器

        Args:
            watch_paths: 监控路径列表
            callback: 文件创建回调函数
            file_patterns: 文件模式列表
            check_interval: 检查间隔（秒）
        """
        self.watch_paths = [Path(p) for p in watch_paths]
        self.callback = callback
        self.file_patterns = file_patterns or ['*.jpg', '*.jpeg', '*.png']
        self.check_interval = check_interval

        self.is_running = False
        self.existing_files: Set[str] = set()

    def start(self):
        """启动监控"""
        if self.is_running:
            logger.warning("文件监控器已在运行")
            return

        # 初始化已存在文件列表
        for watch_path in self.watch_paths:
            if watch_path.exists():
                for pattern in self.file_patterns:
                    for file_path in watch_path.rglob(pattern):
                        self.existing_files.add(str(file_path))

        self.is_running = True
        logger.info(f"简单文件监控器已启动，已记录 {len(self.existing_files)} 个现有文件")

        # 开始轮询
        self._poll_loop()

    def stop(self):
        """停止监控"""
        self.is_running = False
        logger.info("简单文件监控器已停止")

    def _poll_loop(self):
        """轮询循环"""
        while self.is_running:
            try:
                self._check_new_files()
                time.sleep(self.check_interval)
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"轮询异常: {e}")
                time.sleep(self.check_interval)

    def _check_new_files(self):
        """检查新文件"""
        for watch_path in self.watch_paths:
            if not watch_path.exists():
                continue

            for pattern in self.file_patterns:
                for file_path in watch_path.rglob(pattern):
                    file_str = str(file_path)

                    if file_str not in self.existing_files:
                        self.existing_files.add(file_str)
                        logger.info(f"检测到新文件: {file_path}")

                        try:
                            self.callback(file_path)
                        except Exception as e:
                            logger.error(f"处理文件失败 {file_path}: {e}")

    def __enter__(self):
        """上下文管理器入口"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.stop()
