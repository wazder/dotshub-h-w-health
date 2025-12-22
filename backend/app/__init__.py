"""
Tıbbi X-Ray Analiz Pipeline - Backend API
==========================================

Bu modül, DICOM görüntülerini analiz eden ve benzer vakaları bulan
bir tıbbi yapay zeka pipeline'ı sağlar.

Modüller:
    - main: FastAPI uygulama giriş noktası
    - models: Pydantic veri modelleri
    - services: İş mantığı servisleri
        - pacs_service: Orthanc PACS entegrasyonu
        - ai_service: AI analiz motoru
        - search_service: Vektör benzerlik araması
        - data_service: Hasta verisi yönetimi
"""

__version__ = "1.0.0-prototype"
__author__ = "Medical AI Team"
