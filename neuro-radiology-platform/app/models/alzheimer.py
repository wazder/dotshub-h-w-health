"""
3D ResNet Architecture for Alzheimer's Disease Classification.

Implements a 3D ResNet for volumetric analysis and classification
of Alzheimer's Disease stages (CN, MCI, AD).
"""

from typing import Any

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from app.config import settings
from app.models.base import BaseModel


class ResidualBlock3D(nn.Module):
    """3D Residual block with skip connection."""
    
    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        stride: int = 1,
        downsample: nn.Module | None = None,
    ) -> None:
        super().__init__()
        
        self.conv1 = nn.Conv3d(
            in_channels, out_channels, kernel_size=3,
            stride=stride, padding=1, bias=False
        )
        self.bn1 = nn.BatchNorm3d(out_channels)
        
        self.conv2 = nn.Conv3d(
            out_channels, out_channels, kernel_size=3,
            stride=1, padding=1, bias=False
        )
        self.bn2 = nn.BatchNorm3d(out_channels)
        
        self.relu = nn.ReLU(inplace=True)
        self.downsample = downsample
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        identity = x
        
        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)
        
        out = self.conv2(out)
        out = self.bn2(out)
        
        if self.downsample is not None:
            identity = self.downsample(x)
        
        out += identity
        out = self.relu(out)
        
        return out


class BottleneckBlock3D(nn.Module):
    """3D Bottleneck residual block for deeper networks."""
    
    expansion = 4
    
    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        stride: int = 1,
        downsample: nn.Module | None = None,
    ) -> None:
        super().__init__()
        
        self.conv1 = nn.Conv3d(in_channels, out_channels, kernel_size=1, bias=False)
        self.bn1 = nn.BatchNorm3d(out_channels)
        
        self.conv2 = nn.Conv3d(
            out_channels, out_channels, kernel_size=3,
            stride=stride, padding=1, bias=False
        )
        self.bn2 = nn.BatchNorm3d(out_channels)
        
        self.conv3 = nn.Conv3d(
            out_channels, out_channels * self.expansion,
            kernel_size=1, bias=False
        )
        self.bn3 = nn.BatchNorm3d(out_channels * self.expansion)
        
        self.relu = nn.ReLU(inplace=True)
        self.downsample = downsample
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        identity = x
        
        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)
        
        out = self.conv2(out)
        out = self.bn2(out)
        out = self.relu(out)
        
        out = self.conv3(out)
        out = self.bn3(out)
        
        if self.downsample is not None:
            identity = self.downsample(x)
        
        out += identity
        out = self.relu(out)
        
        return out


class AlzheimerClassifierModel(BaseModel):
    """
    3D ResNet for Alzheimer's Disease classification.
    
    Architecture:
    - Initial convolution and pooling
    - 4 residual layers with increasing channels
    - Global average pooling
    - Fully connected classifier
    
    Output classes:
    - 0: CN (Cognitively Normal)
    - 1: MCI (Mild Cognitive Impairment)
    - 2: AD (Alzheimer's Disease)
    
    Also outputs volumetric features for atrophy analysis.
    """
    
    def __init__(
        self,
        in_channels: int = 1,
        num_classes: int = 3,
        base_features: int = 64,
        layers: list[int] | None = None,
        use_bottleneck: bool = False,
        device: str = "cpu",
    ) -> None:
        """
        Initialize ResNet classifier for Alzheimer's detection.
        
        Args:
            in_channels: Number of input channels
            num_classes: Number of output classes
            base_features: Base number of features
            layers: Number of blocks in each layer [default: [2, 2, 2, 2]]
            use_bottleneck: Use bottleneck blocks for deeper network
            device: Device to run model on
        """
        super().__init__(device=device)
        
        self.in_channels = in_channels
        self.num_classes = num_classes
        self.base_features = base_features
        
        if layers is None:
            layers = [2, 2, 2, 2]  # ResNet-18 style
        
        self.layers_config = layers
        self.use_bottleneck = use_bottleneck
        
        block = BottleneckBlock3D if use_bottleneck else ResidualBlock3D
        expansion = 4 if use_bottleneck else 1
        
        self._current_channels = base_features
        
        # Initial convolution
        self.conv1 = nn.Conv3d(
            in_channels, base_features, kernel_size=7,
            stride=2, padding=3, bias=False
        )
        self.bn1 = nn.BatchNorm3d(base_features)
        self.relu = nn.ReLU(inplace=True)
        self.maxpool = nn.MaxPool3d(kernel_size=3, stride=2, padding=1)
        
        # Residual layers
        self.layer1 = self._make_layer(block, base_features, layers[0])
        self.layer2 = self._make_layer(block, base_features * 2, layers[1], stride=2)
        self.layer3 = self._make_layer(block, base_features * 4, layers[2], stride=2)
        self.layer4 = self._make_layer(block, base_features * 8, layers[3], stride=2)
        
        # Global pooling and classifier
        self.avgpool = nn.AdaptiveAvgPool3d((1, 1, 1))
        self.fc = nn.Linear(base_features * 8 * expansion, num_classes)
        
        # Additional head for atrophy score regression
        self.atrophy_head = nn.Sequential(
            nn.Linear(base_features * 8 * expansion, 64),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(64, 1),
            nn.Sigmoid(),
        )
        
        # Initialize weights
        self._init_weights()
        
        # Move to device
        self.to_device()
    
    def _make_layer(
        self,
        block: type[ResidualBlock3D] | type[BottleneckBlock3D],
        out_channels: int,
        num_blocks: int,
        stride: int = 1,
    ) -> nn.Sequential:
        """Create a residual layer with multiple blocks."""
        expansion = getattr(block, "expansion", 1)
        downsample = None
        
        if stride != 1 or self._current_channels != out_channels * expansion:
            downsample = nn.Sequential(
                nn.Conv3d(
                    self._current_channels, out_channels * expansion,
                    kernel_size=1, stride=stride, bias=False
                ),
                nn.BatchNorm3d(out_channels * expansion),
            )
        
        layers: list[nn.Module] = [
            block(self._current_channels, out_channels, stride, downsample)
        ]
        self._current_channels = out_channels * expansion
        
        for _ in range(1, num_blocks):
            layers.append(block(self._current_channels, out_channels))
        
        return nn.Sequential(*layers)
    
    def _init_weights(self) -> None:
        """Initialize network weights."""
        for m in self.modules():
            if isinstance(m, nn.Conv3d):
                nn.init.kaiming_normal_(m.weight, mode="fan_out", nonlinearity="relu")
            elif isinstance(m, nn.BatchNorm3d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0, 0.01)
                nn.init.constant_(m.bias, 0)
    
    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass through the ResNet.
        
        Args:
            x: Input tensor of shape (B, C, H, W, D)
            
        Returns:
            Tuple of (class_logits, atrophy_score)
        """
        # Initial layers
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.maxpool(x)
        
        # Residual layers
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)
        
        # Global pooling
        x = self.avgpool(x)
        features = torch.flatten(x, 1)
        
        # Classification head
        class_logits = self.fc(features)
        
        # Atrophy regression head
        atrophy_score = self.atrophy_head(features)
        
        return class_logits, atrophy_score
    
    @torch.no_grad()
    def predict(self, image: np.ndarray) -> dict[str, Any]:
        """
        Run inference on a preprocessed MRI image.
        
        Args:
            image: Preprocessed 3D MRI volume
            
        Returns:
            Dictionary containing:
            - classification: Predicted class label (CN, MCI, AD)
            - confidence: Confidence of prediction
            - probabilities: Per-class probabilities
            - atrophy_score: Estimated brain atrophy score (0-1)
            - brain_volume_mm3: Estimated brain volume
        """
        self.eval()
        
        # Prepare input
        x = self.prepare_input(image)
        
        # Forward pass
        logits, atrophy = self.forward(x)
        
        # Get probabilities
        probs = F.softmax(logits, dim=1)
        pred_class = torch.argmax(logits, dim=1)
        
        # Move to numpy
        probs_np = probs.cpu().numpy()[0]
        pred_class_np = int(pred_class.cpu().numpy()[0])
        atrophy_np = float(atrophy.cpu().numpy()[0, 0])
        
        # Map class index to label
        class_labels = ["CN", "MCI", "AD"]
        predicted_label = class_labels[pred_class_np]
        confidence = float(probs_np[pred_class_np])
        
        # Estimate brain volume (non-zero voxels)
        brain_volume = float(np.sum(image > 0))
        
        return {
            "classification": predicted_label,
            "confidence": confidence,
            "probabilities": {
                "CN": float(probs_np[0]),
                "MCI": float(probs_np[1]),
                "AD": float(probs_np[2]),
            },
            "atrophy_score": atrophy_np,
            "brain_volume_mm3": brain_volume,
        }
    
    def extract_features(self, image: np.ndarray) -> np.ndarray:
        """
        Extract deep features for visualization or analysis.
        
        Args:
            image: Preprocessed 3D MRI volume
            
        Returns:
            Feature vector
        """
        self.eval()
        x = self.prepare_input(image)
        
        with torch.no_grad():
            x = self.conv1(x)
            x = self.bn1(x)
            x = self.relu(x)
            x = self.maxpool(x)
            
            x = self.layer1(x)
            x = self.layer2(x)
            x = self.layer3(x)
            x = self.layer4(x)
            
            x = self.avgpool(x)
            features = torch.flatten(x, 1)
        
        return features.cpu().numpy()[0]
    
    def get_model_info(self) -> dict[str, Any]:
        """Get model architecture information."""
        info = super().get_model_info()
        info.update({
            "architecture": "3D ResNet",
            "in_channels": self.in_channels,
            "num_classes": self.num_classes,
            "base_features": self.base_features,
            "layers_config": self.layers_config,
            "use_bottleneck": self.use_bottleneck,
            "class_labels": ["CN", "MCI", "AD"],
        })
        return info


def create_alzheimer_model(
    weights_path: str | None = None,
    device: str | None = None,
    model_variant: str = "resnet18",
) -> AlzheimerClassifierModel:
    """
    Factory function to create and optionally load Alzheimer classifier.
    
    Args:
        weights_path: Optional path to pretrained weights
        device: Device to run model on
        model_variant: ResNet variant (resnet18, resnet34, resnet50)
        
    Returns:
        Initialized AlzheimerClassifierModel
    """
    if device is None:
        device = settings.model.device
    
    # Layer configurations for different variants
    layer_configs = {
        "resnet18": ([2, 2, 2, 2], False),
        "resnet34": ([3, 4, 6, 3], False),
        "resnet50": ([3, 4, 6, 3], True),
    }
    
    layers, use_bottleneck = layer_configs.get(model_variant, ([2, 2, 2, 2], False))
    
    model = AlzheimerClassifierModel(
        in_channels=1,
        num_classes=settings.model.num_classes_alzheimer,
        layers=layers,
        use_bottleneck=use_bottleneck,
        device=device,
    )
    
    if weights_path is not None:
        try:
            model.load_weights(weights_path)
        except FileNotFoundError:
            pass  # Use random weights for MVP
    
    return model
