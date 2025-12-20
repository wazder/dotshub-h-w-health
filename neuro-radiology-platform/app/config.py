"""Configuration settings for the Neuro-Radiology Platform."""

from pathlib import Path
from typing import Literal
from pydantic import BaseModel


class ModelConfig(BaseModel):
    """Configuration for model parameters."""
    
    device: Literal["cuda", "cpu", "mps"] = "cpu"
    tumor_weights_path: Path | None = None
    alzheimer_weights_path: Path | None = None
    input_shape: tuple[int, int, int] = (128, 128, 128)
    num_classes_tumor: int = 4  # Background, Necrotic, Edema, Enhancing
    num_classes_alzheimer: int = 3  # CN, MCI, AD


class PreprocessingConfig(BaseModel):
    """Configuration for preprocessing pipeline."""
    
    target_spacing: tuple[float, float, float] = (1.0, 1.0, 1.0)
    target_shape: tuple[int, int, int] = (128, 128, 128)
    intensity_min: float = 0.0
    intensity_max: float = 1.0
    template_path: Path | None = None


class APIConfig(BaseModel):
    """Configuration for API settings."""
    
    max_file_size_mb: int = 500
    allowed_extensions: list[str] = [".nii", ".nii.gz", ".dcm"]
    temp_dir: Path = Path("/tmp/neuro_radiology")


class Settings(BaseModel):
    """Main settings container."""
    
    model: ModelConfig = ModelConfig()
    preprocessing: PreprocessingConfig = PreprocessingConfig()
    api: APIConfig = APIConfig()
    debug: bool = True


# Global settings instance
settings = Settings()
