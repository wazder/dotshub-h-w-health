"""
FastAPI entry point for the Neuro-Radiology Platform.

Provides endpoints for MRI analysis including tumor segmentation
and Alzheimer's disease classification.
"""

import tempfile
import uuid
from pathlib import Path
from typing import Literal

import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.config import settings
from app.services.inference import InferencePipeline
from app.utils.io import validate_mri_file

app = FastAPI(
    title="Neuro-Radiology Platform",
    description="Modular brain pathology detection system for tumor segmentation and Alzheimer's classification",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize inference pipeline
pipeline = InferencePipeline()


class AnalysisRequest(BaseModel):
    """Request model for analysis parameters."""
    
    analysis_type: Literal["auto", "tumor", "alzheimer"] = "auto"
    patient_id: str | None = None
    include_segmentation: bool = True


class TumorResult(BaseModel):
    """Result model for tumor segmentation."""
    
    detected: bool
    confidence: float
    tumor_volume_mm3: float | None = None
    regions: dict[str, float] | None = None  # Region-wise volumes


class AlzheimerResult(BaseModel):
    """Result model for Alzheimer's classification."""
    
    classification: Literal["CN", "MCI", "AD"]  # Cognitively Normal, Mild Cognitive Impairment, Alzheimer's Disease
    confidence: float
    probabilities: dict[str, float]
    brain_volume_mm3: float | None = None
    atrophy_score: float | None = None


class AnalysisResponse(BaseModel):
    """Response model for analysis results."""
    
    request_id: str
    status: Literal["success", "error"]
    analysis_type: str
    tumor_result: TumorResult | None = None
    alzheimer_result: AlzheimerResult | None = None
    preprocessing_info: dict | None = None
    error_message: str | None = None


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0"}


@app.get("/models/status")
async def models_status() -> dict[str, dict]:
    """Get status of loaded models."""
    return {
        "tumor_model": {
            "loaded": pipeline.tumor_model is not None,
            "device": str(settings.model.device),
        },
        "alzheimer_model": {
            "loaded": pipeline.alzheimer_model is not None,
            "device": str(settings.model.device),
        },
    }


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_mri(
    file: UploadFile = File(..., description="MRI file in NIfTI format (.nii, .nii.gz)"),
    analysis_type: Literal["auto", "tumor", "alzheimer"] = Form(default="auto"),
    patient_id: str | None = Form(default=None),
) -> AnalysisResponse:
    """
    Analyze an MRI scan for brain pathologies.
    
    - **file**: MRI file in NIfTI format
    - **analysis_type**: Type of analysis to perform (auto, tumor, alzheimer)
    - **patient_id**: Optional patient identifier
    
    Returns a JSON report with diagnosis and confidence scores.
    """
    request_id = str(uuid.uuid4())
    
    # Create temp directory for processing
    temp_dir = Path(tempfile.mkdtemp(prefix="neuro_"))
    temp_file_path = temp_dir / file.filename
    
    try:
        # Save uploaded file
        content = await file.read()
        
        if len(content) > settings.api.max_file_size_mb * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail=f"File size exceeds maximum allowed size of {settings.api.max_file_size_mb}MB",
            )
        
        with open(temp_file_path, "wb") as f:
            f.write(content)
        
        # Validate file
        is_valid, validation_msg = validate_mri_file(temp_file_path)
        if not is_valid:
            raise HTTPException(status_code=400, detail=validation_msg)
        
        # Run inference pipeline
        result = pipeline.run(
            file_path=temp_file_path,
            analysis_type=analysis_type,
        )
        
        # Build response
        response = AnalysisResponse(
            request_id=request_id,
            status="success",
            analysis_type=result["analysis_type"],
            preprocessing_info=result.get("preprocessing_info"),
        )
        
        if result["analysis_type"] == "tumor":
            response.tumor_result = TumorResult(
                detected=result["tumor"]["detected"],
                confidence=result["tumor"]["confidence"],
                tumor_volume_mm3=result["tumor"].get("volume_mm3"),
                regions=result["tumor"].get("regions"),
            )
        elif result["analysis_type"] == "alzheimer":
            response.alzheimer_result = AlzheimerResult(
                classification=result["alzheimer"]["classification"],
                confidence=result["alzheimer"]["confidence"],
                probabilities=result["alzheimer"]["probabilities"],
                brain_volume_mm3=result["alzheimer"].get("brain_volume_mm3"),
                atrophy_score=result["alzheimer"].get("atrophy_score"),
            )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        return AnalysisResponse(
            request_id=request_id,
            status="error",
            analysis_type=analysis_type,
            error_message=str(e),
        )
    finally:
        # Cleanup temp files
        if temp_file_path.exists():
            temp_file_path.unlink()
        if temp_dir.exists():
            temp_dir.rmdir()


@app.post("/preprocess")
async def preprocess_only(
    file: UploadFile = File(...),
) -> dict:
    """
    Run preprocessing only (skull stripping + registration) without model inference.
    Useful for debugging and validation.
    """
    request_id = str(uuid.uuid4())
    temp_dir = Path(tempfile.mkdtemp(prefix="neuro_"))
    temp_file_path = temp_dir / file.filename
    
    try:
        content = await file.read()
        with open(temp_file_path, "wb") as f:
            f.write(content)
        
        from app.preprocessing import PreprocessingPipeline
        from app.utils.io import load_nifti
        
        data, affine, header_info = load_nifti(temp_file_path)
        preprocessor = PreprocessingPipeline()
        processed_data, preprocess_info = preprocessor.run(data, affine)
        
        return {
            "request_id": request_id,
            "status": "success",
            "original_shape": header_info["shape"],
            "processed_shape": processed_data.shape,
            "preprocessing_info": preprocess_info,
        }
        
    except Exception as e:
        return {
            "request_id": request_id,
            "status": "error",
            "error_message": str(e),
        }
    finally:
        if temp_file_path.exists():
            temp_file_path.unlink()
        if temp_dir.exists():
            temp_dir.rmdir()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
