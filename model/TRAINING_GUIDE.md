# NIH Chest X-ray Multi-Label Model Training

## 🎯 Objective
Train a multi-label classification model capable of detecting 14 diseases individually.

### Detectable Diseases:
| English | Description |
|---------|-------------|
| Atelectasis | Lung collapse |
| Cardiomegaly | Enlarged heart |
| Effusion | Pleural effusion |
| Infiltration | Lung infiltration |
| Mass | Lung mass |
| Nodule | Lung nodule |
| Pneumonia | Lung infection |
| Pneumothorax | Collapsed lung |
| Consolidation | Lung consolidation |
| Edema | Pulmonary edema |
| Emphysema | Lung emphysema |
| Fibrosis | Lung fibrosis |
| Pleural_Thickening | Pleural thickening |
| Hernia | Hernia |

## 📁 Dataset Structure

The dataset must be organized in the following structure on RunPod:

```
/workspace/data/
├── Data_Entry_2017.csv          # Main metadata file
├── train_val_list_NIH.txt       # Train/val image list
├── test_list_NIH.txt            # Test image list
└── images/                      # or images-224/
    ├── 00000001_000.png
    ├── 00000001_001.png
    └── ...
```

## 🚀 Training on RunPod

### 1. Prepare the Environment

```bash
# In RunPod terminal
cd /workspace

# Clone this repo or upload files
git clone https://github.com/wazder/dotshub-h-w-health.git
cd dotshub-h-w-health/model

# Install dependencies
pip install -r requirements_training.txt
```

### 2. Start Training

```bash
# Basic training (recommended settings)
python train_multilabel.py \
    --data_dir /workspace/data \
    --output_dir /workspace/output \
    --epochs 50 \
    --batch_size 32 \
    --lr 1e-4 \
    --image_size 224

# Larger batch size (if GPU memory allows)
python train_multilabel.py \
    --data_dir /workspace/data \
    --output_dir /workspace/output \
    --epochs 50 \
    --batch_size 64 \
    --lr 2e-4 \
    --image_size 224

# For larger images (512x512)
python train_multilabel.py \
    --data_dir /workspace/data \
    --output_dir /workspace/output \
    --epochs 50 \
    --batch_size 16 \
    --lr 1e-4 \
    --image_size 512
```

### 3. Training Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--data_dir` | (required) | Path to the dataset |
| `--output_dir` | ./output | Model output folder |
| `--epochs` | 50 | Number of epochs |
| `--batch_size` | 32 | Batch size |
| `--lr` | 1e-4 | Learning rate |
| `--image_size` | 224 | Image size |
| `--dropout` | 0.5 | Dropout rate |
| `--patience` | 10 | Early stopping patience |
| `--augment` | True | Data augmentation |
| `--mixed_precision` | True | FP16 training |

## 📊 Expected Results

Expected metrics from a well-trained model:

| Disease | Target AUC |
|---------|------------|
| Cardiomegaly | >0.90 |
| Edema | >0.85 |
| Consolidation | >0.80 |
| Atelectasis | >0.75 |
| Pneumothorax | >0.85 |
| ... | ... |
| **Macro Average** | **>0.80** |

## 🔄 Post-Training

### 1. Download the Model

```bash
# Download model from RunPod
scp runpod:/workspace/output/best_model.pth ./model/
```

### 2. Integrate into the System

After the trained model is saved as `model/best_model.pth`:

1. Update the `backend/app/services/ai_service_real.py` file
2. Change model output count from 1 to 14
3. Parse sigmoid outputs

I can help with detailed integration in the next step.

## 🔧 Troubleshooting

### CUDA Out of Memory
```bash
# Reduce batch size
python train_multilabel.py --data_dir /workspace/data --batch_size 16
```

### Images Not Found
```bash
# Check image folder
ls /workspace/data/images/ | head
# or
ls /workspace/data/images-224/images-224/ | head
```

### Slow Training
```bash
# Increase number of workers
python train_multilabel.py --data_dir /workspace/data --num_workers 8
```

## 📈 Monitoring with TensorBoard (Optional)

```bash
# In a separate terminal
tensorboard --logdir /workspace/output/logs --port 6006
```

## ⏱️ Estimated Time

| GPU | Batch Size | Epoch Duration | 50 Epochs |
|-----|------------|----------------|-----------|
| RTX 3090 | 32 | ~15 min | ~12 hours |
| A100 | 64 | ~8 min | ~7 hours |
| V100 | 32 | ~20 min | ~17 hours |
