import { motion } from 'framer-motion';
import { FileText, FileInput, Download, FileBarChart } from 'lucide-react';
import Card from '../ui/Card';
import { useThemeStore } from '../../stores/themeStore';

const actions = [
  { icon: FileInput, label: 'Upload Data', description: 'Add energy, carbon, or waste records' },
  { icon: FileText, label: 'Generate Report', description: 'Create your monthly ESG summary' },
  { icon: Download, label: 'Export Data', description: 'Download in CSV or PDF format' },
  { icon: FileBarChart, label: 'View Analytics', description: 'Deep dive into trends and insights' },
];

export default function QuickActions() {
  const { theme } = useThemeStore();
  const isDark = theme === 'dark';

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.5 }}
      className="grid grid-cols-2 lg:grid-cols-4 gap-3"
    >
      {actions.map((action, index) => (
        <motion.div
          key={action.label}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 + index * 0.1 }}
        >
          <Card hover className="text-center h-full">
            <action.icon className="w-6 h-6 mx-auto mb-2" style={{ color: '#2d9e6b' }} />
            <h4 className={`font-body font-medium text-sm mb-1 ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>
              {action.label}
            </h4>
            <p className={`text-xs ${isDark ? 'text-white/55' : 'text-[#6b7c93]'}`}>
              {action.description}
            </p>
          </Card>
        </motion.div>
      ))}
    </motion.div>
  );
}