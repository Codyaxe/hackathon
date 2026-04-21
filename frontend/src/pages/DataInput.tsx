import { useEffect, useMemo, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { Upload, FileText, Image, Table, X, Check } from 'lucide-react';
import AppLayout from '../components/layout/AppLayout';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import Card from '../components/ui/Card';
import EmptyState from '../components/ui/EmptyState';
import { useThemeStore } from '../stores/themeStore';
import { getStoredCompanyProfile } from '../lib/companyProfile';
import {
  getMonthlyUpdateQuestions,
  submitMonthlyUpdate,
  uploadFiles,
} from '../lib/workflowApi';
import type {
  FileExtractionResponse,
  MonthlyUpdateQuestion,
  MonthlyUpdateQuestionsResponse,
  MonthlyUpdateResponse,
} from '../types/workflow';

type Tab = 'upload' | 'manual';
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

function getDefaultMonth(): string {
  return new Date().toISOString().slice(0, 7);
}

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
  const profile = useMemo(() => getStoredCompanyProfile(), []);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [activeTab, setActiveTab] = useState<Tab>('upload');
  const [selectedFiles, setSelectedFiles] = useState<SelectedFile[]>([]);
  const [uploadNotes, setUploadNotes] = useState('');
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadResult, setUploadResult] = useState<FileExtractionResponse | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [month, setMonth] = useState(getDefaultMonth());
  const [monthlyQuestions, setMonthlyQuestions] = useState<MonthlyUpdateQuestionsResponse | null>(null);
  const [monthlyAnswers, setMonthlyAnswers] = useState<Record<string, unknown>>({});
  const [monthlyNotes, setMonthlyNotes] = useState('');
  const [isLoadingQuestions, setIsLoadingQuestions] = useState(false);
  const [isSubmittingMonthly, setIsSubmittingMonthly] = useState(false);
  const [monthlyError, setMonthlyError] = useState<string | null>(null);
  const [monthlyResult, setMonthlyResult] = useState<MonthlyUpdateResponse | null>(null);
  const { theme } = useThemeStore();
  const isDark = theme === 'dark';

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

  const loadMonthlyQuestions = async () => {
    try {
      setIsLoadingQuestions(true);
      setMonthlyError(null);
      const response = await getMonthlyUpdateQuestions(profile.companyId, month);
      setMonthlyQuestions(response);
      setMonthlyAnswers({});
      setMonthlyResult(null);
    } catch (error) {
      setMonthlyError(error instanceof Error ? error.message : 'Could not load monthly questions.');
    } finally {
      setIsLoadingQuestions(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'manual' && !monthlyQuestions) {
      void loadMonthlyQuestions();
    }
  }, [activeTab, monthlyQuestions]);

  const setQuestionAnswer = (question: MonthlyUpdateQuestion, value: unknown) => {
    const normalized = question.input_type === 'number' ? Number(value) : value;
    setMonthlyAnswers((prev) => ({
      ...prev,
      [question.field_name]: normalized,
    }));
  };

  const submitMonthly = async () => {
    try {
      setIsSubmittingMonthly(true);
      setMonthlyError(null);
      const response = await submitMonthlyUpdate({
        company_id: profile.companyId,
        month,
        changes: monthlyAnswers,
        notes: monthlyNotes || undefined,
      });
      setMonthlyResult(response);
    } catch (error) {
      setMonthlyError(error instanceof Error ? error.message : 'Could not submit monthly update.');
    } finally {
      setIsSubmittingMonthly(false);
    }
  };

  const renderMonthlyInput = (question: MonthlyUpdateQuestion) => {
    const value = monthlyAnswers[question.field_name];

    if (question.input_type === 'single_choice') {
      return (
        <select
          value={typeof value === 'string' ? value : ''}
          onChange={(event) => setQuestionAnswer(question, event.target.value)}
          className={`mt-2 w-full border rounded-lg px-3 py-2 text-sm ${
            isDark
              ? 'bg-[#0f2040] border-white/15 text-white'
              : 'bg-white border-[#e2e8f0] text-[#1a2b3c]'
          }`}
        >
          <option value="">Select option</option>
          {question.options.map((option) => (
            <option key={option} value={option}>{option}</option>
          ))}
        </select>
      );
    }

    if (question.input_type === 'boolean') {
      return (
        <div className="mt-2 flex gap-2">
          {[true, false].map((option) => (
            <button
              key={`${question.field_name}-${String(option)}`}
              type="button"
              onClick={() => setQuestionAnswer(question, option)}
              className={`px-3 py-1.5 rounded-md text-xs border ${
                value === option
                  ? 'text-white border-transparent'
                  : isDark
                    ? 'text-white/60 border-white/20'
                    : 'text-[#6b7c93] border-[#d4dde8]'
              }`}
              style={value === option ? { background: 'linear-gradient(135deg, #2d9e6b 0%, #1B4332 100%)' } : undefined}
            >
              {option ? 'Yes' : 'No'}
            </button>
          ))}
        </div>
      );
    }

    if (question.input_type === 'number') {
      return (
        <input
          type="number"
          value={typeof value === 'number' ? String(value) : ''}
          onChange={(event) => setQuestionAnswer(question, event.target.value)}
          placeholder="Enter value"
          className={`mt-2 w-full border rounded-lg px-3 py-2 text-sm ${
            isDark
              ? 'bg-[#0f2040] border-white/15 text-white placeholder:text-white/40'
              : 'bg-white border-[#e2e8f0] text-[#1a2b3c]'
          }`}
        />
      );
    }

    return (
      <input
        type="text"
        value={typeof value === 'string' ? value : ''}
        onChange={(event) => setQuestionAnswer(question, event.target.value)}
        placeholder="Enter details"
        className={`mt-2 w-full border rounded-lg px-3 py-2 text-sm ${
          isDark
            ? 'bg-[#0f2040] border-white/15 text-white placeholder:text-white/40'
            : 'bg-white border-[#e2e8f0] text-[#1a2b3c]'
        }`}
      />
    );
  };

  return (
    <AppLayout title="Data Input" subtitle="Upload or manually enter ESG data">
      <div className="space-y-6">
        {/* Tabs */}
        <div className={`flex gap-2 p-1 rounded-lg w-fit border ${
          isDark ? 'bg-[#111e33] border-white/10' : 'bg-white border-[#e2e8f0]'
        }`}>
          {(['upload', 'manual'] as Tab[]).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                activeTab === tab
                  ? 'text-white shadow-sm'
                  : isDark ? 'text-white/55 hover:text-white' : 'text-[#6b7c93] hover:text-[#1a2b3c]'
              }`}
              style={activeTab === tab ? { background: 'linear-gradient(135deg, #2d9e6b 0%, #1B4332 100%)' } : undefined}
            >
              {tab === 'upload' ? 'Upload Files' : 'Manual Entry'}
            </button>
          ))}
        </div>

        {activeTab === 'upload' ? (
          <motion.div
            key="upload"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            {/* Drop Zone */}
            <div
              onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
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

            {/* Uploaded Files */}
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
                <p className={`text-sm ${isDark ? 'text-white/70' : 'text-[#3a4d63]'}`}>{uploadResult.ai_summary}</p>
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
        ) : (
          <motion.div
            key="manual"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <Card className="max-w-2xl space-y-6">
              <h3 className={`font-display text-lg ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>Monthly Update Flow</h3>

              <div className="grid grid-cols-2 gap-4 items-end">
                <Input
                  label="Month"
                  type="month"
                  value={month}
                  onChange={(event) => setMonth(event.target.value)}
                />
                <Button variant="secondary" onClick={loadMonthlyQuestions} loading={isLoadingQuestions}>
                  Load Questions
                </Button>
              </div>

              {monthlyQuestions && (
                <p className={`text-sm ${isDark ? 'text-white/55' : 'text-[#6b7c93]'}`}>
                  {monthlyQuestions.context_message}
                </p>
              )}

              {monthlyQuestions?.questions.map((question) => (
                <div key={question.question_id}>
                  <p className={`text-sm font-medium ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>{question.prompt}</p>
                  {renderMonthlyInput(question)}
                </div>
              ))}

              <Input
                label="Additional Notes"
                value={monthlyNotes}
                onChange={(event) => setMonthlyNotes(event.target.value)}
                placeholder="Optional details for this month"
              />

              {monthlyError && (
                <div className={`rounded-lg p-3 text-sm ${isDark ? 'bg-red-500/10 text-red-300' : 'bg-red-50 text-red-600'}`}>
                  {monthlyError}
                </div>
              )}

              <div className="flex justify-end gap-3 pt-4">
                <Button variant="ghost" onClick={() => setMonthlyAnswers({})}>Reset</Button>
                <Button onClick={submitMonthly} loading={isSubmittingMonthly}>Submit Monthly Update</Button>
              </div>

              {monthlyResult && (
                <div className={`rounded-lg p-4 ${isDark ? 'bg-white/5' : 'bg-[#f4f6f9]'}`}>
                  <h4 className={`font-medium mb-2 ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>Update submitted</h4>
                  <ul className={`space-y-1 text-sm ${isDark ? 'text-white/70' : 'text-[#3a4d63]'}`}>
                    {monthlyResult.change_summary.map((line) => (
                      <li key={line}>• {line}</li>
                    ))}
                  </ul>
                </div>
              )}
            </Card>
          </motion.div>
        )}
      </div>
    </AppLayout>
  );
}