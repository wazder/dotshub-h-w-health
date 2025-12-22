"""
NIH Chest X-ray Multi-Label Classification Training Script
==========================================================

14 hastalık için multi-label sınıflandırma modeli eğitimi.
RunPod veya GPU sunucusunda çalıştırılmak üzere tasarlandı.

Hastalıklar:
- Atelectasis, Cardiomegaly, Effusion, Infiltration, Mass
- Nodule, Pneumonia, Pneumothorax, Consolidation, Edema
- Emphysema, Fibrosis, Pleural_Thickening, Hernia
- (No Finding ayrı bir sınıf olarak ele alınır)

Kullanım:
    python train_multilabel.py --data_dir /path/to/data --epochs 50

RunPod için:
    python train_multilabel.py --data_dir /workspace/data --epochs 50 --batch_size 32
"""

import os
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Tuple, List, Dict, Optional

import numpy as np
import pandas as pd
from PIL import Image
from tqdm import tqdm

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler
from torch.cuda.amp import autocast, GradScaler

from torchvision import transforms, models
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, f1_score, precision_recall_fscore_support

# Logging ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('training.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==================== Sabitler ====================

# NIH Chest X-ray 14 hastalık listesi
DISEASE_LABELS = [
    "Atelectasis", "Cardiomegaly", "Effusion", "Infiltration", "Mass",
    "Nodule", "Pneumonia", "Pneumothorax", "Consolidation", "Edema",
    "Emphysema", "Fibrosis", "Pleural_Thickening", "Hernia"
]

# Türkçe etiketler (UI için)
LABEL_TR = {
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

NUM_CLASSES = len(DISEASE_LABELS)

# ImageNet normalization
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


# ==================== Dataset ====================

class ChestXrayDataset(Dataset):
    """
    NIH Chest X-ray Dataset for multi-label classification.
    """
    
    def __init__(
        self,
        csv_path: str,
        image_dir: str,
        image_list: Optional[List[str]] = None,
        transform=None,
        target_size: Tuple[int, int] = (224, 224)
    ):
        """
        Args:
            csv_path: Data_Entry_2017.csv dosyasının yolu
            image_dir: Görüntülerin bulunduğu klasör
            image_list: Kullanılacak görüntü listesi (train/val/test split için)
            transform: Görüntü dönüşümleri
            target_size: Hedef görüntü boyutu
        """
        self.image_dir = Path(image_dir)
        self.transform = transform
        self.target_size = target_size
        
        # CSV'yi oku
        logger.info(f"CSV yükleniyor: {csv_path}")
        self.df = pd.read_csv(csv_path)
        
        # Image list varsa filtrele
        if image_list is not None:
            self.df = self.df[self.df['Image Index'].isin(image_list)]
        
        # Görüntü yollarını kontrol et ve geçerli olanları tut
        valid_indices = []
        for idx, row in tqdm(self.df.iterrows(), total=len(self.df), desc="Görüntüler kontrol ediliyor"):
            img_path = self._find_image(row['Image Index'])
            if img_path is not None:
                valid_indices.append(idx)
        
        self.df = self.df.loc[valid_indices].reset_index(drop=True)
        logger.info(f"Toplam geçerli görüntü: {len(self.df)}")
        
        # Multi-label encoding
        self.labels = self._encode_labels()
        
        # Sınıf ağırlıklarını hesapla (class imbalance için)
        self.class_weights = self._calculate_class_weights()
    
    def _find_image(self, image_name: str) -> Optional[Path]:
        """Görüntü dosyasını bul (farklı klasör yapılarını destekler)."""
        possible_paths = [
            self.image_dir / image_name,
            self.image_dir / "images" / image_name,
            self.image_dir / "images-224" / "images-224" / image_name,
            self.image_dir / "images-224" / image_name,
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        return None
    
    def _encode_labels(self) -> np.ndarray:
        """Finding Labels'ı multi-hot encoding'e çevir."""
        labels = np.zeros((len(self.df), NUM_CLASSES), dtype=np.float32)
        
        for idx, row in self.df.iterrows():
            findings = str(row['Finding Labels']).split('|')
            for finding in findings:
                finding = finding.strip()
                if finding in DISEASE_LABELS:
                    label_idx = DISEASE_LABELS.index(finding)
                    labels[idx, label_idx] = 1.0
        
        return labels
    
    def _calculate_class_weights(self) -> torch.Tensor:
        """Sınıf dengesizliği için ağırlıkları hesapla."""
        pos_counts = self.labels.sum(axis=0)
        neg_counts = len(self.labels) - pos_counts
        
        # pos_weight = neg_count / pos_count (BCEWithLogitsLoss için)
        weights = neg_counts / (pos_counts + 1e-5)
        weights = np.clip(weights, 1.0, 50.0)  # Aşırı ağırlıkları sınırla
        
        logger.info("Sınıf ağırlıkları:")
        for i, label in enumerate(DISEASE_LABELS):
            logger.info(f"  {label}: {weights[i]:.2f} (pozitif: {int(pos_counts[i])}, negatif: {int(neg_counts[i])})")
        
        return torch.tensor(weights, dtype=torch.float32)
    
    def __len__(self) -> int:
        return len(self.df)
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        row = self.df.iloc[idx]
        img_path = self._find_image(row['Image Index'])
        
        # Görüntüyü yükle
        image = Image.open(img_path).convert('RGB')
        
        # Resize (eğer gerekiyorsa)
        if image.size != self.target_size:
            image = image.resize(self.target_size, Image.LANCZOS)
        
        # Transform uygula
        if self.transform:
            image = self.transform(image)
        
        # Label
        label = torch.tensor(self.labels[idx], dtype=torch.float32)
        
        return image, label


# ==================== Model ====================

class ChestXrayMultiLabelModel(nn.Module):
    """
    ResNet50 tabanlı multi-label sınıflandırma modeli.
    14 hastalık için ayrı sigmoid çıktıları.
    """
    
    def __init__(
        self,
        num_classes: int = NUM_CLASSES,
        pretrained: bool = True,
        dropout: float = 0.5
    ):
        super().__init__()
        
        # Pretrained ResNet50 backbone
        if pretrained:
            self.backbone = models.resnet50(weights=models.ResNet50_Weights.DEFAULT)
        else:
            self.backbone = models.resnet50(weights=None)
        
        # Son FC katmanını değiştir
        num_features = self.backbone.fc.in_features
        self.backbone.fc = nn.Identity()  # FC'yi kaldır
        
        # Yeni classifier head
        self.classifier = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(num_features, 512),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout / 2),
            nn.Linear(512, num_classes)
        )
        
        # Embedding çıkarmak için
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


# ==================== Training Functions ====================

def get_transforms(target_size: int = 224, augment: bool = True):
    """Eğitim ve validation için transform'ları döndür."""
    
    if augment:
        train_transform = transforms.Compose([
            transforms.Resize((target_size + 32, target_size + 32)),
            transforms.RandomCrop(target_size),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomRotation(degrees=15),
            transforms.ColorJitter(brightness=0.2, contrast=0.2),
            transforms.ToTensor(),
            transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
            transforms.RandomErasing(p=0.1)
        ])
    else:
        train_transform = transforms.Compose([
            transforms.Resize((target_size, target_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)
        ])
    
    val_transform = transforms.Compose([
        transforms.Resize((target_size, target_size)),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)
    ])
    
    return train_transform, val_transform


def train_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    optimizer: optim.Optimizer,
    device: torch.device,
    scaler: Optional[GradScaler] = None
) -> Tuple[float, float]:
    """Bir epoch eğitim."""
    model.train()
    total_loss = 0.0
    all_preds = []
    all_labels = []
    
    pbar = tqdm(dataloader, desc="Training")
    for images, labels in pbar:
        images = images.to(device)
        labels = labels.to(device)
        
        optimizer.zero_grad()
        
        # Mixed precision training
        if scaler is not None:
            with autocast():
                outputs = model(images)
                loss = criterion(outputs, labels)
            
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
        else:
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
        
        total_loss += loss.item()
        
        # Predictions
        with torch.no_grad():
            probs = torch.sigmoid(outputs)
            all_preds.append(probs.cpu().numpy())
            all_labels.append(labels.cpu().numpy())
        
        pbar.set_postfix({'loss': f'{loss.item():.4f}'})
    
    avg_loss = total_loss / len(dataloader)
    
    # Macro AUC hesapla
    all_preds = np.vstack(all_preds)
    all_labels = np.vstack(all_labels)
    
    try:
        auc = roc_auc_score(all_labels, all_preds, average='macro')
    except:
        auc = 0.0
    
    return avg_loss, auc


def validate(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    device: torch.device
) -> Tuple[float, float, Dict]:
    """Validation."""
    model.eval()
    total_loss = 0.0
    all_preds = []
    all_labels = []
    
    with torch.no_grad():
        for images, labels in tqdm(dataloader, desc="Validation"):
            images = images.to(device)
            labels = labels.to(device)
            
            outputs = model(images)
            loss = criterion(outputs, labels)
            
            total_loss += loss.item()
            
            probs = torch.sigmoid(outputs)
            all_preds.append(probs.cpu().numpy())
            all_labels.append(labels.cpu().numpy())
    
    avg_loss = total_loss / len(dataloader)
    
    all_preds = np.vstack(all_preds)
    all_labels = np.vstack(all_labels)
    
    # Per-class metrics
    metrics = {}
    for i, label in enumerate(DISEASE_LABELS):
        try:
            auc = roc_auc_score(all_labels[:, i], all_preds[:, i])
        except:
            auc = 0.0
        
        # Binary predictions (threshold=0.5)
        preds_binary = (all_preds[:, i] > 0.5).astype(int)
        precision, recall, f1, _ = precision_recall_fscore_support(
            all_labels[:, i], preds_binary, average='binary', zero_division=0
        )
        
        metrics[label] = {
            'auc': auc,
            'precision': precision,
            'recall': recall,
            'f1': f1
        }
    
    # Macro average AUC
    try:
        macro_auc = roc_auc_score(all_labels, all_preds, average='macro')
    except:
        macro_auc = 0.0
    
    return avg_loss, macro_auc, metrics


def save_checkpoint(
    model: nn.Module,
    optimizer: optim.Optimizer,
    epoch: int,
    best_auc: float,
    save_path: str
):
    """Model checkpoint kaydet."""
    torch.save({
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'best_auc': best_auc,
        'disease_labels': DISEASE_LABELS,
        'num_classes': NUM_CLASSES
    }, save_path)
    logger.info(f"Checkpoint kaydedildi: {save_path}")


# ==================== Main Training ====================

def main(args):
    """Ana eğitim fonksiyonu."""
    
    # Device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Device: {device}")
    
    if torch.cuda.is_available():
        logger.info(f"GPU: {torch.cuda.get_device_name(0)}")
        logger.info(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
    
    # Data paths
    data_dir = Path(args.data_dir)
    csv_path = data_dir / "Data_Entry_2017.csv"
    
    # Image directory - birden fazla olası yol
    image_dir = None
    for possible_dir in [
        data_dir / "images",
        data_dir / "images-224" / "images-224",
        data_dir / "images-224",
        data_dir
    ]:
        if possible_dir.exists():
            image_dir = possible_dir
            break
    
    if image_dir is None:
        raise ValueError(f"Görüntü klasörü bulunamadı: {data_dir}")
    
    logger.info(f"CSV: {csv_path}")
    logger.info(f"Images: {image_dir}")
    
    # Train/val/test split dosyalarını oku
    train_list_path = data_dir / "train_val_list_NIH.txt"
    test_list_path = data_dir / "test_list_NIH.txt"
    
    if train_list_path.exists() and test_list_path.exists():
        with open(train_list_path, 'r') as f:
            train_val_list = [line.strip() for line in f.readlines()]
        with open(test_list_path, 'r') as f:
            test_list = [line.strip() for line in f.readlines()]
        
        # Train/val split
        train_list, val_list = train_test_split(
            train_val_list, test_size=0.1, random_state=42
        )
        logger.info(f"Train: {len(train_list)}, Val: {len(val_list)}, Test: {len(test_list)}")
    else:
        logger.warning("Train/test split dosyaları bulunamadı, rastgele bölünecek")
        train_list = val_list = test_list = None
    
    # Transforms
    train_transform, val_transform = get_transforms(
        target_size=args.image_size,
        augment=args.augment
    )
    
    # Datasets
    logger.info("Dataset'ler yükleniyor...")
    train_dataset = ChestXrayDataset(
        csv_path=str(csv_path),
        image_dir=str(image_dir),
        image_list=train_list,
        transform=train_transform,
        target_size=(args.image_size, args.image_size)
    )
    
    val_dataset = ChestXrayDataset(
        csv_path=str(csv_path),
        image_dir=str(image_dir),
        image_list=val_list,
        transform=val_transform,
        target_size=(args.image_size, args.image_size)
    )
    
    # DataLoaders
    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        pin_memory=True
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=True
    )
    
    # Model
    logger.info("Model oluşturuluyor...")
    model = ChestXrayMultiLabelModel(
        num_classes=NUM_CLASSES,
        pretrained=True,
        dropout=args.dropout
    ).to(device)
    
    # Loss function (weighted BCEWithLogitsLoss)
    pos_weights = train_dataset.class_weights.to(device)
    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weights)
    
    # Optimizer
    optimizer = optim.AdamW(
        model.parameters(),
        lr=args.lr,
        weight_decay=args.weight_decay
    )
    
    # Learning rate scheduler
    scheduler = optim.lr_scheduler.CosineAnnealingLR(
        optimizer,
        T_max=args.epochs,
        eta_min=args.lr / 100
    )
    
    # Mixed precision scaler
    scaler = GradScaler() if args.mixed_precision and torch.cuda.is_available() else None
    
    # Output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Training loop
    best_auc = 0.0
    patience_counter = 0
    
    logger.info("=" * 50)
    logger.info("Eğitim başlıyor...")
    logger.info(f"Epochs: {args.epochs}")
    logger.info(f"Batch size: {args.batch_size}")
    logger.info(f"Learning rate: {args.lr}")
    logger.info(f"Image size: {args.image_size}")
    logger.info("=" * 50)
    
    for epoch in range(1, args.epochs + 1):
        logger.info(f"\nEpoch {epoch}/{args.epochs}")
        logger.info(f"Learning rate: {scheduler.get_last_lr()[0]:.6f}")
        
        # Train
        train_loss, train_auc = train_epoch(
            model, train_loader, criterion, optimizer, device, scaler
        )
        
        # Validate
        val_loss, val_auc, val_metrics = validate(
            model, val_loader, criterion, device
        )
        
        # Scheduler step
        scheduler.step()
        
        # Logging
        logger.info(f"Train Loss: {train_loss:.4f}, Train AUC: {train_auc:.4f}")
        logger.info(f"Val Loss: {val_loss:.4f}, Val AUC: {val_auc:.4f}")
        
        # Per-class metrics (her 5 epoch'ta bir)
        if epoch % 5 == 0:
            logger.info("\nPer-class metrics:")
            for label, m in val_metrics.items():
                logger.info(f"  {label}: AUC={m['auc']:.3f}, F1={m['f1']:.3f}")
        
        # Best model kaydet
        if val_auc > best_auc:
            best_auc = val_auc
            patience_counter = 0
            
            save_checkpoint(
                model, optimizer, epoch, best_auc,
                str(output_dir / "best_model.pth")
            )
            logger.info(f"✅ Yeni en iyi model! AUC: {best_auc:.4f}")
        else:
            patience_counter += 1
        
        # Checkpoint (her 10 epoch'ta)
        if epoch % 10 == 0:
            save_checkpoint(
                model, optimizer, epoch, best_auc,
                str(output_dir / f"checkpoint_epoch_{epoch}.pth")
            )
        
        # Early stopping
        if patience_counter >= args.patience:
            logger.info(f"Early stopping! {args.patience} epoch boyunca iyileşme yok.")
            break
    
    logger.info("=" * 50)
    logger.info(f"Eğitim tamamlandı! En iyi AUC: {best_auc:.4f}")
    logger.info(f"Model kaydedildi: {output_dir / 'best_model.pth'}")
    
    # Final metrics'i kaydet
    with open(output_dir / "training_results.txt", 'w') as f:
        f.write(f"Best Validation AUC: {best_auc:.4f}\n")
        f.write(f"Epochs trained: {epoch}\n")
        f.write(f"\nPer-class metrics:\n")
        for label, m in val_metrics.items():
            f.write(f"  {label}: AUC={m['auc']:.3f}, Precision={m['precision']:.3f}, "
                   f"Recall={m['recall']:.3f}, F1={m['f1']:.3f}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NIH Chest X-ray Multi-Label Training")
    
    # Data arguments
    parser.add_argument("--data_dir", type=str, required=True,
                       help="Veri setinin bulunduğu klasör (Data_Entry_2017.csv ve images içermeli)")
    parser.add_argument("--output_dir", type=str, default="./output",
                       help="Model ve checkpoint'ların kaydedileceği klasör")
    
    # Training arguments
    parser.add_argument("--epochs", type=int, default=50, help="Epoch sayısı")
    parser.add_argument("--batch_size", type=int, default=32, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning rate")
    parser.add_argument("--weight_decay", type=float, default=1e-5, help="Weight decay")
    parser.add_argument("--dropout", type=float, default=0.5, help="Dropout rate")
    parser.add_argument("--patience", type=int, default=10, help="Early stopping patience")
    
    # Data arguments
    parser.add_argument("--image_size", type=int, default=224, help="Görüntü boyutu")
    parser.add_argument("--num_workers", type=int, default=4, help="DataLoader worker sayısı")
    parser.add_argument("--augment", action="store_true", default=True, help="Data augmentation")
    parser.add_argument("--no_augment", action="store_false", dest="augment")
    
    # Performance
    parser.add_argument("--mixed_precision", action="store_true", default=True,
                       help="Mixed precision training (FP16)")
    parser.add_argument("--no_mixed_precision", action="store_false", dest="mixed_precision")
    
    args = parser.parse_args()
    
    main(args)
