# Neuro-Radiology Platform

Modular Brain Pathology Detection System for tumor segmentation and Alzheimer's disease classification.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the API server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/models/status` | GET | Model loading status |
| `/analyze` | POST | Analyze MRI scan |
| `/preprocess` | POST | Preprocessing only |

## Architecture

```
Input (NIfTI/DICOM)
        ↓
  Preprocessing
  (Skull Strip → Registration → Normalize)
        ↓
    Router
  (Mass Effect vs Atrophy)
        ↓
  ┌─────┴─────┐
  ↓           ↓
Tumor      Alzheimer
(U-Net)    (ResNet)
  ↓           ↓
  └─────┬─────┘
        ↓
  JSON Report
```

## Project Structure

```
neuro-radiology-platform/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Configuration
│   ├── preprocessing.py     # Skull stripping & registration
│   ├── router.py            # Intelligent model router
│   ├── models/
│   │   ├── base.py          # Base model interface
│   │   ├── tumor.py         # 3D U-Net
│   │   └── alzheimer.py     # 3D ResNet
│   ├── services/
│   │   └── inference.py     # Pipeline orchestrator
│   └── utils/
│       └── io.py            # File I/O utilities
├── data/templates/          # MNI152 template
├── weights/                 # Model weights
└── tests/
```

## Usage Example

```python
from app.services.inference import InferencePipeline

pipeline = InferencePipeline()
result = pipeline.run("path/to/brain_mri.nii.gz", analysis_type="auto")
print(result)
```
