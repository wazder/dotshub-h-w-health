"""
Image Converter Service - Multi-Format Converter
Supported formats: DICOM, NIFTI, PNG, JPEG, JPG

Since NIH ChestX-ray14 dataset is in PNG format,
we convert incoming images to PNG and feed to model.
"""

import logging
from io import BytesIO
from typing import Optional, Tuple
from enum import Enum
import numpy as np

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import pydicom
    from pydicom.pixel_data_handlers.util import apply_voi_lut
    PYDICOM_AVAILABLE = True
except ImportError:
    PYDICOM_AVAILABLE = False

try:
    import nibabel as nib
    NIBABEL_AVAILABLE = True
except ImportError:
    NIBABEL_AVAILABLE = False

logger = logging.getLogger(__name__)


class ImageFormat(Enum):
    """Supported image formats."""
    DICOM = "dicom"
    NIFTI = "nifti"
    PNG = "png"
    JPEG = "jpeg"
    JPG = "jpg"
    UNKNOWN = "unknown"


class ImageConverterService:
    """
    Multi-format image converter.
    
    Supported formats:
    - DICOM (.dcm)
    - NIFTI (.nii, .nii.gz)
    - PNG (.png)
    - JPEG/JPG (.jpeg, .jpg)
    
    NIH ChestX-ray14 dataset specifications:
    - Format: PNG
    - Size: 1024x1024 pixels
    - Channel: Grayscale (1 channel)
    - Bit depth: 8-bit (0-255)
    """
    
    # NIH ChestX-ray14 dataset size
    TARGET_SIZE = (1024, 1024)
    
    # Magic bytes for format detection
    MAGIC_BYTES = {
        b'\x89PNG': ImageFormat.PNG,
        b'\xff\xd8\xff': ImageFormat.JPEG,
    }
    
    def __init__(self):
        self._log_available_formats()
        logger.info("Image Converter Service initialized")
    
    def _log_available_formats(self):
        """Log available formats."""
        formats = []
        if PIL_AVAILABLE:
            formats.extend(["PNG", "JPEG", "JPG"])
        if PYDICOM_AVAILABLE:
            formats.append("DICOM")
        if NIBABEL_AVAILABLE:
            formats.append("NIFTI")
        logger.info(f"Supported formats: {', '.join(formats)}")
        
        if not PIL_AVAILABLE:
            logger.warning("PIL/Pillow not installed! pip install Pillow")
        if not NIBABEL_AVAILABLE:
            logger.warning("nibabel not installed! For NIFTI support: pip install nibabel")
    
    def detect_format(self, image_bytes: bytes, filename: Optional[str] = None) -> ImageFormat:
        """
        Auto-detect image format.
        
        Args:
            image_bytes: Image byte content
            filename: Optional filename (for extension check)
            
        Returns:
            ImageFormat: Detected format
        """
        # 1. Detect from filename
        if filename:
            filename_lower = filename.lower()
            if filename_lower.endswith('.dcm'):
                return ImageFormat.DICOM
            elif filename_lower.endswith('.nii') or filename_lower.endswith('.nii.gz'):
                return ImageFormat.NIFTI
            elif filename_lower.endswith('.png'):
                return ImageFormat.PNG
            elif filename_lower.endswith('.jpeg'):
                return ImageFormat.JPEG
            elif filename_lower.endswith('.jpg'):
                return ImageFormat.JPG
        
        # 2. Detect from magic bytes
        for magic, fmt in self.MAGIC_BYTES.items():
            if image_bytes[:len(magic)] == magic:
                return fmt
        
        # 3. DICOM check (DICM magic at offset 128)
        if len(image_bytes) > 132 and image_bytes[128:132] == b'DICM':
            return ImageFormat.DICOM
        
        # 4. NIFTI check
        if len(image_bytes) > 4:
            # NIfTI-1 header size check (348 bytes)
            if image_bytes[:2] in [b'\x5c\x01', b'\x01\x5c']:  # 348 in little/big endian
                return ImageFormat.NIFTI
            # Gzip compressed NIFTI
            if image_bytes[:2] == b'\x1f\x8b':
                return ImageFormat.NIFTI
        
        return ImageFormat.UNKNOWN
    
    def convert_to_numpy(
        self, 
        image_bytes: bytes,
        target_size: Optional[Tuple[int, int]] = None,
        filename: Optional[str] = None,
        image_format: Optional[ImageFormat] = None
    ) -> Optional[np.ndarray]:
        """
        Convert any format image to numpy array.
        
        Args:
            image_bytes: Image byte content
            target_size: Target size (width, height)
            filename: Optional filename
            image_format: Optional format (auto-detect if None)
            
        Returns:
            np.ndarray: Normalized image (0-1 range, float32, shape: H,W,1)
        """
        target_size = target_size or self.TARGET_SIZE
        
        # Detect format
        if image_format is None:
            image_format = self.detect_format(image_bytes, filename)
        
        logger.info(f"Image format: {image_format.value}")
        
        # Convert by format
        if image_format == ImageFormat.DICOM:
            return self.dicom_to_numpy(image_bytes, target_size)
        elif image_format == ImageFormat.NIFTI:
            return self.nifti_to_numpy(image_bytes, target_size)
        elif image_format in [ImageFormat.PNG, ImageFormat.JPEG, ImageFormat.JPG]:
            return self.standard_image_to_numpy(image_bytes, target_size)
        else:
            logger.error(f"Unknown format: {image_format}")
            return None
    
    def dicom_to_numpy(
        self, 
        dicom_bytes: bytes,
        target_size: Optional[Tuple[int, int]] = None
    ) -> Optional[np.ndarray]:
        """
        Convert DICOM file to numpy array.
        """
        if not PYDICOM_AVAILABLE:
            logger.error("pydicom not installed!")
            return None
        
        if not PIL_AVAILABLE:
            logger.error("PIL/Pillow not installed!")
            return None
            
        target_size = target_size or self.TARGET_SIZE
        
        try:
            # Read DICOM
            ds = pydicom.dcmread(BytesIO(dicom_bytes))
            logger.info(f"DICOM read - Modality: {getattr(ds, 'Modality', 'Unknown')}")
            
            # Get pixel array
            pixel_array = ds.pixel_array
            
            # Apply VOI LUT
            pixel_array = apply_voi_lut(pixel_array, ds)
            
            # Normalize to 0-255
            pixel_array = self._normalize_to_uint8(pixel_array)
            
            # MONOCHROME1 check
            if hasattr(ds, 'PhotometricInterpretation'):
                if ds.PhotometricInterpretation == "MONOCHROME1":
                    pixel_array = 255 - pixel_array
            
            # Convert to PIL Image and process
            return self._process_array(pixel_array, target_size)
            
        except Exception as e:
            logger.error(f"DICOM conversion error: {e}", exc_info=True)
            return None
    
    def nifti_to_numpy(
        self, 
        nifti_bytes: bytes,
        target_size: Optional[Tuple[int, int]] = None
    ) -> Optional[np.ndarray]:
        """
        Convert NIFTI file to numpy array.
        
        Note: NIFTI can be 3D/4D. We take the middle slice.
        """
        if not NIBABEL_AVAILABLE:
            logger.error("nibabel not installed! pip install nibabel")
            return None
        
        if not PIL_AVAILABLE:
            logger.error("PIL/Pillow not installed!")
            return None
            
        target_size = target_size or self.TARGET_SIZE
        
        try:
            # Read NIFTI (from BytesIO)
            # nibabel cannot read directly from bytes, workaround needed
            import tempfile
            import os
            
            # Write to temp file
            with tempfile.NamedTemporaryFile(suffix='.nii.gz', delete=False) as tmp:
                tmp.write(nifti_bytes)
                tmp_path = tmp.name
            
            try:
                # Load NIFTI
                nii = nib.load(tmp_path)
                data = nii.get_fdata()
                logger.info(f"NIFTI read - Shape: {data.shape}")
                
                # Take middle slice for 3D/4D
                if len(data.shape) >= 3:
                    mid_slice = data.shape[2] // 2
                    pixel_array = data[:, :, mid_slice]
                    if len(data.shape) == 4:
                        pixel_array = pixel_array[:, :, 0]  # First time point
                else:
                    pixel_array = data
                
                # Normalize to 0-255
                pixel_array = self._normalize_to_uint8(pixel_array)
                
                return self._process_array(pixel_array, target_size)
                
            finally:
                # Delete temp file
                os.unlink(tmp_path)
            
        except Exception as e:
            logger.error(f"NIFTI conversion error: {e}", exc_info=True)
            return None
    
    def standard_image_to_numpy(
        self, 
        image_bytes: bytes,
        target_size: Optional[Tuple[int, int]] = None
    ) -> Optional[np.ndarray]:
        """
        Convert PNG/JPEG/JPG file to numpy array.
        """
        if not PIL_AVAILABLE:
            logger.error("PIL/Pillow not installed!")
            return None
            
        target_size = target_size or self.TARGET_SIZE
        
        try:
            image = Image.open(BytesIO(image_bytes))
            logger.info(f"Image read - Size: {image.size}, Mode: {image.mode}")
            
            # Convert to grayscale
            if image.mode != 'L':
                image = image.convert('L')
            
            # Resize
            if image.size != target_size:
                image = image.resize(target_size, Image.Resampling.LANCZOS)
            
            # Numpy array
            img_array = np.array(image, dtype=np.float32) / 255.0
            
            # Add channel dimension
            if len(img_array.shape) == 2:
                img_array = np.expand_dims(img_array, axis=-1)
            
            logger.info(f"Conversion complete: shape={img_array.shape}")
            return img_array
            
        except Exception as e:
            logger.error(f"Image conversion error: {e}", exc_info=True)
            return None
    
    def _process_array(
        self, 
        pixel_array: np.ndarray, 
        target_size: Tuple[int, int]
    ) -> np.ndarray:
        """
        Process pixel array: resize, normalize, add channel.
        """
        # Create PIL Image
        image = Image.fromarray(pixel_array)
        
        # Convert to grayscale
        if image.mode != 'L':
            image = image.convert('L')
        
        # Resize
        if image.size != target_size:
            image = image.resize(target_size, Image.Resampling.LANCZOS)
        
        # Numpy array and normalize to 0-1
        img_array = np.array(image, dtype=np.float32) / 255.0
        
        # Add channel dimension: (H, W) -> (H, W, 1)
        if len(img_array.shape) == 2:
            img_array = np.expand_dims(img_array, axis=-1)
        
        logger.info(f"Array ready: shape={img_array.shape}, range=[{img_array.min():.2f}, {img_array.max():.2f}]")
        return img_array
    
    def _normalize_to_uint8(self, pixel_array: np.ndarray) -> np.ndarray:
        """Normalize pixel array to 0-255 range."""
        img_min = pixel_array.min()
        img_max = pixel_array.max()
        
        if img_max > img_min:
            pixel_array = (pixel_array - img_min) / (img_max - img_min)
        else:
            pixel_array = np.zeros_like(pixel_array)
        
        return (pixel_array * 255).astype(np.uint8)
    
    def convert_to_png(
        self, 
        image_bytes: bytes,
        target_size: Optional[Tuple[int, int]] = None,
        filename: Optional[str] = None
    ) -> Optional[bytes]:
        """
        Convert any format image to PNG.
        
        Returns:
            bytes: Image in PNG format
        """
        img_array = self.convert_to_numpy(image_bytes, target_size, filename)
        
        if img_array is None:
            return None
        
        try:
            # Convert back to 0-255
            img_uint8 = (img_array[:, :, 0] * 255).astype(np.uint8)
            image = Image.fromarray(img_uint8)
            
            # Save as PNG
            png_buffer = BytesIO()
            image.save(png_buffer, format='PNG')
            return png_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"PNG conversion error: {e}")
            return None
    
    def check_health(self) -> Tuple[bool, str]:
        """Service health check."""
        formats = []
        if PIL_AVAILABLE:
            formats.extend(["PNG", "JPEG", "JPG"])
        if PYDICOM_AVAILABLE:
            formats.append("DICOM")
        if NIBABEL_AVAILABLE:
            formats.append("NIFTI")
        
        if formats:
            return True, f"Image Converter running - Formats: {', '.join(formats)}"
        return False, "No format libraries installed"


# Singleton instance
image_converter = ImageConverterService()
