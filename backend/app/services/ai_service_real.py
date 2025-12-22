"""
AI Service - Gerçek PyTorch ResNet50 Model Entegrasyonu
X-Ray görüntülerini analiz eder ve vektör gömülümü üretir

Bu servis gerçek eğitilmiş modeli kullanır:
- Model: ResNet50 (Binary Classification)
- Dataset: NIH Chest X-rays
- Sınıflar: No Finding (0) vs Mass/Nodule (1)

Pipeline:
    Image → Resize (224x224) → Normalize → ResNet50 → Prediction + Embedding
"""

import os
import logging
from typing import Optional, Tuple, Dict
from pathlib import Path

import numpy as np
from PIL import Image
from io import BytesIO

import torch
import torch.nn as nn
from torchvision import transforms, models

from dotenv import load_dotenv
from .image_converter import image_converter

load_dotenv()

logger = logging.getLogger(__name__)


# Model sınıfları (Binary classification)
BINARY_LABELS = ["No Finding", "Pathology"]  # 0: Normal, 1: Mass/Nodule

# NIH ChestX-ray14 tüm sınıflar (multi-label için referans)
NIH_LABELS = [
    "Atelectasis", "Cardiomegaly", "Effusion", "Infiltration", "Mass",
    "Nodule", "Pneumonia", "Pneumothorax", "Consolidation", "Edema",
    "Emphysema", "Fibrosis", "Pleural_Thickening", "Hernia", "No Finding"
]

# Türkçe etiket çevirisi
LABEL_TR = {
    "No Finding": "Normal",
    "Pathology": "Patoloji Tespit Edildi",
    "Mass": "Kitle",
    "Nodule": "Nodül",
    "Mass|Nodule": "Kitle/Nodül",
    "Atelectasis": "Atelektazi",
    "Cardiomegaly": "Kardiyomegali",
    "Effusion": "Plevral Efüzyon",
    "Infiltration": "İnfiltrasyon",
    "Pneumonia": "Pnömoni",
    "Pneumothorax": "Pnömotoraks",
    "Consolidation": "Konsolidasyon",
    "Edema": "Pulmoner Ödem",
    "Emphysema": "Amfizem",
    "Fibrosis": "Fibrozis",
    "Pleural_Thickening": "Plevral Kalınlaşma",
    "Hernia": "Herni"
}


class ChestXrayModel(nn.Module):
    """
    ResNet50 tabanlı Chest X-ray sınıflandırma modeli.
    Binary classification: No Finding vs Pathology (Mass/Nodule)
    """
    
    def __init__(self, num_classes: int = 1):
        super(ChestXrayModel, self).__init__()
        
        # Fine-tuned ResNet50 (sınıflandırma için)
        self.resnet = models.resnet50(weights=None)
        
        # Son fully connected katmanı değiştir
        num_features = self.resnet.fc.in_features
        self.resnet.fc = nn.Linear(num_features, num_classes)
        
        # Embedding çıkarmak için hook
        self.embedding = None
        self._register_hook()
        
        # Pretrained ResNet50 (benzerlik araması için)
        # Fine-tuned model patoloji sınıflandırma için optimize edilmiş,
        # görsel benzerlik için ImageNet pretrained ağırlıkları daha iyi
        self.pretrained_resnet = models.resnet50(weights=models.ResNet50_Weights.DEFAULT)
        self.pretrained_resnet.fc = nn.Identity()  # FC katmanını kaldır
        self.pretrained_embedding = None
        self._register_pretrained_hook()
    
    def _register_hook(self):
        """ResNet'in son avgpool katmanından embedding çıkarmak için hook."""
        def hook(module, input, output):
            self.embedding = output.squeeze()
        
        self.resnet.avgpool.register_forward_hook(hook)
    
    def _register_pretrained_hook(self):
        """Pretrained ResNet'ten embedding çıkarmak için hook."""
        def hook(module, input, output):
            self.pretrained_embedding = output.squeeze()
        
        self.pretrained_resnet.avgpool.register_forward_hook(hook)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.resnet(x)
    
    def forward_pretrained(self, x: torch.Tensor) -> torch.Tensor:
        """Pretrained model ile forward pass - benzerlik embedding'i için."""
        return self.pretrained_resnet(x)
    
    def get_embedding(self) -> Optional[torch.Tensor]:
        """Son forward pass'tan fine-tuned embedding döndür."""
        return self.embedding
    
    def get_pretrained_embedding(self) -> Optional[torch.Tensor]:
        """Pretrained model embedding'i döndür (benzerlik için daha iyi)."""
        return self.pretrained_embedding


class RealAIService:
    """
    Gerçek PyTorch model ile AI analiz servisi.
    """
    
    # ResNet50 standart giriş boyutu
    INPUT_SIZE = (224, 224)
    
    def __init__(self):
        self.model: Optional[ChestXrayModel] = None
        self.model_loaded = False
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.vector_dimension = 2048  # ResNet50 avgpool çıktısı
        
        # Model yolu
        self.model_path = self._find_model_path()
        
        # Görüntü dönüşümleri (eğitimle aynı)
        self.transform = transforms.Compose([
            transforms.Resize(self.INPUT_SIZE),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],  # ImageNet normalization
                std=[0.229, 0.224, 0.225]
            )
        ])
        
        # Modeli yükle
        self._load_model()
        
        logger.info(f"AI Service başlatıldı - Device: {self.device}, Model: {'Loaded' if self.model_loaded else 'Not Found'}")
    
    def _find_model_path(self) -> Optional[Path]:
        """Model dosyasını bul."""
        possible_paths = [
            Path(__file__).parent.parent.parent.parent / "model" / "best_model.pth",
            Path("/Users/wazder/Documents/GitHub/dotshub-h-w-health/model/best_model.pth"),
            Path("model/best_model.pth"),
            Path("../model/best_model.pth"),
        ]
        
        for path in possible_paths:
            if path.exists():
                logger.info(f"Model dosyası bulundu: {path}")
                return path
        
        logger.warning("Model dosyası bulunamadı!")
        return None
    
    def _load_model(self) -> bool:
        """PyTorch modelini yükle."""
        if self.model_path is None or not self.model_path.exists():
            logger.error(f"Model dosyası bulunamadı: {self.model_path}")
            return False
        
        try:
            # Model oluştur
            self.model = ChestXrayModel(num_classes=1)
            
            # Ağırlıkları yükle (fine-tuned model için)
            state_dict = torch.load(self.model_path, map_location=self.device, weights_only=False)
            
            # State dict formatını kontrol et
            if isinstance(state_dict, dict) and 'model_state_dict' in state_dict:
                state_dict = state_dict['model_state_dict']
            
            self.model.load_state_dict(state_dict, strict=False)
            self.model.to(self.device)
            
            # Pretrained modeli de aynı device'a taşı
            self.model.pretrained_resnet.to(self.device)
            
            self.model.eval()
            
            self.model_loaded = True
            logger.info(f"✅ Model başarıyla yüklendi: {self.model_path}")
            return True
            
        except Exception as e:
            logger.error(f"Model yükleme hatası: {e}", exc_info=True)
            self.model_loaded = False
            return False
    
    def analyze_image(self, image_bytes: bytes, filename: Optional[str] = None) -> Dict:
        """
        Görüntüyü analiz eder.
        
        Args:
            image_bytes: Görüntü dosyasının byte içeriği
            filename: Opsiyonel dosya adı
            
        Returns:
            dict: Analiz sonucu
        """
        if not self.model_loaded:
            logger.error("Model yüklenmemiş!")
            return self._get_error_result("Model yüklenmemiş")
        
        try:
            # Format algıla
            detected_format = image_converter.detect_format(image_bytes, filename)
            logger.info(f"AI analizi başlatılıyor - Format: {detected_format.value}")
            
            # 1. Görüntüyü PIL Image'a dönüştür
            pil_image = self._bytes_to_pil(image_bytes, filename)
            
            if pil_image is None:
                return self._get_error_result("Görüntü okunamadı")
            
            # 2. RGB'ye dönüştür (grayscale ise)
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            
            logger.info(f"Görüntü hazır: {pil_image.size}, mode: {pil_image.mode}")
            
            # 3. Transform uygula
            input_tensor = self.transform(pil_image).unsqueeze(0).to(self.device)
            
            # 4. Inference - hem sınıflandırma hem de benzerlik embedding'i
            with torch.no_grad():
                # Sınıflandırma modeli
                output = self.model(input_tensor)
                probability = torch.sigmoid(output).item()
                
                # Pretrained model (benzerlik için)
                self.model.forward_pretrained(input_tensor)
                pretrained_embedding = self.model.get_pretrained_embedding()
            
            # 5. Pretrained embedding'i numpy'a çevir (benzerlik için daha iyi)
            if pretrained_embedding is not None:
                embedding_np = pretrained_embedding.cpu().numpy().flatten()
                # L2 normalize
                embedding_np = embedding_np / (np.linalg.norm(embedding_np) + 1e-8)
            else:
                embedding_np = np.zeros(self.vector_dimension, dtype=np.float32)
            
            # 6. Sınıflandırma
            is_pathology = probability > 0.5
            label = "Pathology" if is_pathology else "No Finding"
            label_detailed = "Mass|Nodule" if is_pathology else "No Finding"
            
            # 7. Güven seviyesi
            conf_score = probability if is_pathology else (1 - probability)
            if conf_score >= 0.85:
                confidence = "Yüksek"
            elif conf_score >= 0.65:
                confidence = "Orta"
            else:
                confidence = "Düşük"
            
            result = {
                "label": label_detailed,
                "label_tr": LABEL_TR.get(label_detailed, LABEL_TR.get(label, label)),
                "probability": round(probability, 4),
                "confidence": confidence,
                "embedding": embedding_np.tolist(),
                "is_pathology": is_pathology,
                "all_predictions": {
                    "No Finding": round(1 - probability, 4),
                    "Mass|Nodule": round(probability, 4)
                }
            }
            
            logger.info(f"AI analizi tamamlandı - {label_detailed} ({LABEL_TR.get(label_detailed, label)}): {probability:.2%}")
            
            return result
            
        except Exception as e:
            logger.error(f"Analiz hatası: {e}", exc_info=True)
            return self._get_error_result(str(e))
    
    def _bytes_to_pil(self, image_bytes: bytes, filename: Optional[str] = None) -> Optional[Image.Image]:
        """Byte verisini PIL Image'a dönüştür."""
        try:
            # Önce doğrudan PIL ile dene
            pil_image = Image.open(BytesIO(image_bytes))
            return pil_image
        except Exception as e:
            logger.warning(f"Direct PIL failed: {e}, trying image_converter...")
        
        try:
            # image_converter ile numpy'a çevir, sonra PIL
            np_array = image_converter.convert_to_numpy(image_bytes, self.INPUT_SIZE, filename)
            if np_array is not None:
                # Grayscale ise (H, W, 1) -> (H, W)
                if np_array.ndim == 3 and np_array.shape[2] == 1:
                    np_array = np_array.squeeze(2)
                
                # 0-1 aralığındaysa 0-255'e çevir
                if np_array.max() <= 1.0:
                    np_array = (np_array * 255).astype(np.uint8)
                
                return Image.fromarray(np_array)
        except Exception as e:
            logger.error(f"Image conversion failed: {e}")
        
        return None
    
    def _get_error_result(self, error_msg: str = "Unknown error") -> Dict:
        """Hata durumunda döndürülecek sonuç."""
        return {
            "label": "Error",
            "label_tr": f"Hata: {error_msg}",
            "probability": 0.0,
            "confidence": "Yok",
            "embedding": [0.0] * self.vector_dimension,
            "is_pathology": False,
            "all_predictions": {"No Finding": 0.0, "Mass|Nodule": 0.0}
        }
    
    def get_embedding_for_image(self, image_path: str) -> Optional[np.ndarray]:
        """
        Bir görüntü dosyasından embedding çıkar.
        Vektör veritabanı oluşturmak için kullanılır.
        """
        try:
            with open(image_path, 'rb') as f:
                image_bytes = f.read()
            
            result = self.analyze_image(image_bytes, os.path.basename(image_path))
            
            if result["label"] != "Error":
                return np.array(result["embedding"], dtype=np.float32)
            
            return None
            
        except Exception as e:
            logger.error(f"Embedding extraction error: {e}")
            return None
    
    def get_model_info(self) -> Dict:
        """Model bilgilerini döndürür."""
        return {
            "name": "ChestXray-ResNet50-Binary",
            "version": "1.0.0",
            "dataset": "NIH ChestX-ray14",
            "task": "Binary Classification (No Finding vs Mass/Nodule)",
            "num_classes": 2,
            "classes": BINARY_LABELS,
            "input_size": self.INPUT_SIZE,
            "vector_dimension": self.vector_dimension,
            "device": str(self.device),
            "status": "loaded" if self.model_loaded else "not_loaded",
            "model_path": str(self.model_path) if self.model_path else None
        }
    
    def check_health(self) -> Tuple[bool, str]:
        """Servis sağlık kontrolü."""
        converter_ok, converter_msg = image_converter.check_health()
        
        if self.model_loaded and converter_ok:
            return True, f"AI servisi çalışıyor (Gerçek Model) - Device: {self.device}"
        elif not self.model_loaded:
            return False, f"Model yüklenemedi: {self.model_path}"
        elif not converter_ok:
            return False, f"Image Converter hatası: {converter_msg}"
        return False, "Bilinmeyen hata"


# Singleton instance
ai_service = RealAIService()
