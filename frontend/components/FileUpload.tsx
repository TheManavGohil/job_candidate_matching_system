"use client";

import { useCallback, useState } from "react";
import { Upload, FileText, X } from "lucide-react";

interface FileUploadProps {
  accept?: string;
  label?: string;
  onFileSelect: (file: File) => void;
  onTextSubmit?: (text: string) => void;
  showTextInput?: boolean;
}

export default function FileUpload({
  accept = ".pdf,.docx,.csv,.txt",
  label = "Upload Document",
  onFileSelect,
  onTextSubmit,
  showTextInput = false,
}: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [textValue, setTextValue] = useState("");

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") setIsDragging(true);
    else setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files?.[0];
      if (file) {
        setSelectedFile(file);
        onFileSelect(file);
      }
    },
    [onFileSelect]
  );

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      onFileSelect(file);
    }
  };

  return (
    <div className="space-y-4">
      <div
        className={`dropzone ${isDragging ? "active" : ""}`}
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        onClick={() => document.getElementById("file-input")?.click()}
      >
        <input
          id="file-input"
          type="file"
          accept={accept}
          onChange={handleFileInput}
          className="hidden"
        />
        {selectedFile ? (
          <div className="flex items-center justify-center gap-3">
            <FileText size={24} className="text-cyan-400" />
            <div>
              <p className="text-sm font-medium">{selectedFile.name}</p>
              <p className="text-xs text-[var(--muted-foreground)]">
                {(selectedFile.size / 1024).toFixed(1)} KB
              </p>
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setSelectedFile(null);
              }}
              className="ml-2 text-[var(--muted-foreground)] hover:text-[var(--danger)]"
            >
              <X size={16} />
            </button>
          </div>
        ) : (
          <div className="space-y-2">
            <Upload
              size={32}
              className="mx-auto text-[var(--muted-foreground)]"
            />
            <p className="text-sm font-medium">{label}</p>
            <p className="text-xs text-[var(--muted-foreground)]">
              Drag & drop or click to browse • PDF, DOCX, CSV, TXT
            </p>
          </div>
        )}
      </div>

      {showTextInput && (
        <div className="space-y-2">
          <p className="text-xs text-[var(--muted-foreground)] text-center">
            — or paste text directly —
          </p>
          <textarea
            value={textValue}
            onChange={(e) => setTextValue(e.target.value)}
            className="input min-h-[120px] resize-y"
            placeholder="Paste job description or resume text here..."
          />
          {textValue.trim() && onTextSubmit && (
            <button
              onClick={() => onTextSubmit(textValue)}
              className="btn-primary w-full justify-center"
            >
              Submit Text
            </button>
          )}
        </div>
      )}
    </div>
  );
}
