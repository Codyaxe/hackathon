import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import type { ScoreCard } from '../../types/esg';
import { useThemeStore } from '../../stores/themeStore';

interface MetricCardProps {
  data: ScoreCard;
  delay?: number;
}

const scoreColors = {
  excellent: '#2d9e6b',
  good: '#2D6A4F',
  fair: '#D4A574',
  poor: '#ef4444',
};

const TrendIcon = ({ trend }: { trend: 'up' | 'down' | 'stable' }) => {
  if (trend === 'up') return <TrendingUp className="w-4 h-4" style={{ color: '#2d9e6b' }} />;
  if (trend === 'down') return <TrendingDown className="w-4 h-4" style={{ color: '#ef4444' }} />;
  return <Minus className="w-4 h-4" style={{ color: '#6b7c93' }} />;
};

export default function MetricCard({ data, delay = 0 }: MetricCardProps) {
  const { theme } = useThemeStore();
  const isDark = theme === 'dark';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
      whileHover={{ y: -4 }}
      className={`rounded-xl shadow-sm p-5 transition-shadow duration-300 hover:shadow-md ${
        isDark
          ? 'bg-[#111e33] border border-white/[0.08]'
          : 'bg-white border border-[#e2e8f0]'
      }`}
    >
      <div className="flex items-start justify-between mb-3">
        <span className={`text-sm font-body ${isDark ? 'text-white/55' : 'text-[#6b7c93]'}`}>
          {data.label}
        </span>
        <TrendIcon trend={data.trend} />
      </div>
      <div className="flex items-baseline gap-2 mb-1">
        <span className="text-3xl font-display" style={{ color: scoreColors[data.score] }}>
          {data.value}
        </span>
        <span className={`text-sm ${isDark ? 'text-white/40' : 'text-[#6b7c93]'}`}>{data.unit}</span>
      </div>
      {data.change !== undefined && (
        <div className="flex items-center gap-1">
          <span className="text-xs font-mono" style={{ color: data.change >= 0 ? '#2d9e6b' : '#ef4444' }}>
            {data.change >= 0 ? '+' : ''}{data.change}%
          </span>
          <span className={`text-xs ${isDark ? 'text-white/40' : 'text-[#6b7c93]'}`}>vs last year</span>
        </div>
      )}
    </motion.div>
  );
}