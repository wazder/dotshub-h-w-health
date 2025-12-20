"""
Intelligent Router for model selection.

Analyzes image characteristics and metadata to route to the
appropriate specialist model (Tumor vs Alzheimer).
"""

from enum import Enum
from typing import Any, Literal

import numpy as np

from app.preprocessing import compute_histogram_stats


class PathologyType(str, Enum):
    """Enumeration of pathology types for routing."""
    
    TUMOR = "tumor"
    ALZHEIMER = "alzheimer"
    UNKNOWN = "unknown"


class RoutingDecision:
    """Container for routing decision with confidence and reasoning."""
    
    def __init__(
        self,
        pathology_type: PathologyType,
        confidence: float,
        reasoning: list[str],
        features: dict[str, float] | None = None,
    ) -> None:
        self.pathology_type = pathology_type
        self.confidence = confidence
        self.reasoning = reasoning
        self.features = features or {}
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "pathology_type": self.pathology_type.value,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "features": self.features,
        }


class PathologyRouter:
    """
    Intelligent router that decides which specialist model to invoke.
    
    Uses a combination of:
    1. User-provided hints/metadata
    2. Image histogram analysis
    3. Volumetric features
    4. Intensity distribution patterns
    
    For MVP, implements heuristic-based routing.
    In production, this could be a trained classifier.
    """
    
    # Thresholds for heuristic routing (tunable)
    INTENSITY_VARIANCE_THRESHOLD = 0.15
    ASYMMETRY_THRESHOLD = 0.10
    HIGH_INTENSITY_RATIO_THRESHOLD = 0.05
    
    def __init__(self) -> None:
        """Initialize the pathology router."""
        self._routing_history: list[RoutingDecision] = []
    
    def route(
        self,
        image: np.ndarray,
        metadata: dict[str, Any] | None = None,
        user_hint: Literal["auto", "tumor", "alzheimer"] = "auto",
    ) -> RoutingDecision:
        """
        Determine which specialist model should process the image.
        
        Args:
            image: Preprocessed 3D MRI volume
            metadata: Optional metadata from image header
            user_hint: User-provided hint for routing
            
        Returns:
            RoutingDecision with pathology type and confidence
        """
        # If user explicitly specifies, use that
        if user_hint == "tumor":
            decision = RoutingDecision(
                pathology_type=PathologyType.TUMOR,
                confidence=1.0,
                reasoning=["User explicitly requested tumor analysis"],
            )
            self._routing_history.append(decision)
            return decision
        
        if user_hint == "alzheimer":
            decision = RoutingDecision(
                pathology_type=PathologyType.ALZHEIMER,
                confidence=1.0,
                reasoning=["User explicitly requested Alzheimer analysis"],
            )
            self._routing_history.append(decision)
            return decision
        
        # Auto-routing based on image analysis
        return self._analyze_and_route(image, metadata)
    
    def _analyze_and_route(
        self,
        image: np.ndarray,
        metadata: dict[str, Any] | None = None,
    ) -> RoutingDecision:
        """
        Analyze image features and make routing decision.
        
        Heuristics for Tumor (Mass Effect):
        - High local intensity variations
        - Asymmetric intensity distribution
        - Presence of abnormally bright regions (contrast enhancement)
        - Irregular texture patterns
        
        Heuristics for Alzheimer (Atrophy):
        - Reduced brain volume
        - Enlarged ventricles
        - Symmetric but diffuse changes
        - More uniform intensity distribution
        
        Args:
            image: 3D MRI volume
            metadata: Image metadata
            
        Returns:
            RoutingDecision with analysis results
        """
        features: dict[str, float] = {}
        reasoning: list[str] = []
        tumor_score = 0.0
        alzheimer_score = 0.0
        
        # Feature 1: Histogram statistics
        hist_stats = compute_histogram_stats(image)
        features.update(hist_stats)
        
        # Check for high intensity variance (suggests tumor)
        if hist_stats["std"] > self.INTENSITY_VARIANCE_THRESHOLD:
            tumor_score += 0.3
            reasoning.append(f"High intensity variance ({hist_stats['std']:.3f}) suggests mass lesion")
        else:
            alzheimer_score += 0.2
            reasoning.append(f"Normal intensity variance ({hist_stats['std']:.3f}) suggests diffuse process")
        
        # Feature 2: Asymmetry analysis
        asymmetry_score = self._compute_asymmetry(image)
        features["asymmetry"] = asymmetry_score
        
        if asymmetry_score > self.ASYMMETRY_THRESHOLD:
            tumor_score += 0.25
            reasoning.append(f"Asymmetric intensity pattern ({asymmetry_score:.3f}) suggests focal lesion")
        else:
            alzheimer_score += 0.2
            reasoning.append(f"Symmetric pattern ({asymmetry_score:.3f}) suggests diffuse atrophy")
        
        # Feature 3: High intensity ratio (potential contrast enhancement)
        high_intensity_ratio = self._compute_high_intensity_ratio(image)
        features["high_intensity_ratio"] = high_intensity_ratio
        
        if high_intensity_ratio > self.HIGH_INTENSITY_RATIO_THRESHOLD:
            tumor_score += 0.3
            reasoning.append(f"Abnormal bright regions ({high_intensity_ratio:.3f}) suggest enhancing tumor")
        else:
            alzheimer_score += 0.15
            reasoning.append(f"No abnormal enhancement ({high_intensity_ratio:.3f})")
        
        # Feature 4: Texture entropy
        texture_entropy = self._compute_local_entropy(image)
        features["texture_entropy"] = texture_entropy
        
        # Feature 5: Check metadata hints
        if metadata:
            # Check for clinical hints in metadata
            clinical_history = metadata.get("clinical_history", "").lower()
            if any(term in clinical_history for term in ["tumor", "mass", "lesion", "glioma"]):
                tumor_score += 0.4
                reasoning.append("Clinical history suggests tumor evaluation")
            elif any(term in clinical_history for term in ["dementia", "memory", "cognitive", "alzheimer"]):
                alzheimer_score += 0.4
                reasoning.append("Clinical history suggests cognitive evaluation")
            
            # Check patient age (older patients more likely Alzheimer)
            age = metadata.get("patient_age")
            if age is not None:
                if age > 65:
                    alzheimer_score += 0.1
                    reasoning.append(f"Patient age ({age}) increases Alzheimer likelihood")
                features["patient_age"] = float(age)
        
        # Make final decision
        total_score = tumor_score + alzheimer_score
        if total_score > 0:
            tumor_confidence = tumor_score / total_score
            alzheimer_confidence = alzheimer_score / total_score
        else:
            tumor_confidence = 0.5
            alzheimer_confidence = 0.5
        
        features["tumor_score"] = tumor_score
        features["alzheimer_score"] = alzheimer_score
        
        if tumor_confidence > alzheimer_confidence:
            decision = RoutingDecision(
                pathology_type=PathologyType.TUMOR,
                confidence=tumor_confidence,
                reasoning=reasoning,
                features=features,
            )
        elif alzheimer_confidence > tumor_confidence:
            decision = RoutingDecision(
                pathology_type=PathologyType.ALZHEIMER,
                confidence=alzheimer_confidence,
                reasoning=reasoning,
                features=features,
            )
        else:
            # Default to tumor if tie (more urgent)
            decision = RoutingDecision(
                pathology_type=PathologyType.TUMOR,
                confidence=0.5,
                reasoning=reasoning + ["Defaulting to tumor analysis due to equal scores"],
                features=features,
            )
        
        self._routing_history.append(decision)
        return decision
    
    def _compute_asymmetry(self, image: np.ndarray) -> float:
        """
        Compute left-right asymmetry in the image.
        
        Higher asymmetry suggests focal lesion (tumor).
        Lower asymmetry suggests diffuse process (Alzheimer).
        
        Args:
            image: 3D MRI volume
            
        Returns:
            Asymmetry score (0-1, higher = more asymmetric)
        """
        # Get mid-sagittal plane
        mid_x = image.shape[0] // 2
        
        left_half = image[:mid_x, :, :]
        right_half = np.flip(image[mid_x:, :, :], axis=0)
        
        # Ensure same shape
        min_x = min(left_half.shape[0], right_half.shape[0])
        left_half = left_half[:min_x]
        right_half = right_half[:min_x]
        
        # Compute normalized difference
        diff = np.abs(left_half - right_half)
        max_val = max(np.max(left_half), np.max(right_half), 1e-8)
        
        asymmetry = np.mean(diff) / max_val
        
        return float(asymmetry)
    
    def _compute_high_intensity_ratio(
        self,
        image: np.ndarray,
        percentile: float = 98,
    ) -> float:
        """
        Compute ratio of voxels with abnormally high intensity.
        
        High ratio suggests contrast enhancement (tumor marker).
        
        Args:
            image: 3D MRI volume
            percentile: Percentile threshold for "high" intensity
            
        Returns:
            Ratio of high-intensity voxels
        """
        nonzero = image[image > 0]
        if len(nonzero) == 0:
            return 0.0
        
        threshold = np.percentile(nonzero, percentile)
        high_intensity_count = np.sum(image > threshold)
        total_brain_voxels = np.sum(image > 0)
        
        return float(high_intensity_count / max(total_brain_voxels, 1))
    
    def _compute_local_entropy(
        self,
        image: np.ndarray,
        sample_size: int = 10000,
    ) -> float:
        """
        Compute local texture entropy using histogram.
        
        Higher entropy suggests more heterogeneous tissue (tumor).
        
        Args:
            image: 3D MRI volume
            sample_size: Number of voxels to sample
            
        Returns:
            Entropy value
        """
        nonzero = image[image > 0].flatten()
        
        if len(nonzero) < sample_size:
            sample = nonzero
        else:
            indices = np.random.choice(len(nonzero), sample_size, replace=False)
            sample = nonzero[indices]
        
        # Compute histogram
        hist, _ = np.histogram(sample, bins=256, density=True)
        hist = hist[hist > 0]  # Remove zero bins
        
        # Compute entropy
        entropy = -np.sum(hist * np.log2(hist + 1e-10))
        
        return float(entropy)
    
    def get_routing_history(self) -> list[dict[str, Any]]:
        """Get history of routing decisions."""
        return [d.to_dict() for d in self._routing_history]
    
    def clear_history(self) -> None:
        """Clear routing history."""
        self._routing_history.clear()
