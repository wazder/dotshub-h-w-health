import React, { useRef } from 'react';

const UploadZone = ({ onUpload }) => {
    const fileInputRef = useRef(null);

    const handleDrop = (e) => {
        e.preventDefault();
        const files = e.dataTransfer.files;
        if (files?.[0]) {
            onUpload(files[0]);
        }
    };

    const handleChange = (e) => {
        const files = e.target.files;
        if (files?.[0]) {
            onUpload(files[0]);
        }
    };

    return (
        <div
            className="w-full h-full flex flex-col items-center justify-center relative p-12 transition hover:bg-[var(--bg-card-hover)] cursor-pointer group"
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
        >
            <input
                type="file"
                ref={fileInputRef}
                className="hidden"
                accept="image/*,.dcm,.dicom,.nii,.nii.gz"
                onChange={handleChange}
            />

            <div className="w-20 h-20 rounded-full bg-[rgba(59,130,246,0.1)] flex items-center justify-center mb-6 group-hover:scale-110 transition duration-300">
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="var(--primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                    <polyline points="17 8 12 3 7 8" />
                    <line x1="12" y1="3" x2="12" y2="15" />
                </svg>
            </div>

            <h3 className="text-xl font-bold mb-2">Upload X-Ray Image</h3>
            <p className="text-[var(--text-muted)] max-w-sm text-center mb-8">
                You can upload images in DICOM (.dcm), NIfTI, PNG or JPEG format. <br />
                <span className="text-[var(--text-muted)] text-xs mt-2 block">
                    AI analysis will begin after the image is uploaded.
                </span>
            </p>

            <button className="btn btn-primary px-8">
                Select File
            </button>
        </div>
    );
};

export default UploadZone;
