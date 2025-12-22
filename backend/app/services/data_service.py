"""
Data Service - Hasta Verisi Servisi
NIH Dataset + Sentetik JSON verilerini birleştirir
"""

import os
import json
import logging
from typing import Optional, Dict, List
from pathlib import Path

logger = logging.getLogger(__name__)


class DataService:
    """
    Hasta verisi yönetim servisi.
    NIH Dataset'ten gerçek hasta bilgilerini ve
    JSON dosyasından ek sentetik verileri okur.
    """
    
    def __init__(self, data_path: Optional[str] = None):
        """
        DataService'i başlatır.
        
        Args:
            data_path: Veri dosyası yolu (opsiyonel)
        """
        if data_path is None:
            # Varsayılan yol: app/data/synthetic_patients.json
            current_dir = Path(__file__).parent.parent
            data_path = current_dir / "data" / "synthetic_patients.json"
        
        self.data_path = Path(data_path)
        self._data_cache: Optional[Dict] = None
        self._dataset_service = None
        self._load_data()
    
    def set_dataset_service(self, dataset_service):
        """Dataset service referansını ayarla."""
        self._dataset_service = dataset_service
        logger.info("Dataset service bağlandı")
    
    def _load_data(self) -> None:
        """
        JSON dosyasından verileri yükler ve cache'ler.
        """
        try:
            if self.data_path.exists():
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    self._data_cache = json.load(f)
                patient_count = len(self._data_cache.get('patients', {}))
                logger.info(f"Sentetik hasta verileri yüklendi: {patient_count} hasta")
            else:
                logger.warning(f"Veri dosyası bulunamadı: {self.data_path}")
                self._data_cache = {"patients": {}, "metadata": {}}
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse hatası: {e}")
            self._data_cache = {"patients": {}, "metadata": {}}
        except Exception as e:
            logger.error(f"Veri yükleme hatası: {e}")
            self._data_cache = {"patients": {}, "metadata": {}}
    
    def get_patient_history(self, patient_id: str) -> Optional[Dict]:
        """
        Belirli bir hastanın geçmiş bilgilerini getirir.
        Önce dataset_service'den, sonra sentetik verilerden bakar.
        
        Args:
            patient_id: Hasta ID
            
        Returns:
            dict: Hasta bilgileri veya None
        """
        # Önce NIH dataset'ten ara
        if self._dataset_service:
            patient = self._dataset_service.get_patient_info(patient_id)
            if patient:
                logger.info(f"NIH Dataset'ten hasta bulundu: {patient_id}")
                return patient
        
        # Sonra sentetik verilerden ara
        if self._data_cache is None:
            self._load_data()
        
        patients = self._data_cache.get('patients', {})
        patient = patients.get(str(patient_id))
        
        if patient:
            logger.info(f"Sentetik veriden hasta bulundu: {patient_id}")
            return patient
        
        logger.warning(f"Hasta bulunamadı: {patient_id}")
        return None
    
    def get_patient_summary(self, patient_id: str) -> str:
        """
        Hastanın özet hikaye metnini döndürür.
        
        Args:
            patient_id: Hasta ID
            
        Returns:
            str: Hasta hikayesi özeti
        """
        patient = self.get_patient_history(patient_id)
        
        if patient:
            return patient.get('history', f"Hasta {patient_id} için detay bulunamadı.")
        
        return f"Hasta {patient_id} kayıtlarda bulunamadı."
    
    def list_all_patients(self) -> List[str]:
        """
        Tüm hasta ID'lerini listeler.
        NIH dataset ve sentetik verileri birleştirir.
        
        Returns:
            List[str]: Hasta ID listesi
        """
        patient_ids = set()
        
        # NIH dataset'ten
        if self._dataset_service:
            dataset_patients = self._dataset_service.list_patients(limit=100)
            patient_ids.update(dataset_patients)
        
        # Sentetik verilerden
        if self._data_cache is None:
            self._load_data()
        
        patient_ids.update(self._data_cache.get('patients', {}).keys())
        
        return list(patient_ids)
    
    def search_by_diagnosis(self, diagnosis: str) -> List[Dict]:
        """
        Belirli bir tanıya göre hastaları arar.
        
        Args:
            diagnosis: Aranacak tanı (kısmi eşleşme)
            
        Returns:
            List[Dict]: Eşleşen hastalar
        """
        if self._data_cache is None:
            self._load_data()
        
        results = []
        diagnosis_lower = diagnosis.lower()
        
        for patient_id, patient_data in self._data_cache.get('patients', {}).items():
            patient_diagnosis = patient_data.get('diagnosis', '').lower()
            if diagnosis_lower in patient_diagnosis:
                results.append(patient_data)
        
        logger.info(f"Tanı araması: '{diagnosis}' - {len(results)} sonuç")
        return results
    
    def add_patient(self, patient_data: Dict) -> bool:
        """
        Yeni hasta ekler (runtime cache'e - dosyaya yazmaz).
        
        Args:
            patient_data: Hasta verisi (patient_id içermeli)
            
        Returns:
            bool: Başarılı mı
        """
        if self._data_cache is None:
            self._load_data()
        
        patient_id = patient_data.get('patient_id')
        if not patient_id:
            logger.error("patient_id alanı gerekli")
            return False
        
        self._data_cache['patients'][str(patient_id)] = patient_data
        logger.info(f"Hasta eklendi (cache): {patient_id}")
        return True
    
    def get_metadata(self) -> Dict:
        """
        Veri dosyası metadata'sını döndürür.
        
        Returns:
            Dict: Metadata
        """
        if self._data_cache is None:
            self._load_data()
        
        return self._data_cache.get('metadata', {})
    
    def reload_data(self) -> None:
        """
        Verileri dosyadan yeniden yükler.
        """
        self._data_cache = None
        self._load_data()
        logger.info("Veriler yeniden yüklendi")
    
    def check_health(self) -> tuple:
        """
        Servis sağlık kontrolü.
        
        Returns:
            tuple: (durum, mesaj)
        """
        patient_count = 0
        
        # NIH Dataset
        if self._dataset_service:
            try:
                stats = self._dataset_service.get_stats()
                patient_count += stats.get('patient_count', 0)
            except:
                pass
        
        # Sentetik veriler
        if self._data_cache is not None:
            patient_count += len(self._data_cache.get('patients', {}))
        
        if patient_count > 0:
            return True, f"Veri servisi çalışıyor - {patient_count} hasta (NIH + sentetik)"
        
        return False, "Veri yüklenemedi"


# Singleton instance
data_service = DataService()
