"""
Medical X-Ray Analysis Pipeline - Backend API
==============================================

This module provides a medical AI pipeline that analyzes
DICOM images and finds similar cases.

Modules:
    - main: FastAPI application entry point
    - models: Pydantic data models
    - services: Business logic services
        - pacs_service: Orthanc PACS integration
        - ai_service: AI analysis engine
        - search_service: Vector similarity search
        - data_service: Patient data management
"""

__version__ = "1.0.0-prototype"
__author__ = "Medical AI Team"
