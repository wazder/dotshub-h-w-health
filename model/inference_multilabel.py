"""
Multi-Label Model Inference Service
====================================

Eğitilen 14-hastalık modelini kullanarak görüntü analizi yapar.
Bu dosya eğitim sonrası ai_service_real.py ile değiştirilecek.

Kullanım:
    from inference_multilabel import MultiLabelInference
    
    model = MultiLabelInference("path/to/best_model.pth")
    result = model.predict(image_bytes)
"""

import os
import logging
from typing import Optional, Dict, List, Tuple
from pathlib import Path

import numpy as np
from PIL import Image
from io import BytesIO

import torch
import torch.nn as nn
from torchvision import transforms, models

logger = logging.getLogger(__name__)

# 14 Hastalık listesi (eğitim sırasıyla aynı)
DISEASE_LABELS = [
    "Atelectasis", "Cardiomegaly", "Effusion", "Infiltration", "Mass",
    "Nodule", "Pneumonia", "Pneumothorax", "Consolidation", "Edema",
    "Emphysema", "Fibrosis", "Pleural_Thickening", "Hernia"
]

# Türkçe karşılıklar
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
    "Pneumothorax": "Akciğer ile göğüs duvarı arasında hava birikimi. ACİL müdahale gerektirebilir.",
    "Consolidation": "Akciğer dokusunun yoğunlaşması, genellikle zatürre belirtisi.",
    "Edema": "Akciğerlerde sıvı birikimi.",
    "Emphysema": "Akciğer hava keseciklerinin hasar görmesi, KOAH'ın bir türü.",
    "Fibrosis": "Akciğer dokusunun sertleşmesi ve skarlaşması.",
    "Pleural_Thickening": "Akciğer zarının kalınlaşması.",
    "Hernia": "Diyafram fıtığı."
}

NUM_CLASSES = len(DISEASE_LABELS)

# ImageNet normalization
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


class ChestXrayMultiLabelModel(nn.Module):
    """
    ResNet50 tabanlı multi-label sınıflandırma modeli.
    """
    
    def __init__(self, num_classes: int = NUM_CLASSES, dropout: float = 0.5):
        super().__init__()
        
        self.backbone = models.resnet50(weights=None)
        num_features = self.backbone.fc.in_features
        self.backbone.fc = nn.Identity()
        
        self.classifier = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(num_features, 512),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout / 2),
            nn.Linear(512, num_classes)
        )
        
        self.embedding = None
        self._register_hook()
    
    def _register_hook(self):
        def hook(module, input, output):
            self.embedding = output.squeeze()
        self.backbone.avgpool.register_forward_hook(hook)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        features = self.backbone(x)
        logits = self.classifier(features)
        return logits
    
    def get_embedding(self) -> Optional[torch.Tensor]:
        return self.embedding


class MultiLabelInference:
    """
    Multi-label model ile görüntü analizi.
    """
    
    INPUT_SIZE = (224, 224)
    THRESHOLD = 0.5  # Varsayılan threshold
    
    def __init__(self, model_path: str, device: Optional[str] = None):
        """
        Args:
            model_path: Eğitilmiş model dosyasının yolu
            device: 'cuda' veya 'cpu' (None ise otomatik seç)
        """
        self.model_path = Path(model_path)
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
        self.model = None
        self.model_loaded = False
        
        # Transform
        self.transform = transforms.Compose([
            transforms.Resize(self.INPUT_SIZE),
            transforms.ToTensor(),
            transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)
        ])
        
        # Load model
        self._load_model()
        
        logger.info(f"MultiLabelInference başlatıldı - Device: {self.device}")
    
    def _load_model(self) -> bool:
        """Modeli yükle."""
        if not self.model_path.exists():
            logger.error(f"Model dosyası bulunamadı: {self.model_path}")
            return False
        
        try:
            self.model = ChestXrayMultiLabelModel(num_classes=NUM_CLASSES)
            
            checkpoint = torch.load(self.model_path, map_location=self.device, weights_only=False)
            
            if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
                self.model.load_state_dict(checkpoint['model_state_dict'])
                logger.info(f"Checkpoint yüklendi - Epoch: {checkpoint.get('epoch', '?')}, "
                           f"Best AUC: {checkpoint.get('best_auc', '?'):.4f}")
            else:
                self.model.load_state_dict(checkpoint)
            
            self.model.to(self.device)
            self.model.eval()
            self.model_loaded = True
            
            logger.info(f"✅ Model yüklendi: {self.model_path}")
            return True
            
        except Exception as e:
            logger.error(f"Model yükleme hatası: {e}")
            return False
    
    def predict(
        self,
        image_bytes: bytes,
        threshold: float = 0.5,
        return_all: bool = False
    ) -> Dict:
        """
        Görüntüyü analiz et.
        
        Args:
            image_bytes: Görüntü byte verisi
            threshold: Hastalık tespit eşiği (0-1)
            return_all: Tüm hastalık olasılıklarını döndür
            
        Returns:
            dict: Analiz sonucu
        """
        if not self.model_loaded:
            return self._error_result("Model yüklenmemiş")
        
        try:
            # Görüntüyü yükle
            pil_image = Image.open(BytesIO(image_bytes)).convert('RGB')
            
            # Transform
            input_tensor = self.transform(pil_image).unsqueeze(0).to(self.device)
            
            # Inference
            with torch.no_grad():
                logits = self.model(input_tensor)
                probs = torch.sigmoid(logits).cpu().numpy()[0]
                embedding = self.model.get_embedding()
            
            # Embedding
            if embedding is not None:
                embedding_np = embedding.cpu().numpy().flatten()
                embedding_np = embedding_np / (np.linalg.norm(embedding_np) + 1e-8)
            else:
                embedding_np = np.zeros(2048, dtype=np.float32)
            
            # Tespit edilen hastalıklar
            detected = []
            all_predictions = {}
            
            for i, label in enumerate(DISEASE_LABELS):
                prob = float(probs[i])
                all_predictions[label] = round(prob, 4)
                
                if prob >= threshold:
                    detected.append({
                        "label": label,
                        "label_tr": LABEL_TR.get(label, label),
                        "probability": round(prob, 4),
                        "description": DISEASE_DESCRIPTIONS.get(label, "")
                    })
            
            # Sonuçları olasılığa göre sırala
            detected.sort(key=lambda x: x['probability'], reverse=True)
            
            # Ana sonuç
            if len(detected) == 0:
                primary_label = "No Finding"
                primary_label_tr = "Normal - Bulgu Yok"
                is_pathology = False
                confidence = "Yüksek"
            else:
                primary_label = detected[0]['label']
                primary_label_tr = detected[0]['label_tr']
                is_pathology = True
                
                # Güven seviyesi
                max_prob = detected[0]['probability']
                if max_prob >= 0.85:
                    confidence = "Yüksek"
                elif max_prob >= 0.65:
                    confidence = "Orta"
                else:
                    confidence = "Düşük"
            
            result = {
                "label": primary_label,
                "label_tr": primary_label_tr,
                "confidence": confidence,
                "is_pathology": is_pathology,
                "detected_diseases": detected,
                "disease_count": len(detected),
                "embedding": embedding_np.tolist()
            }
            
            if return_all:
                result["all_predictions"] = all_predictions
            
            logger.info(f"Analiz tamamlandı - {len(detected)} hastalık tespit edildi")
            
            return result
            
        except Exception as e:
            logger.error(f"Prediction hatası: {e}")
            return self._error_result(str(e))
    
    def _error_result(self, message: str) -> Dict:
        """Hata durumunda döndürülecek sonuç."""
        return {
            "label": "Error",
            "label_tr": "Hata",
            "confidence": "Yok",
            "is_pathology": False,
            "detected_diseases": [],
            "disease_count": 0,
            "error": message,
            "embedding": []
        }
    
    def get_disease_info(self, label: str) -> Dict:
        """Hastalık hakkında bilgi döndür."""
        return {
            "label": label,
            "label_tr": LABEL_TR.get(label, label),
            "description": DISEASE_DESCRIPTIONS.get(label, "Bilgi mevcut değil.")
        }


# Test
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Kullanım: python inference_multilabel.py <model_path> <image_path>")
        sys.exit(1)
    
    model_path = sys.argv[1]
    image_path = sys.argv[2]
    
    # Model yükle
    inference = MultiLabelInference(model_path)
    
    # Görüntüyü oku
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    
    # Analiz et
    result = inference.predict(image_bytes, threshold=0.3, return_all=True)
    
    print("\n" + "=" * 50)
    print("ANALİZ SONUCU")
    print("=" * 50)
    print(f"Ana Tanı: {result['label_tr']} ({result['label']})")
    print(f"Güven: {result['confidence']}")
    print(f"Patoloji: {'Evet' if result['is_pathology'] else 'Hayır'}")
    print(f"\nTespit Edilen Hastalıklar ({result['disease_count']}):")
    
    for disease in result['detected_diseases']:
        print(f"  - {disease['label_tr']}: %{disease['probability']*100:.1f}")
        print(f"    {disease['description']}")
    
    if 'all_predictions' in result:
        print("\nTüm Olasılıklar:")
        for label, prob in sorted(result['all_predictions'].items(), key=lambda x: x[1], reverse=True):
            bar = "█" * int(prob * 20)
            print(f"  {LABEL_TR.get(label, label):20} {prob*100:5.1f}% {bar}")
