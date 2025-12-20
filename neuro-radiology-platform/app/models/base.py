"""Base model interface for all specialist models."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn


class BaseModel(ABC, nn.Module):
    """Abstract base class for all specialist models."""
    
    def __init__(self, device: str = "cpu") -> None:
        """
        Initialize base model.
        
        Args:
            device: Device to run model on (cpu, cuda, mps)
        """
        super().__init__()
        self._device = torch.device(device)
        self._is_loaded = False
    
    @property
    def device(self) -> torch.device:
        """Get model device."""
        return self._device
    
    @property
    def is_loaded(self) -> bool:
        """Check if model weights are loaded."""
        return self._is_loaded
    
    @abstractmethod
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through the model."""
        pass
    
    @abstractmethod
    def predict(self, image: np.ndarray) -> dict[str, Any]:
        """
        Run inference on a preprocessed image.
        
        Args:
            image: Preprocessed 3D MRI volume (H, W, D) or (B, C, H, W, D)
            
        Returns:
            Dictionary containing prediction results
        """
        pass
    
    def load_weights(self, weights_path: Path | str) -> None:
        """
        Load pretrained weights from file.
        
        Args:
            weights_path: Path to weights file (.pth)
        """
        weights_path = Path(weights_path)
        
        if not weights_path.exists():
            raise FileNotFoundError(f"Weights file not found: {weights_path}")
        
        state_dict = torch.load(weights_path, map_location=self._device)
        self.load_state_dict(state_dict)
        self._is_loaded = True
    
    def save_weights(self, output_path: Path | str) -> None:
        """
        Save model weights to file.
        
        Args:
            output_path: Path for output weights file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(self.state_dict(), output_path)
    
    def to_device(self, device: str | None = None) -> "BaseModel":
        """
        Move model to specified device.
        
        Args:
            device: Target device (uses self._device if None)
            
        Returns:
            Self for chaining
        """
        if device is not None:
            self._device = torch.device(device)
        return self.to(self._device)
    
    def prepare_input(self, image: np.ndarray) -> torch.Tensor:
        """
        Prepare numpy image for model input.
        
        Args:
            image: Image as numpy array
            
        Returns:
            Tensor ready for model
        """
        # Ensure correct dimensions (B, C, H, W, D)
        if image.ndim == 3:
            image = image[np.newaxis, np.newaxis, ...]
        elif image.ndim == 4:
            image = image[np.newaxis, ...]
        
        tensor = torch.from_numpy(image.astype(np.float32))
        return tensor.to(self._device)
    
    def get_model_info(self) -> dict[str, Any]:
        """Get model information and statistics."""
        total_params = sum(p.numel() for p in self.parameters())
        trainable_params = sum(p.numel() for p in self.parameters() if p.requires_grad)
        
        return {
            "model_class": self.__class__.__name__,
            "device": str(self._device),
            "is_loaded": self._is_loaded,
            "total_parameters": total_params,
            "trainable_parameters": trainable_params,
        }
