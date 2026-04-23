import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { FileText, FileInput, Zap, Sparkles } from 'lucide-react';
import Card from '../ui/Card';
import { useThemeStore } from '../../stores/themeStore';
import type { QuickWinItem } from '../../types/workflow';

const actions = [
  { icon: FileInput, label: 'Upload Data', description: 'Add energy, carbon, or waste records', path: '/data-input' },
  { icon: Zap, label: 'Generate One Plan', description: 'Create your one-page ESG action plan', path: '/one-plan' },
  { icon: FileText, label: 'Open ESG Report', description: 'View GRI disclosures and download PDF', path: '/reports' },
];

interface QuickActionsProps {
  quickWins?: QuickWinItem[];
  isLoading?: boolean;
}

export default function QuickActions({ quickWins = [], isLoading = false }: QuickActionsProps) {
  const navigate = useNavigate();
  const { theme } = useThemeStore();
  const isDark = theme === 'dark';

  return (
    <div className="space-y-4">
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="grid grid-cols-2 lg:grid-cols-3 gap-3"
      >
        {actions.map((action, index) => (
          <motion.button
            key={action.label}
            type="button"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 + index * 0.1 }}
            onClick={() => navigate(action.path)}
            className="text-left"
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
          </motion.button>
        ))}
      </motion.div>

      <Card>
        <div className="flex items-center gap-2 mb-3">
          <Sparkles className="w-4 h-4" style={{ color: '#2d9e6b' }} />
          <h4 className={`font-body font-medium ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>
            Quick Wins
          </h4>
        </div>
        {isLoading ? (
          <p className={`text-sm ${isDark ? 'text-white/55' : 'text-[#6b7c93]'}`}>Loading recommendations...</p>
        ) : quickWins.length === 0 ? (
          <p className={`text-sm ${isDark ? 'text-white/55' : 'text-[#6b7c93]'}`}>
            Upload evidence files first to get AI-generated quick-win recommendations.
          </p>
        ) : (
          <div className="space-y-3">
            <p className={`text-xs ${isDark ? 'text-white/45' : 'text-[#6b7c93]'}`}>
              Amounts shown are estimated cost savings in PHP.
            </p>
            {quickWins.slice(0, 3).map((item) => (
              <div
                key={item.title}
                className={`rounded-lg p-3 ${isDark ? 'bg-white/5' : 'bg-[#f4f6f9]'}`}
              >
                <div className="flex items-start justify-between mb-1">
                  <p className={`text-sm font-medium ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>{item.title}</p>
                  {item.estimated_cost_savings_php && (
                    <div className="text-right">
                      <p className="text-[10px] uppercase tracking-wide" style={{ color: isDark ? 'rgba(255,255,255,0.45)' : '#6b7c93' }}>
                        Est. savings
                      </p>
                      <span className="text-xs font-semibold" style={{ color: '#2d9e6b' }}>
                        ₱{item.estimated_cost_savings_php.toLocaleString()}
                      </span>
                    </div>
                  )}
                </div>
                <p className={`text-xs mt-1 ${isDark ? 'text-white/55' : 'text-[#6b7c93]'}`}>{item.first_step}</p>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}