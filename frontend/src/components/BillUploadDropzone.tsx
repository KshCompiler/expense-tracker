import { useRef, useState } from 'react';
import { api, ApiError } from '../api/client';
import { useToast } from '../context/ToastContext';
import type { BillExtraction } from '../types';

const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp'];
const MAX_BYTES = 5 * 1024 * 1024;

interface BillUploadDropzoneProps {
  endpoint: string;
  fieldKey: 'category' | 'source';
  scanningText: string;
  emptyMessage: string;
  successMessage: string;
  idleText: string;
  onExtracted: (data: BillExtraction) => void;
}

export function BillUploadDropzone({
  endpoint,
  fieldKey,
  scanningText,
  emptyMessage,
  successMessage,
  idleText,
  onExtracted,
}: BillUploadDropzoneProps) {
  const { showToast } = useToast();
  const [scanning, setScanning] = useState(false);
  const [dragover, setDragover] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = async (file: File | null | undefined) => {
    if (!file) return;

    if (!ALLOWED_TYPES.includes(file.type)) {
      showToast('Please upload a JPG, PNG, or WEBP image.', 'error');
      return;
    }
    if (file.size > MAX_BYTES) {
      showToast('That image is too large — please use a photo under 5MB.', 'error');
      return;
    }

    setScanning(true);
    try {
      const formData = new FormData();
      formData.append('bill_image', file);
      const data = await api.postForm<BillExtraction>(endpoint, formData);

      const filled: string[] = [];
      const missing: string[] = [];
      if (data.amount != null) filled.push('amount');
      else missing.push('amount');
      if (data[fieldKey]) filled.push(fieldKey);
      else missing.push(fieldKey);
      if (data.date) filled.push('date');
      else missing.push('date');

      onExtracted(data);

      if (filled.length === 0) {
        showToast(emptyMessage, 'error');
      } else if (missing.length > 0) {
        showToast(`Filled in ${filled.join(', ')} — please check ${missing.join(', ')} yourself.`, 'warning');
      } else {
        showToast(successMessage, 'success');
      }
    } catch (err) {
      showToast(err instanceof ApiError ? err.message : "Couldn't reach the server — please enter the details manually.", 'error');
    } finally {
      setScanning(false);
    }
  };

  return (
    <div
      className={`bill-drop ${dragover ? 'dragover' : ''} ${scanning ? 'scanning' : ''}`}
      tabIndex={0}
      role="button"
      aria-label="Upload a photo to auto-fill this form"
      aria-busy={scanning}
      onClick={() => !scanning && fileInputRef.current?.click()}
      onKeyDown={(e) => {
        if ((e.key === 'Enter' || e.key === ' ') && !scanning) {
          e.preventDefault();
          fileInputRef.current?.click();
        }
      }}
      onDragEnter={(e) => {
        e.preventDefault();
        setDragover(true);
      }}
      onDragOver={(e) => {
        e.preventDefault();
        setDragover(true);
      }}
      onDragLeave={(e) => {
        e.preventDefault();
        setDragover(false);
      }}
      onDrop={(e) => {
        e.preventDefault();
        setDragover(false);
        handleFile(e.dataTransfer.files?.[0]);
      }}
    >
      <span className="bill-drop-icon" aria-hidden="true">
        🧾
      </span>
      <span className="bill-drop-text">{scanning ? scanningText : idleText}</span>
      <input
        ref={fileInputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        hidden
        onChange={(e) => {
          handleFile(e.target.files?.[0]);
          e.target.value = '';
        }}
      />
    </div>
  );
}
