"""
Vector Search Service - Vektör Veritabanı Arama Servisi
Benzer vakaları bulmak için vektör benzerlik araması yapar
"""

import logging
from typing import List, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class VectorSearchService:
    """
    Vektör benzerlik arama servisi.
    Prototip aşamasında mock olarak çalışır.
    Gerçek implementasyonda FAISS, Qdrant veya Pinecone kullanılabilir.
    """
    
    def __init__(self):
        self.index_loaded = True  # Mock için her zaman True
        self.mock_mode = True
        
        # Mock vektör veritabanı - gerçekte bu FAISS/Qdrant'ta olacak
        self._mock_database = self._initialize_mock_db()
        
        logger.info("Vector Search Service başlatıldı (mock mod)")
    
    def _initialize_mock_db(self) -> dict:
        """
        Mock vektör veritabanını başlatır.
        
        Returns:
            dict: Hasta ID -> vektör eşlemesi
        """
        np.random.seed(42)  # Tutarlı sonuçlar için
        
        database = {
            "1045": np.random.randn(128).astype(np.float32),
            "1046": np.random.randn(128).astype(np.float32),
            "1047": np.random.randn(128).astype(np.float32),
            "1048": np.random.randn(128).astype(np.float32),
        }
        
        # Vektörleri normalize et
        for patient_id in database:
            vec = database[patient_id]
            database[patient_id] = vec / np.linalg.norm(vec)
        
        return database
    
    def search_similar(
        self, 
        query_vector: List[float], 
        top_k: int = 1
    ) -> List[Tuple[str, float]]:
        """
        Verilen vektöre en benzer vakaları bulur.
        
        Args:
            query_vector: Sorgu vektörü
            top_k: Döndürülecek sonuç sayısı
            
        Returns:
            List[Tuple[str, float]]: (hasta_id, benzerlik_skoru) listesi
        """
        logger.info(f"Vektör araması başlatılıyor - top_k: {top_k}")
        
        if self.mock_mode:
            return self._mock_search(query_vector, top_k)
        
        # Gerçek implementasyon buraya gelecek
        # FAISS veya Qdrant kullanılacak
        raise NotImplementedError("Gerçek vektör arama henüz implementlenmedi")
    
    def _mock_search(
        self, 
        query_vector: List[float], 
        top_k: int
    ) -> List[Tuple[str, float]]:
        """
        Mock vektör araması.
        Prototip için her zaman Hasta 1045'i döndürür.
        
        Args:
            query_vector: Sorgu vektörü
            top_k: Döndürülecek sonuç sayısı
            
        Returns:
            List[Tuple[str, float]]: Benzer vakalar
        """
        query = np.array(query_vector, dtype=np.float32)
        
        # Query vektörünü normalize et
        query_norm = np.linalg.norm(query)
        if query_norm > 0:
            query = query / query_norm
        
        # Tüm vektörlerle cosine similarity hesapla
        similarities = []
        for patient_id, db_vector in self._mock_database.items():
            # Cosine similarity = dot product (vektörler zaten normalize)
            similarity = float(np.dot(query, db_vector))
            # Similarity'yi 0-1 arasına normalize et
            similarity = (similarity + 1) / 2
            similarities.append((patient_id, similarity))
        
        # Benzerliğe göre sırala (en yüksek önce)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Prototip için: Her zaman 1045'i en üste koy
        # Bu, demo akışının tutarlı olmasını sağlar
        result = [("1045", 0.89)]  # Sabit yüksek benzerlik skoru
        
        # Diğer sonuçları ekle (top_k > 1 ise)
        for patient_id, score in similarities:
            if patient_id != "1045" and len(result) < top_k:
                result.append((patient_id, score * 0.7))  # Daha düşük skor
        
        logger.info(f"Vektör araması tamamlandı - En benzer: {result[0][0]} ({result[0][1]:.2%})")
        
        return result[:top_k]
    
    def add_vector(self, patient_id: str, vector: List[float]) -> bool:
        """
        Yeni bir vektörü veritabanına ekler.
        
        Args:
            patient_id: Hasta ID
            vector: Vektör gömülümü
            
        Returns:
            bool: Başarılı mı
        """
        if self.mock_mode:
            vec = np.array(vector, dtype=np.float32)
            vec = vec / np.linalg.norm(vec)
            self._mock_database[patient_id] = vec
            logger.info(f"[MOCK] Vektör eklendi: {patient_id}")
            return True
        
        raise NotImplementedError("Gerçek vektör ekleme henüz implementlenmedi")
    
    def get_index_stats(self) -> dict:
        """
        Vektör index istatistiklerini döndürür.
        
        Returns:
            dict: Index metadata
        """
        return {
            "total_vectors": len(self._mock_database),
            "dimension": 128,
            "index_type": "mock_cosine",
            "status": "loaded" if self.index_loaded else "not_loaded"
        }
    
    def check_health(self) -> Tuple[bool, str]:
        """
        Servis sağlık kontrolü.
        
        Returns:
            tuple: (durum, mesaj)
        """
        if self.index_loaded:
            return True, f"Vektör DB çalışıyor - {len(self._mock_database)} vektör (mock mod)"
        return False, "Vektör index yüklenemedi"


# Singleton instance
search_service = VectorSearchService()
