"""
Dataset Service - NIH Chest X-ray Dataset Management
Reads patient and image data from CSV, builds vector database.
"""

import os
import csv
import json
import random
import logging
from typing import Optional, Dict, List, Tuple
from pathlib import Path
from collections import defaultdict

import numpy as np

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class DatasetService:
    """
    NIH Chest X-ray dataset management service.
    Reads patient and image information from CSV file.
    """
    
    def __init__(self):
        self.data_path = self._find_data_path()
        self.csv_path = self.data_path / "archive" / "Data_Entry_2017.csv" if self.data_path else None
        self.images_path = self.data_path / "archive" / "images-224" / "images-224" if self.data_path else None
        
        # Caches
        self._patient_cache: Dict[str, Dict] = {}
        self._image_cache: Dict[str, Dict] = {}
        self._pathology_images: List[str] = []  # Images with any disease
        self._loaded = False
        
        logger.info("Dataset Service initialized - call load() to load data")
    
    def load(self) -> bool:
        """Load dataset. Called at startup."""
        if self._loaded:
            return True
        
        if self._load_dataset():
            self._loaded = True
            logger.info(f"Dataset loaded: {len(self._patient_cache)} patients, {len(self._image_cache)} images")
            return True
        return False
    
    def _find_data_path(self) -> Optional[Path]:
        """Find data directory."""
        possible_paths = [
            Path(__file__).parent.parent.parent.parent / "data",
            Path("/Users/wazder/Documents/GitHub/dotshub-h-w-health/data"),
            Path("/workspace/dotshub-h-w-health/data"),
            Path("data"),
            Path("../data"),
        ]
        
        for path in possible_paths:
            if path.exists() and (path / "archive" / "Data_Entry_2017.csv").exists():
                logger.info(f"Data directory found: {path}")
                return path
        
        logger.warning("Data directory not found!")
        return None
    
    def _load_dataset(self) -> bool:
        """Load dataset from CSV file."""
        if self.csv_path is None or not self.csv_path.exists():
            logger.error(f"CSV file not found: {self.csv_path}")
            return False
        
        try:
            patient_images = defaultdict(list)
            
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    image_id = row.get('Image Index', '').strip()
                    patient_id = row.get('Patient ID', '').strip()
                    finding_labels = row.get('Finding Labels', '').strip()
                    age_str = row.get('Patient Age', '').strip()
                    gender = row.get('Patient Gender', '').strip()
                    view_pos = row.get('View Position', '').strip()
                    
                    # Parse age (e.g., "058Y" -> 58)
                    age = None
                    if age_str and age_str.endswith('Y'):
                        try:
                            age = int(age_str[:-1])
                        except ValueError:
                            pass
                    
                    # Consider all 14 diseases as pathology
                    all_diseases = ['Atelectasis', 'Cardiomegaly', 'Effusion', 'Infiltration', 'Mass',
                                    'Nodule', 'Pneumonia', 'Pneumothorax', 'Consolidation', 'Edema',
                                    'Emphysema', 'Fibrosis', 'Pleural_Thickening', 'Hernia']
                    has_any_disease = any(disease in finding_labels for disease in all_diseases)
                    
                    # Image info - gender in English
                    image_info = {
                        'image_id': image_id,
                        'patient_id': patient_id,
                        'finding_labels': finding_labels,
                        'age': age,
                        'gender': 'Male' if gender == 'M' else 'Female' if gender == 'F' else gender,
                        'view_position': view_pos,
                        'has_pathology': has_any_disease
                    }
                    
                    self._image_cache[image_id] = image_info
                    patient_images[patient_id].append(image_info)
                    
                    # Keep pathology images separate
                    if image_info['has_pathology']:
                        self._pathology_images.append(image_id)
            
            # Build patient info
            for patient_id, images in patient_images.items():
                # Get info from latest image
                latest = images[-1]
                
                # Collect all findings
                all_findings = set()
                for img in images:
                    for finding in img['finding_labels'].split('|'):
                        finding = finding.strip()
                        if finding:
                            all_findings.add(finding)
                
                # Determine primary diagnosis
                primary_diagnosis = self._determine_primary_diagnosis(all_findings)
                
                self._patient_cache[patient_id] = {
                    'patient_id': patient_id,
                    'age': latest['age'],
                    'gender': latest['gender'],
                    'diagnosis': primary_diagnosis,
                    'all_findings': list(all_findings),
                    'image_count': len(images),
                    'images': [img['image_id'] for img in images],
                    'has_pathology': any(img['has_pathology'] for img in images)
                }
            
            logger.info(f"Dataset loaded: {len(self._patient_cache)} patients, {len(self._image_cache)} images, {len(self._pathology_images)} pathological")
            return True
            
        except Exception as e:
            logger.error(f"Dataset loading error: {e}", exc_info=True)
            return False
    
    def _determine_primary_diagnosis(self, findings: set) -> str:
        """Determine primary diagnosis from findings."""
        # Priority order
        priority = ['Mass', 'Nodule', 'Pneumonia', 'Cardiomegaly', 'Effusion', 
                   'Infiltration', 'Atelectasis', 'Pneumothorax', 'Consolidation',
                   'Edema', 'Emphysema', 'Fibrosis', 'Pleural_Thickening', 'Hernia']
        
        for condition in priority:
            if condition in findings:
                return condition
        
        if 'No Finding' in findings or len(findings) == 0:
            return 'No Finding'
        
        return list(findings)[0]
    
    def get_patient_info(self, patient_id: str) -> Optional[Dict]:
        """Get patient information."""
        return self._patient_cache.get(patient_id)
    
    def get_image_info(self, image_id: str) -> Optional[Dict]:
        """Get image information."""
        return self._image_cache.get(image_id)
    
    def get_image_path(self, image_id: str) -> Optional[Path]:
        """Get image file path."""
        if self.images_path is None:
            return None
        
        image_path = self.images_path / image_id
        
        if image_path.exists():
            return image_path
        
        return None
    
    def get_patient_by_image(self, image_id: str) -> Optional[Dict]:
        """Get patient information from image."""
        image_info = self.get_image_info(image_id)
        if image_info:
            return self.get_patient_info(image_info['patient_id'])
        return None
    
    def get_pathology_images(self, limit: Optional[int] = None) -> List[str]:
        """Get pathology-containing images."""
        if limit:
            return self._pathology_images[:limit]
        return self._pathology_images
    
    def get_similar_patients(self, finding: str, exclude_patient_id: Optional[str] = None, limit: int = 5) -> List[Dict]:
        """Get patients with similar diagnosis."""
        similar = []
        
        for patient_id, patient in self._patient_cache.items():
            if patient_id == exclude_patient_id:
                continue
            
            if finding in patient.get('all_findings', []):
                similar.append(patient)
                
                if len(similar) >= limit:
                    break
        
        return similar
    
    def get_random_pathology_patient(self) -> Optional[Dict]:
        """Get a random pathology patient."""
        pathology_patients = [p for p in self._patient_cache.values() if p.get('has_pathology')]
        
        if pathology_patients:
            return random.choice(pathology_patients)
        
        return None
    
    def search_patients(self, query: str) -> List[Dict]:
        """Search patients (by ID or diagnosis)."""
        results = []
        query_lower = query.lower()
        
        for patient_id, patient in self._patient_cache.items():
            # ID match
            if query in patient_id:
                results.append(patient)
                continue
            
            # Diagnosis match
            diagnosis = patient.get('diagnosis', '').lower()
            if query_lower in diagnosis:
                results.append(patient)
        
        return results[:20]  # Max 20 results
    
    def list_patients(self, limit: int = 100) -> List[str]:
        """List patient IDs."""
        return list(self._patient_cache.keys())[:limit]
    
    def get_stats(self) -> Dict:
        """Get dataset statistics."""
        finding_counts = defaultdict(int)
        age_sum = 0
        age_count = 0
        gender_counts = {'Male': 0, 'Female': 0}
        
        for patient in self._patient_cache.values():
            diagnosis = patient.get('diagnosis', 'Unknown')
            finding_counts[diagnosis] += 1
            
            age = patient.get('age')
            if age:
                age_sum += age
                age_count += 1
            
            gender = patient.get('gender')
            if gender in gender_counts:
                gender_counts[gender] += 1
        
        return {
            'total_patients': len(self._patient_cache),
            'total_images': len(self._image_cache),
            'pathology_images': len(self._pathology_images),
            'finding_distribution': dict(finding_counts),
            'average_age': round(age_sum / age_count, 1) if age_count > 0 else 0,
            'gender_distribution': gender_counts
        }
    
    def check_health(self) -> Tuple[bool, str]:
        """Service health check."""
        if len(self._patient_cache) > 0:
            return True, f"Dataset service running - {len(self._patient_cache)} patients"
        return False, "Dataset not loaded"


# Singleton instance
dataset_service = DatasetService()
