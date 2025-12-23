"""
Vector Search Service - Real Embedding-Based Similar Case Search
Finds most similar cases using cosine similarity.

This service:
1. Extracts embeddings from sample images at startup
2. Gets embedding for new image
3. Finds most similar cases using cosine similarity
"""

import os
import json
import logging
from typing import Optional, List, Tuple, Dict
from pathlib import Path
import random

import numpy as np

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class VectorSearchService:
    """
    Real vector-based similar case search service.
    """
    
    def __init__(self):
        self.vector_dimension = 2048  # ResNet50 avgpool output
        
        # Check for full index in main data folder first, then fallback to backend/app/data
        main_data_index = Path(__file__).parent.parent.parent.parent / "data" / "vector_index.npz"
        backend_index = Path(__file__).parent.parent / "data" / "vector_index.npz"
        
        if main_data_index.exists():
            self.index_path = main_data_index
            logger.info(f"Using full vector index from: {main_data_index}")
        else:
            self.index_path = backend_index
            logger.info(f"Using backend vector index from: {backend_index}")
        
        # Vector database
        self.embeddings: Optional[np.ndarray] = None
        self.image_ids: List[str] = []
        self.patient_ids: List[str] = []
        
        # Index loading/creation
        self._initialized = False
        
        logger.info("Vector Search Service initialized")
    
    def initialize(self, dataset_service, ai_service, sample_size: int = 100):
        """
        Initialize vector database.
        Load saved index if available, otherwise create new one.
        """
        if self._initialized:
            return True
        
        # First check for saved index
        if self._load_index():
            self._initialized = True
            return True
        
        # Create index if not found
        logger.info(f"Creating vector index - {sample_size} samples...")
        
        try:
            # Sample from pathology images
            pathology_images = dataset_service.get_pathology_images(limit=sample_size * 2)
            
            if len(pathology_images) == 0:
                logger.warning("No pathology images found!")
                self._create_mock_index(dataset_service)
                self._initialized = True
                return True
            
            # Random selection
            sample_images = random.sample(pathology_images, min(sample_size, len(pathology_images)))
            
            embeddings_list = []
            image_ids_list = []
            patient_ids_list = []
            
            for image_id in sample_images:
                image_path = dataset_service.get_image_path(image_id)
                
                if image_path is None:
                    continue
                
                # Extract embedding
                embedding = ai_service.get_embedding_for_image(str(image_path))
                
                if embedding is not None:
                    embeddings_list.append(embedding)
                    image_ids_list.append(image_id)
                    
                    # Get patient ID
                    image_info = dataset_service.get_image_info(image_id)
                    if image_info:
                        patient_ids_list.append(image_info['patient_id'])
                    else:
                        patient_ids_list.append("unknown")
                
                # Progress log
                if len(embeddings_list) % 10 == 0:
                    logger.info(f"Embedding progress: {len(embeddings_list)}/{sample_size}")
            
            if len(embeddings_list) > 0:
                self.embeddings = np.array(embeddings_list, dtype=np.float32)
                self.image_ids = image_ids_list
                self.patient_ids = patient_ids_list
                
                # Save index
                self._save_index()
                
                logger.info(f"Vector index created: {len(self.image_ids)} images")
                self._initialized = True
                return True
            else:
                logger.warning("No embeddings extracted, using mock index")
                self._create_mock_index(dataset_service)
                self._initialized = True
                return True
            
        except Exception as e:
            logger.error(f"Index creation error: {e}", exc_info=True)
            self._create_mock_index(dataset_service)
            self._initialized = True
            return False
    
    def _create_mock_index(self, dataset_service):
        """Create mock index when model cannot be loaded."""
        logger.info("Creating mock vector index...")
        
        pathology_images = dataset_service.get_pathology_images(limit=50)
        
        self.image_ids = pathology_images[:50] if pathology_images else []
        self.patient_ids = []
        
        for image_id in self.image_ids:
            image_info = dataset_service.get_image_info(image_id)
            if image_info:
                self.patient_ids.append(image_info['patient_id'])
            else:
                self.patient_ids.append("unknown")
        
        # Mock embeddings (random but consistent)
        np.random.seed(42)
        self.embeddings = np.random.randn(len(self.image_ids), self.vector_dimension).astype(np.float32)
        
        # Normalize
        norms = np.linalg.norm(self.embeddings, axis=1, keepdims=True)
        self.embeddings = self.embeddings / (norms + 1e-8)
        
        logger.info(f"Mock index created: {len(self.image_ids)} images")
    
    def _load_index(self) -> bool:
        """Load saved index."""
        if not self.index_path.exists():
            return False
        
        try:
            data = np.load(self.index_path, allow_pickle=True)
            self.embeddings = data['embeddings']
            self.image_ids = data['image_ids'].tolist()
            self.patient_ids = data['patient_ids'].tolist()
            
            logger.info(f"Vector index loaded: {len(self.image_ids)} images")
            return True
            
        except Exception as e:
            logger.warning(f"Index loading error: {e}")
            return False
    
    def _save_index(self):
        """Save index to disk."""
        try:
            self.index_path.parent.mkdir(parents=True, exist_ok=True)
            
            np.savez(
                self.index_path,
                embeddings=self.embeddings,
                image_ids=np.array(self.image_ids),
                patient_ids=np.array(self.patient_ids)
            )
            
            logger.info(f"Vector index saved: {self.index_path}")
            
        except Exception as e:
            logger.error(f"Index saving error: {e}")
    
    def search_similar(self, query_vector: List[float], top_k: int = 5) -> List[Tuple[str, str, float]]:
        """
        Find similar cases.
        
        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            
        Returns:
            List of (patient_id, image_id, similarity_score)
        """
        if self.embeddings is None or len(self.embeddings) == 0:
            logger.warning("Vector index is empty!")
            return []
        
        try:
            # Convert query vector to numpy
            query = np.array(query_vector, dtype=np.float32).flatten()
            
            # Normalize
            query = query / (np.linalg.norm(query) + 1e-8)
            
            # Calculate cosine similarity
            similarities = np.dot(self.embeddings, query)
            
            # Find top k indices
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            results = []
            seen_patients = set()
            
            for idx in top_indices:
                patient_id = self.patient_ids[idx]
                
                # Don't add same patient multiple times
                if patient_id in seen_patients:
                    continue
                
                seen_patients.add(patient_id)
                
                image_id = self.image_ids[idx]
                score = float(similarities[idx])
                
                # Normalize score to 0-1 range
                normalized_score = (score + 1) / 2  # Cosine sim [-1, 1] -> [0, 1]
                
                results.append((patient_id, image_id, normalized_score))
                
                if len(results) >= top_k:
                    break
            
            logger.info(f"Vector search completed - {len(results)} results found")
            
            return results
            
        except Exception as e:
            logger.error(f"Search error: {e}", exc_info=True)
            return []
    
    def add_to_index(self, embedding: List[float], image_id: str, patient_id: str):
        """Add new vector to index."""
        try:
            new_embedding = np.array(embedding, dtype=np.float32).reshape(1, -1)
            new_embedding = new_embedding / (np.linalg.norm(new_embedding) + 1e-8)
            
            if self.embeddings is None:
                self.embeddings = new_embedding
            else:
                self.embeddings = np.vstack([self.embeddings, new_embedding])
            
            self.image_ids.append(image_id)
            self.patient_ids.append(patient_id)
            
            # Save every 10 additions
            if len(self.image_ids) % 10 == 0:
                self._save_index()
            
            logger.info(f"Vector added: {image_id} -> total {len(self.image_ids)}")
            
        except Exception as e:
            logger.error(f"Vector addition error: {e}")
    
    def get_stats(self) -> Dict:
        """Get index statistics."""
        return {
            'total_vectors': len(self.image_ids) if self.image_ids else 0,
            'dimension': self.vector_dimension,
            'unique_patients': len(set(self.patient_ids)) if self.patient_ids else 0,
            'index_path': str(self.index_path),
            'initialized': self._initialized
        }
    
    def check_health(self) -> Tuple[bool, str]:
        """Service health check."""
        if self._initialized and self.embeddings is not None:
            return True, f"Vector DB running - {len(self.image_ids)} vectors"
        elif self._initialized:
            return True, "Vector DB running - Empty index"
        return False, "Vector DB not initialized"


# Singleton instance
vector_search_service = VectorSearchService()
