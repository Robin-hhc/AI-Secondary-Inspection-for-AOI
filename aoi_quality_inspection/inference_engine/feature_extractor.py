"""
PatchCore特征提取器
使用预训练的CNN提取图像特征
"""
import torch
import torch.nn as nn
import torchvision.models as models
import numpy as np
from typing import Tuple, List
import logging

logger = logging.getLogger(__name__)


class FeatureExtractor:
    """PatchCore特征提取器"""

    def __init__(self, backbone: str = 'wide_resnet50',
                 device: str = 'cuda',
                 layers: List[str] = None):
        """
        初始化特征提取器

        Args:
            backbone: 骨干网络类型
            device: 计算设备
            layers: 提取特征的层列表
        """
        self.device = torch.device(device if torch.cuda.is_available() else 'cpu')
        self.backbone = backbone
        self.layers = layers or ['layer2', 'layer3']

        # 加载预训练模型
        self.model = self._load_backbone()
        self.model.eval()

        logger.info(f"特征提取器已初始化: {backbone}, 设备: {self.device}")

    def _load_backbone(self) -> nn.Module:
        """加载骨干网络"""
        if self.backbone == 'wide_resnet50':
            model = models.wide_resnet50_2(pretrained=True)
        elif self.backbone == 'resnet50':
            model = models.resnet50(pretrained=True)
        elif self.backbone == 'resnet34':
            model = models.resnet34(pretrained=True)
        else:
            raise ValueError(f"不支持的骨干网络: {self.backbone}")

        # 移除最后的全连接层
        model = nn.Sequential(*list(model.children())[:-1])

        return model.to(self.device)

    def extract(self, image: np.ndarray) -> np.ndarray:
        """
        提取图像特征

        Args:
            image: 输入图像张量 (C, H, W)

        Returns:
            np.ndarray: 特征向量
        """
        # 转换为Tensor
        if isinstance(image, np.ndarray):
            tensor = torch.from_numpy(image).float()
        else:
            tensor = image

        # 添加batch维度
        if tensor.dim() == 3:
            tensor = tensor.unsqueeze(0)

        tensor = tensor.to(self.device)

        # 提取特征
        with torch.no_grad():
            features = self.model(tensor)

        # 展平特征
        features = features.squeeze().cpu().numpy()

        return features

    def extract_batch(self, images: np.ndarray) -> np.ndarray:
        """
        批量提取特征

        Args:
            images: 图像批次 (N, C, H, W)

        Returns:
            np.ndarray: 特征批次 (N, D)
        """
        if isinstance(images, np.ndarray):
            tensor = torch.from_numpy(images).float()
        else:
            tensor = images

        tensor = tensor.to(self.device)

        with torch.no_grad():
            features = self.model(tensor)

        features = features.squeeze().cpu().numpy()

        return features

    def get_patch_features(self, image: np.ndarray,
                           patch_size: int = 3) -> np.ndarray:
        """
        提取图像块特征

        Args:
            image: 输入图像张量 (C, H, W)
            patch_size: 图像块大小

        Returns:
            np.ndarray: 图像块特征
        """
        # 提取基础特征
        features = self.extract(image)

        # 这里简化处理，实际PatchCore会提取多尺度局部特征
        return features

    def get_feature_dim(self) -> int:
        """
        获取特征维度

        Returns:
            int: 特征维度
        """
        # 测试提取
        dummy_input = np.zeros((3, 256, 256), dtype=np.float32)
        features = self.extract(dummy_input)
        return features.shape[0]
