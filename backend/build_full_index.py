"""
Full Dataset Vector Index Builder
=================================

Computes embeddings for all 112K images and saves them.
This runs once, then just loads at each startup.

Usage:
    cd backend
    python build_full_index.py

Estimated time: ~45-60 minutes (on CPU)
"""

import os
import sys
import time
import logging
from pathlib import Path

import numpy as np

# Import backend modules
sys.path.insert(0, str(Path(__file__).parent))

from app.services.dataset_service import DatasetService
from app.services.ai_service_multilabel import MultiLabelAIService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def build_full_index(batch_size: int = 100, save_interval: int = 1000):
    """
    Build vector index for entire dataset.
    
    Args:
        batch_size: Batch size for logging
        save_interval: How often to save intermediate results
    """
    logger.info("=" * 60)
    logger.info("🚀 Full Dataset Vector Index Builder")
    logger.info("=" * 60)
    
    # Initialize services
    logger.info("📂 Loading dataset...")
    dataset_service = DatasetService()
    dataset_service.load()
    
    logger.info("🧠 Loading AI model...")
    ai_service = MultiLabelAIService()
    
    if not ai_service.model_loaded:
        logger.error("❌ AI model could not be loaded!")
        return False
    
    # Get all pathology images
    all_pathology_images = dataset_service.get_pathology_images(limit=None)
    total_images = len(all_pathology_images)
    
    logger.info(f"📊 Total pathology images: {total_images}")
    logger.info(f"⏱️ Estimated time: {total_images * 0.025 / 60:.1f} minutes")
    logger.info("=" * 60)
    
    # Vector storage
    embeddings_list = []
    image_ids_list = []
    patient_ids_list = []
    
    # Index save path
    index_path = Path(__file__).parent / "app" / "data" / "vector_index_full.npz"
    
    start_time = time.time()
    processed = 0
    skipped = 0
    
    for i, image_id in enumerate(all_pathology_images):
        try:
            # Get image path
            image_path = dataset_service.get_image_path(image_id)
            
            if image_path is None or not image_path.exists():
                skipped += 1
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
                
                processed += 1
            else:
                skipped += 1
            
            # Progress log
            if (i + 1) % batch_size == 0:
                elapsed = time.time() - start_time
                rate = processed / elapsed if elapsed > 0 else 0
                eta = (total_images - i - 1) / rate / 60 if rate > 0 else 0
                
                logger.info(
                    f"[{i+1}/{total_images}] "
                    f"Processed: {processed}, Skipped: {skipped}, "
                    f"Rate: {rate:.1f}/s, ETA: {eta:.1f} min"
                )
            
            # Intermediate save
            if processed > 0 and processed % save_interval == 0:
                _save_index(
                    index_path,
                    embeddings_list,
                    image_ids_list,
                    patient_ids_list,
                    is_partial=True
                )
                
        except Exception as e:
            logger.warning(f"Error processing {image_id}: {e}")
            skipped += 1
            continue
    
    # Final save
    if processed > 0:
        _save_index(
            index_path,
            embeddings_list,
            image_ids_list,
            patient_ids_list,
            is_partial=False
        )
        
        elapsed = time.time() - start_time
        logger.info("=" * 60)
        logger.info(f"✅ Index building completed!")
        logger.info(f"📊 Total processed: {processed}")
        logger.info(f"⏭️ Skipped: {skipped}")
        logger.info(f"⏱️ Total time: {elapsed/60:.1f} minutes")
        logger.info(f"💾 Index saved: {index_path}")
        logger.info("=" * 60)
        return True
    else:
        logger.error("❌ No images could be processed!")
        return False


def _save_index(index_path, embeddings_list, image_ids_list, patient_ids_list, is_partial=False):
    """Save index to disk."""
    try:
        index_path.parent.mkdir(parents=True, exist_ok=True)
        
        embeddings = np.array(embeddings_list, dtype=np.float32)
        
        np.savez(
            index_path,
            embeddings=embeddings,
            image_ids=np.array(image_ids_list),
            patient_ids=np.array(patient_ids_list)
        )
        
        status = "intermediate" if is_partial else "final"
        logger.info(f"💾 Index saved ({status}): {len(image_ids_list)} vectors")
        
    except Exception as e:
        logger.error(f"Index save error: {e}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Build full vector index')
    parser.add_argument('--batch-size', type=int, default=100, help='Logging batch size')
    parser.add_argument('--save-interval', type=int, default=1000, help='Intermediate save interval')
    
    args = parser.parse_args()
    
    success = build_full_index(
        batch_size=args.batch_size,
        save_interval=args.save_interval
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
