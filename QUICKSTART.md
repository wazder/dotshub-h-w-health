# 🏥 Tıbbi X-Ray Analiz Sistemi - Hızlı Başlangıç

## 1. Virtual Environment'a Giriş

```bash
source /Users/wazder/Documents/GitHub/dotshub-h-w-health/venv/bin/activate
```

## 2. Backend'i Başlatma

```bash
cd /Users/wazder/Documents/GitHub/dotshub-h-w-health/backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Backend Adresleri:**
- API: http://localhost:8000
- Docs: http://localhost:8000/docs

## 3. Frontend'i Başlatma

```bash
cd /Users/wazder/Documents/GitHub/dotshub-h-w-health/frontend
npm run dev
```

**Frontend Adresi:**
- http://localhost:5173

---

## Tek Satırda Çalıştırma

### Backend:
```bash
source /Users/wazder/Documents/GitHub/dotshub-h-w-health/venv/bin/activate && cd /Users/wazder/Documents/GitHub/dotshub-h-w-health/backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend:
```bash
cd /Users/wazder/Documents/GitHub/dotshub-h-w-health/frontend && npm run dev
```
