# 🔗 Backend-Frontend Integration Guide

This document explains the integration of backend and frontend components of the `dotshub-h-w-health` project.

## 📋 Quick Start

### 1. Start Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

When backend is running, it will be accessible at:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/health

### 2. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend will run at http://localhost:5173.

---

## 🧪 Integration Test Scenarios

### Test 1: Health Check (Happy Path)

**Goal:** Verify that backend is running and all services are active.

```bash
curl http://localhost:8000/api/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0-prototype",
  "services": {
    "pacs": {"status": "ok", "message": "..."},
    "ai_engine": {"status": "ok", "message": "..."},
    "vector_search": {"status": "ok", "message": "..."},
    "data_service": {"status": "ok", "message": "..."}
  }
}
```

### Test 2: Image Analysis (Happy Path)

**Goal:** Upload an image and get AI analysis results.

**With Terminal:**
```bash
curl -X POST "http://localhost:8000/api/analyze" \
  -F "file=@/path/to/xray.png"
```

**With Frontend:**
1. Go to http://localhost:5173
2. Drag an image to the "Upload X-Ray Image" area on Dashboard
3. Watch the analysis process
4. Verify results are displayed

**Expected Response:**
```json
{
  "success": true,
  "timestamp": "2024-12-22T16:00:00",
  "pacsStatus": {
    "success": true,
    "orthancId": "mock-xxxxx",
    "message": "DICOM successfully uploaded to PACS"
  },
  "aiAnalysis": {
    "label": "Mass",
    "labelTr": "Mass",
    "probability": 0.85,
    "confidence": "High",
    "embedding": [...]
  },
  "similarCase": {
    "patientId": "1045",
    "similarityScore": 0.89,
    "history": {
      "patientId": "1045",
      "age": 58,
      "diagnosis": "Lung Mass",
      "treatment": "Radiotherapy",
      "outcome": "Recovery"
    }
  },
  "summary": "🔬 Analysis Complete. 📊 Detection: Mass (85% probability)..."
}
```

### Test 3: Patient Query

**Goal:** Get patient information with a specific patient ID.

```bash
curl http://localhost:8000/api/patients/1045
```

**With Frontend:**
- Enter `1045` in the header search bar and press Enter

**Expected Response:**
```json
{
  "success": true,
  "patient": {
    "patient_id": "1045",
    "age": 58,
    "gender": "Male",
    "diagnosis": "Lung Mass",
    "treatment": "Radiotherapy",
    "outcome": "Recovery"
  }
}
```

### Test 4: Error Handling

**Goal:** Verify proper error messages are returned for invalid requests.

**Sending empty file:**
```bash
curl -X POST "http://localhost:8000/api/analyze" \
  -F "file=@/dev/null"
```

**Expected:** HTTP 400 - "Empty file uploaded"

**Querying non-existent patient:**
```bash
curl http://localhost:8000/api/patients/9999
```

**Expected:** HTTP 404 - "Patient not found: 9999"

---

## 🔄 Data Transformation (snake_case ↔ camelCase)

Frontend automatically transforms backend data:

| Backend (Python) | Frontend (JavaScript) |
|------------------|----------------------|
| `patient_id` | `patientId` |
| `similarity_score` | `similarityScore` |
| `ai_analysis` | `aiAnalysis` |
| `pacs_status` | `pacsStatus` |
| `diagnosis_date` | `diagnosisDate` |

This transformation is done by `fromBackend()` and `toBackend()` functions in [src/services/api.js](frontend/src/services/api.js).

---

## 📁 Created/Updated Files

### New Files:
- `frontend/.env` - Environment variables
- `frontend/.env.example` - Example environment variables
- `frontend/src/services/api.js` - API client layer
- `frontend/src/hooks/useApi.js` - React hooks
- `frontend/src/components/ErrorBoundary.jsx` - Error boundary
- `frontend/src/components/ToastProvider.jsx` - Notification system

### Updated Files:
- `frontend/vite.config.js` - Proxy added
- `frontend/src/main.jsx` - ErrorBoundary & ToastProvider added
- `frontend/src/components/Dashboard.jsx` - Real API integration
- `frontend/src/components/AnalysisView.jsx` - External progress support
- `frontend/src/components/ResultsView.jsx` - API data support
- `backend/app/main.py` - CORS security configuration
- `backend/.env` - CORS origin list added

---

## ⚠️ Known Limitations (Prototype)

1. **JWT Authentication:** Not ready, added as placeholder
2. **PACS Connection:** Mock mode active
3. **AI Model:** Returns mock results
4. **Vector DB:** In-memory, not persistent
5. **Patient Data:** Limited to 4 synthetic patients

---

## 🔐 Security Notes

- CORS origin list is defined in `.env` file
- In production, only real domains should be added
- JWT token management infrastructure is ready (add auth middleware to backend to activate)
- HTTPS should be used for sensitive data
