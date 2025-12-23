"""
PACS Service - Orthanc PACS Server Communication
Uploads and manages DICOM images
"""

import os
import logging
from typing import Optional, Tuple
from io import BytesIO

import pydicom
from pydicom.dataset import Dataset

# Orthanc client (optional - uses mock if server not available)
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
    Orthanc PACS server communication service.
    Uses mock mode if server is not available.
    """
    
    def __init__(self):
        self.orthanc_url = os.getenv("ORTHANC_URL", "http://localhost:8042")
        self.username = os.getenv("ORTHANC_USERNAME", "orthanc")
        self.password = os.getenv("ORTHANC_PASSWORD", "orthanc")
        self.mock_mode = True  # Default mock mode for prototype
        self.orthanc_client = None
        
        # Try Orthanc connection
        if PYORTHANC_AVAILABLE and not self.mock_mode:
            try:
                self.orthanc_client = Orthanc(
                    self.orthanc_url,
                    username=self.username,
                    password=self.password
                )
                # Connection test
                self.orthanc_client.get_system()
                self.mock_mode = False
                logger.info(f"Orthanc PACS connection successful: {self.orthanc_url}")
            except Exception as e:
                logger.warning(f"Orthanc connection failed, mock mode active: {e}")
                self.mock_mode = True
    
    def upload_dicom(self, dicom_bytes: bytes) -> dict:
        """
        Upload DICOM file to PACS.
        
        Args:
            dicom_bytes: DICOM file byte content
            
        Returns:
            dict: Upload result
        """
        if self.mock_mode:
            return self._mock_upload(dicom_bytes)
        
        try:
            # Real Orthanc upload
            result = self.orthanc_client.post_instances(dicom_bytes)
            
            return {
                "success": True,
                "orthanc_id": result.get("ID"),
                "study_uid": result.get("ParentStudy"),
                "series_uid": result.get("ParentSeries"),
                "message": "DICOM successfully uploaded to PACS",
                "is_mock": False  # Real PACS connection
            }
        except Exception as e:
            logger.error(f"PACS upload error: {e}")
            return {
                "success": False,
                "orthanc_id": None,
                "study_uid": None,
                "series_uid": None,
                "message": f"PACS upload error: {str(e)}"
            }
    
    def _mock_upload(self, dicom_bytes: bytes) -> dict:
        """
        Mock PACS upload - for testing without real server.
        
        Args:
            dicom_bytes: DICOM file byte content
            
        Returns:
            dict: Simulated upload result
        """
        import uuid
        import hashlib
        
        # Try to extract metadata from DICOM file
        study_uid = None
        series_uid = None
        
        try:
            ds = pydicom.dcmread(BytesIO(dicom_bytes))
            study_uid = str(getattr(ds, 'StudyInstanceUID', None))
            series_uid = str(getattr(ds, 'SeriesInstanceUID', None))
            logger.info(f"DICOM metadata read - Study: {study_uid[:20]}...")
        except Exception as e:
            logger.warning(f"DICOM parse failed (mock mode continues): {e}")
            # Create dummy UIDs
            study_uid = f"1.2.826.0.1.{uuid.uuid4().int % 1000000}"
            series_uid = f"1.2.826.0.1.{uuid.uuid4().int % 1000000}.1"
        
        # Create mock Orthanc ID
        orthanc_id = hashlib.md5(dicom_bytes[:1024] if len(dicom_bytes) > 1024 else dicom_bytes).hexdigest()[:16]
        
        logger.info(f"[MOCK] PACS upload simulated - ID: {orthanc_id}")
        
        return {
            "success": True,
            "orthanc_id": orthanc_id,
            "study_uid": study_uid,
            "series_uid": series_uid,
            "message": "[SIMULATION] Image accepted (No real PACS connection)",
            "is_mock": True  # Flag to indicate mock mode
        }
    
    def get_instance(self, orthanc_id: str) -> Optional[bytes]:
        """
        Get instance from PACS.
        
        Args:
            orthanc_id: Orthanc instance ID
            
        Returns:
            bytes: DICOM file content or None
        """
        if self.mock_mode:
            logger.warning("[MOCK] Instance retrieval not supported in mock mode")
            return None
        
        try:
            return self.orthanc_client.get_instance_file(orthanc_id)
        except Exception as e:
            logger.error(f"Instance retrieval error: {e}")
            return None
    
    def check_connection(self) -> Tuple[bool, str]:
        """
        Check PACS connection.
        
        Returns:
            Tuple[bool, str]: (connection_status, message)
        """
        if self.mock_mode:
            return True, "Mock mode active - no real PACS connection"
        
        try:
            system_info = self.orthanc_client.get_system()
            return True, f"Orthanc {system_info.get('Version', 'unknown')} connected"
        except Exception as e:
            return False, f"PACS connection error: {str(e)}"


# Singleton instance
pacs_service = PACSService()
