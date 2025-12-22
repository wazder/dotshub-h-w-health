"""
Vector Search Service - Gerçek Embedding Tabanlı Benzer Vaka Arama
Cosine similarity ile en benzer vakaları bulur.

Bu servis:
1. Başlangıçta dataset'ten sample görüntülerin embedding'lerini çıkarır
2. Yeni görüntü için embedding alır
3. Cosine similarity ile en benzer vakaları bulur
"""

import os
import json
import logging
from typing import Optional, List, Tuple, Dict
from pathlib import Path
import random

import numpy as np

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class VectorSearchService:
    """
    Gerçek vektör tabanlı benzer vaka arama servisi.
    """
    
    def __init__(self):
        self.vector_dimension = 2048  # ResNet50 avgpool output
        self.index_path = Path(__file__).parent.parent / "data" / "vector_index.npz"
        
        # Vektör veritabanı
        self.embeddings: Optional[np.ndarray] = None
        self.image_ids: List[str] = []
        self.patient_ids: List[str] = []
        
        # Index yükleme/oluşturma
        self._initialized = False
        
        logger.info("Vector Search Service başlatıldı")
    
    def initialize(self, dataset_service, ai_service, sample_size: int = 100):
        """
        Vektör veritabanını başlat.
        Eğer kayıtlı index varsa yükle, yoksa oluştur.
        """
        if self._initialized:
            return True
        
        # Önce kayıtlı index'i kontrol et
        if self._load_index():
            self._initialized = True
            return True
        
        # Index yoksa oluştur
        logger.info(f"Vektör index'i oluşturuluyor - {sample_size} örnek...")
        
        try:
            # Patoloji görüntülerinden sample al
            pathology_images = dataset_service.get_pathology_images(limit=sample_size * 2)
            
            if len(pathology_images) == 0:
                logger.warning("Patoloji görüntüsü bulunamadı!")
                self._create_mock_index(dataset_service)
                self._initialized = True
                return True
            
            # Rastgele seç
            sample_images = random.sample(pathology_images, min(sample_size, len(pathology_images)))
            
            embeddings_list = []
            image_ids_list = []
            patient_ids_list = []
            
            for image_id in sample_images:
                image_path = dataset_service.get_image_path(image_id)
                
                if image_path is None:
                    continue
                
                # Embedding çıkar
                embedding = ai_service.get_embedding_for_image(str(image_path))
                
                if embedding is not None:
                    embeddings_list.append(embedding)
                    image_ids_list.append(image_id)
                    
                    # Hasta ID'sini al
                    image_info = dataset_service.get_image_info(image_id)
                    if image_info:
                        patient_ids_list.append(image_info['patient_id'])
                    else:
                        patient_ids_list.append("unknown")
                
                # Progress log
                if len(embeddings_list) % 10 == 0:
                    logger.info(f"Embedding progress: {len(embeddings_list)}/{sample_size}")
            
            if len(embeddings_list) > 0:
                self.embeddings = np.array(embeddings_list, dtype=np.float32)
                self.image_ids = image_ids_list
                self.patient_ids = patient_ids_list
                
                # Index'i kaydet
                self._save_index()
                
                logger.info(f"Vektör index'i oluşturuldu: {len(self.image_ids)} görüntü")
                self._initialized = True
                return True
            else:
                logger.warning("Hiç embedding çıkarılamadı, mock index kullanılıyor")
                self._create_mock_index(dataset_service)
                self._initialized = True
                return True
            
        except Exception as e:
            logger.error(f"Index oluşturma hatası: {e}", exc_info=True)
            self._create_mock_index(dataset_service)
            self._initialized = True
            return False
    
    def _create_mock_index(self, dataset_service):
        """Model yüklenemediğinde mock index oluştur."""
        logger.info("Mock vektör index'i oluşturuluyor...")
        
        pathology_images = dataset_service.get_pathology_images(limit=50)
        
        self.image_ids = pathology_images[:50] if pathology_images else []
        self.patient_ids = []
        
        for image_id in self.image_ids:
            image_info = dataset_service.get_image_info(image_id)
            if image_info:
                self.patient_ids.append(image_info['patient_id'])
            else:
                self.patient_ids.append("unknown")
        
        # Mock embeddings (rastgele ama tutarlı)
        np.random.seed(42)
        self.embeddings = np.random.randn(len(self.image_ids), self.vector_dimension).astype(np.float32)
        
        # Normalize
        norms = np.linalg.norm(self.embeddings, axis=1, keepdims=True)
        self.embeddings = self.embeddings / (norms + 1e-8)
        
        logger.info(f"Mock index oluşturuldu: {len(self.image_ids)} görüntü")
    
    def _load_index(self) -> bool:
        """Kayıtlı index'i yükle."""
        if not self.index_path.exists():
            return False
        
        try:
            data = np.load(self.index_path, allow_pickle=True)
            self.embeddings = data['embeddings']
            self.image_ids = data['image_ids'].tolist()
            self.patient_ids = data['patient_ids'].tolist()
            
            logger.info(f"Vektör index'i yüklendi: {len(self.image_ids)} görüntü")
            return True
            
        except Exception as e:
            logger.warning(f"Index yükleme hatası: {e}")
            return False
    
    def _save_index(self):
        """Index'i diske kaydet."""
        try:
            self.index_path.parent.mkdir(parents=True, exist_ok=True)
            
            np.savez(
                self.index_path,
                embeddings=self.embeddings,
                image_ids=np.array(self.image_ids),
                patient_ids=np.array(self.patient_ids)
            )
            
            logger.info(f"Vektör index'i kaydedildi: {self.index_path}")
            
        except Exception as e:
            logger.error(f"Index kaydetme hatası: {e}")
    
    def search_similar(self, query_vector: List[float], top_k: int = 5) -> List[Tuple[str, str, float]]:
        """
        Benzer vakaları bul.
        
        Args:
            query_vector: Sorgu embedding vektörü
            top_k: Döndürülecek sonuç sayısı
            
        Returns:
            List of (patient_id, image_id, similarity_score)
        """
        if self.embeddings is None or len(self.embeddings) == 0:
            logger.warning("Vektör index'i boş!")
            return []
        
        try:
            # Query vektörünü numpy'a çevir
            query = np.array(query_vector, dtype=np.float32).flatten()
            
            # Normalize
            query = query / (np.linalg.norm(query) + 1e-8)
            
            # Cosine similarity hesapla
            similarities = np.dot(self.embeddings, query)
            
            # En yüksek k indeksi bul
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            results = []
            seen_patients = set()
            
            for idx in top_indices:
                patient_id = self.patient_ids[idx]
                
                # Aynı hastayı birden fazla kez ekleme
                if patient_id in seen_patients:
                    continue
                
                seen_patients.add(patient_id)
                
                image_id = self.image_ids[idx]
                score = float(similarities[idx])
                
                # Skor'u 0-1 arasına normalize et
                normalized_score = (score + 1) / 2  # Cosine sim [-1, 1] -> [0, 1]
                
                results.append((patient_id, image_id, normalized_score))
                
                if len(results) >= top_k:
                    break
            
            logger.info(f"Vektör araması tamamlandı - {len(results)} sonuç bulundu")
            
            return results
            
        except Exception as e:
            logger.error(f"Arama hatası: {e}", exc_info=True)
            return []
    
    def add_to_index(self, embedding: List[float], image_id: str, patient_id: str):
        """Index'e yeni vektör ekle."""
        try:
            new_embedding = np.array(embedding, dtype=np.float32).reshape(1, -1)
            new_embedding = new_embedding / (np.linalg.norm(new_embedding) + 1e-8)
            
            if self.embeddings is None:
                self.embeddings = new_embedding
            else:
                self.embeddings = np.vstack([self.embeddings, new_embedding])
            
            self.image_ids.append(image_id)
            self.patient_ids.append(patient_id)
            
            # Her 10 eklentiden sonra kaydet
            if len(self.image_ids) % 10 == 0:
                self._save_index()
            
            logger.info(f"Vektör eklendi: {image_id} -> toplam {len(self.image_ids)}")
            
        except Exception as e:
            logger.error(f"Vektör ekleme hatası: {e}")
    
    def get_stats(self) -> Dict:
        """Index istatistikleri."""
        return {
            'total_vectors': len(self.image_ids) if self.image_ids else 0,
            'dimension': self.vector_dimension,
            'unique_patients': len(set(self.patient_ids)) if self.patient_ids else 0,
            'index_path': str(self.index_path),
            'initialized': self._initialized
        }
    
    def check_health(self) -> Tuple[bool, str]:
        """Servis sağlık kontrolü."""
        if self._initialized and self.embeddings is not None:
            return True, f"Vektör DB çalışıyor - {len(self.image_ids)} vektör"
        elif self._initialized:
            return True, "Vektör DB çalışıyor - Boş index"
        return False, "Vektör DB başlatılmadı"


# Singleton instance
vector_search_service = VectorSearchService()
