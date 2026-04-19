import { motion } from 'framer-motion';
import { XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts';
import type { EnergyData } from '../../types/esg';
import { useThemeStore } from '../../stores/themeStore';

interface EnergyLineChartProps {
  data: EnergyData[];
}

const CustomTooltip = ({ active, payload, label }: any) => {
  const { theme } = useThemeStore();
  const isDark = theme === 'dark';

  if (active && payload && payload.length) {
    return (
      <div
        className="backdrop-blur border rounded-lg px-3 py-2 shadow-glass"
        style={{
          backgroundColor: isDark ? '#111e33' : '#ffffff',
          border: isDark ? '1px solid rgba(255,255,255,0.1)' : '1px solid #e2e8f0',
          borderRadius: '8px',
          color: isDark ? '#ffffff' : '#1a2b3c',
        }}
      >
        <p className="text-xs mb-1" style={{ color: isDark ? 'rgba(255,255,255,0.55)' : '#6b7c93' }}>{label}</p>
        <p className="font-mono text-sm font-medium" style={{ color: '#2d9e6b' }}>
          {payload[0].value.toLocaleString()} kWh
        </p>
        <p className="font-mono text-xs" style={{ color: '#D4A574' }}>
          ${payload[1]?.value.toLocaleString()}
        </p>
      </div>
    );
  }
  return null;
};

export default function EnergyLineChart({ data }: EnergyLineChartProps) {
  const { theme } = useThemeStore();
  const isDark = theme === 'dark';

  const gridColor = isDark ? 'rgba(255,255,255,0.06)' : '#e2e8f0';
  const textColor = isDark ? 'rgba(255,255,255,0.4)' : '#9ca3af';

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5, delay: 0.2 }}
      className={`rounded-xl shadow-sm p-5 ${
        isDark ? 'bg-[#111e33] border border-white/[0.08]' : 'bg-white border border-[#e2e8f0]'
      }`}
    >
      <div className="mb-4">
        <h3 className={`font-display text-lg ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>
          Energy Consumption
        </h3>
        <p className={`text-sm ${isDark ? 'text-white/55' : 'text-[#6b7c93]'}`}>
          Monthly kWh usage over the past year
        </p>
      </div>
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
            <defs>
              <linearGradient id="energyGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#2d9e6b" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#2d9e6b" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke={gridColor} vertical={false} />
            <XAxis
              dataKey="month"
              axisLine={false}
              tickLine={false}
              tick={{ fill: textColor, fontSize: 12 }}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fill: textColor, fontSize: 12 }}
              tickFormatter={(value) => `${(value / 1000).toFixed(0)}k`}
            />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone"
              dataKey="kWh"
              stroke="#2d9e6b"
              strokeWidth={2}
              fill="url(#energyGradient)"
              animationDuration={1500}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
}