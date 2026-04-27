import { useCallback, useState } from 'react';
import { Upload, FileText, X } from 'lucide-react';

interface FileDropZoneProps {
  onFileSelect: (file: File) => void;
  accept?: string;
  label?: string;
  description?: string;
  selectedFile?: File | null;
  onClear?: () => void;
}

export default function FileDropZone({
  onFileSelect,
  accept = '.pdf,.docx,.csv,.txt',
  label = 'Drop your file here',
  description = 'Supports PDF, DOCX, CSV, TXT',
  selectedFile,
  onClear,
}: FileDropZoneProps) {
  const [isDragging, setIsDragging] = useState(false);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) onFileSelect(file);
  }, [onFileSelect]);

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) onFileSelect(file);
  }, [onFileSelect]);

  if (selectedFile) {
    return (
      <div className="card flex items-center gap-3 border-primary/30 bg-primary/5">
        <FileText className="w-10 h-10 text-primary shrink-0" />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-text truncate">{selectedFile.name}</p>
          <p className="text-xs text-text-secondary">
            {(selectedFile.size / 1024).toFixed(1)} KB
          </p>
        </div>
        {onClear && (
          <button onClick={onClear} className="p-1 rounded hover:bg-primary/10 transition-colors">
            <X className="w-4 h-4 text-text-secondary" />
          </button>
        )}
      </div>
    );
  }

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-all cursor-pointer ${
        isDragging
          ? 'border-primary bg-primary/5 scale-[1.01]'
          : 'border-border hover:border-primary/50 hover:bg-bg'
      }`}
    >
      <input
        type="file"
        accept={accept}
        onChange={handleInputChange}
        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
      />
      <Upload className={`w-10 h-10 mx-auto mb-3 ${isDragging ? 'text-primary' : 'text-text-muted'}`} />
      <p className="text-sm font-semibold text-text">{label}</p>
      <p className="text-xs text-text-secondary mt-1">{description}</p>
    </div>
  );
}
