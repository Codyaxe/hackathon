import { useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Upload, FileText, Image, Table, X, Check } from 'lucide-react';

import AppLayout from '../components/layout/AppLayout';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import Card from '../components/ui/Card';
import EmptyState from '../components/ui/EmptyState';
import { useThemeStore } from '../stores/themeStore';
import { getStoredCompanyProfile } from '../lib/companyProfile';
import { formatAiText } from '../lib/aiText';
import { uploadFiles } from '../lib/workflowApi';
import type { FileExtractionResponse } from '../types/workflow';

type FileType = 'pdf' | 'jpg' | 'xlsx';

type SelectedFile = {
  file: File;
  type: FileType;
  sizeLabel: string;
};

const fileTypeIcons: Record<FileType, React.ReactNode> = {
  pdf: <FileText className="w-5 h-5 text-red-400" />,
  jpg: <Image className="w-5 h-5 text-blue-400" />,
  xlsx: <Table className="w-5 h-5 text-green-400" />,
};

function resolveFileType(filename: string): FileType | null {
  const ext = filename.split('.').pop()?.toLowerCase();
  if (!ext) {
    return null;
  }
  if (ext === 'pdf') {
    return 'pdf';
  }
  if (['jpg', 'jpeg', 'png', 'webp'].includes(ext)) {
    return 'jpg';
  }
  if (['xlsx', 'xls', 'csv'].includes(ext)) {
    return 'xlsx';
  }
  return null;
}

function formatFileSize(bytes: number): string {
  return bytes >= 1024 * 1024 ? `${(bytes / 1024 / 1024).toFixed(1)} MB` : `${Math.max(1, Math.round(bytes / 1024))} KB`;
}

export default function DataInput() {
  const navigate = useNavigate();
  const profile = useMemo(() => getStoredCompanyProfile(), []);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [selectedFiles, setSelectedFiles] = useState<SelectedFile[]>([]);
  const [uploadNotes, setUploadNotes] = useState('');
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadResult, setUploadResult] = useState<FileExtractionResponse | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  const { theme } = useThemeStore();
  const isDark = theme === 'dark';
  const formattedUploadSummary = uploadResult ? formatAiText(uploadResult.ai_summary) : '';

  const addFiles = (incomingFiles: File[]) => {
    const accepted = incomingFiles
      .map((file) => {
        const type = resolveFileType(file.name);
        if (!type) {
          return null;
        }
        return {
          file,
          type,
          sizeLabel: formatFileSize(file.size),
        };
      })
      .filter((file): file is SelectedFile => file !== null);

    if (accepted.length === 0) {
      setUploadError('No supported files detected. Use PDF, image, CSV, or Excel files.');
      return;
    }

    setUploadError(null);
    setSelectedFiles((prev) => [...prev, ...accepted]);
  };

  const handleDrop = (event: React.DragEvent) => {
    event.preventDefault();
    setIsDragging(false);
    addFiles(Array.from(event.dataTransfer.files));
  };

  const handleBrowseFiles = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (!event.target.files) {
      return;
    }
    addFiles(Array.from(event.target.files));
    event.target.value = '';
  };

  const removeFile = (index: number) => {
    setSelectedFiles((prev) => prev.filter((_, fileIndex) => fileIndex !== index));
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) {
      setUploadError('Add at least one file before uploading.');
      return;
    }

    try {
      setIsUploading(true);
      setUploadError(null);
      const response = await uploadFiles(
        profile.companyId,
        selectedFiles.map((item) => item.file),
        uploadNotes,
      );
      setUploadResult(response);
    } catch (error) {
      setUploadError(error instanceof Error ? error.message : 'Upload failed.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <AppLayout title="Data Input" subtitle="Upload ESG source files for extraction">
      <div className="space-y-6">
        <Card className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
          <div>
            <h3 className={`font-display text-base ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>
              Monthly Checkup Is Separate Now
            </h3>
            <p className={`text-sm ${isDark ? 'text-white/55' : 'text-[#6b7c93]'}`}>
              Use the new Monthly Checkup menu item to submit month-by-month ESG updates.
            </p>
          </div>
          <Button variant="outline" onClick={() => navigate('/monthly-checkup')}>
            Open Monthly Checkup
          </Button>
        </Card>

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-6"
        >
          <div
            onDragOver={(event) => { event.preventDefault(); setIsDragging(true); }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-xl p-10 text-center transition-all ${
              isDragging
                ? 'border-[#2d9e6b] bg-[#f0faf5]'
                : isDark
                  ? 'bg-[#111e33] border-white/10 hover:border-white/20'
                  : 'bg-white border-[#e2e8f0] hover:border-[#9ca3af]'
            }`}
          >
            <div className={`w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4 ${
              isDragging ? '' : isDark ? 'bg-white/5' : 'bg-[#f4f6f9]'
            }`}>
              <Upload className={`w-8 h-8 ${isDragging ? 'text-[#2d9e6b]' : isDark ? 'text-white/40' : 'text-[#6b7c93]'}`} />
            </div>
            <h3 className={`font-display text-lg mb-2 ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>
              {isDragging ? 'Drop files here' : 'Drag & drop files'}
            </h3>
            <p className={`text-sm mb-4 ${isDark ? 'text-white/55' : 'text-[#6b7c93]'}`}>
              or click to browse. Supported: PDF, JPG, PNG, CSV, XLSX
            </p>
            <Button variant="secondary" onClick={() => fileInputRef.current?.click()}>
              Browse Files
            </Button>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              className="hidden"
              accept=".pdf,.jpg,.jpeg,.png,.webp,.csv,.xlsx,.xls"
              onChange={handleBrowseFiles}
            />
          </div>

          <Card className="space-y-3">
            <Input
              label="Notes for extraction (optional)"
              placeholder="e.g. Focus on electricity and fuel totals"
              value={uploadNotes}
              onChange={(event) => setUploadNotes(event.target.value)}
            />
            <div className="flex justify-end">
              <Button onClick={handleUpload} loading={isUploading}>Upload & Extract Metrics</Button>
            </div>
          </Card>

          {uploadError && (
            <div className={`rounded-lg p-3 text-sm ${isDark ? 'bg-red-500/10 text-red-300' : 'bg-red-50 text-red-600'}`}>
              {uploadError}
            </div>
          )}

          {selectedFiles.length > 0 ? (
            <Card className="space-y-3">
              <h3 className={`font-display ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>Selected Files</h3>
              {selectedFiles.map((item, index) => (
                <div
                  key={index}
                  className={`flex items-center justify-between p-3 rounded-lg ${
                    isDark ? 'bg-white/5' : 'bg-[#f4f6f9]'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    {fileTypeIcons[item.type]}
                    <div>
                      <p className={`text-sm font-medium ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>{item.file.name}</p>
                      <p className={`text-xs ${isDark ? 'text-white/40' : 'text-[#6b7c93]'}`}>{item.sizeLabel}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded-full flex items-center justify-center" style={{ backgroundColor: 'rgba(45, 158, 107, 0.2)' }}>
                      <Check className="w-3 h-3" style={{ color: '#2d9e6b' }} />
                    </div>
                    <button
                      onClick={() => removeFile(index)}
                      className={`w-6 h-6 rounded-full flex items-center justify-center transition-colors ${
                        isDark ? 'bg-white/5 hover:bg-white/10' : 'bg-white border border-[#e2e8f0] hover:bg-red-50'
                      }`}
                    >
                      <X className="w-3 h-3" style={{ color: isDark ? 'rgba(255,255,255,0.4)' : '#6b7c93' }} />
                    </button>
                  </div>
                </div>
              ))}
            </Card>
          ) : (
            <EmptyState
              title="No files selected"
              description="Upload your energy bills, fuel invoices, or expense reports to get started."
              action={{ label: 'Upload Files', onClick: () => fileInputRef.current?.click() }}
            />
          )}

          {uploadResult && (
            <Card className="space-y-3">
              <h3 className={`font-display ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>Extraction Result</h3>
              <p className={`text-sm whitespace-pre-line ${isDark ? 'text-white/70' : 'text-[#3a4d63]'}`}>{formattedUploadSummary}</p>
              {uploadResult.extracted_metrics.length > 0 && (
                <div className="space-y-2">
                  {uploadResult.extracted_metrics.slice(0, 6).map((metric) => (
                    <div
                      key={`${metric.metric_name}-${metric.category}`}
                      className={`rounded-md p-2 text-sm ${isDark ? 'bg-white/5' : 'bg-[#f4f6f9]'}`}
                    >
                      <span className={`font-medium ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>{metric.metric_name}:</span>{' '}
                      <span className={isDark ? 'text-white/70' : 'text-[#3a4d63]'}>
                        {metric.value} {metric.unit ?? ''}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          )}
        </motion.div>
      </div>
    </AppLayout>
  );
}
