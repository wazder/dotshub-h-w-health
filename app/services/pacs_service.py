"""
PACS Service - Orthanc PACS sunucusu ile iletişim
DICOM görüntülerini yükler ve yönetir
"""

import os
import logging
from typing import Optional, Tuple
from io import BytesIO

import pydicom
from pydicom.dataset import Dataset

# Orthanc client (opsiyonel - sunucu yoksa mock kullanılır)
try:
    from pyorthanc import Orthanc
    PYORTHANC_AVAILABLE = True
except ImportError:
    PYORTHANC_AVAILABLE = False

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class PACSService:
    """
    Orthanc PACS sunucusu ile iletişim servisi.
    Sunucu mevcut değilse mock mod kullanır.
    """
    
    def __init__(self):
        self.orthanc_url = os.getenv("ORTHANC_URL", "http://localhost:8042")
        self.username = os.getenv("ORTHANC_USERNAME", "orthanc")
        self.password = os.getenv("ORTHANC_PASSWORD", "orthanc")
        self.mock_mode = True  # Prototip için varsayılan olarak mock mod
        self.orthanc_client = None
        
        # Orthanc bağlantısını dene
        if PYORTHANC_AVAILABLE and not self.mock_mode:
            try:
                self.orthanc_client = Orthanc(
                    self.orthanc_url,
                    username=self.username,
                    password=self.password
                )
                # Bağlantı testi
                self.orthanc_client.get_system()
                self.mock_mode = False
                logger.info(f"Orthanc PACS bağlantısı başarılı: {self.orthanc_url}")
            except Exception as e:
                logger.warning(f"Orthanc bağlantısı başarısız, mock mod aktif: {e}")
                self.mock_mode = True
    
    def upload_dicom(self, dicom_bytes: bytes) -> dict:
        """
        DICOM dosyasını PACS'a yükler.
        
        Args:
            dicom_bytes: DICOM dosyasının byte içeriği
            
        Returns:
            dict: Yükleme sonucu
        """
        if self.mock_mode:
            return self._mock_upload(dicom_bytes)
        
        try:
            # Gerçek Orthanc yükleme
            result = self.orthanc_client.post_instances(dicom_bytes)
            
            return {
                "success": True,
                "orthanc_id": result.get("ID"),
                "study_uid": result.get("ParentStudy"),
                "series_uid": result.get("ParentSeries"),
                "message": "DICOM başarıyla PACS'a yüklendi"
            }
        except Exception as e:
            logger.error(f"PACS yükleme hatası: {e}")
            return {
                "success": False,
                "orthanc_id": None,
                "study_uid": None,
                "series_uid": None,
                "message": f"PACS yükleme hatası: {str(e)}"
            }
    
    def _mock_upload(self, dicom_bytes: bytes) -> dict:
        """
        Mock PACS yükleme - gerçek sunucu olmadan test için.
        
        Args:
            dicom_bytes: DICOM dosyasının byte içeriği
            
        Returns:
            dict: Simüle edilmiş yükleme sonucu
        """
        import uuid
        import hashlib
        
        # DICOM dosyasından metadata çıkarmayı dene
        study_uid = None
        series_uid = None
        
        try:
            ds = pydicom.dcmread(BytesIO(dicom_bytes))
            study_uid = str(getattr(ds, 'StudyInstanceUID', None))
            series_uid = str(getattr(ds, 'SeriesInstanceUID', None))
            logger.info(f"DICOM metadata okundu - Study: {study_uid[:20]}...")
        except Exception as e:
            logger.warning(f"DICOM parse edilemedi (mock mod devam ediyor): {e}")
            # Dummy UID'ler oluştur
            study_uid = f"1.2.826.0.1.{uuid.uuid4().int % 1000000}"
            series_uid = f"1.2.826.0.1.{uuid.uuid4().int % 1000000}.1"
        
        # Mock Orthanc ID oluştur
        orthanc_id = hashlib.md5(dicom_bytes[:1024] if len(dicom_bytes) > 1024 else dicom_bytes).hexdigest()[:16]
        
        logger.info(f"[MOCK] PACS yükleme simüle edildi - ID: {orthanc_id}")
        
        return {
            "success": True,
            "orthanc_id": orthanc_id,
            "study_uid": study_uid,
            "series_uid": series_uid,
            "message": "[MOCK] DICOM başarıyla simüle PACS'a yüklendi"
        }
    
    def get_instance(self, orthanc_id: str) -> Optional[bytes]:
        """
        PACS'tan bir instance'ı getirir.
        
        Args:
            orthanc_id: Orthanc instance ID
            
        Returns:
            bytes: DICOM dosya içeriği veya None
        """
        if self.mock_mode:
            logger.warning("[MOCK] Instance getirme mock modda desteklenmiyor")
            return None
        
        try:
            return self.orthanc_client.get_instance_file(orthanc_id)
        except Exception as e:
            logger.error(f"Instance getirme hatası: {e}")
            return None
    
    def check_connection(self) -> Tuple[bool, str]:
        """
        PACS bağlantısını kontrol eder.
        
        Returns:
            Tuple[bool, str]: (bağlantı_durumu, mesaj)
        """
        if self.mock_mode:
            return True, "Mock mod aktif - gerçek PACS bağlantısı yok"
        
        try:
            system_info = self.orthanc_client.get_system()
            return True, f"Orthanc {system_info.get('Version', 'unknown')} bağlı"
        except Exception as e:
            return False, f"PACS bağlantı hatası: {str(e)}"


# Singleton instance
pacs_service = PACSService()
