"""Model definitions for neuro-radiology pathology detection."""

from app.models.tumor import TumorSegmentationModel
from app.models.alzheimer import AlzheimerClassifierModel

__all__ = ["TumorSegmentationModel", "AlzheimerClassifierModel"]
