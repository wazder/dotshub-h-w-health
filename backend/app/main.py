"""
Tıbbi X-Ray Analiz Pipeline - FastAPI Ana Modül
================================================

Bu modül, DICOM görüntülerini kabul eden, analiz eden ve
benzer vakaları bulan REST API'yi sağlar.

Kullanım:
    uvicorn app.main:app --reload

API Endpoints:
    POST /api/analyze - DICOM dosyası analizi
    GET /api/health - Sistem sağlık kontrolü
    GET /api/patients/{id} - Hasta bilgisi sorgulama
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .models import (
    AnalysisResponse,
    ErrorResponse,
    HealthCheckResponse,
    PACSUploadResult,
    AIAnalysisResult,
    SimilarCase,
    PatientHistory
)
from .services.pacs_service import pacs_service
from .services.ai_service import ai_service
from .services.search_service import search_service
from .services.data_service import data_service

# Logging konfigürasyonu
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI uygulaması
app = FastAPI(
    title="Tıbbi X-Ray Analiz API",
    description="""
    ## 🏥 Tıbbi Görüntü Analiz Pipeline
    
    Bu API, tıbbi görüntüleri (X-Ray, CT, MRI) analiz eder ve benzer tarihsel vakaları bulur.
    
    ### Desteklenen Formatlar:
    - **DICOM** (.dcm)
    - **NIFTI** (.nii, .nii.gz)
    - **PNG** (.png)
    - **JPEG/JPG** (.jpeg, .jpg)
    
    ### Pipeline Adımları:
    1. **Görüntü Yükleme** - Görüntü PACS sunucusuna gönderilir
    2. **Format Dönüşümü** - Görüntü PNG'ye (1024x1024) dönüştürülür
    3. **CNN Analiz** - CNN modeli görüntüyü sınıflandırır (LLM yok)
    4. **Vektör Arama** - Benzer vakalar vektör veritabanında aranır
    5. **Sonuç** - Analiz ve benzer vaka bilgisi döndürülür
    
    ### Prototip Notları:
    - PACS: Mock mod (Orthanc bağlantısı simüle edilir)
    - AI Model: Mock CNN sonuçları (NIH ChestX-ray14 sınıfları)
    - Vektör DB: In-memory mock veritabanı
    """,
    version="1.0.0-prototype",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Prodüksiyonda kısıtlanmalı
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Ana Analiz Endpoint ====================

@app.post(
    "/api/analyze",
    response_model=AnalysisResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Geçersiz dosya"},
        500: {"model": ErrorResponse, "description": "Sunucu hatası"}
    },
    summary="Tıbbi Görüntü Analizi",
    description="Tıbbi görüntüyü (DICOM, NIFTI, PNG, JPEG) yükler, analiz eder ve benzer vakaları bulur."
)
async def analyze_image(
    file: UploadFile = File(..., description="Tıbbi görüntü dosyası (.dcm, .nii, .nii.gz, .png, .jpg, .jpeg)")
):
    """
    Tıbbi görüntüyü analiz eden ana endpoint.
    
    Desteklenen formatlar: DICOM, NIFTI, PNG, JPEG, JPG
    Format otomatik algılanır.
    
    Pipeline:
    1. Dosyayı PACS'a yükle
    2. PNG'ye dönüştür (1024x1024)
    3. CNN ile analiz et
    4. Vektör araması yap
    5. Benzer vaka bilgisini getir
    6. Sonuçları birleştir ve döndür
    """
    logger.info(f"Analiz isteği alındı - Dosya: {file.filename}")
    
    try:
        # 1. Dosyayı oku
        file_content = await file.read()
        
        if len(file_content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Boş dosya yüklendi"
            )
        
        logger.info(f"Dosya okundu: {len(file_content)} bytes")
        
        # 2. PACS'a yükle
        logger.info("Adım 1/4: PACS'a yükleniyor...")
        pacs_result = pacs_service.upload_dicom(file_content)
        pacs_status = PACSUploadResult(**pacs_result)
        
        # 3. AI Analizi (format otomatik algılanır)
        logger.info("Adım 2/4: AI analizi yapılıyor...")
        ai_result = ai_service.analyze_image(file_content, file.filename)
        ai_analysis = AIAnalysisResult(
            probability=ai_result["probability"],
            label=ai_result["label"],
            confidence=ai_result["confidence"],
            embedding=ai_result["embedding"]
        )
        
        # 4. Vektör Araması
        logger.info("Adım 3/4: Benzer vaka aranıyor...")
        similar_results = search_service.search_similar(
            query_vector=ai_result["embedding"],
            top_k=1
        )
        
        # 5. Hasta Bilgisi Getir
        similar_case: Optional[SimilarCase] = None
        if similar_results:
            similar_patient_id, similarity_score = similar_results[0]
            logger.info(f"Adım 4/4: Hasta bilgisi getiriliyor - ID: {similar_patient_id}")
            
            patient_data = data_service.get_patient_history(similar_patient_id)
            
            if patient_data:
                patient_history = PatientHistory(
                    patient_id=patient_data.get("patient_id", similar_patient_id),
                    age=patient_data.get("age"),
                    gender=patient_data.get("gender"),
                    diagnosis_date=patient_data.get("diagnosis_date"),
                    diagnosis=patient_data.get("diagnosis"),
                    treatment=patient_data.get("treatment"),
                    outcome=patient_data.get("outcome"),
                    history=patient_data.get("history", ""),
                    notes=patient_data.get("notes")
                )
                
                similar_case = SimilarCase(
                    patient_id=similar_patient_id,
                    similarity_score=similarity_score,
                    history=patient_history
                )
        
        # 6. Özet Oluştur
        summary = _generate_summary(ai_analysis, similar_case)
        
        # 7. Response Oluştur
        response = AnalysisResponse(
            success=True,
            timestamp=datetime.now(),
            pacs_status=pacs_status,
            ai_analysis=ai_analysis,
            similar_case=similar_case,
            summary=summary
        )
        
        logger.info("Analiz tamamlandı başarıyla!")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analiz hatası: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analiz sırasında hata oluştu: {str(e)}"
        )


def _generate_summary(ai_analysis: AIAnalysisResult, similar_case: Optional[SimilarCase]) -> str:
    """
    Analiz özeti oluşturur.
    """
    parts = [
        f"🔬 Analiz Tamamlandı.",
        f"📊 Tespit: {ai_analysis.label} ({ai_analysis.probability:.0%} olasılık, {ai_analysis.confidence} güven)"
    ]
    
    if similar_case:
        parts.append(
            f"📁 Benzer Vaka: Hasta {similar_case.patient_id} "
            f"({similar_case.similarity_score:.0%} benzerlik)"
        )
        if similar_case.history.treatment:
            parts.append(f"💊 Uygulanan Tedavi: {similar_case.history.treatment}")
        if similar_case.history.outcome:
            parts.append(f"✅ Sonuç: {similar_case.history.outcome}")
    else:
        parts.append("⚠️ Benzer vaka bulunamadı.")
    
    return " | ".join(parts)


# ==================== Yardımcı Endpoints ====================

@app.get(
    "/api/health",
    response_model=HealthCheckResponse,
    summary="Sistem Sağlık Kontrolü",
    description="Tüm servislerin durumunu kontrol eder."
)
async def health_check():
    """
    Sistem sağlık kontrolü endpoint'i.
    """
    pacs_ok, pacs_msg = pacs_service.check_connection()
    ai_ok, ai_msg = ai_service.check_health()
    search_ok, search_msg = search_service.check_health()
    data_ok, data_msg = data_service.check_health()
    
    return HealthCheckResponse(
        status="healthy" if all([pacs_ok, ai_ok, search_ok, data_ok]) else "degraded",
        version="1.0.0-prototype",
        services={
            "pacs": {"status": "ok" if pacs_ok else "error", "message": pacs_msg},
            "ai_engine": {"status": "ok" if ai_ok else "error", "message": ai_msg},
            "vector_search": {"status": "ok" if search_ok else "error", "message": search_msg},
            "data_service": {"status": "ok" if data_ok else "error", "message": data_msg}
        }
    )


@app.get(
    "/api/patients/{patient_id}",
    summary="Hasta Bilgisi Sorgulama",
    description="Belirli bir hastanın geçmiş bilgilerini getirir."
)
async def get_patient(patient_id: str):
    """
    Hasta bilgisi endpoint'i.
    """
    patient = data_service.get_patient_history(patient_id)
    
    if patient:
        return {
            "success": True,
            "patient": patient
        }
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Hasta bulunamadı: {patient_id}"
    )


@app.get(
    "/api/patients",
    summary="Tüm Hastaları Listele",
    description="Sistemdeki tüm hasta ID'lerini listeler."
)
async def list_patients():
    """
    Tüm hastaları listeler.
    """
    patient_ids = data_service.list_all_patients()
    return {
        "success": True,
        "count": len(patient_ids),
        "patient_ids": patient_ids
    }


@app.get("/", include_in_schema=False)
async def root():
    """
    Ana sayfa - API dokümantasyonuna yönlendirir.
    """
    return {
        "message": "🏥 Tıbbi X-Ray Analiz API",
        "version": "1.0.0-prototype",
        "docs": "/docs",
        "health": "/api/health"
    }


# ==================== Startup/Shutdown Events ====================

@app.on_event("startup")
async def startup_event():
    """
    Uygulama başlangıcında çalışır.
    """
    logger.info("=" * 50)
    logger.info("🏥 Tıbbi X-Ray Analiz API Başlatılıyor...")
    logger.info("=" * 50)
    
    # Servis durumlarını logla
    pacs_ok, pacs_msg = pacs_service.check_connection()
    ai_ok, ai_msg = ai_service.check_health()
    search_ok, search_msg = search_service.check_health()
    data_ok, data_msg = data_service.check_health()
    
    logger.info(f"PACS Servisi: {pacs_msg}")
    logger.info(f"AI Servisi: {ai_msg}")
    logger.info(f"Vektör Arama: {search_msg}")
    logger.info(f"Veri Servisi: {data_msg}")
    logger.info("=" * 50)
    logger.info("✅ API hazır! Docs: http://localhost:8000/docs")
    logger.info("=" * 50)


@app.on_event("shutdown")
async def shutdown_event():
    """
    Uygulama kapanışında çalışır.
    """
    logger.info("🛑 API kapatılıyor...")
