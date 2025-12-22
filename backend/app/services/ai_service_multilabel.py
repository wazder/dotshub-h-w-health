"""
AI Service - Multi-Label PyTorch ResNet50 Model Entegrasyonu
X-Ray görüntülerini analiz eder ve 14 hastalığı tespit eder

Bu servis yeni eğitilmiş multi-label modeli kullanır:
- Model: ResNet50 (Multi-Label Classification)
- Dataset: NIH Chest X-rays (112K görüntü)
- Sınıflar: 14 hastalık + No Finding
- Val AUC: 0.8347

Pipeline:
    Image → Resize (224x224) → Normalize → ResNet50 → 14 Sigmoid Outputs + Embedding
"""

import os
import logging
from typing import Optional, Tuple, Dict, List
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


# 14 Hastalık listesi (eğitim sırasıyla aynı - DEĞİŞTİRME!)
DISEASE_LABELS = [
    "Atelectasis", "Cardiomegaly", "Effusion", "Infiltration", "Mass",
    "Nodule", "Pneumonia", "Pneumothorax", "Consolidation", "Edema",
    "Emphysema", "Fibrosis", "Pleural_Thickening", "Hernia"
]

NUM_CLASSES = len(DISEASE_LABELS)

# Türkçe etiket çevirisi
LABEL_TR = {
    "No Finding": "Normal - Bulgu Yok",
    "Atelectasis": "Atelektazi",
    "Cardiomegaly": "Kardiyomegali",
    "Effusion": "Plevral Efüzyon",
    "Infiltration": "İnfiltrasyon",
    "Mass": "Kitle",
    "Nodule": "Nodül",
    "Pneumonia": "Pnömoni (Zatürre)",
    "Pneumothorax": "Pnömotoraks",
    "Consolidation": "Konsolidasyon",
    "Edema": "Pulmoner Ödem",
    "Emphysema": "Amfizem",
    "Fibrosis": "Fibrozis",
    "Pleural_Thickening": "Plevral Kalınlaşma",
    "Hernia": "Herni"
}

# Hastalık açıklamaları
DISEASE_DESCRIPTIONS = {
    "Atelectasis": "Akciğerin bir bölümünün çökmesi veya hava kaybetmesi.",
    "Cardiomegaly": "Kalp büyümesi, kalp yetmezliği belirtisi olabilir.",
    "Effusion": "Akciğer zarları arasında sıvı birikimi (plevral efüzyon).",
    "Infiltration": "Akciğer dokusuna sıvı veya hücre birikimi. Enfeksiyon belirtisi olabilir.",
    "Mass": "Akciğerde büyük lezyon. İleri tetkik gerektirir.",
    "Nodule": "Akciğerde küçük yuvarlak lezyon. Takip gerektirebilir.",
    "Pneumonia": "Akciğer enfeksiyonu, tedavi gerektirir.",
    "Pneumothorax": "Akciğer ile göğüs duvarı arasında hava birikimi. ACİL müdahale gerektirebilir!",
    "Consolidation": "Akciğer dokusunun yoğunlaşması, genellikle zatürre belirtisi.",
    "Edema": "Akciğerlerde sıvı birikimi.",
    "Emphysema": "Akciğer hava keseciklerinin hasar görmesi, KOAH'ın bir türü.",
    "Fibrosis": "Akciğer dokusunun sertleşmesi ve skarlaşması.",
    "Pleural_Thickening": "Akciğer zarının kalınlaşması.",
    "Hernia": "Diyafram fıtığı."
}

# ImageNet normalization
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


class ChestXrayMultiLabelModel(nn.Module):
    """
    ResNet50 tabanlı multi-label sınıflandırma modeli.
    14 hastalık için ayrı sigmoid çıktıları.
    """
    
    def __init__(self, num_classes: int = NUM_CLASSES, dropout: float = 0.5):
        super().__init__()
        
        # ResNet50 backbone
        self.backbone = models.resnet50(weights=None)
        num_features = self.backbone.fc.in_features
        self.backbone.fc = nn.Identity()
        
        # Classifier head
        self.classifier = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(num_features, 512),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout / 2),
            nn.Linear(512, num_classes)
        )
        
        # Embedding hook
        self.embedding = None
        self._register_hook()
    
    def _register_hook(self):
        """Embedding çıkarmak için hook."""
        def hook(module, input, output):
            self.embedding = output.squeeze()
        self.backbone.avgpool.register_forward_hook(hook)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        features = self.backbone(x)
        logits = self.classifier(features)
        return logits
    
    def get_embedding(self) -> Optional[torch.Tensor]:
        return self.embedding


class MultiLabelAIService:
    """
    Multi-label PyTorch model ile AI analiz servisi.
    14 hastalığı ayrı ayrı tespit eder.
    """
    
    INPUT_SIZE = (224, 224)
    THRESHOLD = 0.5  # Varsayılan eşik
    
    def __init__(self):
        self.model: Optional[ChestXrayMultiLabelModel] = None
        self.model_loaded = False
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.vector_dimension = 2048
        
        # Model yolu - yeni multi-label model
        self.model_path = self._find_model_path()
        
        # Transform
        self.transform = transforms.Compose([
            transforms.Resize(self.INPUT_SIZE),
            transforms.ToTensor(),
            transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)
        ])
        
        # Modeli yükle
        self._load_model()
        
        logger.info(f"MultiLabel AI Service başlatıldı - Device: {self.device}, Model: {'Loaded' if self.model_loaded else 'Not Found'}")
    
    def _find_model_path(self) -> Optional[Path]:
        """Model dosyasını bul."""
        possible_paths = [
            # Yeni multi-label model (öncelikli)
            Path(__file__).parent.parent.parent.parent / "model" / "model-2.pth",
            Path("/Users/wazder/Documents/GitHub/dotshub-h-w-health/model/model-2.pth"),
            # Fallback - best_model.pth
            Path(__file__).parent.parent.parent.parent / "model" / "best_model.pth",
            Path("/Users/wazder/Documents/GitHub/dotshub-h-w-health/model/best_model.pth"),
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
            self.model = ChestXrayMultiLabelModel(num_classes=NUM_CLASSES)
            
            # Checkpoint yükle
            checkpoint = torch.load(self.model_path, map_location=self.device, weights_only=False)
            
            if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
                self.model.load_state_dict(checkpoint['model_state_dict'])
                best_auc = checkpoint.get('best_auc', 'N/A')
                epoch = checkpoint.get('epoch', 'N/A')
                logger.info(f"Checkpoint yüklendi - Epoch: {epoch}, Best AUC: {best_auc}")
            else:
                self.model.load_state_dict(checkpoint)
            
            self.model.to(self.device)
            self.model.eval()
            
            self.model_loaded = True
            logger.info(f"✅ Multi-label model başarıyla yüklendi: {self.model_path}")
            return True
            
        except Exception as e:
            logger.error(f"Model yükleme hatası: {e}", exc_info=True)
            self.model_loaded = False
            return False
    
    def analyze_image(self, image_bytes: bytes, filename: Optional[str] = None, threshold: float = 0.5) -> Dict:
        """
        Görüntüyü analiz eder ve 14 hastalık için olasılıkları döndürür.
        
        Args:
            image_bytes: Görüntü dosyasının byte içeriği
            filename: Opsiyonel dosya adı
            threshold: Hastalık tespit eşiği (0-1)
            
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
            
            # 2. RGB'ye dönüştür
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            
            logger.info(f"Görüntü hazır: {pil_image.size}, mode: {pil_image.mode}")
            
            # 3. Transform uygula
            input_tensor = self.transform(pil_image).unsqueeze(0).to(self.device)
            
            # 4. Inference
            with torch.no_grad():
                logits = self.model(input_tensor)
                probs = torch.sigmoid(logits).cpu().numpy()[0]
                embedding = self.model.get_embedding()
            
            # 5. Embedding
            if embedding is not None:
                embedding_np = embedding.cpu().numpy().flatten()
                embedding_np = embedding_np / (np.linalg.norm(embedding_np) + 1e-8)
            else:
                embedding_np = np.zeros(self.vector_dimension, dtype=np.float32)
            
            # 6. Tespit edilen hastalıklar
            detected_diseases = []
            all_predictions = {}
            
            for i, label in enumerate(DISEASE_LABELS):
                prob = float(probs[i])
                all_predictions[label] = round(prob, 4)
                
                if prob >= threshold:
                    detected_diseases.append({
                        "label": label,
                        "label_tr": LABEL_TR.get(label, label),
                        "probability": round(prob, 4),
                        "description": DISEASE_DESCRIPTIONS.get(label, "")
                    })
            
            # Olasılığa göre sırala
            detected_diseases.sort(key=lambda x: x['probability'], reverse=True)
            
            # 7. Ana sonuç belirle
            if len(detected_diseases) == 0:
                primary_label = "No Finding"
                primary_label_tr = "Normal - Bulgu Yok"
                is_pathology = False
                confidence = "Yüksek"
            else:
                primary_label = detected_diseases[0]['label']
                primary_label_tr = detected_diseases[0]['label_tr']
                is_pathology = True
                
                # Güven seviyesi
                max_prob = detected_diseases[0]['probability']
                if max_prob >= 0.85:
                    confidence = "Yüksek"
                elif max_prob >= 0.65:
                    confidence = "Orta"
                else:
                    confidence = "Düşük"
            
            # Eski API uyumluluğu için probability değeri
            # En yüksek hastalık olasılığı veya (1 - max) normal için
            max_disease_prob = max(probs) if len(probs) > 0 else 0
            
            result = {
                "label": primary_label,
                "label_tr": primary_label_tr,
                "probability": round(float(max_disease_prob), 4),
                "confidence": confidence,
                "embedding": embedding_np.tolist(),
                "is_pathology": is_pathology,
                "detected_diseases": detected_diseases,
                "disease_count": len(detected_diseases),
                "all_predictions": all_predictions
            }
            
            # Log
            if is_pathology:
                diseases_str = ", ".join([d['label_tr'] for d in detected_diseases[:3]])
                logger.info(f"AI analizi tamamlandı - {len(detected_diseases)} hastalık tespit edildi: {diseases_str}")
            else:
                logger.info(f"AI analizi tamamlandı - Normal (Bulgu Yok)")
            
            return result
            
        except Exception as e:
            logger.error(f"Analiz hatası: {e}", exc_info=True)
            return self._get_error_result(str(e))
    
    def _bytes_to_pil(self, image_bytes: bytes, filename: Optional[str] = None) -> Optional[Image.Image]:
        """Byte verisini PIL Image'a dönüştür."""
        try:
            pil_image = Image.open(BytesIO(image_bytes))
            return pil_image
        except Exception as e:
            logger.warning(f"Direct PIL failed: {e}, trying image_converter...")
        
        try:
            np_array = image_converter.convert_to_numpy(image_bytes, self.INPUT_SIZE, filename)
            if np_array is not None:
                if np_array.ndim == 3 and np_array.shape[2] == 1:
                    np_array = np_array.squeeze(2)
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
            "detected_diseases": [],
            "disease_count": 0,
            "all_predictions": {},
            "error": error_msg
        }
    
    def get_disease_info(self, label: str) -> Dict:
        """Hastalık hakkında bilgi döndür."""
        return {
            "label": label,
            "label_tr": LABEL_TR.get(label, label),
            "description": DISEASE_DESCRIPTIONS.get(label, "Bilgi mevcut değil.")
        }
    
    def get_status(self) -> Dict:
        """Servis durumunu döndür."""
        return {
            "model_loaded": self.model_loaded,
            "model_path": str(self.model_path) if self.model_path else None,
            "device": str(self.device),
            "num_classes": NUM_CLASSES,
            "disease_labels": DISEASE_LABELS,
            "model_type": "multi-label"
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
            "name": "ChestXray-ResNet50-MultiLabel",
            "version": "2.0.0",
            "dataset": "NIH ChestX-ray14",
            "task": "Multi-Label Classification (14 diseases)",
            "num_classes": NUM_CLASSES,
            "classes": DISEASE_LABELS,
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
            return True, f"Multi-Label AI servisi çalışıyor (14 hastalık) - Device: {self.device}"
        elif not self.model_loaded:
            return False, f"Model yüklenemedi: {self.model_path}"
        elif not converter_ok:
            return False, f"Image Converter hatası: {converter_msg}"
        return False, "Bilinmeyen hata"


# Singleton instance
ai_service = MultiLabelAIService()
