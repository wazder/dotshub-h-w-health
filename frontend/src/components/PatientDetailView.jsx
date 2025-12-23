import React, { useState, useEffect } from 'react';
import { getPatient } from '../services/api';

// Medical term translations and descriptions
const MEDICAL_TERMS = {
    'No Finding': { tr: 'No Finding', desc: 'No abnormal findings detected on the X-ray.' },
    'Nodule': { tr: 'Nodule', desc: 'Small round lesion in the lung. May be benign or malignant, may require follow-up.' },
    'Infiltration': { tr: 'Infiltration', desc: 'Fluid or cell accumulation in lung tissue. May indicate infection.' },
    'Atelectasis': { tr: 'Atelectasis', desc: 'Collapse or loss of air in a part of the lung.' },
    'Effusion': { tr: 'Effusion', desc: 'Fluid accumulation between lung membranes (pleural effusion).' },
    'Pneumothorax': { tr: 'Pneumothorax', desc: 'Air accumulation between lung and chest wall, may require emergency intervention.' },
    'Mass': { tr: 'Mass', desc: 'Large lesion in the lung. Requires further investigation.' },
    'Consolidation': { tr: 'Consolidation', desc: 'Densification of lung tissue, usually indicates pneumonia.' },
    'Pleural_Thickening': { tr: 'Pleural Thickening', desc: 'Thickening of the lung membrane.' },
    'Cardiomegaly': { tr: 'Cardiomegaly', desc: 'Enlarged heart, may indicate heart failure.' },
    'Emphysema': { tr: 'Emphysema', desc: 'Damage to lung air sacs, a type of COPD.' },
    'Edema': { tr: 'Edema', desc: 'Fluid accumulation in the lungs.' },
    'Fibrosis': { tr: 'Fibrosis', desc: 'Hardening and scarring of lung tissue.' },
    'Pneumonia': { tr: 'Pneumonia', desc: 'Lung infection, requires treatment.' },
    'Hernia': { tr: 'Hernia', desc: 'Diaphragmatic hernia.' }
};

const translateMedicalTerm = (term) => {
    if (!term) return 'No Information';
    const found = MEDICAL_TERMS[term];
    return found ? found.tr : term;
};

const getMedicalDescription = (term) => {
    if (!term) return null;
    const found = MEDICAL_TERMS[term];
    return found ? found.desc : null;
};

const PatientDetailView = ({ patient, onBack, returnToResults }) => {
    const [patientData, setPatientData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Get patient ID
    const patientId = patient?.patientId || patient?.id?.replace('PT-', '') || 'Unknown';

    useEffect(() => {
        const fetchPatientData = async () => {
            try {
                setLoading(true);
                const data = await getPatient(patientId);
                if (data?.patient) {
                    setPatientData(data.patient);
                } else {
                    // If no data from API, use props
                    setPatientData(null);
                }
            } catch (err) {
                // API error - silently use fallback
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        if (patientId && patientId !== 'Unknown') {
            fetchPatientData();
        } else {
            setLoading(false);
        }
    }, [patientId]);

    // Merge data for display
    const displayData = {
        id: patientId,
        age: patientData?.age || patient?.age || 45,
        gender: patientData?.gender || patient?.gender || 'Unknown',
        diagnosis: patientData?.diagnosis || patient?.diagnosis || 'Unknown',
        scans: patientData?.scans || [],
        diagnosisHistory: patientData?.diagnosisHistory || [
            { date: '2023-11-16', diagnosis: patient?.diagnosis || 'Unknown', physician: 'Dr. AI System' }
        ],
        allFindings: patientData?.all_findings || [],
        imageCount: patientData?.image_count || 0,
        // Enhanced data fields
        enhanced: patientData?.enhanced || false,
        name: patientData?.name,
        dateOfBirth: patientData?.date_of_birth,
        bloodType: patientData?.blood_type,
        height: patientData?.height,
        weight: patientData?.weight,
        bmi: patientData?.bmi,
        occupation: patientData?.occupation,
        smokingStatus: patientData?.smoking_status,
        alcoholUse: patientData?.alcohol_use,
        allergies: patientData?.allergies || [],
        chronicConditions: patientData?.chronic_conditions || [],
        primaryDiagnosis: patientData?.primary_diagnosis,
        diagnosisDate: patientData?.diagnosis_date,
        attendingPhysician: patientData?.attending_physician,
        department: patientData?.department,
        chiefComplaint: patientData?.chief_complaint,
        historyOfPresentIllness: patientData?.history_of_present_illness,
        physicalExamination: patientData?.physical_examination,
        laboratoryResults: patientData?.laboratory_results,
        imagingFindings: patientData?.imaging_findings,
        treatmentPlan: patientData?.treatment_plan || [],
        medications: patientData?.medications || [],
        clinicalNotes: patientData?.clinical_notes,
        prognosis: patientData?.prognosis,
        followUp: patientData?.follow_up
    };

    if (loading) {
        return (
            <div className="w-full h-full flex items-center justify-center bg-[var(--bg-dark)]">
                <div className="text-center">
                    <div className="animate-spin w-12 h-12 border-4 border-[var(--primary)] border-t-transparent rounded-full mx-auto mb-4"></div>
                    <p className="text-[var(--text-muted)]">Loading patient information...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="w-full h-full p-8 overflow-y-auto bg-[var(--bg-dark)]">
            <div className="max-w-6xl mx-auto space-y-6">

                {/* Back Button */}
                <button
                    onClick={returnToResults || onBack}
                    className="flex items-center gap-2 text-[var(--text-muted)] hover:text-[var(--text-main)] transition group mb-4"
                >
                    <svg className="group-hover:-translate-x-1 transition-transform" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M19 12H5" /><path d="M12 19l-7-7 7-7" /></svg>
                    <span>Back to Analysis Results</span>
                </button>

                {/* Header Info */}
                <div className="flex items-end justify-between border-b border-[var(--border)] pb-6">
                    <div>
                        <div className="flex items-center gap-4 mb-2">
                            <h1 className="text-4xl font-bold text-[var(--text-main)]">
                                {displayData.name || `Patient #PT-${displayData.id}`}
                            </h1>
                        </div>
                        <div className="flex items-center gap-3 flex-wrap">
                            <span className="px-3 py-1 bg-[var(--bg-card)] border border-[var(--border)] rounded-full text-sm text-[var(--text-muted)]">
                                {displayData.gender === 'F' || displayData.gender === 'Female' ? 'Female' : 
                                 displayData.gender === 'M' || displayData.gender === 'Male' ? 'Male' : displayData.gender}, {displayData.age} Years Old
                            </span>
                            {displayData.bloodType && (
                                <span className="px-3 py-1 bg-red-500/10 border border-red-500/30 rounded-full text-sm text-red-300">
                                    Blood: {displayData.bloodType}
                                </span>
                            )}
                            {displayData.department && (
                                <span className="px-3 py-1 bg-blue-500/10 border border-blue-500/30 rounded-full text-sm text-blue-300">
                                    {displayData.department}
                                </span>
                            )}
                        </div>
                        <p className="text-[var(--text-muted)] mt-2">
                            {displayData.attendingPhysician ? `Attending: ${displayData.attendingPhysician}` : ''}
                            {displayData.diagnosisDate ? ` • ${displayData.diagnosisDate}` : displayData.scans[0]?.date ? ` • ${displayData.scans[0]?.date}` : ''}
                            {displayData.imageCount > 0 && ` • ${displayData.imageCount} images`}
                        </p>
                    </div>
                    <div className="flex gap-3">
                        <button 
                            onClick={() => alert('Report generation feature is not yet active.')}
                            className="btn bg-[var(--primary)] text-white hover:bg-[var(--primary-hover)]"
                        >
                            Generate Report
                        </button>
                        <button 
                            onClick={() => alert('DICOM export feature is not yet active.')}
                            className="btn border border-[var(--border)] hover:bg-[var(--bg-card-hover)] text-[var(--text-main)]"
                        >
                            Download DICOM
                        </button>
                    </div>
                </div>

                <div className="grid grid-cols-12 gap-6">

                    {/* LEFT: Scan Gallery */}
                    <div className="col-span-8 space-y-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <h2 className="text-xl font-bold text-[var(--text-main)]">X-Ray History</h2>
                                <p className="text-xs text-[var(--text-muted)] mt-1">All X-ray images and analysis results for this patient</p>
                            </div>
                            {displayData.scans.length > 4 && (
                                <button className="text-sm text-[var(--primary)] hover:underline">View All</button>
                            )}
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            {displayData.scans.length > 0 ? (
                                displayData.scans.slice(0, 4).map((scan, i) => (
                                    <div key={scan.id || i} className="card p-4 hover:border-[var(--primary)] transition cursor-pointer group">
                                        <div className="aspect-[4/3] bg-black rounded mb-3 overflow-hidden relative">
                                            {scan.imageUrl ? (
                                                <img 
                                                    src={scan.imageUrl}
                                                    alt={`Scan ${scan.id}`}
                                                    className="w-full h-full object-cover grayscale group-hover:scale-105 transition-transform"
                                                    onError={(e) => {
                                                        e.target.style.display = 'none';
                                                    }}
                                                />
                                            ) : (
                                                <div className="absolute inset-0 flex items-center justify-center text-[var(--text-muted)] bg-gray-900">
                                                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1">
                                                        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                                                        <circle cx="8.5" cy="8.5" r="1.5"/>
                                                        <polyline points="21 15 16 10 5 21"/>
                                                    </svg>
                                                </div>
                                            )}
                                            {/* Scan type label */}
                                            <div className="absolute top-2 right-2 px-2 py-0.5 bg-black/70 text-white text-[10px] rounded backdrop-blur-sm" title="Scan type: PA (Posterior-Anterior) = Back to front shot, most common chest X-ray position">
                                                {scan.type}
                                            </div>
                                        </div>
                                        <div className="flex justify-between items-center">
                                            <span className="font-mono text-sm text-[var(--text-muted)]">{scan.date}</span>
                                            {/* Normal/Abnormal status */}
                                            <span 
                                                className={`text-xs px-2 py-0.5 rounded ${scan.status === 'Abnormal' ? 'bg-red-500/20 text-red-300' : 'bg-green-500/20 text-green-300'}`}
                                                title={scan.status === 'Abnormal' ? 'Abnormal findings detected in this image' : 'No abnormal findings in this image'}
                                            >
                                                {scan.status === 'Abnormal' ? 'Abnormal' : 'Normal'}
                                            </span>
                                        </div>
                                        {scan.findings && scan.findings !== 'No Finding' && (
                                            <p className="text-xs text-[var(--primary)] mt-2 truncate" title={getMedicalDescription(scan.findings)}>
                                                {translateMedicalTerm(scan.findings)}
                                            </p>
                                        )}
                                    </div>
                                ))
                            ) : (
                                <div className="col-span-2 card p-8 text-center text-[var(--text-muted)]">
                                    <svg className="mx-auto mb-4" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1">
                                        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                                        <circle cx="8.5" cy="8.5" r="1.5"/>
                                        <polyline points="21 15 16 10 5 21"/>
                                    </svg>
                                    <p>No X-ray data found for this patient</p>
                                </div>
                            )}
                        </div>
                        
                        {/* All Findings - With Descriptions */}
                        {displayData.allFindings.length > 0 && (
                            <div className="card p-4">
                                <div className="mb-3">
                                    <h3 className="font-bold text-[var(--text-main)]">All Detected Findings</h3>
                                    <p className="text-xs text-[var(--text-muted)]">Findings detected across all X-rays for this patient</p>
                                </div>
                                <div className="flex flex-wrap gap-2">
                                    {displayData.allFindings.map((finding, i) => (
                                        <span 
                                            key={i} 
                                            className={`px-3 py-1 rounded-full text-sm cursor-help ${
                                                finding === 'No Finding' 
                                                    ? 'bg-green-500/20 text-green-300' 
                                                    : 'bg-orange-500/20 text-orange-300'
                                            }`}
                                            title={getMedicalDescription(finding) || 'Medical finding'}
                                        >
                                            {translateMedicalTerm(finding)}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>

                    {/* RIGHT: Diagnosis & Vitals */}
                    <div className="col-span-4 space-y-6">
                        <div className="card p-6">
                            <h3 className="font-bold text-[var(--text-main)] mb-4 flex items-center gap-2">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" /><polyline points="14 2 14 8 20 8" /><path d="M16 13H8" /><path d="M16 17H8" /><path d="M10 9H8" /></svg>
                                Diagnosis History
                            </h3>
                            <p className="text-xs text-[var(--text-muted)] mb-4">Diagnoses detected by artificial intelligence</p>
                            <div className="space-y-4 relative before:absolute before:left-1.5 before:top-2 before:bottom-2 before:w-px before:bg-[var(--border)]">
                                {displayData.diagnosisHistory.map((dx, i) => (
                                    <div key={i} className="relative pl-6">
                                        <div className={`absolute left-0 top-1.5 w-3 h-3 rounded-full border-2 border-[var(--bg-card)] ${i === 0 ? 'bg-[var(--primary)]' : 'bg-[var(--border)]'}`}></div>
                                        <p className="text-xs text-[var(--text-muted)] mb-1 font-mono">{dx.date}</p>
                                        <p className="font-bold text-[var(--text-main)]">{translateMedicalTerm(dx.diagnosis)}</p>
                                        <p className="text-xs text-[var(--primary)]">{dx.physician}</p>
                                        {dx.notes && (
                                            <p className="text-xs text-[var(--text-muted)] mt-1 italic">{dx.notes}</p>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>
                        
                        {/* Primary Diagnosis Card - With Description */}
                        <div className="card p-6 bg-gradient-to-br from-[var(--primary)]/10 to-transparent border-[var(--primary)]/30">
                            <h3 className="font-bold text-[var(--text-main)] mb-2">Primary Diagnosis</h3>
                            <p className="text-2xl font-bold text-[var(--primary)]">
                                {displayData.primaryDiagnosis || translateMedicalTerm(displayData.diagnosis)}
                            </p>
                            {(getMedicalDescription(displayData.diagnosis) || displayData.chiefComplaint) && (
                                <p className="text-xs text-[var(--text-muted)] mt-2 bg-[var(--bg-dark)] p-2 rounded">
                                    {displayData.chiefComplaint || getMedicalDescription(displayData.diagnosis)}
                                </p>
                            )}
                            <p className="text-sm text-[var(--text-muted)] mt-3">
                                Age: {displayData.age} • Gender: {
                                    displayData.gender === 'F' || displayData.gender === 'Female' ? 'Female' : 
                                    displayData.gender === 'M' || displayData.gender === 'Male' ? 'Male' : displayData.gender
                                }
                            </p>
                        </div>

                        {/* Patient Demographics - Enhanced */}
                        {displayData.enhanced && (
                            <div className="card p-6">
                                <h3 className="font-bold text-[var(--text-main)] mb-4 flex items-center gap-2">
                                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                                        <circle cx="12" cy="7" r="4"/>
                                    </svg>
                                    Patient Info
                                </h3>
                                <div className="space-y-2 text-sm">
                                    {displayData.dateOfBirth && (
                                        <div className="flex justify-between">
                                            <span className="text-[var(--text-muted)]">DOB</span>
                                            <span className="text-[var(--text-main)]">{displayData.dateOfBirth}</span>
                                        </div>
                                    )}
                                    {displayData.height && (
                                        <div className="flex justify-between">
                                            <span className="text-[var(--text-muted)]">Height</span>
                                            <span className="text-[var(--text-main)]">{displayData.height}</span>
                                        </div>
                                    )}
                                    {displayData.weight && (
                                        <div className="flex justify-between">
                                            <span className="text-[var(--text-muted)]">Weight</span>
                                            <span className="text-[var(--text-main)]">{displayData.weight}</span>
                                        </div>
                                    )}
                                    {displayData.bmi && (
                                        <div className="flex justify-between">
                                            <span className="text-[var(--text-muted)]">BMI</span>
                                            <span className="text-[var(--text-main)]">{displayData.bmi}</span>
                                        </div>
                                    )}
                                    {displayData.occupation && (
                                        <div className="flex justify-between">
                                            <span className="text-[var(--text-muted)]">Occupation</span>
                                            <span className="text-[var(--text-main)]">{displayData.occupation}</span>
                                        </div>
                                    )}
                                    {displayData.smokingStatus && (
                                        <div className="flex justify-between">
                                            <span className="text-[var(--text-muted)]">Smoking</span>
                                            <span className="text-[var(--text-main)] text-xs">{displayData.smokingStatus}</span>
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}

                        {/* Allergies & Conditions */}
                        {displayData.enhanced && (displayData.allergies.length > 0 || displayData.chronicConditions.length > 0) && (
                            <div className="card p-6">
                                <h3 className="font-bold text-[var(--text-main)] mb-4 flex items-center gap-2">
                                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                        <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
                                    </svg>
                                    Alerts
                                </h3>
                                {displayData.allergies.length > 0 && (
                                    <div className="mb-3">
                                        <p className="text-xs text-red-400 font-medium mb-1">Allergies</p>
                                        <div className="flex flex-wrap gap-1">
                                            {displayData.allergies.map((allergy, i) => (
                                                <span key={i} className="px-2 py-0.5 bg-red-500/20 text-red-300 rounded text-xs">
                                                    {allergy}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                )}
                                {displayData.chronicConditions.length > 0 && (
                                    <div>
                                        <p className="text-xs text-yellow-400 font-medium mb-1">Chronic Conditions</p>
                                        <div className="flex flex-wrap gap-1">
                                            {displayData.chronicConditions.map((condition, i) => (
                                                <span key={i} className="px-2 py-0.5 bg-yellow-500/20 text-yellow-300 rounded text-xs">
                                                    {condition}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>

                </div>

                {/* Enhanced Clinical Details Section */}
                {displayData.enhanced && (
                    <div className="space-y-6 mt-8">
                        {/* Clinical Notes */}
                        {displayData.historyOfPresentIllness && (
                            <div className="card p-6">
                                <h3 className="font-bold text-[var(--text-main)] mb-4 flex items-center gap-2">
                                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                                        <polyline points="14 2 14 8 20 8"/>
                                        <line x1="16" y1="13" x2="8" y2="13"/>
                                        <line x1="16" y1="17" x2="8" y2="17"/>
                                        <polyline points="10 9 9 9 8 9"/>
                                    </svg>
                                    History of Present Illness
                                </h3>
                                <p className="text-[var(--text-muted)] text-sm leading-relaxed whitespace-pre-line">
                                    {displayData.historyOfPresentIllness}
                                </p>
                            </div>
                        )}

                        <div className="grid grid-cols-12 gap-6">
                            {/* Physical Examination */}
                            {displayData.physicalExamination && (
                                <div className="col-span-6 card p-6">
                                    <h3 className="font-bold text-[var(--text-main)] mb-4 flex items-center gap-2">
                                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
                                        </svg>
                                        Physical Examination
                                    </h3>
                                    <div className="space-y-3 text-sm">
                                        {displayData.physicalExamination.vitals && (
                                            <div className="bg-[var(--bg-dark)] p-3 rounded">
                                                <p className="text-[var(--primary)] font-medium mb-2">Vital Signs</p>
                                                <div className="grid grid-cols-2 gap-2">
                                                    {Object.entries(displayData.physicalExamination.vitals).map(([key, value]) => (
                                                        <div key={key} className="flex justify-between">
                                                            <span className="text-[var(--text-muted)] capitalize">{key.replace(/_/g, ' ')}</span>
                                                            <span className="text-[var(--text-main)]">{value}</span>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                        {displayData.physicalExamination.general && (
                                            <div>
                                                <span className="text-[var(--text-muted)]">General: </span>
                                                <span className="text-[var(--text-main)]">{displayData.physicalExamination.general}</span>
                                            </div>
                                        )}
                                        {displayData.physicalExamination.chest && (
                                            <div>
                                                <span className="text-[var(--text-muted)]">Chest: </span>
                                                <span className="text-[var(--text-main)]">{displayData.physicalExamination.chest}</span>
                                            </div>
                                        )}
                                        {displayData.physicalExamination.cardiovascular && (
                                            <div>
                                                <span className="text-[var(--text-muted)]">Cardiovascular: </span>
                                                <span className="text-[var(--text-main)]">{displayData.physicalExamination.cardiovascular}</span>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}

                            {/* Laboratory Results */}
                            {displayData.laboratoryResults && (
                                <div className="col-span-6 card p-6">
                                    <h3 className="font-bold text-[var(--text-main)] mb-4 flex items-center gap-2">
                                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
                                        </svg>
                                        Laboratory Results
                                    </h3>
                                    <div className="space-y-2 text-sm">
                                        {Object.entries(displayData.laboratoryResults).map(([key, value]) => (
                                            <div key={key} className="flex justify-between py-1 border-b border-[var(--border)]">
                                                <span className="text-[var(--text-muted)] uppercase text-xs">{key.replace(/_/g, ' ')}</span>
                                                <span className={`text-[var(--text-main)] ${value.includes('elevated') ? 'text-red-300' : ''}`}>{value}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Imaging Findings */}
                        {displayData.imagingFindings && (
                            <div className="card p-6">
                                <h3 className="font-bold text-[var(--text-main)] mb-4 flex items-center gap-2">
                                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                                        <circle cx="8.5" cy="8.5" r="1.5"/>
                                        <polyline points="21 15 16 10 5 21"/>
                                    </svg>
                                    Imaging Findings
                                </h3>
                                <div className="space-y-3 text-sm">
                                    {Object.entries(displayData.imagingFindings).map(([key, value]) => (
                                        <div key={key} className="bg-[var(--bg-dark)] p-3 rounded">
                                            <p className="text-[var(--primary)] font-medium mb-1 capitalize">{key.replace(/_/g, ' ')}</p>
                                            <p className="text-[var(--text-muted)]">{value}</p>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        <div className="grid grid-cols-12 gap-6">
                            {/* Treatment Plan */}
                            {displayData.treatmentPlan.length > 0 && (
                                <div className="col-span-6 card p-6">
                                    <h3 className="font-bold text-[var(--text-main)] mb-4 flex items-center gap-2">
                                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <path d="M9 11l3 3L22 4"/>
                                            <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
                                        </svg>
                                        Treatment Plan
                                    </h3>
                                    <ul className="space-y-2 text-sm">
                                        {displayData.treatmentPlan.map((item, i) => (
                                            <li key={i} className="flex items-start gap-2">
                                                <span className="text-[var(--success)] mt-1">•</span>
                                                <span className="text-[var(--text-muted)]">{item}</span>
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}

                            {/* Medications */}
                            {displayData.medications.length > 0 && (
                                <div className="col-span-6 card p-6">
                                    <h3 className="font-bold text-[var(--text-main)] mb-4 flex items-center gap-2">
                                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <path d="M10.5 20.5L3 13l10-10 7.5 7.5"/>
                                            <path d="M15 9l6 6"/>
                                        </svg>
                                        Current Medications
                                    </h3>
                                    <div className="space-y-2">
                                        {displayData.medications.map((med, i) => (
                                            <div key={i} className="flex justify-between items-center bg-[var(--bg-dark)] p-2 rounded text-sm">
                                                <span className="text-[var(--text-main)] font-medium">{med.name}</span>
                                                <span className="text-[var(--text-muted)]">{med.dose} - {med.frequency}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Prognosis & Follow-up */}
                        {(displayData.prognosis || displayData.followUp || displayData.clinicalNotes) && (
                            <div className="card p-6">
                                <h3 className="font-bold text-[var(--text-main)] mb-4 flex items-center gap-2">
                                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                        <circle cx="12" cy="12" r="10"/>
                                        <polyline points="12 6 12 12 16 14"/>
                                    </svg>
                                    Clinical Summary
                                </h3>
                                <div className="space-y-4 text-sm">
                                    {displayData.clinicalNotes && (
                                        <div>
                                            <p className="text-[var(--primary)] font-medium mb-1">Clinical Notes</p>
                                            <p className="text-[var(--text-muted)] leading-relaxed">{displayData.clinicalNotes}</p>
                                        </div>
                                    )}
                                    {displayData.prognosis && (
                                        <div className="bg-green-500/10 border border-green-500/30 p-3 rounded">
                                            <p className="text-green-400 font-medium mb-1">Prognosis</p>
                                            <p className="text-green-300">{displayData.prognosis}</p>
                                        </div>
                                    )}
                                    {displayData.followUp && (
                                        <div className="bg-blue-500/10 border border-blue-500/30 p-3 rounded">
                                            <p className="text-blue-400 font-medium mb-1">Follow-up</p>
                                            <p className="text-blue-300">{displayData.followUp}</p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

export default PatientDetailView;
