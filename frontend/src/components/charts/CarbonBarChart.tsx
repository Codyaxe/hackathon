import { motion } from 'framer-motion';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import type { CarbonData } from '../../types/esg';
import { useThemeStore } from '../../stores/themeStore';

interface CarbonBarChartProps {
  data: CarbonData[];
}

const CustomTooltip = ({ active, payload, label }: any) => {
  const { theme } = useThemeStore();
  const isDark = theme === 'dark';

  if (active && payload && payload.length) {
    return (
      <div
        className="backdrop-blur border rounded-lg px-3 py-2 shadow-sm"
        style={{
          backgroundColor: isDark ? '#111e33' : '#ffffff',
          border: isDark ? '1px solid rgba(255,255,255,0.1)' : '1px solid #e2e8f0',
          borderRadius: '8px',
          color: isDark ? '#ffffff' : '#1a2b3c',
        }}
      >
        <p className="text-xs mb-2" style={{ color: isDark ? 'rgba(255,255,255,0.55)' : '#6b7c93' }}>{label}</p>
        <div className="space-y-1">
          <p className="font-mono text-xs">
            Scope 1: <span style={{ color: '#D4A574' }}>{payload[0]?.value} t</span>
          </p>
          <p className="font-mono text-xs">
            Scope 2: <span style={{ color: '#2d9e6b' }}>{payload[1]?.value} t</span>
          </p>
          <p className="font-mono text-xs">
            Scope 3: <span style={{ color: isDark ? '#94a3b8' : '#94a3b8' }}>{payload[2]?.value} t</span>
          </p>
          <p
            className="font-mono text-sm font-medium pt-1"
            style={{
              borderColor: isDark ? 'rgba(255,255,255,0.1)' : '#e2e8f0',
              color: isDark ? '#ffffff' : '#1a2b3c'
            }}
          >
            Total: <span>{payload[3]?.value} t</span>
          </p>
        </div>
      </div>
    );
  }
  return null;
};

export default function CarbonBarChart({ data }: CarbonBarChartProps) {
  const { theme } = useThemeStore();
  const isDark = theme === 'dark';
  const hasData = data.length > 0;

  const gridColor = isDark ? 'rgba(255,255,255,0.06)' : '#e2e8f0';
  const textColor = isDark ? 'rgba(255,255,255,0.4)' : '#9ca3af';

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5, delay: 0.3 }}
      className={`rounded-xl shadow-sm p-5 ${
        isDark ? 'bg-[#111e33] border border-white/[0.08]' : 'bg-white border border-[#e2e8f0]'
      }`}
    >
      <div className="mb-4">
        <h3 className={`font-display text-lg ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>
          Carbon Emissions
        </h3>
        <p className={`text-sm ${isDark ? 'text-white/55' : 'text-[#6b7c93]'}`}>
          CO₂e emissions by scope (tons)
        </p>
      </div>
      <div className="h-72">
        {hasData ? (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
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
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend
                verticalAlign="top"
                align="right"
                iconType="circle"
                iconSize={8}
                wrapperStyle={{ paddingBottom: 16 }}
                formatter={(value) => <span className="text-xs" style={{ color: isDark ? 'rgba(255,255,255,0.55)' : '#6b7c93' }}>{value}</span>}
              />
              <Bar dataKey="scope1" stackId="a" fill="#D4A574" radius={[0, 0, 0, 0]} animationDuration={1500} />
              <Bar dataKey="scope2" stackId="a" fill="#2d9e6b" radius={[0, 0, 0, 0]} animationDuration={1500} />
              <Bar dataKey="scope3" stackId="a" fill={isDark ? '#64748b' : '#94a3b8'} radius={[4, 4, 0, 0]} animationDuration={1500} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-full flex items-center justify-center">
            <p className={`text-sm text-center ${isDark ? 'text-white/55' : 'text-[#6b7c93]'}`}>
              No monthly emissions data yet. Submit a monthly checkup to populate this chart.
            </p>
          </div>
        )}
      </div>
    </motion.div>
  );
}