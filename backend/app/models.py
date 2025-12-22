"""
Pydantic modelleri - API request/response şemaları
Tıbbi X-Ray Analiz Pipeline için veri modelleri
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# ==================== AI Analiz Modelleri ====================

class DetectedDisease(BaseModel):
    """Tespit edilen hastalık detayı"""
    label: str = Field(..., description="Hastalık etiketi (İngilizce)")
    label_tr: str = Field(..., description="Hastalık etiketi (Türkçe)")
    probability: float = Field(..., ge=0.0, le=1.0, description="Olasılık")
    description: str = Field("", description="Hastalık açıklaması")


class AIAnalysisResult(BaseModel):
    """AI motorunun döndürdüğü analiz sonucu - Multi-Label Model"""
    probability: float = Field(..., ge=0.0, le=1.0, description="En yüksek olasılık")
    label: str = Field(..., description="Birincil tespit (İngilizce)")
    label_tr: str = Field("", description="Birincil tespit (Türkçe)")
    confidence: str = Field(..., description="Güven seviyesi: Düşük, Orta, Yüksek")
    is_pathology: bool = Field(False, description="Patoloji tespit edildi mi")
    detected_diseases: List[DetectedDisease] = Field(default=[], description="Tespit edilen hastalıklar")
    disease_count: int = Field(0, description="Tespit edilen hastalık sayısı")
    embedding: List[float] = Field(..., description="Görüntü vektör gömülümü")


class DiagnosisDetail(BaseModel):
    """Detaylı tanı bilgisi"""
    condition: str = Field(..., description="Tespit edilen durum")
    probability: float = Field(..., ge=0.0, le=1.0)
    severity: str = Field(..., description="Şiddet: Hafif, Orta, Ciddi")


# ==================== Hasta Modelleri ====================

class PatientHistory(BaseModel):
    """Hasta geçmiş bilgisi"""
    patient_id: str = Field(..., description="Hasta ID")
    age: Optional[int] = Field(None, description="Hasta yaşı")
    gender: Optional[str] = Field(None, description="Cinsiyet")
    diagnosis_date: Optional[str] = Field(None, description="Tanı tarihi")
    diagnosis: Optional[str] = Field(None, description="Tanı")
    treatment: Optional[str] = Field(None, description="Uygulanan tedavi")
    outcome: Optional[str] = Field(None, description="Sonuç")
    history: str = Field(..., description="Hasta hikayesi özeti")
    notes: Optional[str] = Field(None, description="Ek notlar")


class SimilarCase(BaseModel):
    """Benzer vaka bilgisi"""
    patient_id: str = Field(..., description="Benzer hasta ID")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Benzerlik skoru")
    image_id: Optional[str] = Field(None, description="Benzer görüntü ID")
    image_url: Optional[str] = Field(None, description="Görüntü URL'i")
    history: PatientHistory = Field(..., description="Hasta geçmişi")


# ==================== PACS Modelleri ====================

class PACSUploadResult(BaseModel):
    """PACS'a yükleme sonucu"""
    success: bool = Field(..., description="Yükleme başarılı mı")
    orthanc_id: Optional[str] = Field(None, description="Orthanc instance ID")
    study_uid: Optional[str] = Field(None, description="DICOM Study UID")
    series_uid: Optional[str] = Field(None, description="DICOM Series UID")
    message: str = Field(..., description="İşlem mesajı")


# ==================== API Response Modelleri ====================

class AnalysisResponse(BaseModel):
    """Ana analiz API yanıtı"""
    success: bool = Field(..., description="İşlem başarılı mı")
    timestamp: datetime = Field(default_factory=datetime.now, description="İşlem zamanı")
    
    # PACS bilgisi
    pacs_status: PACSUploadResult = Field(..., description="PACS yükleme durumu")
    
    # AI analiz sonuçları
    ai_analysis: AIAnalysisResult = Field(..., description="AI analiz sonuçları")
    
    # Benzer vakalar (birden fazla)
    similar_cases: List[SimilarCase] = Field(default=[], description="Bulunan benzer vakalar")
    
    # Geriye uyumluluk için (deprecated)
    similar_case: Optional[SimilarCase] = Field(None, description="[Deprecated] İlk benzer vaka")
    
    # Özet
    summary: str = Field(..., description="Analiz özeti")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "timestamp": "2024-12-22T16:00:00",
                "pacs_status": {
                    "success": True,
                    "orthanc_id": "abc123",
                    "study_uid": "1.2.3.4.5",
                    "series_uid": "1.2.3.4.5.6",
                    "message": "DICOM başarıyla PACS'a yüklendi"
                },
                "ai_analysis": {
                    "probability": 0.92,
                    "label": "Kitle",
                    "confidence": "Yüksek",
                    "embedding": [0.1, 0.2, 0.3]
                },
                "similar_case": {
                    "patient_id": "1045",
                    "similarity_score": 0.89,
                    "history": {
                        "patient_id": "1045",
                        "history": "Benzer vaka bulundu..."
                    }
                },
                "summary": "Analiz tamamlandı. Kitle tespit edildi (%92). Benzer vaka: Hasta 1045"
            }
        }


class ErrorResponse(BaseModel):
    """Hata yanıtı"""
    success: bool = Field(default=False)
    error_code: str = Field(..., description="Hata kodu")
    message: str = Field(..., description="Hata mesajı")
    details: Optional[str] = Field(None, description="Detaylı hata bilgisi")


class HealthCheckResponse(BaseModel):
    """Sağlık kontrolü yanıtı"""
    status: str = Field(..., description="Sistem durumu")
    version: str = Field(..., description="API versiyonu")
    services: dict = Field(..., description="Servis durumları")
