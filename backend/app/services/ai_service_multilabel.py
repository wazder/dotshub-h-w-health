"""
AI Service - Multi-Label PyTorch ResNet50 Model Integration
Analyzes X-Ray images and detects 14 diseases

This service uses the newly trained multi-label model:
- Model: ResNet50 (Multi-Label Classification)
- Dataset: NIH Chest X-rays (112K images)
- Classes: 14 diseases + No Finding
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


# 14 Disease labels (same order as training - DO NOT CHANGE!)
DISEASE_LABELS = [
    "Atelectasis", "Cardiomegaly", "Effusion", "Infiltration", "Mass",
    "Nodule", "Pneumonia", "Pneumothorax", "Consolidation", "Edema",
    "Emphysema", "Fibrosis", "Pleural_Thickening", "Hernia"
]

NUM_CLASSES = len(DISEASE_LABELS)

# Turkish label translations (for UI display)
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

# Disease descriptions (Turkish - for UI display)
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
    ResNet50-based multi-label classification model.
    Separate sigmoid outputs for 14 diseases.
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
        """Hook for extracting embeddings."""
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
    AI analysis service with multi-label PyTorch model.
    Detects 14 diseases separately.
    """
    
    INPUT_SIZE = (224, 224)
    THRESHOLD = 0.5  # Default threshold
    
    def __init__(self):
        self.model: Optional[ChestXrayMultiLabelModel] = None
        self.model_loaded = False
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.vector_dimension = 2048
        
        # Model path - new multi-label model
        self.model_path = self._find_model_path()
        
        # Transform
        self.transform = transforms.Compose([
            transforms.Resize(self.INPUT_SIZE),
            transforms.ToTensor(),
            transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)
        ])
        
        # Load model
        self._load_model()
        
        logger.info(f"MultiLabel AI Service initialized - Device: {self.device}, Model: {'Loaded' if self.model_loaded else 'Not Found'}")
    
    def _find_model_path(self) -> Optional[Path]:
        """Find model file."""
        possible_paths = [
            # New multi-label model (priority)
            Path(__file__).parent.parent.parent.parent / "model" / "model-2.pth",
            Path("/Users/wazder/Documents/GitHub/dotshub-h-w-health/model/model-2.pth"),
            # Docker/workspace path
            Path("/workspace/dotshub-h-w-health/model/model-2.pth"),
            # Fallback - best_model.pth
            Path(__file__).parent.parent.parent.parent / "model" / "best_model.pth",
        ]
        
        for path in possible_paths:
            if path.exists():
                logger.info(f"Model file found: {path}")
                return path
        
        logger.warning("Model file not found!")
        return None
    
    def _load_model(self) -> bool:
        """Load PyTorch model."""
        if self.model_path is None or not self.model_path.exists():
            logger.error(f"Model file not found: {self.model_path}")
            return False
        
        try:
            # Create model
            self.model = ChestXrayMultiLabelModel(num_classes=NUM_CLASSES)
            
            # Load checkpoint
            checkpoint = torch.load(self.model_path, map_location=self.device, weights_only=False)
            
            if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
                self.model.load_state_dict(checkpoint['model_state_dict'])
                best_auc = checkpoint.get('best_auc', 'N/A')
                epoch = checkpoint.get('epoch', 'N/A')
                logger.info(f"Checkpoint loaded - Epoch: {epoch}, Best AUC: {best_auc}")
            else:
                self.model.load_state_dict(checkpoint)
            
            self.model.to(self.device)
            self.model.eval()
            
            self.model_loaded = True
            logger.info(f"✅ Multi-label model loaded successfully: {self.model_path}")
            return True
            
        except Exception as e:
            logger.error(f"Model loading error: {e}", exc_info=True)
            self.model_loaded = False
            return False
    
    def analyze_image(self, image_bytes: bytes, filename: Optional[str] = None, threshold: float = 0.5) -> Dict:
        """
        Analyzes the image and returns probabilities for 14 diseases.
        
        Args:
            image_bytes: Byte content of the image file
            filename: Optional filename
            threshold: Disease detection threshold (0-1)
            
        Returns:
            dict: Analysis result
        """
        if not self.model_loaded:
            logger.error("Model not loaded!")
            return self._get_error_result("Model not loaded")
        
        try:
            # Detect format
            detected_format = image_converter.detect_format(image_bytes, filename)
            logger.info(f"AI analysis starting - Format: {detected_format.value}")
            
            # 1. Convert to PIL Image
            pil_image = self._bytes_to_pil(image_bytes, filename)
            
            if pil_image is None:
                return self._get_error_result("Could not read image")
            
            # 2. Convert to RGB
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            
            logger.info(f"Image ready: {pil_image.size}, mode: {pil_image.mode}")
            
            # 3. Apply transform
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
            
            # 6. Detected diseases
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
            
            # Sort by probability
            detected_diseases.sort(key=lambda x: x['probability'], reverse=True)
            
            # 7. Determine primary result
            if len(detected_diseases) == 0:
                primary_label = "No Finding"
                primary_label_tr = "Normal - Bulgu Yok"
                is_pathology = False
                confidence = "High"
            else:
                primary_label = detected_diseases[0]['label']
                primary_label_tr = detected_diseases[0]['label_tr']
                is_pathology = True
                
                # Confidence level
                max_prob = detected_diseases[0]['probability']
                if max_prob >= 0.85:
                    confidence = "High"
                elif max_prob >= 0.65:
                    confidence = "Medium"
                else:
                    confidence = "Low"
            
            # Probability value for backward API compatibility
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
                diseases_str = ", ".join([d['label'] for d in detected_diseases[:3]])
                logger.info(f"AI analysis completed - {len(detected_diseases)} diseases detected: {diseases_str}")
            else:
                logger.info(f"AI analysis completed - Normal (No Finding)")
            
            return result
            
        except Exception as e:
            logger.error(f"Analysis error: {e}", exc_info=True)
            return self._get_error_result(str(e))
    
    def _bytes_to_pil(self, image_bytes: bytes, filename: Optional[str] = None) -> Optional[Image.Image]:
        """Convert byte data to PIL Image."""
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
        """Returns result for error case."""
        return {
            "label": "Error",
            "label_tr": f"Error: {error_msg}",
            "probability": 0.0,
            "confidence": "None",
            "embedding": [0.0] * self.vector_dimension,
            "is_pathology": False,
            "detected_diseases": [],
            "disease_count": 0,
            "all_predictions": {},
            "error": error_msg
        }
    
    def get_disease_info(self, label: str) -> Dict:
        """Returns information about a disease."""
        return {
            "label": label,
            "label_tr": LABEL_TR.get(label, label),
            "description": DISEASE_DESCRIPTIONS.get(label, "Information not available.")
        }
    
    def get_status(self) -> Dict:
        """Returns service status."""
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
        Extracts embedding from an image file.
        Used for building vector database.
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
        """Returns model information."""
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
        """Service health check."""
        converter_ok, converter_msg = image_converter.check_health()
        
        if self.model_loaded and converter_ok:
            return True, f"Multi-Label AI service running (14 diseases) - Device: {self.device}"
        elif not self.model_loaded:
            return False, f"Model could not be loaded: {self.model_path}"
        elif not converter_ok:
            return False, f"Image Converter error: {converter_msg}"
        return False, "Unknown error"


# Singleton instance
ai_service = MultiLabelAIService()
