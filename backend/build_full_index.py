"""
Tam Dataset Vektör Index Oluşturucu
====================================

Tüm 112K görüntü için embedding hesaplar ve kaydeder.
Bu bir kerelik çalıştırılır, sonra her başlangıçta sadece yüklenir.

Kullanım:
    cd backend
    python build_full_index.py

Tahmini süre: ~45-60 dakika (CPU'da)
"""

import os
import sys
import time
import logging
from pathlib import Path

import numpy as np

# Backend modüllerini import et
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
    Tüm dataset için vektör index'i oluştur.
    
    Args:
        batch_size: Log için batch boyutu
        save_interval: Kaç görüntüde bir ara kayıt yapılacak
    """
    logger.info("=" * 60)
    logger.info("🚀 Tam Dataset Vektör Index Oluşturucu")
    logger.info("=" * 60)
    
    # Servisleri başlat
    logger.info("📂 Dataset yükleniyor...")
    dataset_service = DatasetService()
    dataset_service.load()
    
    logger.info("🧠 AI modeli yükleniyor...")
    ai_service = MultiLabelAIService()
    
    if not ai_service.model_loaded:
        logger.error("❌ AI modeli yüklenemedi!")
        return False
    
    # Tüm patoloji görüntülerini al
    all_pathology_images = dataset_service.get_pathology_images(limit=None)
    total_images = len(all_pathology_images)
    
    logger.info(f"📊 Toplam patoloji görüntüsü: {total_images}")
    logger.info(f"⏱️ Tahmini süre: {total_images * 0.025 / 60:.1f} dakika")
    logger.info("=" * 60)
    
    # Vektör depolama
    embeddings_list = []
    image_ids_list = []
    patient_ids_list = []
    
    # Index kayıt yolu
    index_path = Path(__file__).parent / "app" / "data" / "vector_index_full.npz"
    
    start_time = time.time()
    processed = 0
    skipped = 0
    
    for i, image_id in enumerate(all_pathology_images):
        try:
            # Görüntü yolunu al
            image_path = dataset_service.get_image_path(image_id)
            
            if image_path is None or not image_path.exists():
                skipped += 1
                continue
            
            # Embedding çıkar
            embedding = ai_service.get_embedding_for_image(str(image_path))
            
            if embedding is not None:
                embeddings_list.append(embedding)
                image_ids_list.append(image_id)
                
                # Hasta ID'sini al
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
                    f"İşlenen: {processed}, Atlanan: {skipped}, "
                    f"Hız: {rate:.1f}/s, Kalan: {eta:.1f} dk"
                )
            
            # Ara kayıt
            if processed > 0 and processed % save_interval == 0:
                _save_index(index_path, embeddings_list, image_ids_list, patient_ids_list)
                logger.info(f"💾 Ara kayıt yapıldı: {processed} vektör")
        
        except KeyboardInterrupt:
            logger.warning("⚠️ Kullanıcı tarafından durduruldu!")
            break
        except Exception as e:
            logger.warning(f"Hata (image_id={image_id}): {e}")
            skipped += 1
            continue
    
    # Final kayıt
    if len(embeddings_list) > 0:
        _save_index(index_path, embeddings_list, image_ids_list, patient_ids_list)
    
    # Sonuç
    elapsed = time.time() - start_time
    logger.info("=" * 60)
    logger.info("✅ Index oluşturma tamamlandı!")
    logger.info(f"   Toplam görüntü: {total_images}")
    logger.info(f"   İşlenen: {processed}")
    logger.info(f"   Atlanan: {skipped}")
    logger.info(f"   Süre: {elapsed/60:.1f} dakika")
    logger.info(f"   Kayıt: {index_path}")
    logger.info("=" * 60)
    
    # Eski index'i yeni ile değiştir
    old_index = Path(__file__).parent / "app" / "data" / "vector_index.npz"
    if old_index.exists():
        old_index.unlink()
    index_path.rename(old_index)
    logger.info(f"🔄 Index aktifleştirildi: {old_index}")
    
    return True


def _save_index(path: Path, embeddings: list, image_ids: list, patient_ids: list):
    """Index'i diske kaydet."""
    path.parent.mkdir(parents=True, exist_ok=True)
    
    embeddings_array = np.array(embeddings, dtype=np.float32)
    
    # Normalize et
    norms = np.linalg.norm(embeddings_array, axis=1, keepdims=True)
    embeddings_array = embeddings_array / (norms + 1e-8)
    
    np.savez(
        path,
        embeddings=embeddings_array,
        image_ids=np.array(image_ids),
        patient_ids=np.array(patient_ids)
    )


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🏥 Tıbbi X-Ray Vektör Index Oluşturucu")
    print("=" * 60)
    print("\nBu işlem tüm patoloji görüntüleri için embedding hesaplar.")
    print("Tahmini süre: 45-60 dakika (CPU)")
    print("\nDevam etmek için Enter'a basın, iptal için Ctrl+C...")
    
    try:
        input()
    except KeyboardInterrupt:
        print("\nİptal edildi.")
        sys.exit(0)
    
    success = build_full_index()
    sys.exit(0 if success else 1)
