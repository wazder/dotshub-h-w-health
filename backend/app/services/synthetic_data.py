"""
Synthetic Data Service - Demo Patient Data Enhancement
Provides rich clinical details for specific demo patients.
"""

import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

# Synthetic detailed patient data for demo purposes
SYNTHETIC_PATIENTS = {
    "00026785": {
        "patient_id": "00026785",
        "name": "John M. Anderson",
        "age": 39,
        "gender": "Male",
        "date_of_birth": "1985-03-14",
        "blood_type": "A+",
        "height": "178 cm",
        "weight": "82 kg",
        "bmi": 25.9,
        "occupation": "Construction Worker",
        "smoking_status": "Former smoker (quit 2019)",
        "alcohol_use": "Occasional",
        "allergies": ["Penicillin", "Dust mites"],
        "chronic_conditions": ["Mild asthma", "Seasonal allergies"],
        "primary_diagnosis": "Infiltration with Atelectasis",
        "diagnosis_date": "2023-08-15",
        "attending_physician": "Dr. Sarah Mitchell, MD",
        "department": "Pulmonology",
        "chief_complaint": "Persistent cough and mild chest discomfort for 3 weeks",
        "history_of_present_illness": """
Patient presented with a 3-week history of persistent productive cough with yellowish sputum. 
Reports mild chest discomfort, particularly on deep inspiration. Denies hemoptysis, fever, or night sweats. 
Patient works in construction and has occupational dust exposure. Former smoker with 10 pack-year history, 
quit 4 years ago. Initial outpatient treatment with amoxicillin showed minimal improvement.
        """.strip(),
        "physical_examination": {
            "general": "Alert, oriented, mild respiratory distress",
            "vitals": {
                "blood_pressure": "128/82 mmHg",
                "heart_rate": "88 bpm",
                "respiratory_rate": "20/min",
                "temperature": "37.2°C",
                "spo2": "94% on room air"
            },
            "chest": "Decreased breath sounds at right lower lobe, fine crackles noted",
            "cardiovascular": "Regular rhythm, no murmurs",
            "abdomen": "Soft, non-tender, no organomegaly"
        },
        "laboratory_results": {
            "wbc": "11.2 x10³/µL (elevated)",
            "hemoglobin": "14.1 g/dL",
            "platelets": "245 x10³/µL",
            "crp": "28 mg/L (elevated)",
            "procalcitonin": "0.15 ng/mL",
            "d_dimer": "0.42 µg/mL",
            "creatinine": "0.9 mg/dL",
            "glucose": "98 mg/dL"
        },
        "imaging_findings": {
            "chest_xray": "Right lower lobe infiltrate with partial atelectasis. No pleural effusion. Heart size normal.",
            "ct_chest": "Ground-glass opacities in RLL with subsegmental atelectasis. No masses or nodules identified."
        },
        # Treatment outcome data - patient already discharged
        "treatment_outcome": {
            "status": "Completed - Successful",
            "admission_date": "2023-08-15",
            "discharge_date": "2023-08-22",
            "treatment_duration": "7 days",
            "outcome_summary": "Full recovery achieved. Patient responded well to antibiotic therapy with complete resolution of symptoms."
        },
        "treatment_phases": [
            {
                "phase": "Acute Treatment",
                "duration": "Days 1-7",
                "start_date": "2023-08-15",
                "end_date": "2023-08-22",
                "methods": ["IV Levofloxacin 750mg daily", "Nebulized bronchodilators Q6H", "Chest physiotherapy BID"],
                "response": "Significant improvement by Day 4. Fever resolved, SpO2 improved to 97%."
            },
            {
                "phase": "Step-down Therapy",
                "duration": "Days 8-14",
                "start_date": "2023-08-22",
                "end_date": "2023-08-29",
                "methods": ["Oral Levofloxacin 750mg daily", "Albuterol inhaler PRN", "Incentive spirometry"],
                "response": "Continued improvement. Follow-up X-ray showed resolving infiltrate."
            },
            {
                "phase": "Recovery & Monitoring",
                "duration": "Days 15-28",
                "start_date": "2023-08-29",
                "end_date": "2023-09-12",
                "methods": ["Outpatient monitoring", "PFT evaluation", "Occupational health consultation"],
                "response": "Complete resolution confirmed. PFT results normal. Cleared to return to work with respiratory protection."
            }
        ],
        "final_outcome": {
            "result": "Success",
            "total_treatment_days": 28,
            "hospitalization_days": 7,
            "complications": "None",
            "readmission": "No",
            "follow_up_status": "Completed - No recurrence at 6-month follow-up",
            "work_status": "Returned to full duty with N95 mask requirement",
            "final_imaging": "2023-09-12 - Chest X-ray clear, no residual infiltrate or atelectasis"
        },
        "clinical_notes": """
39-year-old male construction worker with occupational dust exposure presenting with community-acquired 
pneumonia with associated atelectasis. Given work history, recommend pulmonary function testing after 
resolution of acute infection to evaluate for occupational lung disease. Patient counseled on importance 
of respiratory protection at work site.
        """.strip(),
        "diagnosis_history": [
            {
                "date": "2023-08-15",
                "diagnosis": "Infiltration with Atelectasis",
                "physician": "Dr. Sarah Mitchell, MD",
                "notes": "Initial presentation with productive cough, chest X-ray confirmed RLL infiltrate"
            },
            {
                "date": "2023-07-28",
                "diagnosis": "Upper Respiratory Infection",
                "physician": "Dr. James Wilson, MD",
                "notes": "Outpatient visit, prescribed amoxicillin, symptoms persisted"
            },
            {
                "date": "2022-11-10",
                "diagnosis": "Routine Physical - No Finding",
                "physician": "Dr. James Wilson, MD",
                "notes": "Annual checkup, chest X-ray clear, lung function normal"
            },
            {
                "date": "2021-05-22",
                "diagnosis": "Seasonal Allergies",
                "physician": "Dr. Emily Ross, MD",
                "notes": "Prescribed antihistamines, advised to avoid dust exposure at work"
            }
        ],
        "scan_dates": {
            "00026785_000.png": "2021-03-15",
            "00026785_001.png": "2021-06-22",
            "00026785_002.png": "2021-09-08",
            "00026785_003.png": "2022-01-14",
            "00026785_004.png": "2022-05-20",
            "00026785_005.png": "2022-08-11",
            "00026785_006.png": "2022-11-10",
            "00026785_007.png": "2023-02-17",
            "00026785_008.png": "2023-05-25",
            "00026785_009.png": "2023-07-03",
            "00026785_010.png": "2023-07-28",
            "00026785_011.png": "2023-08-15",
            "00026785_012.png": "2023-08-22",
            "00026785_013.png": "2023-09-12",
            "00026785_014.png": "2023-09-28",
            "00026785_015.png": "2023-10-15",
            "00026785_016.png": "2023-11-20",
            "00026785_017.png": "2023-12-05",
            "00026785_018.png": "2024-01-18",
            "00026785_019.png": "2024-02-22",
            "00026785_020.png": "2024-03-10"
        }
    },
    
    "00026917": {
        "patient_id": "00026917",
        "name": "Robert E. Williams",
        "age": 55,
        "gender": "Male",
        "date_of_birth": "1969-11-22",
        "blood_type": "O+",
        "height": "175 cm",
        "weight": "88 kg",
        "bmi": 28.7,
        "occupation": "Retired Teacher",
        "smoking_status": "Never smoker",
        "alcohol_use": "Moderate (2-3 drinks/week)",
        "allergies": ["Sulfa drugs"],
        "chronic_conditions": ["Type 2 Diabetes (controlled)", "Hypertension", "Hyperlipidemia"],
        "primary_diagnosis": "Atelectasis - Post-procedure",
        "diagnosis_date": "2024-01-10",
        "attending_physician": "Dr. Michael Chen, MD",
        "department": "Internal Medicine",
        "chief_complaint": "Routine chest X-ray follow-up after abdominal surgery",
        "history_of_present_illness": """
Patient is a 55-year-old male with well-controlled type 2 diabetes and hypertension who underwent 
laparoscopic cholecystectomy 2 weeks ago. Post-operative course was uncomplicated. Presented for 
routine follow-up with mild complaints of decreased exercise tolerance and occasional dry cough. 
Denies fever, chest pain, or significant dyspnea at rest.
        """.strip(),
        "physical_examination": {
            "general": "Well-appearing, comfortable at rest",
            "vitals": {
                "blood_pressure": "134/78 mmHg",
                "heart_rate": "76 bpm",
                "respiratory_rate": "16/min",
                "temperature": "36.8°C",
                "spo2": "96% on room air"
            },
            "chest": "Mildly decreased breath sounds at left base, no wheezing or crackles",
            "cardiovascular": "Regular rhythm, no murmurs, no peripheral edema",
            "abdomen": "Surgical incisions well-healed, soft, non-tender"
        },
        "laboratory_results": {
            "wbc": "7.8 x10³/µL",
            "hemoglobin": "13.2 g/dL",
            "platelets": "198 x10³/µL",
            "hba1c": "6.8%",
            "fasting_glucose": "118 mg/dL",
            "creatinine": "1.1 mg/dL",
            "lipid_panel": "Total cholesterol 195, LDL 110, HDL 48, TG 185"
        },
        "imaging_findings": {
            "chest_xray": "Subsegmental atelectasis at left lower lobe, likely post-operative. No infiltrates or effusion.",
            "comparison": "Compared to pre-operative imaging, new finding consistent with post-surgical changes."
        },
        "medications": [
            {"name": "Metformin", "dose": "1000mg", "frequency": "twice daily"},
            {"name": "Lisinopril", "dose": "20mg", "frequency": "once daily"},
            {"name": "Atorvastatin", "dose": "20mg", "frequency": "at bedtime"},
            {"name": "Aspirin", "dose": "81mg", "frequency": "once daily"}
        ],
        # Treatment outcome data - patient already discharged
        "treatment_outcome": {
            "status": "Completed - Successful",
            "admission_date": "2023-12-27",
            "discharge_date": "2023-12-29",
            "treatment_duration": "2 days",
            "outcome_summary": "Post-operative atelectasis resolved completely with conservative management. No complications."
        },
        "treatment_phases": [
            {
                "phase": "Surgical Treatment",
                "duration": "Day 1",
                "start_date": "2023-12-27",
                "end_date": "2023-12-27",
                "methods": ["Laparoscopic cholecystectomy", "General anesthesia", "IV fluids and antibiotics prophylaxis"],
                "response": "Surgery completed successfully without complications. Stable vitals post-op."
            },
            {
                "phase": "Post-operative Recovery",
                "duration": "Days 1-2",
                "start_date": "2023-12-27",
                "end_date": "2023-12-29",
                "methods": ["Early ambulation", "Incentive spirometry Q1H", "Pain management with Toradol", "Clear liquid diet advancing to regular"],
                "response": "Tolerated diet, passed flatus, ambulating independently by Day 2."
            },
            {
                "phase": "Pulmonary Recovery",
                "duration": "Days 3-14",
                "start_date": "2023-12-29",
                "end_date": "2024-01-10",
                "methods": ["Home incentive spirometry TID", "Deep breathing exercises", "Gradual return to activity"],
                "response": "Atelectasis resolved on follow-up imaging. Exercise tolerance returned to baseline."
            },
            {
                "phase": "Follow-up Care",
                "duration": "Week 3-4",
                "start_date": "2024-01-10",
                "end_date": "2024-01-24",
                "methods": ["Outpatient monitoring", "Surgical wound check", "Dietary counseling"],
                "response": "Complete recovery. Incisions healed well. Resumed normal diet and activities."
            }
        ],
        "final_outcome": {
            "result": "Success",
            "total_treatment_days": 28,
            "hospitalization_days": 2,
            "complications": "None - Mild post-operative atelectasis (expected, resolved)",
            "readmission": "No",
            "follow_up_status": "Completed - Full recovery confirmed",
            "work_status": "Retired - Resumed all daily activities without restriction",
            "final_imaging": "2024-01-10 - Chest X-ray clear, atelectasis resolved"
        },
        "clinical_notes": """
55-year-old male with metabolic syndrome who underwent uncomplicated laparoscopic cholecystectomy 
for acute cholecystitis. Post-operative course was smooth with expected transient atelectasis that 
resolved with conservative pulmonary toilet. Chronic conditions remained well-controlled throughout. 
Patient educated on post-cholecystectomy dietary modifications.
        """.strip(),
        "diagnosis_history": [
            {
                "date": "2024-01-10",
                "diagnosis": "Atelectasis - Post-procedure",
                "physician": "Dr. Michael Chen, MD",
                "notes": "Post-operative follow-up, mild atelectasis noted on chest X-ray"
            },
            {
                "date": "2023-12-27",
                "diagnosis": "Cholecystitis - Surgical",
                "physician": "Dr. Amanda Foster, MD",
                "notes": "Laparoscopic cholecystectomy performed, uncomplicated recovery"
            },
            {
                "date": "2023-12-20",
                "diagnosis": "Acute Cholecystitis",
                "physician": "Dr. Michael Chen, MD",
                "notes": "Presented with RUQ pain, ultrasound confirmed gallstones, surgery scheduled"
            },
            {
                "date": "2023-06-15",
                "diagnosis": "Type 2 Diabetes - Controlled",
                "physician": "Dr. Michael Chen, MD",
                "notes": "HbA1c 6.8%, continue current regimen, annual eye exam recommended"
            },
            {
                "date": "2022-11-08",
                "diagnosis": "Hypertension - Stable",
                "physician": "Dr. Michael Chen, MD",
                "notes": "BP well controlled on Lisinopril, continue current dose"
            },
            {
                "date": "2022-05-20",
                "diagnosis": "Routine Physical - No Finding",
                "physician": "Dr. Michael Chen, MD",
                "notes": "Annual wellness visit, chest X-ray clear, labs within normal limits"
            }
        ],
        "scan_dates": {
            "00026917_000.png": "2022-05-20",
            "00026917_001.png": "2024-01-10"
        }
    }
}


class SyntheticDataService:
    """
    Provides enhanced synthetic clinical data for demo patients.
    """
    
    def __init__(self):
        self._patients = SYNTHETIC_PATIENTS
        logger.info(f"Synthetic Data Service initialized with {len(self._patients)} demo patients")
    
    def get_enhanced_patient(self, patient_id: str) -> Optional[Dict]:
        """
        Get enhanced patient data if available.
        
        Args:
            patient_id: Patient ID
            
        Returns:
            Enhanced patient data or None
        """
        return self._patients.get(patient_id)
    
    def has_enhanced_data(self, patient_id: str) -> bool:
        """Check if enhanced data exists for patient."""
        return patient_id in self._patients
    
    def list_demo_patients(self):
        """List all demo patient IDs."""
        return list(self._patients.keys())


# Singleton instance
synthetic_data_service = SyntheticDataService()
