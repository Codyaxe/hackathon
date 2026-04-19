import { motion } from 'framer-motion';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { wasteData } from '../../data/mock/esg-data';
import { useThemeStore } from '../../stores/themeStore';

const data = [
  { name: 'Recycled', value: wasteData.reduce((acc, d) => acc + d.recycled, 0) },
  { name: 'Landfill', value: wasteData.reduce((acc, d) => acc + d.landfill, 0) },
];

const COLORS = ['#2d9e6b', '#D4A574'];

function CustomTooltip({ active, payload }: { active?: boolean; payload?: Array<{ value: number; name: string }> }) {
  const { theme } = useThemeStore();
  const isDark = theme === 'dark';

  if (active && payload && payload.length) {
    const total = data.reduce((acc, d) => acc + d.value, 0);
    const percentage = ((payload[0].value / total) * 100).toFixed(1);
    return (
      <div
        className="rounded-lg px-3 py-2 shadow-sm backdrop-blur border"
        style={{
          backgroundColor: isDark ? '#111e33' : '#ffffff',
          border: isDark ? '1px solid rgba(255,255,255,0.1)' : '1px solid #e2e8f0',
        }}
      >
        <p className="font-mono text-sm font-medium" style={{ color: '#2d9e6b' }}>
          {payload[0].value.toFixed(1)} tons ({percentage}%)
        </p>
        <p className="text-xs capitalize" style={{ color: isDark ? 'rgba(255,255,255,0.55)' : '#6b7c93' }}>
          {payload[0].name}
        </p>
      </div>
    );
  }
  return null;
}

export default function WasteDonutChart() {
  const { theme } = useThemeStore();
  const isDark = theme === 'dark';

  const total = data.reduce((acc, d) => acc + d.value, 0);
  const recycled = data[0].value;
  const rate = ((recycled / total) * 100).toFixed(1);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5, delay: 0.4 }}
      className={`rounded-xl shadow-sm p-5 ${
        isDark ? 'bg-[#111e33] border border-white/[0.08]' : 'bg-white border border-[#e2e8f0]'
      }`}
    >
      <div className="mb-4">
        <h3 className={`font-display text-lg ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>
          Waste Management
        </h3>
        <p className={`text-sm ${isDark ? 'text-white/55' : 'text-[#6b7c93]'}`}>
          Recycling vs. landfill diversion
        </p>
      </div>
      <div className="h-64 relative">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={90}
              paddingAngle={2}
              dataKey="value"
              animationDuration={1500}
            >
              {data.map((_, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index]} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
          </PieChart>
        </ResponsiveContainer>
        {/* Center text */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="text-center">
            <p className="text-3xl font-display" style={{ color: '#2d9e6b' }}>{rate}%</p>
            <p className="text-xs" style={{ color: isDark ? 'rgba(255,255,255,0.55)' : '#6b7c93' }}>Recycled</p>
          </div>
        </div>
      </div>
      {/* Legend */}
      <div className="flex justify-center gap-6 mt-2">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#2d9e6b' }} />
          <span className="text-xs" style={{ color: isDark ? 'rgba(255,255,255,0.55)' : '#6b7c93' }}>Recycled</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#D4A574' }} />
          <span className="text-xs" style={{ color: isDark ? 'rgba(255,255,255,0.55)' : '#6b7c93' }}>Landfill</span>
        </div>
      </div>
    </motion.div>
  );
}