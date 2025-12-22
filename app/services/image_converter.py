"""
Image Converter Service - Çoklu Format Dönüştürücü
Desteklenen formatlar: DICOM, NIFTI, PNG, JPEG, JPG

NIH ChestX-ray14 dataset PNG formatında olduğu için
gelen görüntüleri PNG'ye çevirip modele veririz.
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
    """Desteklenen görüntü formatları."""
    DICOM = "dicom"
    NIFTI = "nifti"
    PNG = "png"
    JPEG = "jpeg"
    JPG = "jpg"
    UNKNOWN = "unknown"


class ImageConverterService:
    """
    Çoklu format görüntü dönüştürücü.
    
    Desteklenen formatlar:
    - DICOM (.dcm)
    - NIFTI (.nii, .nii.gz)
    - PNG (.png)
    - JPEG/JPG (.jpeg, .jpg)
    
    NIH ChestX-ray14 dataset özellikleri:
    - Format: PNG
    - Boyut: 1024x1024 piksel
    - Kanal: Grayscale (1 kanal)
    - Bit derinliği: 8-bit (0-255)
    """
    
    # NIH ChestX-ray14 dataset boyutu
    TARGET_SIZE = (1024, 1024)
    
    # Magic bytes for format detection
    MAGIC_BYTES = {
        b'\x89PNG': ImageFormat.PNG,
        b'\xff\xd8\xff': ImageFormat.JPEG,
    }
    
    def __init__(self):
        self._log_available_formats()
        logger.info("Image Converter Service başlatıldı")
    
    def _log_available_formats(self):
        """Kullanılabilir formatları logla."""
        formats = []
        if PIL_AVAILABLE:
            formats.extend(["PNG", "JPEG", "JPG"])
        if PYDICOM_AVAILABLE:
            formats.append("DICOM")
        if NIBABEL_AVAILABLE:
            formats.append("NIFTI")
        logger.info(f"Desteklenen formatlar: {', '.join(formats)}")
        
        if not PIL_AVAILABLE:
            logger.warning("PIL/Pillow yüklü değil! pip install Pillow")
        if not NIBABEL_AVAILABLE:
            logger.warning("nibabel yüklü değil! NIFTI desteği için: pip install nibabel")
    
    def detect_format(self, image_bytes: bytes, filename: Optional[str] = None) -> ImageFormat:
        """
        Görüntü formatını otomatik algılar.
        
        Args:
            image_bytes: Görüntü byte içeriği
            filename: Opsiyonel dosya adı (uzantı kontrolü için)
            
        Returns:
            ImageFormat: Algılanan format
        """
        # 1. Dosya adından algıla
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
        
        # 2. Magic bytes'dan algıla
        for magic, fmt in self.MAGIC_BYTES.items():
            if image_bytes[:len(magic)] == magic:
                return fmt
        
        # 3. DICOM kontrolü (DICM magic at offset 128)
        if len(image_bytes) > 132 and image_bytes[128:132] == b'DICM':
            return ImageFormat.DICOM
        
        # 4. NIFTI kontrolü
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
        Herhangi bir formattaki görüntüyü numpy array'e dönüştürür.
        
        Args:
            image_bytes: Görüntü byte içeriği
            target_size: Hedef boyut (width, height)
            filename: Opsiyonel dosya adı
            image_format: Opsiyonel format (None ise otomatik algılanır)
            
        Returns:
            np.ndarray: Normalize edilmiş görüntü (0-1 arası, float32, shape: H,W,1)
        """
        target_size = target_size or self.TARGET_SIZE
        
        # Format algıla
        if image_format is None:
            image_format = self.detect_format(image_bytes, filename)
        
        logger.info(f"Görüntü formatı: {image_format.value}")
        
        # Formata göre dönüştür
        if image_format == ImageFormat.DICOM:
            return self.dicom_to_numpy(image_bytes, target_size)
        elif image_format == ImageFormat.NIFTI:
            return self.nifti_to_numpy(image_bytes, target_size)
        elif image_format in [ImageFormat.PNG, ImageFormat.JPEG, ImageFormat.JPG]:
            return self.standard_image_to_numpy(image_bytes, target_size)
        else:
            logger.error(f"Bilinmeyen format: {image_format}")
            return None
    
    def dicom_to_numpy(
        self, 
        dicom_bytes: bytes,
        target_size: Optional[Tuple[int, int]] = None
    ) -> Optional[np.ndarray]:
        """
        DICOM dosyasını numpy array'e dönüştürür.
        """
        if not PYDICOM_AVAILABLE:
            logger.error("pydicom yüklü değil!")
            return None
        
        if not PIL_AVAILABLE:
            logger.error("PIL/Pillow yüklü değil!")
            return None
            
        target_size = target_size or self.TARGET_SIZE
        
        try:
            # DICOM oku
            ds = pydicom.dcmread(BytesIO(dicom_bytes))
            logger.info(f"DICOM okundu - Modality: {getattr(ds, 'Modality', 'Unknown')}")
            
            # Pixel array al
            pixel_array = ds.pixel_array
            
            # VOI LUT uygula
            pixel_array = apply_voi_lut(pixel_array, ds)
            
            # 0-255 normalize
            pixel_array = self._normalize_to_uint8(pixel_array)
            
            # MONOCHROME1 kontrolü
            if hasattr(ds, 'PhotometricInterpretation'):
                if ds.PhotometricInterpretation == "MONOCHROME1":
                    pixel_array = 255 - pixel_array
            
            # PIL Image'e çevir ve işle
            return self._process_array(pixel_array, target_size)
            
        except Exception as e:
            logger.error(f"DICOM dönüşüm hatası: {e}", exc_info=True)
            return None
    
    def nifti_to_numpy(
        self, 
        nifti_bytes: bytes,
        target_size: Optional[Tuple[int, int]] = None
    ) -> Optional[np.ndarray]:
        """
        NIFTI dosyasını numpy array'e dönüştürür.
        
        Not: NIFTI 3D/4D olabilir. Orta dilimi alırız.
        """
        if not NIBABEL_AVAILABLE:
            logger.error("nibabel yüklü değil! pip install nibabel")
            return None
        
        if not PIL_AVAILABLE:
            logger.error("PIL/Pillow yüklü değil!")
            return None
            
        target_size = target_size or self.TARGET_SIZE
        
        try:
            # NIFTI oku (BytesIO'dan)
            # nibabel doğrudan bytes'tan okuyamaz, geçici çözüm
            import tempfile
            import os
            
            # Geçici dosyaya yaz
            with tempfile.NamedTemporaryFile(suffix='.nii.gz', delete=False) as tmp:
                tmp.write(nifti_bytes)
                tmp_path = tmp.name
            
            try:
                # NIFTI yükle
                nii = nib.load(tmp_path)
                data = nii.get_fdata()
                logger.info(f"NIFTI okundu - Shape: {data.shape}")
                
                # 3D/4D ise orta dilimi al
                if len(data.shape) >= 3:
                    mid_slice = data.shape[2] // 2
                    pixel_array = data[:, :, mid_slice]
                    if len(data.shape) == 4:
                        pixel_array = pixel_array[:, :, 0]  # İlk zaman noktası
                else:
                    pixel_array = data
                
                # 0-255 normalize
                pixel_array = self._normalize_to_uint8(pixel_array)
                
                return self._process_array(pixel_array, target_size)
                
            finally:
                # Geçici dosyayı sil
                os.unlink(tmp_path)
            
        except Exception as e:
            logger.error(f"NIFTI dönüşüm hatası: {e}", exc_info=True)
            return None
    
    def standard_image_to_numpy(
        self, 
        image_bytes: bytes,
        target_size: Optional[Tuple[int, int]] = None
    ) -> Optional[np.ndarray]:
        """
        PNG/JPEG/JPG dosyasını numpy array'e dönüştürür.
        """
        if not PIL_AVAILABLE:
            logger.error("PIL/Pillow yüklü değil!")
            return None
            
        target_size = target_size or self.TARGET_SIZE
        
        try:
            image = Image.open(BytesIO(image_bytes))
            logger.info(f"Görüntü okundu - Size: {image.size}, Mode: {image.mode}")
            
            # Grayscale'e çevir
            if image.mode != 'L':
                image = image.convert('L')
            
            # Yeniden boyutlandır
            if image.size != target_size:
                image = image.resize(target_size, Image.Resampling.LANCZOS)
            
            # Numpy array
            img_array = np.array(image, dtype=np.float32) / 255.0
            
            # Kanal boyutu ekle
            if len(img_array.shape) == 2:
                img_array = np.expand_dims(img_array, axis=-1)
            
            logger.info(f"Dönüşüm tamamlandı: shape={img_array.shape}")
            return img_array
            
        except Exception as e:
            logger.error(f"Görüntü dönüşüm hatası: {e}", exc_info=True)
            return None
    
    def _process_array(
        self, 
        pixel_array: np.ndarray, 
        target_size: Tuple[int, int]
    ) -> np.ndarray:
        """
        Pixel array'i işler: resize, normalize, channel ekle.
        """
        # PIL Image oluştur
        image = Image.fromarray(pixel_array)
        
        # Grayscale'e çevir
        if image.mode != 'L':
            image = image.convert('L')
        
        # Yeniden boyutlandır
        if image.size != target_size:
            image = image.resize(target_size, Image.Resampling.LANCZOS)
        
        # Numpy array ve 0-1 normalize
        img_array = np.array(image, dtype=np.float32) / 255.0
        
        # Kanal boyutu ekle: (H, W) -> (H, W, 1)
        if len(img_array.shape) == 2:
            img_array = np.expand_dims(img_array, axis=-1)
        
        logger.info(f"Array hazır: shape={img_array.shape}, range=[{img_array.min():.2f}, {img_array.max():.2f}]")
        return img_array
    
    def _normalize_to_uint8(self, pixel_array: np.ndarray) -> np.ndarray:
        """Pixel array'i 0-255 aralığına normalize eder."""
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
        Herhangi bir formattaki görüntüyü PNG'ye dönüştürür.
        
        Returns:
            bytes: PNG formatında görüntü
        """
        img_array = self.convert_to_numpy(image_bytes, target_size, filename)
        
        if img_array is None:
            return None
        
        try:
            # 0-255'e geri çevir
            img_uint8 = (img_array[:, :, 0] * 255).astype(np.uint8)
            image = Image.fromarray(img_uint8)
            
            # PNG olarak kaydet
            png_buffer = BytesIO()
            image.save(png_buffer, format='PNG')
            return png_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"PNG dönüşüm hatası: {e}")
            return None
    
    def check_health(self) -> Tuple[bool, str]:
        """Servis sağlık kontrolü."""
        formats = []
        if PIL_AVAILABLE:
            formats.extend(["PNG", "JPEG", "JPG"])
        if PYDICOM_AVAILABLE:
            formats.append("DICOM")
        if NIBABEL_AVAILABLE:
            formats.append("NIFTI")
        
        if formats:
            return True, f"Image Converter çalışıyor - Formatlar: {', '.join(formats)}"
        return False, "Hiçbir format kütüphanesi yüklü değil"


# Singleton instance
image_converter = ImageConverterService()

