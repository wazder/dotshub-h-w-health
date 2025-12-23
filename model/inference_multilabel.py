"""
Multi-Label Model Inference Service
====================================

Performs image analysis using the trained 14-disease model.
This file will be replaced with ai_service_real.py after training.

Usage:
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

# 14 Disease list (same order as training)
DISEASE_LABELS = [
    "Atelectasis", "Cardiomegaly", "Effusion", "Infiltration", "Mass",
    "Nodule", "Pneumonia", "Pneumothorax", "Consolidation", "Edema",
    "Emphysema", "Fibrosis", "Pleural_Thickening", "Hernia"
]

# Label descriptions (now using English)
LABEL_TR = {
    "No Finding": "Normal - No Finding",
    "Atelectasis": "Atelectasis",
    "Cardiomegaly": "Cardiomegaly", 
    "Effusion": "Pleural Effusion",
    "Infiltration": "Infiltration",
    "Mass": "Mass",
    "Nodule": "Nodule",
    "Pneumonia": "Pneumonia",
    "Pneumothorax": "Pneumothorax",
    "Consolidation": "Consolidation",
    "Edema": "Pulmonary Edema",
    "Emphysema": "Emphysema",
    "Fibrosis": "Fibrosis",
    "Pleural_Thickening": "Pleural Thickening",
    "Hernia": "Hernia"
}

# Disease descriptions
DISEASE_DESCRIPTIONS = {
    "Atelectasis": "Partial collapse or air loss in a section of the lung.",
    "Cardiomegaly": "Heart enlargement, may indicate heart failure.",
    "Effusion": "Fluid accumulation between lung membranes (pleural effusion).",
    "Infiltration": "Fluid or cell accumulation in lung tissue. May indicate infection.",
    "Mass": "Large lesion in the lung. Requires further investigation.",
    "Nodule": "Small round lesion in the lung. May require follow-up.",
    "Pneumonia": "Lung infection, requires treatment.",
    "Pneumothorax": "Air accumulation between lung and chest wall. May require URGENT intervention.",
    "Consolidation": "Densification of lung tissue, usually indicates pneumonia.",
    "Edema": "Fluid accumulation in the lungs.",
    "Emphysema": "Damage to lung air sacs, a type of COPD.",
    "Fibrosis": "Hardening and scarring of lung tissue.",
    "Pleural_Thickening": "Thickening of the lung membrane.",
    "Hernia": "Diaphragmatic hernia."
}

NUM_CLASSES = len(DISEASE_LABELS)

# ImageNet normalization
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


class ChestXrayMultiLabelModel(nn.Module):
    """
    ResNet50-based multi-label classification model.
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
    Image analysis with multi-label model.
    """
    
    INPUT_SIZE = (224, 224)
    THRESHOLD = 0.5  # Default threshold
    
    def __init__(self, model_path: str, device: Optional[str] = None):
        """
        Args:
            model_path: Path to trained model file
            device: 'cuda' or 'cpu' (None for automatic selection)
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
        
        logger.info(f"MultiLabelInference initialized - Device: {self.device}")
    
    def _load_model(self) -> bool:
        """Load the model."""
        if not self.model_path.exists():
            logger.error(f"Model file not found: {self.model_path}")
            return False
        
        try:
            self.model = ChestXrayMultiLabelModel(num_classes=NUM_CLASSES)
            
            checkpoint = torch.load(self.model_path, map_location=self.device, weights_only=False)
            
            if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
                self.model.load_state_dict(checkpoint['model_state_dict'])
                logger.info(f"Checkpoint loaded - Epoch: {checkpoint.get('epoch', '?')}, "
                           f"Best AUC: {checkpoint.get('best_auc', '?'):.4f}")
            else:
                self.model.load_state_dict(checkpoint)
            
            self.model.to(self.device)
            self.model.eval()
            self.model_loaded = True
            
            logger.info(f"✅ Model loaded: {self.model_path}")
            return True
            
        except Exception as e:
            logger.error(f"Model loading error: {e}")
            return False
    
    def predict(
        self,
        image_bytes: bytes,
        threshold: float = 0.5,
        return_all: bool = False
    ) -> Dict:
        """
        Analyze the image.
        
        Args:
            image_bytes: Image byte data
            threshold: Disease detection threshold (0-1)
            return_all: Return all disease probabilities
            
        Returns:
            dict: Analysis result
        """
        if not self.model_loaded:
            return self._error_result("Model not loaded")
        
        try:
            # Load image
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
            
            # Detected diseases
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
            
            # Sort results by probability
            detected.sort(key=lambda x: x['probability'], reverse=True)
            
            # Main result
            if len(detected) == 0:
                primary_label = "No Finding"
                primary_label_tr = "Normal - No Finding"
                is_pathology = False
                confidence = "High"
            else:
                primary_label = detected[0]['label']
                primary_label_tr = detected[0]['label_tr']
                is_pathology = True
                
                # Confidence level
                max_prob = detected[0]['probability']
                if max_prob >= 0.85:
                    confidence = "High"
                elif max_prob >= 0.65:
                    confidence = "Medium"
                else:
                    confidence = "Low"
            
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
            
            logger.info(f"Analysis complete - {len(detected)} diseases detected")
            
            return result
            
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return self._error_result(str(e))
    
    def _error_result(self, message: str) -> Dict:
        """Result to return in case of error."""
        return {
            "label": "Error",
            "label_tr": "Error",
            "confidence": "None",
            "is_pathology": False,
            "detected_diseases": [],
            "disease_count": 0,
            "error": message,
            "embedding": []
        }
    
    def get_disease_info(self, label: str) -> Dict:
        """Return information about a disease."""
        return {
            "label": label,
            "label_tr": LABEL_TR.get(label, label),
            "description": DISEASE_DESCRIPTIONS.get(label, "Information not available.")
        }


# Test
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python inference_multilabel.py <model_path> <image_path>")
        sys.exit(1)
    
    model_path = sys.argv[1]
    image_path = sys.argv[2]
    
    # Load model
    inference = MultiLabelInference(model_path)
    
    # Read image
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    
    # Analyze
    result = inference.predict(image_bytes, threshold=0.3, return_all=True)
    
    print("\n" + "=" * 50)
    print("ANALYSIS RESULT")
    print("=" * 50)
    print(f"Primary Diagnosis: {result['label_tr']} ({result['label']})")
    print(f"Confidence: {result['confidence']}")
    print(f"Pathology: {'Yes' if result['is_pathology'] else 'No'}")
    print(f"\nDetected Diseases ({result['disease_count']}):")
    
    for disease in result['detected_diseases']:
        print(f"  - {disease['label_tr']}: {disease['probability']*100:.1f}%")
        print(f"    {disease['description']}")
    
    if 'all_predictions' in result:
        print("\nAll Probabilities:")
        for label, prob in sorted(result['all_predictions'].items(), key=lambda x: x[1], reverse=True):
            bar = "█" * int(prob * 20)
            print(f"  {LABEL_TR.get(label, label):20} {prob*100:5.1f}% {bar}")
