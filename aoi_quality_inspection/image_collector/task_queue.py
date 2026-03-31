"""
任务队列
线程安全的任务队列实现
"""
import queue
from typing import Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class Task:
    """任务数据类"""
    task_id: str
    task_type: str
    data: Any
    priority: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)


class TaskQueue:
    """线程安全任务队列"""

    def __init__(self, max_size: int = 1000):
        """
        初始化任务队列

        Args:
            max_size: 队列最大容量
        """
        self.max_size = max_size
        self._queue = queue.PriorityQueue(maxsize=max_size)
        self._counter = 0

    def push(self, task: Task) -> bool:
        """
        入队

        Args:
            task: 任务对象

        Returns:
            bool: 是否成功
        """
        try:
            # 优先级队列按优先级排序，优先级相同时按时间排序
            # 使用负数使高优先级排在前面
            self._queue.put((-task.priority, self._counter, task), block=False)
            self._counter += 1
            logger.debug(f"任务入队: {task.task_id}, 优先级: {task.priority}")
            return True
        except queue.Full:
            logger.warning(f"任务队列已满，无法添加任务: {task.task_id}")
            return False

    def pop(self, timeout: float = None) -> Optional[Task]:
        """
        出队

        Args:
            timeout: 超时时间（秒）

        Returns:
            Optional[Task]: 任务对象，队列为空返回None
        """
        try:
            _, _, task = self._queue.get(block=True, timeout=timeout)
            logger.debug(f"任务出队: {task.task_id}")
            return task
        except queue.Empty:
            return None

    def peek(self) -> Optional[Task]:
        """
        查看队首任务（不出队）

        Returns:
            Optional[Task]: 队首任务
        """
        try:
            _, _, task = self._queue.queue[0]
            return task
        except IndexError:
            return None

    def size(self) -> int:
        """
        获取队列大小

        Returns:
            int: 队列大小
        """
        return self._queue.qsize()

    def is_empty(self) -> bool:
        """
        检查队列是否为空

        Returns:
            bool: 是否为空
        """
        return self._queue.empty()

    def is_full(self) -> bool:
        """
        检查队列是否已满

        Returns:
            bool: 是否已满
        """
        return self._queue.full()

    def clear(self):
        """清空队列"""
        while not self._queue.empty():
            try:
                self._queue.get(block=False)
            except queue.Empty:
                break
        logger.info("任务队列已清空")

    def get_all_tasks(self) -> list:
        """
        获取所有任务（不出队）

        Returns:
            list: 任务列表
        """
        return [task for _, _, task in list(self._queue.queue)]


class SimpleTaskQueue:
    """简单任务队列（FIFO）"""

    def __init__(self, max_size: int = 1000):
        """
        初始化简单任务队列

        Args:
            max_size: 队列最大容量
        """
        self.max_size = max_size
        self._queue = queue.Queue(maxsize=max_size)

    def push(self, task: Task) -> bool:
        """
        入队

        Args:
            task: 任务对象

        Returns:
            bool: 是否成功
        """
        try:
            self._queue.put(task, block=False)
            logger.debug(f"任务入队: {task.task_id}")
            return True
        except queue.Full:
            logger.warning(f"任务队列已满，无法添加任务: {task.task_id}")
            return False

    def pop(self, timeout: float = None) -> Optional[Task]:
        """
        出队

        Args:
            timeout: 超时时间（秒）

        Returns:
            Optional[Task]: 任务对象
        """
        try:
            task = self._queue.get(block=True, timeout=timeout)
            logger.debug(f"任务出队: {task.task_id}")
            return task
        except queue.Empty:
            return None

    def size(self) -> int:
        """获取队列大小"""
        return self._queue.qsize()

    def is_empty(self) -> bool:
        """检查队列是否为空"""
        return self._queue.empty()

    def clear(self):
        """清空队列"""
        while not self._queue.empty():
            try:
                self._queue.get(block=False)
            except queue.Empty:
                break
        logger.info("任务队列已清空")
