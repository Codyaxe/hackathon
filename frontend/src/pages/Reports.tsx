import { motion } from 'framer-motion';
import { FileText, Download, Calendar, Clock } from 'lucide-react';
import AppLayout from '../components/layout/AppLayout';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import { useThemeStore } from '../stores/themeStore';

const reports = [
  {
    id: '1',
    title: 'Q4 2024 ESG Summary',
    description: 'Quarterly environmental impact report covering October-December 2024',
    type: 'Quarterly',
    status: 'ready',
    generatedAt: 'Dec 31, 2024',
    size: '2.4 MB',
  },
  {
    id: '2',
    title: 'Annual Carbon Report 2024',
    description: 'Comprehensive carbon emissions analysis for fiscal year 2024',
    type: 'Annual',
    status: 'ready',
    generatedAt: 'Dec 15, 2024',
    size: '5.1 MB',
  },
  {
    id: '3',
    title: 'November 2024 Energy Audit',
    description: 'Detailed breakdown of monthly energy consumption and costs',
    type: 'Monthly',
    status: 'ready',
    generatedAt: 'Dec 1, 2024',
    size: '1.8 MB',
  },
  {
    id: '4',
    title: 'Waste Diversion Progress',
    description: 'Analysis of recycling rates and waste reduction initiatives',
    type: 'Custom',
    status: 'generating',
    generatedAt: 'In progress...',
    size: '--',
  },
];

const typeColors: Record<string, 'sage' | 'sand' | 'forest' | 'slate'> = {
  Quarterly: 'sage',
  Annual: 'sand',
  Monthly: 'forest',
  Custom: 'slate',
};

export default function Reports() {
  const { theme } = useThemeStore();
  const isDark = theme === 'dark';

  return (
    <AppLayout title="Reports" subtitle="Generate and download ESG reports">
      <div className="space-y-6">
        {/* Generate New Report */}
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
                <h3 className={`font-display ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>Generate New Report</h3>
                <p className={`text-sm ${isDark ? 'text-white/55' : 'text-[#6b7c93]'}`}>Create a custom ESG report based on your data</p>
              </div>
            </div>
            <Button icon={<FileText className="w-4 h-4" />}>
              Create Report
            </Button>
          </Card>
        </motion.div>

        {/* Report List */}
        <div className="space-y-4">
          <h3 className={`font-display text-lg ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>Available Reports</h3>
          {reports.map((report, index) => (
            <motion.div
              key={report.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <Card hover className="flex items-center justify-between">
                <div className="flex items-center gap-4 flex-1">
                  <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                    isDark ? 'bg-white/5 border border-white/10' : 'bg-white border border-[#e2e8f0]'
                  }`}>
                    <FileText className="w-6 h-6" style={{ color: isDark ? 'rgba(255,255,255,0.4)' : '#6b7c93' }} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className={`font-body font-medium truncate ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>{report.title}</h4>
                      <Badge variant={typeColors[report.type]}>{report.type}</Badge>
                      {report.status === 'generating' && (
                        <Badge variant="sand">Generating</Badge>
                      )}
                    </div>
                    <p className={`text-sm truncate mb-2 ${isDark ? 'text-white/55' : 'text-[#6b7c93]'}`}>{report.description}</p>
                    <div className={`flex items-center gap-4 text-xs ${isDark ? 'text-white/40' : 'text-[#6b7c93]'}`}>
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        {report.generatedAt}
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {report.size}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2 ml-4">
                  <Button
                    variant="ghost"
                    size="sm"
                    disabled={report.status === 'generating'}
                    icon={<Download className="w-4 h-4" />}
                  >
                    Download
                  </Button>
                </div>
              </Card>
            </motion.div>
          ))}
        </div>
      </div>
    </AppLayout>
  );
}