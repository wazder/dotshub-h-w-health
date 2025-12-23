"""
Data Service - Patient Data Service
Uses only real NIH Dataset
"""

import logging
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)


class DataService:
    """
    Patient data management service.
    Reads real patient information from NIH Dataset only.
    """
    
    def __init__(self):
        """Initialize DataService."""
        self._dataset_service = None
    
    def set_dataset_service(self, dataset_service):
        """Set dataset service reference."""
        self._dataset_service = dataset_service
        logger.info("Dataset service connected")
    
    def get_patient_history(self, patient_id: str) -> Optional[Dict]:
        """
        Get a specific patient's history from NIH dataset.
        
        Args:
            patient_id: Patient ID
            
        Returns:
            dict: Patient info or None
        """
        if self._dataset_service:
            patient = self._dataset_service.get_patient_info(patient_id)
            if patient:
                logger.info(f"Patient found from NIH Dataset: {patient_id}")
                return patient
        
        logger.warning(f"Patient not found: {patient_id}")
        return None
    
    def get_patient_summary(self, patient_id: str) -> str:
        """
        Returns patient's summary history text.
        
        Args:
            patient_id: Patient ID
            
        Returns:
            str: Patient history summary (in Turkish for UI)
        """
        patient = self.get_patient_history(patient_id)
        
        if patient:
            return patient.get('history', f"Hasta {patient_id} için detay bulunamadı.")
        
        return f"Hasta {patient_id} kayıtlarda bulunamadı."
    
    def list_all_patients(self) -> List[str]:
        """
        List all patient IDs from NIH dataset.
        
        Returns:
            List[str]: Patient ID list
        """
        patient_ids = []
        
        if self._dataset_service:
            patient_ids = self._dataset_service.list_patients(limit=100)
        
        return patient_ids
    
    def search_by_diagnosis(self, diagnosis: str) -> List[Dict]:
        """
        Search patients by diagnosis in NIH dataset.
        
        Args:
            diagnosis: Diagnosis to search
            
        Returns:
            List[Dict]: Matching patients
        """
        results = []
        
        if self._dataset_service:
            # Use dataset service to search
            results = self._dataset_service.search_by_pathology(diagnosis)
        
        logger.info(f"Diagnosis search: '{diagnosis}' - {len(results)} results")
        return results
    
    def get_metadata(self) -> Dict:
        """
        Returns dataset metadata.
        
        Returns:
            Dict: Metadata
        """
        if self._dataset_service:
            return {
                "source": "NIH Chest X-ray14",
                "stats": self._dataset_service.get_stats()
            }
        
        return {"source": "No dataset connected"}
    
    def check_health(self) -> tuple:
        """
        Service health check.
        
        Returns:
            tuple: (status, message)
        """
        if self._dataset_service:
            try:
                stats = self._dataset_service.get_stats()
                patient_count = stats.get('total_patients', 0)
                if patient_count > 0:
                    return True, f"Data service running - {patient_count} patients (NIH Dataset)"
            except Exception as e:
                logger.error(f"Health check error: {e}")
        
        return False, "Data service not connected"


# Singleton instance
data_service = DataService()
