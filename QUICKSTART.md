# 🏥 Medical X-Ray Analysis System - Quick Start

## 1. Enter Virtual Environment

```bash
source /Users/wazder/Documents/GitHub/dotshub-h-w-health/venv/bin/activate
```

## 2. Start Backend

```bash
cd /Users/wazder/Documents/GitHub/dotshub-h-w-health/backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Backend URLs:**
- API: http://localhost:8000
- Docs: http://localhost:8000/docs

## 3. Start Frontend

```bash
cd /Users/wazder/Documents/GitHub/dotshub-h-w-health/frontend
npm run dev
```

**Frontend URL:**
- http://localhost:5173

---

## One-Line Commands

### Backend:
```bash
source /Users/wazder/Documents/GitHub/dotshub-h-w-health/venv/bin/activate && cd /Users/wazder/Documents/GitHub/dotshub-h-w-health/backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend:
```bash
cd /Users/wazder/Documents/GitHub/dotshub-h-w-health/frontend && npm run dev
```
