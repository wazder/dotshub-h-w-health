"""File I/O utilities for medical imaging formats."""

from pathlib import Path
from typing import Any

import nibabel as nib
import numpy as np


def load_nifti(file_path: Path | str) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    """
    Load a NIfTI file and return image data, affine matrix, and header info.
    
    Args:
        file_path: Path to the NIfTI file (.nii or .nii.gz)
        
    Returns:
        Tuple of (image_data, affine_matrix, header_dict)
        
    Raises:
        FileNotFoundError: If file does not exist
        ValueError: If file format is invalid
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"NIfTI file not found: {file_path}")
    
    try:
        img = nib.load(str(file_path))
        data = img.get_fdata().astype(np.float32)
        affine = img.affine
        
        header_info = {
            "shape": data.shape,
            "dtype": str(data.dtype),
            "voxel_size": tuple(img.header.get_zooms()[:3]),
            "orientation": nib.aff2axcodes(affine),
            "file_path": str(file_path),
        }
        
        return data, affine, header_info
        
    except Exception as e:
        raise ValueError(f"Failed to load NIfTI file: {e}") from e


def load_dicom(directory_path: Path | str) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    """
    Load a DICOM series from a directory.
    
    Args:
        directory_path: Path to directory containing DICOM files
        
    Returns:
        Tuple of (image_data, affine_matrix, header_dict)
        
    Raises:
        FileNotFoundError: If directory does not exist
        ValueError: If no valid DICOM files found
    """
    directory_path = Path(directory_path)
    
    if not directory_path.exists():
        raise FileNotFoundError(f"DICOM directory not found: {directory_path}")
    
    try:
        # Using nibabel's DICOM reader for simplicity
        # For production, consider pydicom with proper series sorting
        dcm_files = list(directory_path.glob("*.dcm"))
        
        if not dcm_files:
            raise ValueError(f"No DICOM files found in: {directory_path}")
        
        # Load first file to get basic info (placeholder implementation)
        # In production, use proper DICOM series loading
        from monai.transforms import LoadImage
        
        loader = LoadImage(image_only=False)
        data, meta = loader(str(dcm_files[0]))
        
        affine = meta.get("affine", np.eye(4))
        
        header_info = {
            "shape": data.shape,
            "dtype": str(data.dtype),
            "num_slices": len(dcm_files),
            "file_path": str(directory_path),
        }
        
        return data.numpy() if hasattr(data, "numpy") else np.array(data), affine, header_info
        
    except Exception as e:
        raise ValueError(f"Failed to load DICOM series: {e}") from e


def save_nifti(
    data: np.ndarray,
    affine: np.ndarray,
    output_path: Path | str,
    dtype: np.dtype = np.float32,
) -> Path:
    """
    Save image data as a NIfTI file.
    
    Args:
        data: 3D numpy array of image data
        affine: 4x4 affine transformation matrix
        output_path: Path for output file
        dtype: Data type for saved file
        
    Returns:
        Path to saved file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    img = nib.Nifti1Image(data.astype(dtype), affine)
    nib.save(img, str(output_path))
    
    return output_path


def validate_mri_file(file_path: Path | str) -> tuple[bool, str]:
    """
    Validate if a file is a valid MRI image.
    
    Args:
        file_path: Path to the file to validate
        
    Returns:
        Tuple of (is_valid, message)
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        return False, "File does not exist"
    
    valid_extensions = [".nii", ".nii.gz", ".dcm"]
    suffix = "".join(file_path.suffixes).lower()
    
    if not any(suffix.endswith(ext) for ext in valid_extensions):
        return False, f"Invalid file extension. Allowed: {valid_extensions}"
    
    try:
        if suffix.endswith(".dcm"):
            # Basic DICOM validation
            return True, "Valid DICOM file"
        else:
            # NIfTI validation
            img = nib.load(str(file_path))
            shape = img.shape
            
            if len(shape) < 3:
                return False, "Image must be at least 3D"
            
            return True, f"Valid NIfTI file with shape {shape}"
            
    except Exception as e:
        return False, f"Failed to validate file: {e}"
