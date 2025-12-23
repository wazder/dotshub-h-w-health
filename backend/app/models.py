"""
Pydantic models - API request/response schemas
Data models for Medical X-Ray Analysis Pipeline
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# ==================== AI Analysis Models ====================

class DetectedDisease(BaseModel):
    """Detected disease detail"""
    label: str = Field(..., description="Disease label (English)")
    label_tr: str = Field(..., description="Disease label (Turkish)")
    probability: float = Field(..., ge=0.0, le=1.0, description="Probability")
    description: str = Field("", description="Disease description")


class AIAnalysisResult(BaseModel):
    """AI analysis result from model - Multi-Label Model"""
    probability: float = Field(..., ge=0.0, le=1.0, description="Highest probability")
    label: str = Field(..., description="Primary detection (English)")
    label_tr: str = Field("", description="Primary detection (Turkish)")
    confidence: str = Field(..., description="Confidence level: Low, Medium, High")
    is_pathology: bool = Field(False, description="Was pathology detected")
    detected_diseases: List[DetectedDisease] = Field(default=[], description="Detected diseases")
    disease_count: int = Field(0, description="Number of detected diseases")
    embedding: List[float] = Field(..., description="Image vector embedding")


class DiagnosisDetail(BaseModel):
    """Detailed diagnosis information"""
    condition: str = Field(..., description="Detected condition")
    probability: float = Field(..., ge=0.0, le=1.0)
    severity: str = Field(..., description="Severity: Mild, Moderate, Severe")


# ==================== Patient Models ====================

class PatientHistory(BaseModel):
    """Patient history information"""
    patient_id: str = Field(..., description="Patient ID")
    age: Optional[int] = Field(None, description="Patient age")
    gender: Optional[str] = Field(None, description="Gender")
    diagnosis_date: Optional[str] = Field(None, description="Diagnosis date")
    diagnosis: Optional[str] = Field(None, description="Diagnosis")
    treatment: Optional[str] = Field(None, description="Applied treatment")
    outcome: Optional[str] = Field(None, description="Outcome")
    history: str = Field(..., description="Patient history summary")
    notes: Optional[str] = Field(None, description="Additional notes")


class SimilarCase(BaseModel):
    """Similar case information"""
    patient_id: str = Field(..., description="Similar patient ID")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Similarity score")
    image_id: Optional[str] = Field(None, description="Similar image ID")
    image_url: Optional[str] = Field(None, description="Image URL")
    history: PatientHistory = Field(..., description="Patient history")


# ==================== PACS Models ====================

class PACSUploadResult(BaseModel):
    """PACS upload result"""
    success: bool = Field(..., description="Was upload successful")
    orthanc_id: Optional[str] = Field(None, description="Orthanc instance ID")
    study_uid: Optional[str] = Field(None, description="DICOM Study UID")
    series_uid: Optional[str] = Field(None, description="DICOM Series UID")
    message: str = Field(..., description="Operation message")


# ==================== API Response Models ====================

class AnalysisResponse(BaseModel):
    """Main analysis API response"""
    success: bool = Field(..., description="Was operation successful")
    timestamp: datetime = Field(default_factory=datetime.now, description="Operation time")
    
    # PACS info
    pacs_status: PACSUploadResult = Field(..., description="PACS upload status")
    
    # AI analysis results
    ai_analysis: AIAnalysisResult = Field(..., description="AI analysis results")
    
    # Similar cases (multiple)
    similar_cases: List[SimilarCase] = Field(default=[], description="Found similar cases")
    
    # Backward compatibility (deprecated)
    similar_case: Optional[SimilarCase] = Field(None, description="[Deprecated] First similar case")
    
    # Summary
    summary: str = Field(..., description="Analysis summary")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "timestamp": "2025-01-01T12:00:00",
                "pacs_status": {
                    "success": True,
                    "orthanc_id": "abc123",
                    "study_uid": "1.2.3.4",
                    "series_uid": "1.2.3.4.1",
                    "message": "DICOM başarıyla yüklendi"
                },
                "ai_analysis": {
                    "probability": 0.89,
                    "label": "Mass",
                    "label_tr": "Kitle",
                    "confidence": "High",
                    "is_pathology": True,
                    "detected_diseases": [
                        {"label": "Mass", "label_tr": "Kitle", "probability": 0.89, "description": "Akciğerde kitle tespit edildi"}
                    ],
                    "disease_count": 1,
                    "embedding": [0.1, 0.2, 0.3]
                },
                "similar_cases": [],
                "summary": "Analiz tamamlandı"
            }
        }


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    services: dict = Field(..., description="Individual service statuses")
    timestamp: datetime = Field(default_factory=datetime.now)


class ErrorResponse(BaseModel):
    """Error response"""
    success: bool = Field(False)
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Error details")
