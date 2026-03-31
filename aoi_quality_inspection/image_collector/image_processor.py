"""
图像预处理器
实现图像的缩放、归一化、增强等预处理操作
"""
import cv2
import numpy as np
from pathlib import Path
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class ImageProcessor:
    """图像预处理器"""

    def __init__(self, target_size: Tuple[int, int] = (256, 256),
                 normalize_mean: Tuple[float, float, float] = (0.485, 0.456, 0.406),
                 normalize_std: Tuple[float, float, float] = (0.229, 0.224, 0.225),
                 enhance: bool = False):
        """
        初始化图像预处理器

        Args:
            target_size: 目标尺寸 (width, height)
            normalize_mean: 归一化均值
            normalize_std: 归一化标准差
            enhance: 是否启用图像增强
        """
        self.target_size = target_size
        self.normalize_mean = np.array(normalize_mean).reshape(1, 1, 3)
        self.normalize_std = np.array(normalize_std).reshape(1, 1, 3)
        self.enhance = enhance

    def process(self, image: np.ndarray) -> np.ndarray:
        """
        执行完整预处理流程

        Args:
            image: 输入图像 (BGR格式)

        Returns:
            np.ndarray: 预处理后的图像张量 (C, H, W)
        """
        # 图像增强（可选）
        if self.enhance:
            image = self._enhance(image)

        # 等比例缩放填充
        image = self.resize_with_padding(image, self.target_size)

        # 归一化
        image = self.normalize(image)

        # 转换为张量格式 (H, W, C) -> (C, H, W)
        image = self.convert_to_tensor(image)

        return image

    def resize_with_padding(self, image: np.ndarray, target_size: Tuple[int, int]) -> np.ndarray:
        """
        等比例缩放并填充

        Args:
            image: 输入图像
            target_size: 目标尺寸 (width, height)

        Returns:
            np.ndarray: 缩放填充后的图像
        """
        h, w = image.shape[:2]
        target_w, target_h = target_size

        # 计算缩放比例
        scale = min(target_w / w, target_h / h)
        new_w = int(w * scale)
        new_h = int(h * scale)

        # 缩放图像
        resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

        # 创建目标图像（灰色填充）
        padded = np.full((target_h, target_w, 3), 128, dtype=np.uint8)

        # 计算填充位置
        x_offset = (target_w - new_w) // 2
        y_offset = (target_h - new_h) // 2

        # 填充图像
        padded[y_offset:y_offset + new_h, x_offset:x_offset + new_w] = resized

        return padded

    def normalize(self, image: np.ndarray) -> np.ndarray:
        """
        归一化处理

        Args:
            image: 输入图像 (0-255)

        Returns:
            np.ndarray: 归一化后的图像
        """
        # 转换为float32并归一化到[0, 1]
        image = image.astype(np.float32) / 255.0

        # 标准化
        image = (image - self.normalize_mean) / self.normalize_std

        return image

    def _enhance(self, image: np.ndarray) -> np.ndarray:
        """
        图像增强

        Args:
            image: 输入图像

        Returns:
            np.ndarray: 增强后的图像
        """
        # 直方图均衡化
        if len(image.shape) == 3:
            # 转换到YUV空间
            yuv = cv2.cvtColor(image, cv2.COLOR_BGR2YUV)
            # 对Y通道进行直方图均衡化
            yuv[:, :, 0] = cv2.equalizeHist(yuv[:, :, 0])
            # 转换回BGR
            image = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR)

        return image

    def convert_to_tensor(self, image: np.ndarray) -> np.ndarray:
        """
        转换为张量格式

        Args:
            image: 输入图像 (H, W, C)

        Returns:
            np.ndarray: 张量格式 (C, H, W)
        """
        # HWC -> CHW
        return np.transpose(image, (2, 0, 1))

    def load_image(self, image_path: str) -> Optional[np.ndarray]:
        """
        加载图像

        Args:
            image_path: 图像路径

        Returns:
            Optional[np.ndarray]: 图像数组，失败返回None
        """
        path = Path(image_path)
        if not path.exists():
            logger.error(f"图像文件不存在: {image_path}")
            return None

        image = cv2.imread(str(path))
        if image is None:
            logger.error(f"无法读取图像: {image_path}")
            return None

        return image

    def process_from_file(self, image_path: str) -> Optional[np.ndarray]:
        """
        从文件加载并预处理图像

        Args:
            image_path: 图像路径

        Returns:
            Optional[np.ndarray]: 预处理后的张量，失败返回None
        """
        image = self.load_image(image_path)
        if image is None:
            return None

        return self.process(image)

    def batch_process(self, images: list) -> np.ndarray:
        """
        批量预处理

        Args:
            images: 图像列表

        Returns:
            np.ndarray: 批量张量 (N, C, H, W)
        """
        processed = []
        for image in images:
            if isinstance(image, str):
                # 文件路径
                tensor = self.process_from_file(image)
            else:
                # 图像数组
                tensor = self.process(image)

            if tensor is not None:
                processed.append(tensor)

        return np.stack(processed) if processed else None
