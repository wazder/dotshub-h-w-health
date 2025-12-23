"""
Medical X-Ray Analysis Pipeline - FastAPI Main Module
======================================================

This module provides a REST API that accepts DICOM images,
analyzes them, and finds similar historical cases.

Usage:
    uvicorn app.main:app --reload

API Endpoints:
    POST /api/analyze - DICOM file analysis
    GET /api/health - System health check
    GET /api/patients/{id} - Patient information query
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Optional
from collections import defaultdict
import time

from fastapi import FastAPI, File, UploadFile, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from dotenv import load_dotenv

import torch  # For error handling

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

# Real services - Multi-label model (14 diseases)
from .services.ai_service_multilabel import ai_service
from .services.dataset_service import dataset_service
from .services.vector_search_service import vector_search_service as search_service

# Data service now uses dataset_service
from .services.data_service import data_service

# Load .env file
load_dotenv()

# Create logs directory
LOGS_DIR = os.path.join(os.path.dirname(__file__), '..', 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

# Logging configuration with file handler
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
console_handler.setLevel(logging.INFO)

# File handler with rotation (max 10MB, keep 5 backups)
file_handler = RotatingFileHandler(
    os.path.join(LOGS_DIR, 'api.log'),
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5,
    encoding='utf-8'
)
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.INFO)

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    handlers=[console_handler, file_handler]
)
logger = logging.getLogger(__name__)

# Allowed origins for CORS
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173").split(",")

# FastAPI application
app = FastAPI(
    title="Medical X-Ray Analysis API",
    description="""
    ## 🏥 Medical Image Analysis Pipeline
    
    This API analyzes medical images (X-Ray, CT, MRI) and finds similar historical cases.
    
    ### Supported Formats:
    - **DICOM** (.dcm)
    - **NIFTI** (.nii, .nii.gz)
    - **PNG** (.png)
    - **JPEG/JPG** (.jpeg, .jpg)
    
    ### Pipeline Steps:
    1. **Image Upload** - Image is sent to PACS server
    2. **Format Conversion** - Image is converted to PNG (1024x1024)
    3. **CNN Analysis** - CNN model classifies the image (no LLM)
    4. **Vector Search** - Similar cases are searched in vector database
    5. **Result** - Analysis and similar case information is returned
    """,
    version="1.0.0-prototype",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
    expose_headers=["Content-Length", "X-Request-ID"],
    max_age=600
)


# ==================== Rate Limiting ====================

# Simple in-memory rate limiter
class RateLimiter:
    def __init__(self, requests_per_minute: int = 30):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
    
    def is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        minute_ago = now - 60
        
        # Clean old requests
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip] 
            if req_time > minute_ago
        ]
        
        # Check limit
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            return False
        
        self.requests[client_ip].append(now)
        return True
    
    def get_remaining(self, client_ip: str) -> int:
        now = time.time()
        minute_ago = now - 60
        current_requests = len([
            req_time for req_time in self.requests[client_ip] 
            if req_time > minute_ago
        ])
        return max(0, self.requests_per_minute - current_requests)

rate_limiter = RateLimiter(requests_per_minute=30)  # 30 requests per minute


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Skip rate limiting for health check and docs
    if request.url.path in ["/api/health", "/docs", "/redoc", "/openapi.json", "/"]:
        return await call_next(request)
    
    client_ip = request.client.host if request.client else "unknown"
    
    if not rate_limiter.is_allowed(client_ip):
        logger.warning(f"Rate limit exceeded for {client_ip}")
        return JSONResponse(
            status_code=429,
            content={
                "success": False,
                "error": "Too many requests",
                "detail": "Please wait a minute and try again.",
                "retry_after_seconds": 60
            }
        )
    
    # Add rate limit headers
    response = await call_next(request)
    response.headers["X-RateLimit-Remaining"] = str(rate_limiter.get_remaining(client_ip))
    response.headers["X-RateLimit-Limit"] = str(rate_limiter.requests_per_minute)
    return response


# ==================== Main Analysis Endpoint ====================

@app.post(
    "/api/analyze",
    response_model=AnalysisResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid file"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    summary="Medical Image Analysis",
    description="Uploads a medical image (DICOM, NIFTI, PNG, JPEG), analyzes it, and finds similar cases."
)
async def analyze_image(
    file: UploadFile = File(..., description="Medical image file (.dcm, .nii, .nii.gz, .png, .jpg, .jpeg)")
):
    """
    Main endpoint that analyzes medical images.
    """
    logger.info(f"Analysis request received - File: {file.filename}")
    
    try:
        # 1. Read file
        file_content = await file.read()
        
        if len(file_content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file uploaded"
            )
        
        logger.info(f"File read: {len(file_content)} bytes")
        
        # 2. Upload to PACS
        logger.info("Step 1/4: Uploading to PACS...")
        pacs_result = pacs_service.upload_dicom(file_content)
        pacs_status = PACSUploadResult(**pacs_result)
        
        # 3. AI Analysis
        logger.info("Step 2/4: Running AI analysis...")
        ai_result = ai_service.analyze_image(file_content, file.filename)
        ai_analysis = AIAnalysisResult(
            probability=ai_result["probability"],
            label=ai_result["label"],
            label_tr=ai_result.get("label_tr", ""),
            confidence=ai_result["confidence"],
            is_pathology=ai_result.get("is_pathology", False),
            detected_diseases=ai_result.get("detected_diseases", []),
            disease_count=ai_result.get("disease_count", 0),
            embedding=ai_result["embedding"]
        )
        
        # 4. Vector Search - Multiple similar cases
        logger.info("Step 3/4: Searching for similar cases...")
        similar_results = search_service.search_similar(
            query_vector=ai_result["embedding"],
            top_k=5
        )
        
        # 5. Get Similar Cases Information
        similar_cases: list = []
        if similar_results:
            for similar_patient_id, similar_image_id, similarity_score in similar_results:
                logger.info(f"Getting patient info - ID: {similar_patient_id}")
                
                patient_info = dataset_service.get_patient_info(similar_patient_id)
                
                if patient_info:
                    patient_history = PatientHistory(
                        patient_id=patient_info.get("patient_id", similar_patient_id),
                        age=patient_info.get("age"),
                        gender=patient_info.get("gender"),
                        diagnosis_date=patient_info.get("diagnosis_date"),
                        diagnosis=patient_info.get("diagnosis"),
                        treatment=patient_info.get("treatment"),
                        outcome=patient_info.get("outcome"),
                        history=patient_info.get("history", ""),
                        notes=f"Image: {similar_image_id}"
                    )
                    
                    similar_case = SimilarCase(
                        patient_id=similar_patient_id,
                        similarity_score=similarity_score,
                        image_id=similar_image_id,
                        image_url=f"/api/images/{similar_image_id}",
                        history=patient_history
                    )
                    similar_cases.append(similar_case)
        
        first_similar_case = similar_cases[0] if similar_cases else None
        
        # 6. Generate Summary
        summary = _generate_summary(ai_analysis, first_similar_case, len(similar_cases))
        
        # 7. Create Response
        response = AnalysisResponse(
            success=True,
            timestamp=datetime.now(),
            pacs_status=pacs_status,
            ai_analysis=ai_analysis,
            similar_cases=similar_cases,
            similar_case=first_similar_case,
            summary=summary
        )
        
        logger.info("Analysis completed successfully!")
        return response
        
    except HTTPException:
        raise
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Required file not found. Please contact system administrator."
        )
    except torch.cuda.OutOfMemoryError:
        logger.error("GPU memory exhausted")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GPU memory insufficient. Please try again later."
        )
    except ValueError as e:
        logger.error(f"Value error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid data: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Analysis error: {e}", exc_info=True)
        
        # More user-friendly error messages
        error_msg = str(e).lower()
        if "model" in error_msg or "load" in error_msg:
            detail = "AI model could not be loaded. Please contact system administrator."
        elif "image" in error_msg or "format" in error_msg:
            detail = "Image format not recognized. Please upload a DICOM, PNG, or JPEG file."
        elif "memory" in error_msg:
            detail = "Insufficient memory. Please try a smaller image."
        elif "timeout" in error_msg:
            detail = "Operation timed out. Please try again."
        else:
            detail = f"An error occurred during analysis: {str(e)}"
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


def _generate_summary(ai_analysis: AIAnalysisResult, similar_case: Optional[SimilarCase], total_matches: int = 0) -> str:
    """Generates analysis summary."""
    if ai_analysis.label == "No Finding":
        detection = "Normal - No findings"
    elif ai_analysis.label in ["Mass|Nodule", "Pathology"]:
        detection = "Pathological findings detected"
    else:
        detection = ai_analysis.label
    
    parts = [
        f"Analysis Completed",
        f"Result: {detection} (Confidence: {ai_analysis.confidence})"
    ]
    
    if similar_case and total_matches > 0:
        parts.append(
            f"Closest case: Patient {similar_case.patient_id} "
            f"({similar_case.similarity_score*100:.0f}% similarity)"
        )
        if total_matches > 1:
            parts.append(f"Total {total_matches} similar cases found")
    else:
        parts.append("No similar cases found")
    
    return " | ".join(parts)


# ==================== Image Endpoints ====================

@app.get(
    "/api/images/{image_id}",
    summary="Get X-Ray Image",
    description="Returns the X-ray image for the specified image ID."
)
async def get_image(image_id: str):
    """Serves image file from NIH Dataset."""
    image_path = dataset_service.get_image_path(image_id)
    
    if image_path is None or not image_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image not found: {image_id}"
        )
    
    return FileResponse(
        path=str(image_path),
        media_type="image/png",
        filename=image_id
    )


# ==================== Helper Endpoints ====================

@app.get(
    "/api/health",
    response_model=HealthCheckResponse,
    summary="System Health Check",
    description="Checks the status of all services."
)
async def health_check():
    """System health check endpoint."""
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
    summary="Patient Information Query",
    description="Gets the historical information of a specific patient."
)
async def get_patient(patient_id: str):
    """Patient information endpoint."""
    
    patient = dataset_service.get_patient_info(patient_id)
    
    if patient:
        images = patient.get('images', [])
        scans = []
        
        for idx, image_id in enumerate(images[:6]):
            image_info = dataset_service.get_image_info(image_id)
            if image_info:
                # NIH dataset doesn't have actual scan dates
                scans.append({
                    'id': image_id,
                    'date': 'Date Unknown',  # Real date not available in NIH dataset
                    'type': image_info.get('view_position', 'PA'),
                    'status': 'Abnormal' if image_info.get('has_pathology') else 'Normal',
                    'imageUrl': f"/api/images/{image_id}",
                    'findings': image_info.get('finding_labels', '')
                })
        
        return {
            "success": True,
            "patient": {
                **patient,
                "scans": scans,
                "diagnosisHistory": [
                    {
                        "date": "Date Unknown",  # Real date not available
                        "diagnosis": patient.get('diagnosis', 'No Information'),
                        "physician": "NIH Dataset - Retrospective Data"
                    }
                ]
            }
        }
    
    patient = data_service.get_patient_history(patient_id)
    
    if patient:
        return {
            "success": True,
            "patient": patient
        }
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Patient not found: {patient_id}"
    )


@app.get(
    "/api/patients",
    summary="List All Patients",
    description="Lists all patient IDs in the system."
)
async def list_patients():
    """Lists all patients."""
    patient_ids = data_service.list_all_patients()
    return {
        "success": True,
        "count": len(patient_ids),
        "patient_ids": patient_ids
    }


@app.get("/", include_in_schema=False)
async def root():
    """Home page - redirects to API documentation."""
    return {
        "message": "🏥 Medical X-Ray Analysis API",
        "version": "1.0.0-prototype",
        "docs": "/docs",
        "health": "/api/health"
    }


# ==================== Startup/Shutdown Events ====================

@app.on_event("startup")
async def startup_event():
    """Runs on application startup."""
    logger.info("=" * 50)
    logger.info("🏥 Medical X-Ray Analysis API Starting...")
    logger.info("🔬 REAL MODE - PyTorch AI Model Active")
    logger.info("=" * 50)
    
    # Start dataset service
    logger.info("📂 Loading NIH Chest X-ray Dataset...")
    dataset_service.load()
    dataset_ok, dataset_msg = dataset_service.check_health()
    logger.info(f"Dataset Service: {dataset_msg}")
    
    # Connect data service with dataset_service
    data_service.set_dataset_service(dataset_service)
    
    # Start AI service
    logger.info("🧠 Loading AI Model (ResNet50)...")
    ai_ok, ai_msg = ai_service.check_health()
    logger.info(f"AI Service: {ai_msg}")
    
    # Initialize vector index
    logger.info("🔍 Creating vector index...")
    search_service.initialize(dataset_service, ai_service, sample_size=200)
    search_ok, search_msg = search_service.check_health()
    logger.info(f"Vector Search: {search_msg}")
    
    # Other services
    pacs_ok, pacs_msg = pacs_service.check_connection()
    logger.info(f"PACS Service: {pacs_msg}")
    
    data_ok, data_msg = data_service.check_health()
    logger.info(f"Data Service: {data_msg}")
    
    logger.info("=" * 50)
    logger.info("✅ API ready! Docs: http://localhost:8000/docs")
    logger.info("💡 Frontend: http://localhost:5173")
    logger.info("=" * 50)


@app.on_event("shutdown")
async def shutdown_event():
    """Runs on application shutdown."""
    logger.info("🛑 API shutting down...")
