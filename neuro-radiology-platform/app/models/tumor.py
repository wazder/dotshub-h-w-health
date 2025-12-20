"""
3D U-Net Architecture for Brain Tumor Segmentation.

Implements a 3D U-Net with encoder-decoder structure for 
multi-class segmentation of brain tumors (BraTS-style).
"""

from typing import Any

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from app.config import settings
from app.models.base import BaseModel


class ConvBlock3D(nn.Module):
    """3D Convolutional block with BatchNorm and ReLU."""
    
    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int = 3,
        padding: int = 1,
        use_batch_norm: bool = True,
    ) -> None:
        super().__init__()
        
        layers: list[nn.Module] = [
            nn.Conv3d(in_channels, out_channels, kernel_size, padding=padding),
        ]
        
        if use_batch_norm:
            layers.append(nn.BatchNorm3d(out_channels))
        
        layers.append(nn.ReLU(inplace=True))
        layers.append(nn.Conv3d(out_channels, out_channels, kernel_size, padding=padding))
        
        if use_batch_norm:
            layers.append(nn.BatchNorm3d(out_channels))
        
        layers.append(nn.ReLU(inplace=True))
        
        self.block = nn.Sequential(*layers)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.block(x)


class EncoderBlock(nn.Module):
    """Encoder block with convolution and max pooling."""
    
    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        pool: bool = True,
    ) -> None:
        super().__init__()
        
        self.conv = ConvBlock3D(in_channels, out_channels)
        self.pool = nn.MaxPool3d(kernel_size=2, stride=2) if pool else None
    
    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass returning both pre-pool and post-pool features.
        
        Returns:
            Tuple of (skip_connection, pooled_output)
        """
        features = self.conv(x)
        
        if self.pool is not None:
            pooled = self.pool(features)
        else:
            pooled = features
        
        return features, pooled


class DecoderBlock(nn.Module):
    """Decoder block with upsampling and skip connection."""
    
    def __init__(
        self,
        in_channels: int,
        skip_channels: int,
        out_channels: int,
        use_transpose: bool = True,
    ) -> None:
        super().__init__()
        
        if use_transpose:
            self.upsample = nn.ConvTranspose3d(
                in_channels, in_channels, kernel_size=2, stride=2
            )
        else:
            self.upsample = nn.Upsample(
                scale_factor=2, mode="trilinear", align_corners=True
            )
        
        self.conv = ConvBlock3D(in_channels + skip_channels, out_channels)
    
    def forward(
        self,
        x: torch.Tensor,
        skip: torch.Tensor,
    ) -> torch.Tensor:
        """Forward pass with skip connection concatenation."""
        x = self.upsample(x)
        
        # Handle size mismatch
        if x.shape[2:] != skip.shape[2:]:
            x = F.interpolate(x, size=skip.shape[2:], mode="trilinear", align_corners=True)
        
        x = torch.cat([x, skip], dim=1)
        return self.conv(x)


class TumorSegmentationModel(BaseModel):
    """
    3D U-Net for multi-class brain tumor segmentation.
    
    Architecture:
    - 4 encoder blocks (downsampling path)
    - 1 bottleneck block
    - 4 decoder blocks (upsampling path)
    - Output: Multi-class segmentation map
    
    Output classes (BraTS-style):
    - 0: Background
    - 1: Necrotic/Non-Enhancing Tumor Core
    - 2: Peritumoral Edema
    - 3: GD-Enhancing Tumor
    """
    
    def __init__(
        self,
        in_channels: int = 1,
        num_classes: int = 4,
        base_features: int = 32,
        device: str = "cpu",
    ) -> None:
        """
        Initialize U-Net for tumor segmentation.
        
        Args:
            in_channels: Number of input channels (1 for single modality)
            num_classes: Number of output segmentation classes
            base_features: Base number of features (doubled each encoder level)
            device: Device to run model on
        """
        super().__init__(device=device)
        
        self.in_channels = in_channels
        self.num_classes = num_classes
        self.base_features = base_features
        
        # Feature sizes at each level
        f = base_features
        
        # Encoder path
        self.enc1 = EncoderBlock(in_channels, f)
        self.enc2 = EncoderBlock(f, f * 2)
        self.enc3 = EncoderBlock(f * 2, f * 4)
        self.enc4 = EncoderBlock(f * 4, f * 8)
        
        # Bottleneck
        self.bottleneck = ConvBlock3D(f * 8, f * 16)
        
        # Decoder path
        self.dec4 = DecoderBlock(f * 16, f * 8, f * 8)
        self.dec3 = DecoderBlock(f * 8, f * 4, f * 4)
        self.dec2 = DecoderBlock(f * 4, f * 2, f * 2)
        self.dec1 = DecoderBlock(f * 2, f, f)
        
        # Output layer
        self.output = nn.Conv3d(f, num_classes, kernel_size=1)
        
        # Move to device
        self.to_device()
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through the U-Net.
        
        Args:
            x: Input tensor of shape (B, C, H, W, D)
            
        Returns:
            Segmentation logits of shape (B, num_classes, H, W, D)
        """
        # Encoder
        skip1, x = self.enc1(x)
        skip2, x = self.enc2(x)
        skip3, x = self.enc3(x)
        skip4, x = self.enc4(x)
        
        # Bottleneck
        x = self.bottleneck(x)
        
        # Decoder with skip connections
        x = self.dec4(x, skip4)
        x = self.dec3(x, skip3)
        x = self.dec2(x, skip2)
        x = self.dec1(x, skip1)
        
        # Output
        return self.output(x)
    
    @torch.no_grad()
    def predict(self, image: np.ndarray) -> dict[str, Any]:
        """
        Run inference on a preprocessed MRI image.
        
        Args:
            image: Preprocessed 3D MRI volume
            
        Returns:
            Dictionary containing:
            - segmentation: 3D array with class labels
            - probabilities: 4D array with class probabilities
            - detected: Boolean indicating if tumor detected
            - confidence: Overall detection confidence
            - volume_mm3: Estimated tumor volume
            - regions: Per-region volumes
        """
        self.eval()
        
        # Prepare input
        x = self.prepare_input(image)
        
        # Forward pass
        logits = self.forward(x)
        
        # Get probabilities and predictions
        probs = F.softmax(logits, dim=1)
        preds = torch.argmax(logits, dim=1)
        
        # Move to numpy
        probs_np = probs.cpu().numpy()[0]  # (num_classes, H, W, D)
        preds_np = preds.cpu().numpy()[0]  # (H, W, D)
        
        # Compute volumes (assuming 1mm³ voxels for MVP)
        region_labels = {
            "necrotic": 1,
            "edema": 2,
            "enhancing": 3,
        }
        
        region_volumes = {}
        total_tumor_volume = 0.0
        
        for region_name, label in region_labels.items():
            volume = float(np.sum(preds_np == label))
            region_volumes[region_name] = volume
            total_tumor_volume += volume
        
        # Detection threshold
        tumor_detected = total_tumor_volume > 100  # Minimum 100 voxels
        
        # Confidence: max probability of tumor classes
        tumor_probs = probs_np[1:].max(axis=0)
        confidence = float(tumor_probs.max()) if tumor_detected else 0.0
        
        return {
            "segmentation": preds_np,
            "probabilities": probs_np,
            "detected": tumor_detected,
            "confidence": confidence,
            "volume_mm3": total_tumor_volume,
            "regions": region_volumes,
        }
    
    def get_model_info(self) -> dict[str, Any]:
        """Get model architecture information."""
        info = super().get_model_info()
        info.update({
            "architecture": "3D U-Net",
            "in_channels": self.in_channels,
            "num_classes": self.num_classes,
            "base_features": self.base_features,
            "class_labels": ["background", "necrotic", "edema", "enhancing"],
        })
        return info


def create_tumor_model(
    weights_path: str | None = None,
    device: str | None = None,
) -> TumorSegmentationModel:
    """
    Factory function to create and optionally load tumor model.
    
    Args:
        weights_path: Optional path to pretrained weights
        device: Device to run model on
        
    Returns:
        Initialized TumorSegmentationModel
    """
    if device is None:
        device = settings.model.device
    
    model = TumorSegmentationModel(
        in_channels=1,
        num_classes=settings.model.num_classes_tumor,
        device=device,
    )
    
    if weights_path is not None:
        try:
            model.load_weights(weights_path)
        except FileNotFoundError:
            pass  # Use random weights for MVP
    
    return model
