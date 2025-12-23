# 🩻 Chest X-Ray Pathology Detection

This project aims to analyze chest X-ray images and detect specific pathologies (Mass/Nodule) using Deep Learning techniques. The model has been trained on the NIH Chest X-ray dataset.

## 🚀 About the Project

In this work, a binary classification model has been developed to distinguish between healthy lung images ("No Finding") and images showing signs of disease ("Mass" or "Nodule").

**Transfer Learning** was used in this project, and the **ResNet50** architecture, pre-trained on ImageNet, was customized for X-ray images.

### 🎯 Objectives
* To establish the foundation for a Clinical Decision Support System (CDSS) that can assist radiologists.
* To perform GPU-accelerated (NVIDIA L40) deep learning training on large datasets.
* To analyze CNN (Convolutional Neural Networks) performance in medical image processing.

---

## 🛠️ Technologies and Architecture Used

* **Model:** ResNet50 (Pretrained)
* **Framework:** PyTorch
* **Hardware:** NVIDIA L40 (48GB VRAM) - RunPod Cloud
* **Dataset:** NIH Chest X-rays (National Institutes of Health)
* **Optimizer:** Adam Optimizer
* **Loss Function:** Binary Cross Entropy (BCELoss)

---

## 📊 Training Parameters

The following hyperparameters were used during model training:

| Parameter | Value | Description |
| :--- | :--- | :--- |
| **Image Size** | 224x224 | ResNet standard input size |
| **Batch Size** | 128 | L40 GPU memory optimization |
| **Number of Epochs** | 5 | Number of training rounds |
| **Learning Rate** | 0.0001 | Learning coefficient |
| **Data Balancing** | Active | Positive and Negative samples equalized |

---

## 💻 Installation and Usage

Follow the steps below to run this project on your local machine.

### 1. Install Requirements
```bash
pip install torch torchvision pandas scikit-learn pillow tqdm
```
