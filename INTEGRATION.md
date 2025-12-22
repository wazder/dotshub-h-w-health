# 🔗 Backend-Frontend Entegrasyon Rehberi

Bu doküman, `dotshub-h-w-health` projesinin backend ve frontend bileşenlerinin entegrasyonunu açıklar.

## 📋 Hızlı Başlangıç

### 1. Backend'i Başlatın

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend çalıştığında şu URL'lerde erişilebilir olacak:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/health

### 2. Frontend'i Başlatın

```bash
cd frontend
npm install
npm run dev
```

Frontend http://localhost:5173 adresinde çalışacak.

---

## 🧪 Entegrasyon Test Senaryoları

### Test 1: Health Check (Happy Path)

**Amaç:** Backend'in çalıştığını ve tüm servislerin aktif olduğunu doğrula.

```bash
curl http://localhost:8000/api/health
```

**Beklenen Yanıt:**
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

### Test 2: Görüntü Analizi (Happy Path)

**Amaç:** Bir görüntü yükleyip AI analiz sonucu alabilmek.

**Terminal ile:**
```bash
curl -X POST "http://localhost:8000/api/analyze" \
  -F "file=@/path/to/xray.png"
```

**Frontend ile:**
1. http://localhost:5173 adresine gidin
2. Dashboard'da "Drop MRI Scan Here" alanına bir görüntü sürükleyin
3. Analiz sürecini izleyin
4. Sonuçların görüntülendiğini doğrulayın

**Beklenen Yanıt:**
```json
{
  "success": true,
  "timestamp": "2024-12-22T16:00:00",
  "pacsStatus": {
    "success": true,
    "orthancId": "mock-xxxxx",
    "message": "DICOM başarıyla PACS'a yüklendi"
  },
  "aiAnalysis": {
    "label": "Mass",
    "labelTr": "Kitle",
    "probability": 0.85,
    "confidence": "Yüksek",
    "embedding": [...]
  },
  "similarCase": {
    "patientId": "1045",
    "similarityScore": 0.89,
    "history": {
      "patientId": "1045",
      "age": 58,
      "diagnosis": "Akciğer Kitlesi",
      "treatment": "Radyoterapi",
      "outcome": "İyileşme"
    }
  },
  "summary": "🔬 Analiz Tamamlandı. 📊 Tespit: Kitle (85% olasılık)..."
}
```

### Test 3: Hasta Sorgulama

**Amaç:** Belirli bir hasta ID ile hasta bilgisi getirmek.

```bash
curl http://localhost:8000/api/patients/1045
```

**Frontend ile:**
- Header'daki arama çubuğuna `1045` yazıp Enter'a basın

**Beklenen Yanıt:**
```json
{
  "success": true,
  "patient": {
    "patient_id": "1045",
    "age": 58,
    "gender": "Erkek",
    "diagnosis": "Akciğer Kitlesi",
    "treatment": "Radyoterapi",
    "outcome": "İyileşme"
  }
}
```

### Test 4: Hata Yönetimi

**Amaç:** Hatalı isteklerde uygun hata mesajı döndüğünü doğrula.

**Boş dosya gönderme:**
```bash
curl -X POST "http://localhost:8000/api/analyze" \
  -F "file=@/dev/null"
```

**Beklenen:** HTTP 400 - "Boş dosya yüklendi"

**Olmayan hasta sorgulama:**
```bash
curl http://localhost:8000/api/patients/9999
```

**Beklenen:** HTTP 404 - "Hasta bulunamadı: 9999"

---

## 🔄 Veri Dönüşümü (snake_case ↔ camelCase)

Frontend otomatik olarak backend verisini dönüştürür:

| Backend (Python) | Frontend (JavaScript) |
|------------------|----------------------|
| `patient_id` | `patientId` |
| `similarity_score` | `similarityScore` |
| `ai_analysis` | `aiAnalysis` |
| `pacs_status` | `pacsStatus` |
| `diagnosis_date` | `diagnosisDate` |

Bu dönüşüm [src/services/api.js](frontend/src/services/api.js) dosyasındaki `fromBackend()` ve `toBackend()` fonksiyonları tarafından yapılır.

---

## 📁 Oluşturulan/Güncellenen Dosyalar

### Yeni Dosyalar:
- `frontend/.env` - Çevre değişkenleri
- `frontend/.env.example` - Örnek çevre değişkenleri
- `frontend/src/services/api.js` - API istemci katmanı
- `frontend/src/hooks/useApi.js` - React hooks
- `frontend/src/components/ErrorBoundary.jsx` - Hata sınırı
- `frontend/src/components/ToastProvider.jsx` - Bildirim sistemi

### Güncellenen Dosyalar:
- `frontend/vite.config.js` - Proxy eklendi
- `frontend/src/main.jsx` - ErrorBoundary & ToastProvider eklendi
- `frontend/src/components/Dashboard.jsx` - Gerçek API entegrasyonu
- `frontend/src/components/AnalysisView.jsx` - External progress desteği
- `frontend/src/components/ResultsView.jsx` - API verisi desteği
- `backend/app/main.py` - CORS güvenlik yapılandırması
- `backend/.env` - CORS origin listesi eklendi

---

## ⚠️ Bilinen Sınırlamalar (Prototip)

1. **JWT Authentication:** Hazır değil, placeholder olarak eklenmiş
2. **PACS Bağlantısı:** Mock mod aktif
3. **AI Model:** Mock sonuçlar döndürüyor
4. **Vektör DB:** In-memory, kalıcı değil
5. **Hasta Verisi:** 4 sentetik hasta ile sınırlı

---

## 🔐 Güvenlik Notları

- CORS origin listesi `.env` dosyasında tanımlı
- Production'da sadece gerçek domain'ler eklenmeli
- JWT token yönetimi için altyapı hazır (aktifleştirmek için backend'e auth middleware eklenmeli)
- Hassas veriler için HTTPS kullanılmalı
