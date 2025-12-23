# 🏥 Medical X-Ray Analysis Pipeline

> Backend system that analyzes DICOM images with artificial intelligence and finds similar historical cases.

---

## 📋 Table of Contents

1. [Project Overview](#-project-overview)
2. [System Architecture](#-system-architecture)
3. [Pipeline Flow](#-pipeline-flow)
4. [File Structure](#-file-structure)
5. [Installation](#-installation)
6. [API Usage](#-api-usage)
7. [Services Details](#-services-details)
8. [Development Roadmap](#-development-roadmap)

---

## 🎯 Project Overview

This project is a **medical artificial intelligence pipeline** that analyzes X-ray images (in DICOM format) and finds similar historical cases.

### What Does It Do?
1. Takes an X-Ray DICOM file
2. Saves it to the PACS server
3. Performs disease classification with **CNN model** (no LLM)
4. Finds similar cases in the vector database
5. Returns the treatment history of the similar patient

### ⚠️ Important Note:
**LLM/GPT is NOT used in this project.** The AI service only:
- Image classification (CNN - Convolutional Neural Network)
- Vector embedding generation (for similarity search)

### Example Scenario:
\`\`\`
Doctor uploads a chest X-ray
    ↓
CNN Model: {label: "Mass", probability: 0.92}
    ↓
Vector Search: Most similar case → Patient 1045
    ↓
System: Returns Patient 1045 history from JSON
\`\`\`

---

## 🏗 System Architecture

\`\`\`
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT (Swagger UI)                       │
│                    http://localhost:8000/docs                    │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                         FastAPI (main.py)                        │
│                    Main API Controller Layer                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ POST        │  │ GET         │  │ GET                     │  │
│  │ /api/analyze│  │ /api/health │  │ /api/patients/{id}      │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      SERVICE LAYER (services/)                   │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │ PACS Service │  │  AI Service  │  │Search Service│           │
│  │              │  │              │  │              │           │
│  │ • DICOM      │  │ • Image      │  │ • Vector     │           │
│  │   Upload     │  │   Analysis   │  │   Similarity │           │
│  │ • Orthanc    │  │ • Embedding  │  │ • FAISS/     │           │
│  │   Mock       │  │   Generation │  │   Qdrant     │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│         │                  │                  │                  │
│         ▼                  ▼                  ▼                  │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Data Service                          │   │
│  │           Patient History JSON Database                  │   │
│  │              (synthetic_patients.json)                    │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
\`\`\`

---

## 🔄 Pipeline Flow

\`\`\`
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   1. UPLOAD  │────▶│   2. PACS    │────▶│   3. AI      │
│              │     │              │     │              │
│ DICOM file   │     │ Upload to    │     │ Image        │
│ sent to      │     │ Orthanc      │     │ analysis     │
│ API          │     │ (mock)       │     │ (mock)       │
└──────────────┘     └──────────────┘     └──────────────┘
                                                 │
                                                 ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   6. OUTPUT  │◀────│   5. DATA    │◀────│  4. SEARCH   │
│              │     │              │     │              │
│ Return JSON  │     │ Get Patient  │     │ Find similar │
│ response     │     │ 1045         │     │ case with    │
│              │     │ history      │     │ embedding    │
└──────────────┘     └──────────────┘     └──────────────┘
\`\`\`

### Step by Step Explanation:

| Step | Service | Description |
|------|---------|-------------|
| 1 | \`main.py\` | User POSTs DICOM file to \`/api/analyze\` endpoint |
| 2 | \`pacs_service.py\` | File is uploaded to PACS server (currently mock mode) |
| 3 | \`ai_service.py\` | AI model analyzes the image, returns disease + embedding |
| 4 | \`search_service.py\` | Similar case is searched in vector DB with embedding |
| 5 | \`data_service.py\` | Found patient ID's history is read from JSON |
| 6 | \`main.py\` | All results are combined and returned as JSON |

---

## 📁 File Structure

\`\`\`
dotshub-h-w-health/
│
├── 📄 .env                        # Environment variables (config)
├── 📄 .gitattributes              # Git settings
├── 📄 requirements.txt            # Python dependencies
├── 📄 README.md                   # This file
│
└── 📂 app/                        # Main application folder
    │
    ├── 📄 __init__.py             # Module definition
    ├── 📄 main.py                 # ⭐ FastAPI entry point
    ├── 📄 models.py               # Pydantic data models
    │
    ├── 📂 data/                   # Data files
    │   └── 📄 synthetic_patients.json  # Sample patient data
    │
    └── 📂 services/               # Business logic services
        ├── 📄 __init__.py
        ├── 📄 pacs_service.py     # PACS/Orthanc integration
        ├── 📄 ai_service.py       # Artificial intelligence engine
        ├── 📄 search_service.py   # Vector search service
        └── 📄 data_service.py     # Patient data management
\`\`\`

---

## ⚙️ Installation

### 1. Install Dependencies
\`\`\`bash
pip install -r requirements.txt
\`\`\`

### 2. Start the API
\`\`\`bash
python -m uvicorn app.main:app --reload --port 8000
\`\`\`

### 3. Open in Browser
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/api/health

---

## 🌐 API Usage

### POST /api/analyze
Analyzes the DICOM file.

**Request:**
\`\`\`bash
curl -X POST "http://localhost:8000/api/analyze" \\
  -H "Content-Type: multipart/form-data" \\
  -F "file=@xray.dcm"
\`\`\`

**Response:**
\`\`\`json
{
  "success": true,
  "timestamp": "2024-12-22T16:00:00",
  "pacs_status": {
    "success": true,
    "orthanc_id": "abc123",
    "message": "[MOCK] DICOM successfully uploaded to simulated PACS"
  },
  "ai_analysis": {
    "probability": 0.92,
    "label": "Mass",
    "confidence": "High",
    "embedding": [0.1, 0.2, 0.3, ...]
  },
  "similar_case": {
    "patient_id": "1045",
    "similarity_score": 0.89,
    "history": {
      "patient_id": "1045",
      "diagnosis": "Lung Mass",
      "treatment": "Radiotherapy",
      "outcome": "Recovery",
      "history": "Similar Case Found: Patient 1045. A similar mass was observed two years ago, Radiotherapy was applied and recovery was achieved in 6 months."
    }
  },
  "summary": "🔬 Analysis Complete. | 📊 Detection: Mass (92% probability) | 📁 Similar Case: Patient 1045"
}
\`\`\`

### GET /api/health
Checks the system status.

**Response:**
\`\`\`json
{
  "status": "healthy",
  "version": "1.0.0-prototype",
  "services": {
    "pacs": {"status": "ok", "message": "Mock mode active"},
    "ai_engine": {"status": "ok", "message": "AI service running"},
    "vector_search": {"status": "ok", "message": "4 vectors (mock mode)"},
    "data_service": {"status": "ok", "message": "4 patients"}
  }
}
\`\`\`

### GET /api/patients/{id}
Retrieves information for a specific patient.

---

## 🔧 Services Details

### 1. PACS Service (\`pacs_service.py\`)

**Task:** Uploads DICOM files to the PACS (Picture Archiving and Communication System) server.

**Currently:** Mock mode - simulates without a real Orthanc server.

\`\`\`python
# Usage
from app.services.pacs_service import pacs_service

result = pacs_service.upload_dicom(dicom_bytes)
# {"success": True, "orthanc_id": "abc123", ...}
\`\`\`

**For real integration:**
- Set \`ORTHANC_URL\` in \`.env\` file
- Install \`pyorthanc\` package

---

### 2. AI Service (\`ai_service.py\`)

**Task:** Analyzes X-Ray image with **CNN model** (NO LLM):
- Performs disease classification (e.g.: "Mass", "Pneumonia")
- Returns probability (between 0-1)
- Generates vector embedding (for similarity search)

**⚠️ NOTE:** This service does NOT use LLM/GPT. Only image processing CNN model.

**Currently:** Mock mode - returns random but consistent results.

\`\`\`python
# Usage
from app.services.ai_service import ai_service

result = ai_service.analyze_image(dicom_bytes)
# {"probability": 0.92, "label": "Mass", "embedding": [...]}
\`\`\`

**For real integration:**
- CNN model trained with PyTorch/TensorFlow
- Architectures like ResNet, EfficientNet, DenseNet
- Training with NIH ChestX-ray14 dataset

---

### 3. Search Service (\`search_service.py\`)

**Task:** Takes vector embedding, finds the most similar case in the database.

**Currently:** Mock mode - searches with cosine similarity, always returns Patient 1045.

\`\`\`python
# Usage
from app.services.search_service import search_service

results = search_service.search_similar(embedding, top_k=1)
# [("1045", 0.89)]  # (patient_id, similarity_score)
\`\`\`

**For real integration:**
- Use FAISS (Facebook AI Similarity Search) or
- Vector DB like Qdrant, Pinecone, Weaviate

---

### 4. Data Service (\`data_service.py\`)

**Task:** Reads patient history information from JSON file.

\`\`\`python
# Usage
from app.services.data_service import data_service

patient = data_service.get_patient_history("1045")
# {"patient_id": "1045", "diagnosis": "Lung Mass", ...}
\`\`\`

**Data File:** \`app/data/synthetic_patients.json\`

Currently 4 sample patients:
- **1045:** Lung Mass → Radiotherapy → Recovery
- **1046:** Pneumonia → Antibiotics → Full Recovery
- **1047:** Tuberculosis → Anti-TB Treatment → Ongoing
- **1048:** Pleural Effusion → Thoracentesis → Recovery

---

## 📊 Data Models (\`models.py\`)

| Model | Description |
|-------|-------------|
| \`AnalysisResponse\` | Main API response model |
| \`AIAnalysisResult\` | AI analysis results |
| \`PatientHistory\` | Patient history information |
| \`SimilarCase\` | Similar case information |
| \`PACSUploadResult\` | PACS upload status |
| \`HealthCheckResponse\` | System health status |

---

## 🛣 Development Roadmap

### Phase 1: Prototype (CURRENT) ✅
- [x] FastAPI structure
- [x] Mock services
- [x] Basic pipeline
- [x] Swagger documentation

### Phase 2: Real AI Integration
- [ ] Trained CNN model integration
- [ ] Real DICOM processing
- [ ] GPU support

### Phase 3: Vector DB Integration
- [ ] FAISS or Qdrant setup
- [ ] Real patient vectors
- [ ] Similarity threshold settings

### Phase 4: PACS Integration
- [ ] Orthanc server setup
- [ ] pyorthanc integration
- [ ] DICOM standard compliance

### Phase 5: Production
- [ ] Docker containerization
- [ ] Kubernetes deployment
- [ ] Monitoring & Logging
- [ ] Authentication/Authorization

---

## 🔐 Environment Variables (\`.env\`)

\`\`\`env
# PACS Settings
ORTHANC_URL=http://localhost:8042
ORTHANC_USERNAME=your_orthanc_username
ORTHANC_PASSWORD=your_orthanc_password

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# AI Model Settings
AI_MODEL_DELAY=0.5      # Simulated delay (seconds)
VECTOR_DIMENSION=128    # Embedding dimension
\`\`\`

---

## 📝 Notes

- **Mock Mode:** All services are currently running in mock mode. This allows you to develop without a real AI model or Orthanc server.

- **Prototype Purpose:** This code is not for production, it's for proof of concept (PoC).

- **For Testing:** You can easily test with "Try it out" in Swagger UI (\`/docs\`).

---

## 👥 Contributing

1. Create a branch: \`git checkout -b feature/new-feature\`
2. Commit your changes: \`git commit -m 'New feature added'\`
3. Push: \`git push origin feature/new-feature\`
4. Open a Pull Request

---

## 📄 License

MIT License

---

**For questions:** Explore the API at \`/docs\` in Swagger UI!
