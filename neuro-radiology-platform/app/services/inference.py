"""
Inference Pipeline Orchestrator.

Ties together preprocessing, routing, and model inference
into a unified pipeline for MRI analysis.
"""

from pathlib import Path
from typing import Any, Literal

import numpy as np

from app.config import settings
from app.models.alzheimer import AlzheimerClassifierModel, create_alzheimer_model
from app.models.tumor import TumorSegmentationModel, create_tumor_model
from app.preprocessing import PreprocessingPipeline
from app.router import PathologyRouter, PathologyType
from app.utils.io import load_nifti, load_dicom


class InferencePipeline:
    """
    Main inference pipeline orchestrator.
    
    Pipeline stages:
    1. Load MRI data (NIfTI or DICOM)
    2. Preprocess (skull stripping, registration, normalization)
    3. Route to appropriate specialist model
    4. Run inference
    5. Return structured results
    """
    
    def __init__(
        self,
        device: str | None = None,
        preload_models: bool = True,
    ) -> None:
        """
        Initialize the inference pipeline.
        
        Args:
            device: Device for model inference
            preload_models: Whether to load models at initialization
        """
        self.device = device or settings.model.device
        
        # Initialize components
        self.preprocessor = PreprocessingPipeline()
        self.router = PathologyRouter()
        
        # Models (lazy loaded or preloaded)
        self._tumor_model: TumorSegmentationModel | None = None
        self._alzheimer_model: AlzheimerClassifierModel | None = None
        
        if preload_models:
            self._load_models()
    
    @property
    def tumor_model(self) -> TumorSegmentationModel | None:
        """Get tumor segmentation model."""
        return self._tumor_model
    
    @property
    def alzheimer_model(self) -> AlzheimerClassifierModel | None:
        """Get Alzheimer classifier model."""
        return self._alzheimer_model
    
    def _load_models(self) -> None:
        """Load all specialist models."""
        try:
            self._tumor_model = create_tumor_model(
                weights_path=str(settings.model.tumor_weights_path)
                if settings.model.tumor_weights_path
                else None,
                device=self.device,
            )
        except Exception as e:
            print(f"Warning: Failed to load tumor model: {e}")
            self._tumor_model = None
        
        try:
            self._alzheimer_model = create_alzheimer_model(
                weights_path=str(settings.model.alzheimer_weights_path)
                if settings.model.alzheimer_weights_path
                else None,
                device=self.device,
            )
        except Exception as e:
            print(f"Warning: Failed to load Alzheimer model: {e}")
            self._alzheimer_model = None
    
    def _ensure_model_loaded(self, model_type: str) -> None:
        """Ensure the specified model is loaded."""
        if model_type == "tumor" and self._tumor_model is None:
            self._tumor_model = create_tumor_model(device=self.device)
        elif model_type == "alzheimer" and self._alzheimer_model is None:
            self._alzheimer_model = create_alzheimer_model(device=self.device)
    
    def run(
        self,
        file_path: Path | str,
        analysis_type: Literal["auto", "tumor", "alzheimer"] = "auto",
        metadata: dict[str, Any] | None = None,
        skip_preprocessing: bool = False,
    ) -> dict[str, Any]:
        """
        Run the complete inference pipeline.
        
        Args:
            file_path: Path to MRI file (NIfTI or DICOM directory)
            analysis_type: Type of analysis (auto, tumor, alzheimer)
            metadata: Optional clinical metadata for routing
            skip_preprocessing: Skip preprocessing (for pre-processed data)
            
        Returns:
            Dictionary containing analysis results
        """
        file_path = Path(file_path)
        result: dict[str, Any] = {
            "file_path": str(file_path),
            "status": "processing",
        }
        
        try:
            # Stage 1: Load data
            image, affine, header_info = self._load_data(file_path)
            result["header_info"] = header_info
            
            # Stage 2: Preprocessing
            if not skip_preprocessing:
                preprocessed, preprocess_info = self.preprocessor.run(image, affine)
                result["preprocessing_info"] = preprocess_info
            else:
                preprocessed = image
                result["preprocessing_info"] = {"skipped": True}
            
            # Stage 3: Routing
            if analysis_type == "auto":
                routing_decision = self.router.route(
                    preprocessed,
                    metadata=metadata,
                    user_hint="auto",
                )
                pathology_type = routing_decision.pathology_type
                result["routing"] = routing_decision.to_dict()
            else:
                pathology_type = PathologyType(analysis_type)
                result["routing"] = {
                    "pathology_type": analysis_type,
                    "confidence": 1.0,
                    "reasoning": ["User specified analysis type"],
                }
            
            # Stage 4: Model Inference
            model_input = self.preprocessor.prepare_for_model(preprocessed)
            
            if pathology_type == PathologyType.TUMOR:
                result["analysis_type"] = "tumor"
                result["tumor"] = self._run_tumor_inference(model_input)
            elif pathology_type == PathologyType.ALZHEIMER:
                result["analysis_type"] = "alzheimer"
                result["alzheimer"] = self._run_alzheimer_inference(model_input)
            else:
                result["analysis_type"] = "unknown"
                result["error"] = "Unable to determine pathology type"
            
            result["status"] = "success"
            
        except FileNotFoundError as e:
            result["status"] = "error"
            result["error"] = f"File not found: {e}"
        except ValueError as e:
            result["status"] = "error"
            result["error"] = f"Invalid data: {e}"
        except Exception as e:
            result["status"] = "error"
            result["error"] = f"Inference failed: {e}"
        
        return result
    
    def _load_data(
        self,
        file_path: Path,
    ) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
        """
        Load MRI data from file.
        
        Args:
            file_path: Path to MRI file
            
        Returns:
            Tuple of (image_data, affine, header_info)
        """
        suffix = "".join(file_path.suffixes).lower()
        
        if suffix.endswith(".dcm") or file_path.is_dir():
            return load_dicom(file_path)
        else:
            return load_nifti(file_path)
    
    def _run_tumor_inference(
        self,
        image: np.ndarray,
    ) -> dict[str, Any]:
        """
        Run tumor segmentation inference.
        
        Args:
            image: Preprocessed image array (B, C, H, W, D)
            
        Returns:
            Tumor analysis results
        """
        self._ensure_model_loaded("tumor")
        
        if self._tumor_model is None:
            return {
                "detected": False,
                "confidence": 0.0,
                "error": "Tumor model not available",
            }
        
        # Remove batch/channel dims for model predict method
        image_3d = image[0, 0] if image.ndim == 5 else image
        
        result = self._tumor_model.predict(image_3d)
        
        # Remove large arrays from response (segmentation maps)
        response = {
            "detected": result["detected"],
            "confidence": result["confidence"],
            "volume_mm3": result["volume_mm3"],
            "regions": result["regions"],
        }
        
        return response
    
    def _run_alzheimer_inference(
        self,
        image: np.ndarray,
    ) -> dict[str, Any]:
        """
        Run Alzheimer classification inference.
        
        Args:
            image: Preprocessed image array (B, C, H, W, D)
            
        Returns:
            Alzheimer analysis results
        """
        self._ensure_model_loaded("alzheimer")
        
        if self._alzheimer_model is None:
            return {
                "classification": "unknown",
                "confidence": 0.0,
                "probabilities": {"CN": 0.0, "MCI": 0.0, "AD": 0.0},
                "error": "Alzheimer model not available",
            }
        
        # Remove batch/channel dims for model predict method
        image_3d = image[0, 0] if image.ndim == 5 else image
        
        result = self._alzheimer_model.predict(image_3d)
        
        return result
    
    def run_batch(
        self,
        file_paths: list[Path | str],
        analysis_type: Literal["auto", "tumor", "alzheimer"] = "auto",
    ) -> list[dict[str, Any]]:
        """
        Run inference on a batch of files.
        
        Args:
            file_paths: List of paths to MRI files
            analysis_type: Type of analysis to perform
            
        Returns:
            List of analysis results
        """
        results = []
        
        for file_path in file_paths:
            result = self.run(file_path, analysis_type)
            results.append(result)
        
        return results
    
    def get_pipeline_info(self) -> dict[str, Any]:
        """Get information about the pipeline configuration."""
        info = {
            "device": self.device,
            "preprocessing": {
                "target_shape": settings.preprocessing.target_shape,
                "target_spacing": settings.preprocessing.target_spacing,
            },
            "models": {},
        }
        
        if self._tumor_model is not None:
            info["models"]["tumor"] = self._tumor_model.get_model_info()
        else:
            info["models"]["tumor"] = {"status": "not loaded"}
        
        if self._alzheimer_model is not None:
            info["models"]["alzheimer"] = self._alzheimer_model.get_model_info()
        else:
            info["models"]["alzheimer"] = {"status": "not loaded"}
        
        return info


class InferenceResult:
    """Container for structured inference results."""
    
    def __init__(self, raw_result: dict[str, Any]) -> None:
        """
        Initialize from raw pipeline result.
        
        Args:
            raw_result: Dictionary from InferencePipeline.run()
        """
        self._raw = raw_result
    
    @property
    def status(self) -> str:
        """Get status of inference."""
        return self._raw.get("status", "unknown")
    
    @property
    def success(self) -> bool:
        """Check if inference was successful."""
        return self.status == "success"
    
    @property
    def analysis_type(self) -> str:
        """Get type of analysis performed."""
        return self._raw.get("analysis_type", "unknown")
    
    @property
    def error(self) -> str | None:
        """Get error message if any."""
        return self._raw.get("error")
    
    def get_tumor_result(self) -> dict[str, Any] | None:
        """Get tumor analysis results."""
        return self._raw.get("tumor")
    
    def get_alzheimer_result(self) -> dict[str, Any] | None:
        """Get Alzheimer analysis results."""
        return self._raw.get("alzheimer")
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return self._raw.copy()
    
    def to_json_report(self) -> dict[str, Any]:
        """Generate a JSON report for frontend consumption."""
        report = {
            "status": self.status,
            "analysis_type": self.analysis_type,
        }
        
        if self.error:
            report["error"] = self.error
            return report
        
        if self.analysis_type == "tumor":
            tumor = self.get_tumor_result()
            if tumor:
                report["diagnosis"] = {
                    "detected": tumor.get("detected", False),
                    "condition": "Brain Tumor" if tumor.get("detected") else "No Tumor Detected",
                    "confidence": tumor.get("confidence", 0.0),
                    "details": {
                        "total_volume_mm3": tumor.get("volume_mm3"),
                        "regions": tumor.get("regions"),
                    },
                }
        
        elif self.analysis_type == "alzheimer":
            alzheimer = self.get_alzheimer_result()
            if alzheimer:
                classification = alzheimer.get("classification", "unknown")
                condition_map = {
                    "CN": "Cognitively Normal",
                    "MCI": "Mild Cognitive Impairment",
                    "AD": "Alzheimer's Disease",
                }
                
                report["diagnosis"] = {
                    "classification": classification,
                    "condition": condition_map.get(classification, "Unknown"),
                    "confidence": alzheimer.get("confidence", 0.0),
                    "probabilities": alzheimer.get("probabilities"),
                    "details": {
                        "atrophy_score": alzheimer.get("atrophy_score"),
                        "brain_volume_mm3": alzheimer.get("brain_volume_mm3"),
                    },
                }
        
        return report
