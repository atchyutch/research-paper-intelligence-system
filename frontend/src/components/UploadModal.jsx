import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { documents as docsApi } from '../lib/api';
import toast from 'react-hot-toast';
import { X, Upload, FileText, Loader2, CheckCircle2 } from 'lucide-react';

export default function UploadModal({ onClose, onDone }) {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [done, setDone] = useState(false);

  const onDrop = useCallback((accepted) => {
    const pdfs = accepted.filter((f) => f.type === 'application/pdf' || f.name.endsWith('.pdf'));
    if (pdfs.length !== accepted.length) {
      toast.error('Only PDF files are supported');
    }
    setFiles((prev) => [...prev, ...pdfs]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    multiple: true,
  });

  function removeFile(idx) {
    setFiles((f) => f.filter((_, i) => i !== idx));
  }

  async function handleUpload() {
    if (files.length === 0) return;
    setUploading(true);
    try {
      await docsApi.uploadMultiple(files);
      setDone(true);
      toast.success(`${files.length} file(s) uploaded`);
      setTimeout(() => onDone(), 800);
    } catch (err) {
      toast.error(err.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink-950/30 backdrop-blur-sm animate-fade-in"
      onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-2xl border border-paper-300/60 w-full max-w-lg mx-4 animate-slide-up"
        onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-paper-200">
          <h2 className="font-display text-lg font-semibold text-ink-900">Upload Papers</h2>
          <button onClick={onClose} className="p-1 rounded-lg hover:bg-paper-200 transition-colors">
            <X size={18} className="text-ink-400" />
          </button>
        </div>

        <div className="px-6 py-5">
          {/* Dropzone */}
          <div {...getRootProps()}
            className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all
              ${isDragActive ? 'border-accent bg-accent-muted' : 'border-paper-300 hover:border-ink-300 hover:bg-paper-50'}`}>
            <input {...getInputProps()} />
            <Upload className={`w-8 h-8 mx-auto mb-3 ${isDragActive ? 'text-accent' : 'text-ink-300'}`} strokeWidth={1.4} />
            <p className="text-sm text-ink-600">
              {isDragActive ? 'Drop files here' : 'Drag & drop PDFs, or click to browse'}
            </p>
            <p className="text-xs text-ink-400 mt-1">PDF files only</p>
          </div>

          {/* File list */}
          {files.length > 0 && (
            <div className="mt-4 space-y-2 max-h-48 overflow-y-auto">
              {files.map((f, i) => (
                <div key={i} className="flex items-center gap-3 px-3 py-2 rounded-lg bg-paper-50 border border-paper-200">
                  <FileText size={16} className="text-accent flex-shrink-0" />
                  <span className="text-sm text-ink-800 truncate flex-1">{f.name}</span>
                  <span className="text-xs text-ink-400 flex-shrink-0">
                    {(f.size / 1024 / 1024).toFixed(1)} MB
                  </span>
                  {!uploading && (
                    <button onClick={() => removeFile(i)} className="text-ink-400 hover:text-red-500 transition-colors">
                      <X size={14} />
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-paper-200 flex justify-end gap-3">
          <button onClick={onClose}
            className="px-4 py-2 rounded-lg text-sm text-ink-600 hover:bg-paper-200 transition-colors">
            Cancel
          </button>
          <button onClick={handleUpload}
            disabled={files.length === 0 || uploading || done}
            className="px-5 py-2 rounded-lg bg-ink-950 text-paper-50 text-sm font-medium
              hover:bg-ink-800 transition-all disabled:opacity-40 disabled:cursor-not-allowed
              flex items-center gap-2">
            {done ? (
              <><CheckCircle2 size={15} /> Uploaded</>
            ) : uploading ? (
              <><Loader2 size={15} className="animate-spin" /> Uploading...</>
            ) : (
              <><Upload size={15} /> Upload {files.length} file{files.length !== 1 ? 's' : ''}</>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
