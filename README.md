# 🏥 Tıbbi X-Ray Analiz Pipeline

> DICOM görüntülerini yapay zeka ile analiz eden ve benzer tarihsel vakaları bulan backend sistemi.

---

## 📋 İçindekiler

1. [Proje Özeti](#-proje-özeti)
2. [Sistem Mimarisi](#-sistem-mimarisi)
3. [Pipeline Akışı](#-pipeline-akışı)
4. [Dosya Yapısı](#-dosya-yapısı)
5. [Kurulum](#-kurulum)
6. [API Kullanımı](#-api-kullanımı)
7. [Servisler Detayı](#-servisler-detayı)
8. [Geliştirme Yol Haritası](#-geliştirme-yol-haritası)

---

## 🎯 Proje Özeti

Bu proje, röntgen görüntülerini (DICOM formatında) analiz eden ve benzer tarihsel vakaları bulan bir **tıbbi yapay zeka pipeline'ı**dır.

### Ne Yapar?
1. Bir X-Ray DICOM dosyası alır
2. PACS sunucusuna kaydeder
3. **CNN modeli** ile hastalık sınıflandırması yapar (LLM yok)
4. Vektör veritabanında benzer vakaları bulur
5. Benzer hastanın tedavi geçmişini döndürür

### ⚠️ Önemli Not:
**Bu projede LLM/GPT kullanılmıyor.** AI servisi sadece:
- Görüntü sınıflandırma (CNN - Convolutional Neural Network)
- Vektör embedding üretimi (benzerlik araması için)

### Örnek Senaryo:
```
Doktor bir akciğer röntgeni yükler
    ↓
CNN Model: {label: "Kitle", probability: 0.92}
    ↓
Vektör Arama: En benzer vaka → Hasta 1045
    ↓
Sistem: Hasta 1045 geçmişini JSON'dan döndürür
```

---

## 🏗 Sistem Mimarisi

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT (Swagger UI)                       │
│                    http://localhost:8000/docs                    │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                         FastAPI (main.py)                        │
│                    Ana API Controller Katmanı                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ POST        │  │ GET         │  │ GET                     │  │
│  │ /api/analyze│  │ /api/health │  │ /api/patients/{id}      │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      SERVİS KATMANI (services/)                  │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │ PACS Service │  │  AI Service  │  │Search Service│           │
│  │              │  │              │  │              │           │
│  │ • DICOM      │  │ • Görüntü    │  │ • Vektör     │           │
│  │   Yükleme    │  │   Analizi    │  │   Benzerlik  │           │
│  │ • Orthanc    │  │ • Embedding  │  │ • FAISS/     │           │
│  │   Mock       │  │   Üretimi    │  │   Qdrant     │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│         │                  │                  │                  │
│         ▼                  ▼                  ▼                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    Data Service                          │   │
│  │           Hasta Geçmişi JSON Veritabanı                  │   │
│  │              (synthetic_patients.json)                    │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Pipeline Akışı

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   1. UPLOAD  │────▶│   2. PACS    │────▶│   3. AI      │
│              │     │              │     │              │
│ DICOM dosya  │     │ Orthanc'a    │     │ Görüntü      │
│ API'ye       │     │ yükle        │     │ analizi      │
│ gönderilir   │     │ (mock)       │     │ (mock)       │
└──────────────┘     └──────────────┘     └──────────────┘
                                                 │
                                                 ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   6. OUTPUT  │◀────│   5. DATA    │◀────│  4. SEARCH   │
│              │     │              │     │              │
│ JSON yanıt   │     │ Hasta 1045   │     │ Embedding    │
│ döndür       │     │ geçmişini    │     │ ile benzer   │
│              │     │ getir        │     │ vaka bul     │
└──────────────┘     └──────────────┘     └──────────────┘
```

### Adım Adım Açıklama:

| Adım | Servis | Açıklama |
|------|--------|----------|
| 1 | `main.py` | Kullanıcı DICOM dosyasını `/api/analyze` endpoint'ine POST eder |
| 2 | `pacs_service.py` | Dosya PACS sunucusuna yüklenir (şu an mock mod) |
| 3 | `ai_service.py` | AI modeli görüntüyü analiz eder, hastalık + embedding döndürür |
| 4 | `search_service.py` | Embedding ile vektör DB'de benzer vaka aranır |
| 5 | `data_service.py` | Bulunan hasta ID'sinin geçmiş bilgisi JSON'dan okunur |
| 6 | `main.py` | Tüm sonuçlar birleştirilip JSON olarak döndürülür |

---

## 📁 Dosya Yapısı

```
dotshub-h-w-health/
│
├── 📄 .env                        # Çevre değişkenleri (config)
├── 📄 .gitattributes              # Git ayarları
├── 📄 requirements.txt            # Python bağımlılıkları
├── 📄 README.md                   # Bu dosya
│
└── 📂 app/                        # Ana uygulama klasörü
    │
    ├── 📄 __init__.py             # Modül tanımı
    ├── 📄 main.py                 # ⭐ FastAPI giriş noktası
    ├── 📄 models.py               # Pydantic veri modelleri
    │
    ├── 📂 data/                   # Veri dosyaları
    │   └── 📄 synthetic_patients.json  # Örnek hasta verileri
    │
    └── 📂 services/               # İş mantığı servisleri
        ├── 📄 __init__.py
        ├── 📄 pacs_service.py     # PACS/Orthanc entegrasyonu
        ├── 📄 ai_service.py       # Yapay zeka motoru
        ├── 📄 search_service.py   # Vektör arama servisi
        └── 📄 data_service.py     # Hasta verisi yönetimi
```

---

## ⚙️ Kurulum

### 1. Bağımlılıkları Yükle
```bash
pip install -r requirements.txt
```

### 2. API'yi Başlat
```bash
python -m uvicorn app.main:app --reload --port 8000
```

### 3. Tarayıcıda Aç
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/api/health

---

## 🌐 API Kullanımı

### POST /api/analyze
DICOM dosyasını analiz eder.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/analyze" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@xray.dcm"
```

**Response:**
```json
{
  "success": true,
  "timestamp": "2024-12-22T16:00:00",
  "pacs_status": {
    "success": true,
    "orthanc_id": "abc123",
    "message": "[MOCK] DICOM başarıyla simüle PACS'a yüklendi"
  },
  "ai_analysis": {
    "probability": 0.92,
    "label": "Kitle",
    "confidence": "Yüksek",
    "embedding": [0.1, 0.2, 0.3, ...]
  },
  "similar_case": {
    "patient_id": "1045",
    "similarity_score": 0.89,
    "history": {
      "patient_id": "1045",
      "diagnosis": "Akciğer Kitlesi",
      "treatment": "Radyoterapi",
      "outcome": "İyileşme",
      "history": "Benzer Vaka Bulundu: Hasta 1045. İki yıl önce benzer bir kitle görüldü, Radyoterapi uygulandı ve 6 ayda iyileşme sağlandı."
    }
  },
  "summary": "🔬 Analiz Tamamlandı. | 📊 Tespit: Kitle (92% olasılık) | 📁 Benzer Vaka: Hasta 1045"
}
```

### GET /api/health
Sistem durumunu kontrol eder.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0-prototype",
  "services": {
    "pacs": {"status": "ok", "message": "Mock mod aktif"},
    "ai_engine": {"status": "ok", "message": "AI servisi çalışıyor"},
    "vector_search": {"status": "ok", "message": "4 vektör (mock mod)"},
    "data_service": {"status": "ok", "message": "4 hasta"}
  }
}
```

### GET /api/patients/{id}
Belirli bir hastanın bilgisini getirir.

---

## 🔧 Servisler Detayı

### 1. PACS Service (`pacs_service.py`)

**Görev:** DICOM dosyalarını PACS (Picture Archiving and Communication System) sunucusuna yükler.

**Şu an:** Mock mod - gerçek Orthanc sunucusu olmadan simüle eder.

```python
# Kullanım
from app.services.pacs_service import pacs_service

result = pacs_service.upload_dicom(dicom_bytes)
# {"success": True, "orthanc_id": "abc123", ...}
```

**Gerçek entegrasyon için:**
- `.env` dosyasında `ORTHANC_URL` ayarla
- `pyorthanc` paketini yükle

---

### 2. AI Service (`ai_service.py`)

**Görev:** X-Ray görüntüsünü **CNN modeli** ile analiz eder (LLM YOK):
- Hastalık sınıflandırması yapar (örn: "Kitle", "Pnömoni")
- Olasılık döndürür (0-1 arası)
- Vektör embedding üretir (benzerlik araması için)

**⚠️ NOT:** Bu servis LLM/GPT kullanmaz. Sadece görüntü işleme CNN modeli.

**Şu an:** Mock mod - rastgele ama tutarlı sonuçlar döndürür.

```python
# Kullanım
from app.services.ai_service import ai_service

result = ai_service.analyze_image(dicom_bytes)
# {"probability": 0.92, "label": "Kitle", "embedding": [...]}
```

**Gerçek entegrasyon için:**
- PyTorch/TensorFlow ile eğitilmiş CNN modeli
- ResNet, EfficientNet, DenseNet gibi mimariler
- NIH ChestX-ray14 dataset ile eğitim

---

### 3. Search Service (`search_service.py`)

**Görev:** Vektör embedding'i alır, veritabanında en benzer vakayı bulur.

**Şu an:** Mock mod - cosine similarity ile arama yapar, her zaman Hasta 1045 döndürür.

```python
# Kullanım
from app.services.search_service import search_service

results = search_service.search_similar(embedding, top_k=1)
# [("1045", 0.89)]  # (hasta_id, benzerlik_skoru)
```

**Gerçek entegrasyon için:**
- FAISS (Facebook AI Similarity Search) veya
- Qdrant, Pinecone, Weaviate gibi vektör DB kullan

---

### 4. Data Service (`data_service.py`)

**Görev:** Hasta geçmiş bilgilerini JSON dosyasından okur.

```python
# Kullanım
from app.services.data_service import data_service

patient = data_service.get_patient_history("1045")
# {"patient_id": "1045", "diagnosis": "Akciğer Kitlesi", ...}
```

**Veri Dosyası:** `app/data/synthetic_patients.json`

Şu an 4 örnek hasta var:
- **1045:** Akciğer Kitlesi → Radyoterapi → İyileşme
- **1046:** Pnömoni → Antibiyotik → Tam İyileşme
- **1047:** Tüberküloz → Anti-TB Tedavi → Devam Ediyor
- **1048:** Plevral Efüzyon → Torasentez → İyileşme

---

## 📊 Veri Modelleri (`models.py`)

| Model | Açıklama |
|-------|----------|
| `AnalysisResponse` | Ana API yanıt modeli |
| `AIAnalysisResult` | AI analiz sonuçları |
| `PatientHistory` | Hasta geçmiş bilgisi |
| `SimilarCase` | Benzer vaka bilgisi |
| `PACSUploadResult` | PACS yükleme durumu |
| `HealthCheckResponse` | Sistem sağlık durumu |

---

## 🛣 Geliştirme Yol Haritası

### Faz 1: Prototip (ŞU AN) ✅
- [x] FastAPI yapısı
- [x] Mock servisler
- [x] Temel pipeline
- [x] Swagger dokümantasyonu

### Faz 2: Gerçek AI Entegrasyonu
- [ ] Eğitilmiş CNN modeli entegrasyonu
- [ ] Gerçek DICOM işleme
- [ ] GPU desteği

### Faz 3: Vektör DB Entegrasyonu
- [ ] FAISS veya Qdrant kurulumu
- [ ] Gerçek hasta vektörleri
- [ ] Benzerlik eşik ayarları

### Faz 4: PACS Entegrasyonu
- [ ] Orthanc sunucu kurulumu
- [ ] pyorthanc entegrasyonu
- [ ] DICOM standardı uyumu

### Faz 5: Prodüksiyon
- [ ] Docker containerization
- [ ] Kubernetes deployment
- [ ] Monitoring & Logging
- [ ] Authentication/Authorization

---

## 🔐 Çevre Değişkenleri (`.env`)

```env
# PACS Ayarları
ORTHANC_URL=http://localhost:8042
ORTHANC_USERNAME=your_orthanc_username
ORTHANC_PASSWORD=your_orthanc_password

# API Ayarları
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# AI Model Ayarları
AI_MODEL_DELAY=0.5      # Simüle gecikme (saniye)
VECTOR_DIMENSION=128    # Embedding boyutu
```

---

## 📝 Notlar

- **Mock Mod:** Tüm servisler şu an mock modda çalışıyor. Bu, gerçek AI modeli veya Orthanc sunucusu olmadan geliştirme yapmanızı sağlar.

- **Prototip Amaçlı:** Bu kod üretim için değil, konsept kanıtlama (PoC) içindir.

- **Test için:** Swagger UI'da (`/docs`) "Try it out" ile kolayca test edebilirsiniz.

---

## 👥 Katkıda Bulunma

1. Branch oluştur: `git checkout -b feature/yeni-ozellik`
2. Değişiklikleri commit et: `git commit -m 'Yeni özellik eklendi'`
3. Push et: `git push origin feature/yeni-ozellik`
4. Pull Request aç

---

## 📄 Lisans

MIT License

---

**Sorularınız için:** Swagger UI'da `/docs` adresinde API'yi keşfedin!
