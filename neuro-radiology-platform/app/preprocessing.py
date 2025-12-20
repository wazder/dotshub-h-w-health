"""
Preprocessing pipeline for MRI images.

Includes skull stripping, registration to MNI152 template,
intensity normalization, and resampling.
"""

from typing import Any

import numpy as np
from monai.transforms import (
    Compose,
    EnsureChannelFirst,
    NormalizeIntensity,
    Orientation,
    Resize,
    ScaleIntensity,
    Spacing,
)

from app.config import settings


class SkullStripper:
    """
    Skull stripping module to remove non-brain tissue.
    
    In production, this would use a trained model (e.g., HD-BET, SynthStrip).
    For MVP, implements a simple intensity-based thresholding approach.
    """
    
    def __init__(self, threshold_percentile: float = 15.0) -> None:
        """
        Initialize skull stripper.
        
        Args:
            threshold_percentile: Percentile for intensity thresholding
        """
        self.threshold_percentile = threshold_percentile
    
    def __call__(self, image: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """
        Apply skull stripping to the input image.
        
        Args:
            image: 3D numpy array of MRI data
            
        Returns:
            Tuple of (skull_stripped_image, brain_mask)
        """
        return self.strip(image)
    
    def strip(self, image: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """
        Remove skull and non-brain tissue using intensity thresholding.
        
        This is a placeholder implementation. For production use:
        - HD-BET (deep learning based)
        - SynthStrip (FreeSurfer)
        - ANTs Brain Extraction
        
        Args:
            image: 3D MRI volume
            
        Returns:
            Tuple of (skull_stripped_image, brain_mask)
        """
        # Simple intensity-based thresholding (placeholder)
        threshold = np.percentile(image[image > 0], self.threshold_percentile)
        
        # Create initial mask
        mask = image > threshold
        
        # Apply morphological operations to clean up mask
        from scipy import ndimage
        
        # Fill holes
        mask = ndimage.binary_fill_holes(mask)
        
        # Remove small objects
        labeled_array, num_features = ndimage.label(mask)
        if num_features > 0:
            component_sizes = ndimage.sum(mask, labeled_array, range(1, num_features + 1))
            largest_component = np.argmax(component_sizes) + 1
            mask = labeled_array == largest_component
        
        # Apply morphological closing
        struct = ndimage.generate_binary_structure(3, 2)
        mask = ndimage.binary_closing(mask, structure=struct, iterations=2)
        mask = ndimage.binary_opening(mask, structure=struct, iterations=1)
        
        # Apply mask to image
        skull_stripped = image * mask.astype(np.float32)
        
        return skull_stripped, mask.astype(np.uint8)


class TemplateRegistration:
    """
    Registration module to align MRI to MNI152 template space.
    
    For MVP, implements affine registration placeholder.
    In production, use ANTs or MONAI's registration transforms.
    """
    
    def __init__(self, template_path: str | None = None) -> None:
        """
        Initialize template registration.
        
        Args:
            template_path: Path to MNI152 template file
        """
        self.template_path = template_path
        self._template_data: np.ndarray | None = None
        self._template_affine: np.ndarray | None = None
    
    def _load_template(self) -> None:
        """Load MNI152 template if path is provided."""
        if self.template_path is not None:
            try:
                import nibabel as nib
                
                img = nib.load(self.template_path)
                self._template_data = img.get_fdata().astype(np.float32)
                self._template_affine = img.affine
            except Exception:
                self._template_data = None
                self._template_affine = None
    
    def register(
        self,
        image: np.ndarray,
        affine: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
        """
        Register image to MNI152 template space.
        
        Placeholder implementation that performs basic resampling.
        For production, integrate with ANTsPy or SimpleITK.
        
        Args:
            image: 3D MRI volume
            affine: Affine transformation matrix
            
        Returns:
            Tuple of (registered_image, transform_matrix, registration_info)
        """
        # Load template if available
        if self._template_data is None:
            self._load_template()
        
        # For MVP, we'll just resample to a standard shape
        # Real registration would involve:
        # 1. Rigid registration (6 DOF)
        # 2. Affine registration (12 DOF)
        # 3. Optional: Non-linear registration
        
        target_shape = settings.preprocessing.target_shape
        
        # Calculate zoom factors
        zoom_factors = [t / s for t, s in zip(target_shape, image.shape[:3])]
        
        from scipy import ndimage
        
        registered = ndimage.zoom(
            image,
            zoom_factors,
            order=1,  # Linear interpolation
            mode="constant",
            cval=0,
        )
        
        # Update affine for the new voxel sizes
        scale_matrix = np.diag([1/z for z in zoom_factors] + [1])
        new_affine = affine @ scale_matrix
        
        registration_info = {
            "method": "affine_placeholder",
            "original_shape": image.shape,
            "registered_shape": registered.shape,
            "zoom_factors": zoom_factors,
        }
        
        return registered, new_affine, registration_info


class PreprocessingPipeline:
    """
    Complete preprocessing pipeline for MRI analysis.
    
    Steps:
    1. Skull stripping
    2. Registration to template space
    3. Intensity normalization
    4. Resampling to target resolution
    """
    
    def __init__(self) -> None:
        """Initialize preprocessing pipeline with default settings."""
        self.skull_stripper = SkullStripper()
        self.registration = TemplateRegistration(
            template_path=str(settings.preprocessing.template_path)
            if settings.preprocessing.template_path
            else None
        )
        
        # MONAI transforms for intensity processing
        self.intensity_transforms = Compose([
            NormalizeIntensity(nonzero=True),
            ScaleIntensity(minv=0.0, maxv=1.0),
        ])
    
    def run(
        self,
        image: np.ndarray,
        affine: np.ndarray,
        skip_skull_strip: bool = False,
        skip_registration: bool = False,
    ) -> tuple[np.ndarray, dict[str, Any]]:
        """
        Run the complete preprocessing pipeline.
        
        Args:
            image: 3D MRI volume as numpy array
            affine: 4x4 affine transformation matrix
            skip_skull_strip: Skip skull stripping step
            skip_registration: Skip registration step
            
        Returns:
            Tuple of (preprocessed_image, preprocessing_info)
        """
        info: dict[str, Any] = {
            "original_shape": image.shape,
            "original_dtype": str(image.dtype),
            "steps_performed": [],
        }
        
        current_image = image.copy()
        current_affine = affine.copy()
        
        # Step 1: Skull stripping
        if not skip_skull_strip:
            try:
                current_image, brain_mask = self.skull_stripper(current_image)
                info["steps_performed"].append("skull_stripping")
                info["brain_mask_volume"] = int(np.sum(brain_mask))
            except Exception as e:
                info["skull_stripping_error"] = str(e)
        
        # Step 2: Registration
        if not skip_registration:
            try:
                current_image, current_affine, reg_info = self.registration.register(
                    current_image, current_affine
                )
                info["steps_performed"].append("registration")
                info["registration"] = reg_info
            except Exception as e:
                info["registration_error"] = str(e)
        
        # Step 3: Intensity normalization
        try:
            # Add channel dimension for MONAI transforms
            current_image = current_image[np.newaxis, ...]
            current_image = self.intensity_transforms(current_image)
            # Remove channel dimension
            current_image = current_image[0]
            info["steps_performed"].append("intensity_normalization")
        except Exception as e:
            info["intensity_normalization_error"] = str(e)
        
        info["final_shape"] = current_image.shape
        info["final_dtype"] = str(current_image.dtype)
        info["intensity_range"] = (float(current_image.min()), float(current_image.max()))
        
        return current_image, info
    
    def prepare_for_model(
        self,
        image: np.ndarray,
        target_shape: tuple[int, int, int] | None = None,
    ) -> np.ndarray:
        """
        Prepare preprocessed image for model input.
        
        Args:
            image: Preprocessed 3D image
            target_shape: Target shape for model input
            
        Returns:
            Image tensor ready for model (with batch and channel dims)
        """
        if target_shape is None:
            target_shape = settings.model.input_shape
        
        # Resize if needed
        if image.shape != target_shape:
            from scipy import ndimage
            
            zoom_factors = [t / s for t, s in zip(target_shape, image.shape)]
            image = ndimage.zoom(image, zoom_factors, order=1)
        
        # Add batch and channel dimensions: (H, W, D) -> (1, 1, H, W, D)
        image = image[np.newaxis, np.newaxis, ...]
        
        return image.astype(np.float32)


def compute_histogram_stats(image: np.ndarray) -> dict[str, float]:
    """
    Compute histogram statistics for routing decisions.
    
    Args:
        image: 3D MRI volume
        
    Returns:
        Dictionary of histogram statistics
    """
    # Get non-zero voxels
    nonzero = image[image > 0].flatten()
    
    if len(nonzero) == 0:
        return {
            "mean": 0.0,
            "std": 0.0,
            "skewness": 0.0,
            "kurtosis": 0.0,
            "entropy": 0.0,
        }
    
    from scipy import stats
    
    return {
        "mean": float(np.mean(nonzero)),
        "std": float(np.std(nonzero)),
        "median": float(np.median(nonzero)),
        "skewness": float(stats.skew(nonzero)),
        "kurtosis": float(stats.kurtosis(nonzero)),
        "percentile_5": float(np.percentile(nonzero, 5)),
        "percentile_95": float(np.percentile(nonzero, 95)),
        "dynamic_range": float(np.percentile(nonzero, 95) - np.percentile(nonzero, 5)),
    }
