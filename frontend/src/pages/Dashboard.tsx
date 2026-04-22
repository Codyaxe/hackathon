import { useCallback, useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import AppLayout from '../components/layout/AppLayout';
import OnboardingCard from '../components/dashboard/OnboardingCard';
import MetricCard from '../components/dashboard/MetricCard';
import QuickActions from '../components/dashboard/QuickActions';
import EnergyLineChart from '../components/charts/EnergyLineChart';
import CarbonBarChart from '../components/charts/CarbonBarChart';
import WasteDonutChart from '../components/charts/WasteDonutChart';
import { energyData, carbonData } from '../data/mock/esg-data';
import type { ScoreCard } from '../types/esg';
import { useThemeStore } from '../stores/themeStore';
import { getStoredCompanyProfile } from '../lib/companyProfile';
import { getProgress, getQuickWins, getResponseLibrary } from '../lib/workflowApi';
import type { ProgressTrackerResponse, QuickWinItem, ResponseLibraryEntry } from '../types/workflow';

type RecentFile = {
  name: string;
  size: string;
  date: string;
};

function formatFileSize(sizeBytes: number): string {
  if (sizeBytes >= 1024 * 1024) {
    return `${(sizeBytes / 1024 / 1024).toFixed(1)} MB`;
  }
  if (sizeBytes >= 1024) {
    return `${(sizeBytes / 1024).toFixed(0)} KB`;
  }
  return `${sizeBytes} B`;
}

function parseRecentFiles(entries: ResponseLibraryEntry[]): RecentFile[] {
  return entries
    .filter((entry) => entry.entry_type === 'upload_extraction')
    .flatMap((entry) => {
      const payload = entry.payload as { files?: Array<{ filename?: string; size_bytes?: number; uploaded_at?: string }> };
      return (payload.files ?? []).map((file) => {
        const uploadedDate = file.uploaded_at ? new Date(file.uploaded_at) : new Date();
        return {
          name: file.filename ?? 'uploaded-file',
          size: formatFileSize(file.size_bytes ?? 0),
          date: uploadedDate.toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
        };
      });
    })
    .slice(0, 3);
}

export default function Dashboard() {
  const profile = useMemo(() => getStoredCompanyProfile(), []);
  const [showOnboarding, setShowOnboarding] = useState(true);
  const [progress, setProgress] = useState<ProgressTrackerResponse | null>(null);
  const [quickWins, setQuickWins] = useState<QuickWinItem[]>([]);
  const [libraryEntries, setLibraryEntries] = useState<ResponseLibraryEntry[]>([]);
  const [isLoadingInsights, setIsLoadingInsights] = useState(true);
  const [apiError, setApiError] = useState<string | null>(null);
  const { theme } = useThemeStore();
  const isDark = theme === 'dark';

  const refreshDashboard = useCallback(async () => {
    setIsLoadingInsights(true);
    setApiError(null);

    const [progressResult, quickWinsResult, libraryResult] = await Promise.allSettled([
      getProgress(profile.companyId),
      getQuickWins(profile.companyId),
      getResponseLibrary(profile.companyId, 20),
    ]);

    if (progressResult.status === 'fulfilled') {
      setProgress(progressResult.value);
    } else if (!progressResult.reason?.message?.includes('Company not found')) {
      setApiError(progressResult.reason instanceof Error ? progressResult.reason.message : 'Could not load progress.');
    }

    if (quickWinsResult.status === 'fulfilled') {
      setQuickWins(quickWinsResult.value);
    } else if (!quickWinsResult.reason?.message?.includes('Company not found')) {
      setApiError(quickWinsResult.reason instanceof Error ? quickWinsResult.reason.message : 'Could not load quick wins.');
    }

    if (libraryResult.status === 'fulfilled') {
      setLibraryEntries(libraryResult.value.entries);
    } else if (!libraryResult.reason?.message?.includes('Company not found')) {
      setApiError(libraryResult.reason instanceof Error ? libraryResult.reason.message : 'Could not load response library.');
    }

    setIsLoadingInsights(false);
  }, [profile.companyId]);

  useEffect(() => {
    void refreshDashboard();
  }, [refreshDashboard]);

  const recentFiles = useMemo(() => parseRecentFiles(libraryEntries), [libraryEntries]);
  const completion = progress?.completion_percentage ?? 0;
  const hasCompletedOnboarding = progress?.steps.find((step) => step.step_id === 'onboarding')?.completed ?? false;
  
  // Build metrics from real ESG data
  const esgScore = progress?.esg_score ?? Math.round(completion);
  const esgScoreLabel: ScoreCard['score'] = esgScore >= 85 ? 'excellent' : esgScore >= 70 ? 'good' : esgScore >= 50 ? 'fair' : 'poor';
  const complianceStatus = progress?.compliance_status ?? 'Needs Attention';
  const complianceScore: ScoreCard['score'] = complianceStatus === 'On Track' ? 'excellent' : 'fair';

  const metrics: ScoreCard[] = [
    {
      label: 'ESG Score',
      value: esgScore,
      unit: '/100',
      score: esgScoreLabel,
      trend: 'up',
      change: completion,
    },
    {
      label: 'Compliance Status',
      value: complianceStatus,
      unit: '',
      score: complianceScore,
      trend: complianceStatus === 'On Track' ? 'up' : 'down',
      change: 0,
    },
  ];

  return (
    <AppLayout title="Dashboard" subtitle={`${profile.companyName} — ${profile.industry}`}>
      <div className="space-y-6">
        {/* Onboarding Card */}
        {showOnboarding && !hasCompletedOnboarding && (
          <OnboardingCard onDismiss={() => setShowOnboarding(false)} onComplete={refreshDashboard} />
        )}

        {/* Quick Actions */}
        <QuickActions quickWins={quickWins} isLoading={isLoadingInsights} />

        {apiError && (
          <div className={`rounded-lg p-3 text-sm ${isDark ? 'bg-red-500/10 text-red-300' : 'bg-red-50 text-red-600'}`}>
            {apiError}
          </div>
        )}

        {/* Metrics Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {metrics.map((metric, index) => (
            <MetricCard key={metric.label} data={metric} delay={0.2 + index * 0.1} />
          ))}
        </div>

        {/* KPIs Grid */}
        {progress?.kpis && progress.kpis.length > 0 && (
          <div className="space-y-3">
            <h2 className={`text-lg font-display font-semibold ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>
              Key Performance Indicators
            </h2>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              {progress.kpis.map((kpi, index) => {
                const ratingColor = kpi.rating === 'Best' ? '#2d9e6b' : kpi.rating === 'Better' ? '#2D6A4F' : '#D4A574';
                return (
                  <motion.div
                    key={kpi.name}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.4, delay: 0.4 + index * 0.1 }}
                    whileHover={{ y: -4 }}
                    className={`rounded-xl shadow-sm p-4 transition-shadow duration-300 hover:shadow-md ${
                      isDark ? 'bg-[#111e33] border border-white/[0.08]' : 'bg-white border border-[#e2e8f0]'
                    }`}
                  >
                    <p className={`text-sm font-medium mb-2 ${isDark ? 'text-white/70' : 'text-[#6b7c93]'}`}>
                      {kpi.name}
                    </p>
                    <p className="text-2xl font-display font-semibold mb-2" style={{ color: ratingColor }}>
                      {kpi.value}
                      {kpi.unit && <span className="text-sm ml-1">{kpi.unit}</span>}
                    </p>
                    <span
                      className="text-xs font-semibold px-2 py-1 rounded-full"
                      style={{ color: ratingColor, backgroundColor: `${ratingColor}15` }}
                    >
                      {kpi.rating}
                    </span>
                  </motion.div>
                );
              })}
            </div>
          </div>
        )}

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <EnergyLineChart data={energyData} />
          <CarbonBarChart data={carbonData} />
        </div>

        {/* Bottom Row */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <WasteDonutChart />
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5, delay: 0.5 }}
            className={`
              rounded-xl shadow-sm p-5
              ${isDark
                ? 'bg-[#111e33] border border-white/[0.08]'
                : 'bg-white border border-[#e2e8f0]'
              }
            `}
          >
            <h3 className={`font-display text-lg mb-4 ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>
              Recent Files
            </h3>
            <div className="space-y-3">
              {(recentFiles.length > 0 ? recentFiles : [
                { name: 'No uploads yet', size: 'Run Data Input upload', date: '--' },
              ]).map((file) => (
                <div
                  key={file.name}
                  className={`
                    flex items-center justify-between p-3 rounded-lg transition-colors cursor-pointer
                    ${isDark ? 'hover:bg-white/5' : 'hover:bg-gray-100'}
                  `}
                >
                  <div className="flex items-center gap-3">
                    <div className={`
                      w-10 h-10 rounded-lg flex items-center justify-center
                      ${isDark ? 'bg-white/5' : 'bg-white border border-[#e2e8f0]'}
                    `}>
                      <span className={`text-xs font-mono uppercase ${isDark ? 'text-white/40' : 'text-[#6b7c93]'}`}>
                        {file.name.split('.').pop()}
                      </span>
                    </div>
                    <div>
                      <p className={`text-sm font-medium ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>
                        {file.name}
                      </p>
                      <p className={`text-xs ${isDark ? 'text-white/40' : 'text-[#6b7c93]'}`}>
                        {file.size}
                      </p>
                    </div>
                  </div>
                  <span className={`text-xs ${isDark ? 'text-white/40' : 'text-[#6b7c93]'}`}>
                    {file.date}
                  </span>
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      </div>
    </AppLayout>
  );
}