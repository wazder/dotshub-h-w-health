# NIH Chest X-ray Multi-Label Model Eğitimi

## 🎯 Amaç
14 hastalığı ayrı ayrı tespit edebilen multi-label sınıflandırma modeli eğitmek.

### Tespit Edilebilecek Hastalıklar:
| İngilizce | Türkçe |
|-----------|--------|
| Atelectasis | Atelektazi |
| Cardiomegaly | Kardiyomegali |
| Effusion | Plevral Efüzyon |
| Infiltration | İnfiltrasyon |
| Mass | Kitle |
| Nodule | Nodül |
| Pneumonia | Pnömoni (Zatürre) |
| Pneumothorax | Pnömotoraks |
| Consolidation | Konsolidasyon |
| Edema | Pulmoner Ödem |
| Emphysema | Amfizem |
| Fibrosis | Fibrozis |
| Pleural_Thickening | Plevral Kalınlaşma |
| Hernia | Herni |

## 📁 Veri Seti Yapısı

RunPod'da veri setinin şu yapıda olması gerekiyor:

```
/workspace/data/
├── Data_Entry_2017.csv          # Ana metadata dosyası
├── train_val_list_NIH.txt       # Train/val görüntü listesi
├── test_list_NIH.txt            # Test görüntü listesi
└── images/                      # veya images-224/
    ├── 00000001_000.png
    ├── 00000001_001.png
    └── ...
```

## 🚀 RunPod'da Eğitim

### 1. Ortamı Hazırla

```bash
# RunPod terminal'inde
cd /workspace

# Bu repo'yu klonla veya dosyaları yükle
git clone https://github.com/wazder/dotshub-h-w-health.git
cd dotshub-h-w-health/model

# Dependencies yükle
pip install -r requirements_training.txt
```

### 2. Eğitimi Başlat

```bash
# Temel eğitim (önerilen ayarlar)
python train_multilabel.py \
    --data_dir /workspace/data \
    --output_dir /workspace/output \
    --epochs 50 \
    --batch_size 32 \
    --lr 1e-4 \
    --image_size 224

# Daha büyük batch size (eğer GPU belleği yeterliyse)
python train_multilabel.py \
    --data_dir /workspace/data \
    --output_dir /workspace/output \
    --epochs 50 \
    --batch_size 64 \
    --lr 2e-4 \
    --image_size 224

# Daha büyük görüntüler için (512x512)
python train_multilabel.py \
    --data_dir /workspace/data \
    --output_dir /workspace/output \
    --epochs 50 \
    --batch_size 16 \
    --lr 1e-4 \
    --image_size 512
```

### 3. Eğitim Parametreleri

| Parametre | Varsayılan | Açıklama |
|-----------|------------|----------|
| `--data_dir` | (zorunlu) | Veri setinin yolu |
| `--output_dir` | ./output | Model çıktı klasörü |
| `--epochs` | 50 | Epoch sayısı |
| `--batch_size` | 32 | Batch size |
| `--lr` | 1e-4 | Learning rate |
| `--image_size` | 224 | Görüntü boyutu |
| `--dropout` | 0.5 | Dropout oranı |
| `--patience` | 10 | Early stopping sabır |
| `--augment` | True | Data augmentation |
| `--mixed_precision` | True | FP16 eğitim |

## 📊 Beklenen Sonuçlar

İyi eğitilmiş bir modelden beklenen metrikler:

| Hastalık | Hedef AUC |
|----------|-----------|
| Cardiomegaly | >0.90 |
| Edema | >0.85 |
| Consolidation | >0.80 |
| Atelectasis | >0.75 |
| Pneumothorax | >0.85 |
| ... | ... |
| **Macro Average** | **>0.80** |

## 🔄 Eğitim Sonrası

### 1. Modeli İndir

```bash
# RunPod'dan modeli indir
scp runpod:/workspace/output/best_model.pth ./model/
```

### 2. Sisteme Entegre Et

Eğitilen model `model/best_model.pth` olarak kaydedildikten sonra:

1. `backend/app/services/ai_service_real.py` dosyasını güncelle
2. Model çıktı sayısını 1'den 14'e değiştir
3. Sigmoid çıktılarını parse et

Detaylı entegrasyon için bir sonraki adımda yardımcı olabilirim.

## 🔧 Troubleshooting

### CUDA Out of Memory
```bash
# Batch size'ı düşür
python train_multilabel.py --data_dir /workspace/data --batch_size 16
```

### Görüntüler Bulunamıyor
```bash
# Görüntü klasörünü kontrol et
ls /workspace/data/images/ | head
# veya
ls /workspace/data/images-224/images-224/ | head
```

### Slow Training
```bash
# Worker sayısını artır
python train_multilabel.py --data_dir /workspace/data --num_workers 8
```

## 📈 TensorBoard ile İzleme (Opsiyonel)

```bash
# Ayrı bir terminalde
tensorboard --logdir /workspace/output/logs --port 6006
```

## ⏱️ Tahmini Süre

| GPU | Batch Size | Epoch Süresi | 50 Epoch |
|-----|------------|--------------|----------|
| RTX 3090 | 32 | ~15 dk | ~12 saat |
| A100 | 64 | ~8 dk | ~7 saat |
| V100 | 32 | ~20 dk | ~17 saat |
