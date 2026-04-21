import { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { FileText, Download, RefreshCw, Paperclip } from 'lucide-react';

import AppLayout from '../components/layout/AppLayout';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import { useThemeStore } from '../stores/themeStore';
import { getStoredCompanyProfile } from '../lib/companyProfile';
import {
  downloadESGReportPdf,
  downloadEvidenceFile,
  getESGReport,
  getEvidenceFiles,
} from '../lib/workflowApi';
import { formatAiText } from '../lib/aiText';
import type { ESGReportResponse, EvidenceFileRecord } from '../types/workflow';

export default function Reports() {
  const company = useMemo(() => getStoredCompanyProfile(), []);
  const [report, setReport] = useState<ESGReportResponse | null>(null);
  const [evidenceFiles, setEvidenceFiles] = useState<EvidenceFileRecord[]>([]);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isDownloadingPdf, setIsDownloadingPdf] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const { theme } = useThemeStore();
  const isDark = theme === 'dark';

  const refreshReport = async () => {
    try {
      setIsRefreshing(true);
      setErrorMessage(null);
      const [reportResponse, evidenceResponse] = await Promise.all([
        getESGReport(company.companyId),
        getEvidenceFiles(company.companyId),
      ]);
      setReport(reportResponse);
      setEvidenceFiles(evidenceResponse.evidence_files);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Could not load ESG report.');
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleDownloadPdf = async () => {
    try {
      setIsDownloadingPdf(true);
      const blob = await downloadESGReportPdf(company.companyId);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = `${company.companyId}-esg-report.pdf`;
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Could not download PDF report.');
    } finally {
      setIsDownloadingPdf(false);
    }
  };

  const handleDownloadEvidence = async (file: EvidenceFileRecord) => {
    try {
      const blob = await downloadEvidenceFile(company.companyId, file.file_id);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = file.filename;
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Could not download evidence file.');
    }
  };

  useEffect(() => {
    void refreshReport();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <AppLayout title="ESG Report" subtitle="Structured GRI disclosure output and evidence downloads">
      <div className="space-y-6">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <Card className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #2d9e6b 0%, #1B4332 100%)' }}>
                <FileText className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className={`font-display ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>Generate or Refresh ESG Report</h3>
                <p className={`text-sm ${isDark ? 'text-white/55' : 'text-[#6b7c93]'}`}>Build disclosures for GRI 302, 305, 306, and 401 from latest computations.</p>
              </div>
            </div>
            <div className="flex gap-2">
              <Button variant="secondary" icon={<RefreshCw className="w-4 h-4" />} onClick={refreshReport} loading={isRefreshing}>
                Refresh
              </Button>
              <Button icon={<Download className="w-4 h-4" />} onClick={handleDownloadPdf} loading={isDownloadingPdf} disabled={!report}>
                Download PDF
              </Button>
            </div>
          </Card>
        </motion.div>

        {errorMessage && (
          <div className={`rounded-lg p-3 text-sm ${isDark ? 'bg-red-500/10 text-red-300' : 'bg-red-50 text-red-600'}`}>
            {errorMessage}
          </div>
        )}

        {report && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
            <Card className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className={`font-display text-lg ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>GRI Disclosures</h3>
                  <p className={`text-sm ${isDark ? 'text-white/55' : 'text-[#6b7c93]'}`}>
                    Generated {new Date(report.generated_at).toLocaleString()}
                  </p>
                </div>
                <Badge variant="sage">{report.source_submission_id ? 'Computed' : 'Draft'}</Badge>
              </div>

              <div className="space-y-3">
                {report.disclosures.map((item) => (
                  <div key={item.disclosure} className={`rounded-lg p-3 ${isDark ? 'bg-white/5' : 'bg-[#f4f6f9]'}`}>
                    <div className="flex items-center justify-between gap-2">
                      <p className={`text-sm font-medium ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>
                        {item.disclosure} • {item.title}
                      </p>
                      {item.computed ? <Badge variant="forest">Computed</Badge> : <Badge variant="sand">Omitted</Badge>}
                    </div>
                    <p className={`text-xs mt-1 ${isDark ? 'text-white/70' : 'text-[#3a4d63]'}`}>
                      {item.computed
                        ? `${formatAiText(String(item.value ?? ''))} ${item.unit ?? ''}`.trim()
                        : formatAiText(item.reason_for_omission ?? 'Not enough data.')}
                    </p>
                  </div>
                ))}
              </div>

              {report.reasons_for_omission.length > 0 && (
                <div className="space-y-2">
                  <h4 className={`font-medium ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>Reasons for Omission</h4>
                  <div className="space-y-2">
                    {report.reasons_for_omission.map((reason) => (
                      <div key={`${reason.disclosure}-${reason.reason}`} className={`rounded-lg p-2 text-sm ${isDark ? 'bg-white/5 text-white/70' : 'bg-[#f4f6f9] text-[#3a4d63]'}`}>
                        <strong>{reason.disclosure}</strong>: {formatAiText(reason.reason)}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </Card>
          </motion.div>
        )}

        <Card className="space-y-3">
          <div className="flex items-center gap-2">
            <Paperclip className="w-4 h-4" style={{ color: '#2d9e6b' }} />
            <h3 className={`font-display ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>Evidence Files</h3>
          </div>
          {evidenceFiles.length === 0 ? (
            <p className={`text-sm ${isDark ? 'text-white/55' : 'text-[#6b7c93]'}`}>
              No evidence files found yet. Upload source files to build the report pipeline.
            </p>
          ) : (
            <div className="space-y-2">
              {evidenceFiles.map((file) => (
                <div
                  key={file.file_id}
                  className={`flex items-center justify-between rounded-lg p-3 ${isDark ? 'bg-white/5' : 'bg-[#f4f6f9]'}`}
                >
                  <div>
                    <p className={`text-sm font-medium ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>{file.filename}</p>
                    <p className={`text-xs ${isDark ? 'text-white/55' : 'text-[#6b7c93]'}`}>
                      {file.disclosure_tag ?? 'Unmapped disclosure'} • {(file.size_bytes / 1024).toFixed(1)} KB
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    icon={<Download className="w-4 h-4" />}
                    onClick={() => handleDownloadEvidence(file)}
                  >
                    Download
                  </Button>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </AppLayout>
  );
}