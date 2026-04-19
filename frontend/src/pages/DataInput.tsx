import { useState } from 'react';
import { motion } from 'framer-motion';
import { Upload, FileText, Image, Table, X, Check } from 'lucide-react';
import AppLayout from '../components/layout/AppLayout';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import Card from '../components/ui/Card';
import EmptyState from '../components/ui/EmptyState';
import { useThemeStore } from '../stores/themeStore';

type Tab = 'upload' | 'manual';
type FileType = 'pdf' | 'jpg' | 'xlsx';

const fileTypeIcons: Record<FileType, React.ReactNode> = {
  pdf: <FileText className="w-5 h-5 text-red-400" />,
  jpg: <Image className="w-5 h-5 text-blue-400" />,
  xlsx: <Table className="w-5 h-5 text-green-400" />,
};

export default function DataInput() {
  const [activeTab, setActiveTab] = useState<Tab>('upload');
  const [uploadedFiles, setUploadedFiles] = useState<Array<{ name: string; type: FileType; size: string }>>([]);
  const [isDragging, setIsDragging] = useState(false);
  const { theme } = useThemeStore();
  const isDark = theme === 'dark';

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const files = Array.from(e.dataTransfer.files);
    files.forEach(file => {
      const ext = file.name.split('.').pop()?.toLowerCase();
      if (ext && ['pdf', 'jpg', 'jpeg', 'xlsx', 'xls'].includes(ext)) {
        const fileType: FileType = ext === 'jpeg' ? 'jpg' : ext as FileType;
        setUploadedFiles(prev => [...prev, {
          name: file.name,
          type: fileType,
          size: `${(file.size / 1024 / 1024).toFixed(1)} MB`,
        }]);
      }
    });
  };

  const removeFile = (index: number) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index));
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
                or click to browse. Supported: PDF, JPG, XLSX
              </p>
              <Button variant="secondary">
                Browse Files
              </Button>
            </div>

            {/* Uploaded Files */}
            {uploadedFiles.length > 0 ? (
              <Card className="space-y-3">
                <h3 className={`font-display ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>Uploaded Files</h3>
                {uploadedFiles.map((file, index) => (
                  <div
                    key={index}
                    className={`flex items-center justify-between p-3 rounded-lg ${
                      isDark ? 'bg-white/5' : 'bg-[#f4f6f9]'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      {fileTypeIcons[file.type]}
                      <div>
                        <p className={`text-sm font-medium ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>{file.name}</p>
                        <p className={`text-xs ${isDark ? 'text-white/40' : 'text-[#6b7c93]'}`}>{file.size}</p>
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
                title="No files uploaded"
                description="Upload your energy bills, fuel invoices, or expense reports to get started."
                action={{ label: 'Upload Files', onClick: () => {} }}
              />
            )}
          </motion.div>
        ) : (
          <motion.div
            key="manual"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <Card className="max-w-2xl space-y-6">
              <h3 className={`font-display text-lg ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>Manual Data Entry</h3>

              <div className="grid grid-cols-2 gap-4">
                <Input label="Energy Usage (kWh)" type="number" placeholder="0" />
                <Input label="Cost ($)" type="number" placeholder="0.00" />
              </div>

              <div className="grid grid-cols-3 gap-4">
                <Input label="Scope 1 (t CO₂e)" type="number" placeholder="0.0" />
                <Input label="Scope 2 (t CO₂e)" type="number" placeholder="0.0" />
                <Input label="Scope 3 (t CO₂e)" type="number" placeholder="0.0" />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <Input label="Landfill Waste (tons)" type="number" placeholder="0.0" />
                <Input label="Recycled (tons)" type="number" placeholder="0.0" />
              </div>

              <div className="flex justify-end gap-3 pt-4">
                <Button variant="ghost">Cancel</Button>
                <Button>Save Entry</Button>
              </div>
            </Card>
          </motion.div>
        )}
      </div>
    </AppLayout>
  );
}