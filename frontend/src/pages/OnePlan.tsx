import { useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { Target, RefreshCw, FileCheck } from 'lucide-react';

import AppLayout from '../components/layout/AppLayout';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import { useThemeStore } from '../stores/themeStore';
import { getStoredCompanyProfile } from '../lib/companyProfile';
import { generatePlan } from '../lib/workflowApi';
import { formatAiText } from '../lib/aiText';
import type { ESGPlanResponse } from '../types/workflow';

export default function OnePlan() {
  const company = useMemo(() => getStoredCompanyProfile(), []);
  const [plan, setPlan] = useState<ESGPlanResponse | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const { theme } = useThemeStore();
  const isDark = theme === 'dark';

  const handleGeneratePlan = async () => {
    try {
      setIsGenerating(true);
      setErrorMessage(null);
      const generated = await generatePlan(company.companyId, 90);
      setPlan(generated);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Could not generate one-page plan.');
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <AppLayout title="One Plan" subtitle="Your single-page ESG execution plan">
      <div className="space-y-6">
        <Card className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #2d9e6b 0%, #1B4332 100%)' }}>
              <Target className="w-6 h-6 text-white" />
            </div>
            <div>
              <h3 className={`font-display ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>Auto-generate One Plan</h3>
              <p className={`text-sm ${isDark ? 'text-white/55' : 'text-[#6b7c93]'}`}>
                Build a concise execution plan from onboarding, uploads, and monthly updates.
              </p>
            </div>
          </div>
          <Button icon={<RefreshCw className="w-4 h-4" />} onClick={handleGeneratePlan} loading={isGenerating}>
            Generate One Plan
          </Button>
        </Card>

        {errorMessage && (
          <div className={`rounded-lg p-3 text-sm ${isDark ? 'bg-red-500/10 text-red-300' : 'bg-red-50 text-red-600'}`}>
            {errorMessage}
          </div>
        )}

        {plan && (
          <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
            <Card className="space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h3 className={`font-display text-lg ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>One Plan Summary</h3>
                  <p className={`text-sm ${isDark ? 'text-white/55' : 'text-[#6b7c93]'}`}>
                    Generated {new Date(plan.generated_at).toLocaleString()}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="sage">Live</Badge>
                  {plan.ready_for_pdf ? <Badge variant="forest">PDF Ready</Badge> : <Badge variant="sand">Not PDF Ready</Badge>}
                </div>
              </div>

              <p className={`text-sm whitespace-pre-line ${isDark ? 'text-white/70' : 'text-[#3a4d63]'}`}>
                {formatAiText(plan.one_page_summary)}
              </p>

              <div className="space-y-2">
                <h4 className={`font-medium ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>Priority Themes</h4>
                <div className="flex flex-wrap gap-2">
                  {plan.priority_themes.map((theme) => (
                    <span
                      key={theme}
                      className="px-2 py-1 text-xs rounded-full text-white"
                      style={{ background: 'linear-gradient(135deg, #2d9e6b 0%, #1B4332 100%)' }}
                    >
                      {theme.replaceAll('_', ' ')}
                    </span>
                  ))}
                </div>
              </div>

              {plan.kpis.length > 0 && (
                <div className="space-y-2">
                  <h4 className={`font-medium ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>KPI Focus</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    {plan.kpis.map((kpi) => (
                      <div key={kpi} className={`rounded-lg p-3 text-sm ${isDark ? 'bg-white/5' : 'bg-[#f4f6f9]'}`}>
                        {kpi}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="space-y-2">
                <h4 className={`font-medium ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>Action Items</h4>
                <div className="space-y-2">
                  {plan.actions.map((action) => (
                    <div key={action.title} className={`rounded-lg p-3 ${isDark ? 'bg-white/5' : 'bg-[#f4f6f9]'}`}>
                      <div className="flex items-center justify-between gap-2">
                        <p className={`text-sm font-medium ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>{action.title}</p>
                        <FileCheck className="w-4 h-4" style={{ color: '#2d9e6b' }} />
                      </div>
                      <p className={`text-xs mt-1 ${isDark ? 'text-white/55' : 'text-[#6b7c93]'}`}>{formatAiText(action.success_metric)}</p>
                    </div>
                  ))}
                </div>
              </div>
            </Card>
          </motion.div>
        )}
      </div>
    </AppLayout>
  );
}
