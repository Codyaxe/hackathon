import { useState } from 'react';
import { motion } from 'framer-motion';
import AppLayout from '../components/layout/AppLayout';
import OnboardingCard from '../components/dashboard/OnboardingCard';
import MetricCard from '../components/dashboard/MetricCard';
import QuickActions from '../components/dashboard/QuickActions';
import EnergyLineChart from '../components/charts/EnergyLineChart';
import CarbonBarChart from '../components/charts/CarbonBarChart';
import WasteDonutChart from '../components/charts/WasteDonutChart';
import { energyData, carbonData, totalEnergy, totalCarbon, recyclingRate } from '../data/mock/esg-data';
import type { ScoreCard } from '../types/esg';
import { useThemeStore } from '../stores/themeStore';

export default function Dashboard() {
  const [showOnboarding, setShowOnboarding] = useState(true);
  const { theme } = useThemeStore();
  const isDark = theme === 'dark';

  const metrics: ScoreCard[] = [
    { label: 'Total Energy', value: totalEnergy.toLocaleString(), unit: 'kWh', score: 'good', trend: 'down', change: -8.2 },
    { label: 'Carbon Footprint', value: totalCarbon.toFixed(0), unit: 't CO₂e', score: 'fair', trend: 'down', change: -5.4 },
    { label: 'Recycling Rate', value: recyclingRate.toFixed(1), unit: '%', score: 'excellent', trend: 'up', change: 12.3 },
    { label: 'ESG Score', value: 78, unit: '/100', score: 'good', trend: 'stable', change: 3.1 },
  ];

  return (
    <AppLayout title="Dashboard" subtitle="Apex Manufacturing Co. — Manufacturing">
      <div className="space-y-6">
        {/* Onboarding Card */}
        {showOnboarding && (
          <OnboardingCard onDismiss={() => setShowOnboarding(false)} />
        )}

        {/* Quick Actions */}
        <QuickActions />

        {/* Metrics Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {metrics.map((metric, index) => (
            <MetricCard key={metric.label} data={metric} delay={0.2 + index * 0.1} />
          ))}
        </div>

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
              {[
                { name: 'Fuel_Invoice.pdf', size: '2.4 MB', date: 'Dec 15' },
                { name: 'Electricity_Bill.jpg', size: '1.8 MB', date: 'Dec 10' },
                { name: 'Expense_Report.xlsx', size: '856 KB', date: 'Dec 8' },
              ].map((file) => (
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