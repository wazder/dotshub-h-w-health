# 🩻 Chest X-Ray Pathology Detection (Göğüs Röntgeni Hastalık Tespiti)

Bu proje, Derin Öğrenme (Deep Learning) teknikleri kullanılarak akciğer röntgen görüntülerinin analiz edilmesini ve belirli patolojilerin (Kitle/Nodül) tespit edilmesini amaçlar. Model, NIH Chest X-ray veri seti üzerinde eğitilmiştir.

## 🚀 Proje Hakkında

Bu çalışmada, sağlıklı akciğer görüntüleri ("No Finding") ile hastalık belirtisi taşıyan ("Mass" veya "Nodule") görüntüleri birbirinden ayıran ikili sınıflandırma (binary classification) modeli geliştirilmiştir. 

Proje kapsamında **Transfer Learning (Transfer Öğrenme)** yöntemi kullanılmış ve ImageNet üzerinde önceden eğitilmiş **ResNet50** mimarisi, röntgen görüntüleri için özelleştirilmiştir.

### 🎯 Amaç
* Radyologlara yardımcı olabilecek bir Karar Destek Sistemi (CDSS) temeli oluşturmak.
* Büyük veri setleri üzerinde GPU destekli (NVIDIA L40) derin öğrenme eğitimi gerçekleştirmek.
* Tıbbi görüntü işlemede CNN (Convolutional Neural Networks) performansını analiz etmek.

---

## 🛠️ Kullanılan Teknolojiler ve Mimari

* **Model:** ResNet50 (Pretrained)
* **Framework:** PyTorch
* **Donanım:** NVIDIA L40 (48GB VRAM) - RunPod Cloud
* **Veri Seti:** NIH Chest X-rays (National Institutes of Health)
* **Optimize Edici:** Adam Optimizer
* **Loss Fonksiyonu:** Binary Cross Entropy (BCELoss)

---

## 📊 Eğitim Parametreleri

Modelin eğitimi sırasında aşağıdaki hiperparametreler kullanılmıştır:

| Parametre | Değer | Açıklama |
| :--- | :--- | :--- |
| **Görüntü Boyutu** | 224x224 | ResNet standart giriş boyutu |
| **Batch Size** | 128 | L40 GPU bellek optimizasyonu |
| **Epoch Sayısı** | 5 | Eğitim turu sayısı |
| **Learning Rate** | 0.0001 | Öğrenme katsayısı |
| **Veri Dengeleme** | Aktif | Pozitif ve Negatif örnekler eşitlendi |

---

## 💻 Kurulum ve Kullanım

Bu projeyi yerel bilgisayarınızda çalıştırmak için aşağıdaki adımları izleyin.

### 1. Gereksinimleri Yükleyin
```bash
pip install torch torchvision pandas scikit-learn pillow tqdm