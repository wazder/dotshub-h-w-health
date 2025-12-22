"""
AI Service - CNN Tabanlı Görüntü Sınıflandırma
X-Ray görüntülerini analiz eder ve vektör gömülümü üretir

⚠️ NOT: Bu servis LLM/GPT KULLANMAZ!
Sadece CNN (Convolutional Neural Network) tabanlı görüntü sınıflandırma yapar.

Pipeline:
    DICOM → PNG (1024x1024) → CNN Model → Sınıflandırma + Embedding
"""

import os
import time
import random
import logging
from typing import Optional, Union
from io import BytesIO

import numpy as np
from dotenv import load_dotenv

from .image_converter import image_converter

load_dotenv()

logger = logging.getLogger(__name__)


# NIH ChestX-ray14 Dataset sınıfları
NIH_LABELS = [
    "Atelectasis",      # Atelektazi
    "Cardiomegaly",     # Kardiyomegali
    "Effusion",         # Efüzyon
    "Infiltration",     # İnfiltrasyon
    "Mass",             # Kitle
    "Nodule",           # Nodül
    "Pneumonia",        # Pnömoni
    "Pneumothorax",     # Pnömotoraks
    "Consolidation",    # Konsolidasyon
    "Edema",            # Ödem
    "Emphysema",        # Amfizem
    "Fibrosis",         # Fibrozis
    "Pleural_Thickening",  # Plevral Kalınlaşma
    "Hernia",           # Herni
    "No Finding"        # Normal
]

# Türkçe etiket çevirisi
LABEL_TR = {
    "Atelectasis": "Atelektazi",
    "Cardiomegaly": "Kardiyomegali",
    "Effusion": "Plevral Efüzyon",
    "Infiltration": "İnfiltrasyon",
    "Mass": "Kitle",
    "Nodule": "Nodül",
    "Pneumonia": "Pnömoni",
    "Pneumothorax": "Pnömotoraks",
    "Consolidation": "Konsolidasyon",
    "Edema": "Pulmoner Ödem",
    "Emphysema": "Amfizem",
    "Fibrosis": "Fibrozis",
    "Pleural_Thickening": "Plevral Kalınlaşma",
    "Hernia": "Herni",
    "No Finding": "Normal"
}


class AIService:
    """
    CNN tabanlı tıbbi görüntü sınıflandırma servisi.
    
    Pipeline:
        1. DICOM/PNG al
        2. PNG'ye dönüştür (1024x1024, grayscale)
        3. CNN modeline ver
        4. Sınıflandırma sonucu + embedding döndür
    
    Prototip aşamasında mock sonuçlar döndürür.
    Gerçek implementasyonda PyTorch/TensorFlow modeli entegre edilir.
    """
    
    # NIH ChestX-ray14 dataset ile uyumlu boyut
    INPUT_SIZE = (1024, 1024)
    
    def __init__(self):
        self.model_delay = float(os.getenv("AI_MODEL_DELAY", "0.5"))
        self.vector_dimension = int(os.getenv("VECTOR_DIMENSION", "128"))
        self.model_loaded = True  # Mock için her zaman True
        self.model = None  # Gerçek model buraya yüklenecek
        
        logger.info(f"AI Service başlatıldı - Input: {self.INPUT_SIZE}, Embedding: {self.vector_dimension}D")
    
    def analyze_image(self, image_bytes: bytes, filename: Optional[str] = None) -> dict:
        """
        Görüntüyü analiz eder.
        
        Desteklenen formatlar: DICOM, NIFTI, PNG, JPEG, JPG
        Format otomatik algılanır.
        
        Args:
            image_bytes: Görüntü dosyasının byte içeriği
            filename: Opsiyonel dosya adı (format algılama için)
            
        Returns:
            dict: Analiz sonucu
                - label: Tespit edilen durum (İngilizce)
                - label_tr: Türkçe etiket
                - probability: Olasılık (0-1)
                - confidence: Güven seviyesi
                - embedding: Vektör gömülümü (list)
                - all_predictions: Tüm sınıflar için olasılıklar
        """
        # Format algıla
        detected_format = image_converter.detect_format(image_bytes, filename)
        logger.info(f"AI analizi başlatılıyor - Format: {detected_format.value}")
        
        # 1. Görüntüyü numpy array'e dönüştür (tüm formatlar desteklenir)
        img_array = image_converter.convert_to_numpy(
            image_bytes, 
            self.INPUT_SIZE, 
            filename
        )
        
        if img_array is None:
            logger.error("Görüntü dönüştürülemedi!")
            return self._get_error_result()
        
        logger.info(f"Görüntü hazır: shape={img_array.shape}")
        
        # 2. Model inference (şu an mock)
        time.sleep(self.model_delay)  # Model işlem süresini simüle et
        predictions, embedding = self._run_inference(img_array)
        
        # 3. En yüksek olasılıklı sınıfı bul
        max_idx = np.argmax(predictions)
        label = NIH_LABELS[max_idx]
        probability = float(predictions[max_idx])
        
        # 4. Güven seviyesi belirle
        if probability >= 0.85:
            confidence = "Yüksek"
        elif probability >= 0.65:
            confidence = "Orta"
        else:
            confidence = "Düşük"
        
        # 5. Tüm predictions'ı dict olarak hazırla
        all_predictions = {
            NIH_LABELS[i]: float(predictions[i]) 
            for i in range(len(NIH_LABELS))
        }
        
        result = {
            "label": label,
            "label_tr": LABEL_TR.get(label, label),
            "probability": round(probability, 4),
            "confidence": confidence,
            "embedding": embedding.tolist(),
            "all_predictions": all_predictions
        }
        
        logger.info(f"AI analizi tamamlandı - {label} ({LABEL_TR.get(label)}): {probability:.2%}")
        
        return result
    
    def _run_inference(self, img_array: np.ndarray) -> tuple:
        """
        Model inference çalıştırır.
        
        Gerçek implementasyonda:
            - img_array'i model formatına çevir (batch, channel, height, width)
            - PyTorch/TensorFlow modeline ver
            - Softmax çıktısı al (predictions)
            - Son dense katmandan embedding al
        
        Args:
            img_array: Normalize edilmiş görüntü (H, W, 1), değerler 0-1 arası
            
        Returns:
            tuple: (predictions, embedding)
                - predictions: (15,) shape, her sınıf için olasılık
                - embedding: (vector_dimension,) shape, özellik vektörü
        """
        # === MOCK IMPLEMENTATION ===
        # Gerçek model yüklendiğinde bu fonksiyon değişecek
        
        # Görüntüden "seed" oluştur (tutarlı sonuçlar için)
        img_seed = int(np.mean(img_array) * 10000) % 10000
        np.random.seed(img_seed)
        
        # Mock predictions (softmax benzeri)
        raw_scores = np.random.randn(len(NIH_LABELS))
        
        # Prototip için "Mass" (Kitle) sınıfını yüksek tut (Hasta 1045 eşleşmesi için)
        mass_idx = NIH_LABELS.index("Mass")
        raw_scores[mass_idx] += 2.0  # Mass'ı öne çıkar
        
        # Softmax uygula
        exp_scores = np.exp(raw_scores - np.max(raw_scores))
        predictions = exp_scores / exp_scores.sum()
        
        # Mock embedding
        embedding = np.random.randn(self.vector_dimension).astype(np.float32)
        embedding = embedding / np.linalg.norm(embedding)  # L2 normalize
        
        return predictions, embedding
    
    def _get_error_result(self) -> dict:
        """Hata durumunda döndürülecek sonuç."""
        return {
            "label": "Error",
            "label_tr": "Hata",
            "probability": 0.0,
            "confidence": "Yok",
            "embedding": [0.0] * self.vector_dimension,
            "all_predictions": {label: 0.0 for label in NIH_LABELS}
        }
    
    def get_model_info(self) -> dict:
        """Model bilgilerini döndürür."""
        return {
            "name": "ChestXray-CNN-Mock-v1",
            "version": "1.0.0-prototype",
            "dataset": "NIH ChestX-ray14",
            "num_classes": len(NIH_LABELS),
            "classes": NIH_LABELS,
            "input_size": self.INPUT_SIZE,
            "vector_dimension": self.vector_dimension,
            "status": "loaded" if self.model_loaded else "not_loaded"
        }
    
    def check_health(self) -> tuple:
        """Servis sağlık kontrolü."""
        converter_ok, converter_msg = image_converter.check_health()
        
        if self.model_loaded and converter_ok:
            return True, f"AI servisi çalışıyor (mock mod) - {len(NIH_LABELS)} sınıf"
        elif not converter_ok:
            return False, f"Image Converter hatası: {converter_msg}"
        return False, "Model yüklenemedi"


# Singleton instance
ai_service = AIService()

