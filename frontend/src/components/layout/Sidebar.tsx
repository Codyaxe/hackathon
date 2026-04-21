import { motion } from 'framer-motion';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  FileInput,
  Calendar,
  FileText,
  Library,
  Settings,
  Leaf,
} from 'lucide-react';
import { useThemeStore } from '../../stores/themeStore';

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/data-input', icon: FileInput, label: 'Data Input' },
  { to: '/monthly-checkup', icon: Calendar, label: 'Monthly Checkup' },
  { to: '/reports', icon: FileText, label: 'Reports' },
  { to: '/response-library', icon: Library, label: 'Response Library' },
];

const bottomItems = [
  { to: '/settings', icon: Settings, label: 'Settings' },
];

export default function Sidebar() {
  const { theme } = useThemeStore();
  const isDark = theme === 'dark';

  return (
    <motion.aside
      initial={{ x: -20, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      className={`w-64 h-screen backdrop-blur-md flex flex-col fixed left-0 top-0 ${
        isDark
          ? 'bg-[#0f1f35] border-r border-white/[0.06]'
          : 'bg-white border-r border-[#e2e8f0]'
      }`}
    >
      {/* Logo header */}
      <div className={`h-20 relative overflow-hidden flex items-center px-5 ${
        isDark ? 'border-b border-white/[0.06]' : 'border-b border-[#e2e8f0]'
      }`}>
        <div className="absolute inset-0 bg-gradient-to-br from-[#2d9e6b] to-[#1B4332] opacity-90" />
        <div className="relative flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#2d9e6b] to-[#1B4332] flex items-center justify-center shadow-md">
            <Leaf className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className={`font-display text-lg leading-tight ${isDark ? 'text-white font-bold' : 'text-[#1a2b3c] font-bold'}`}>
              ESG Hub
            </h1>
            <p className={`text-xs ${isDark ? 'text-white/50' : 'text-[#6b7c93]'}`}>
              Sustainability Tracker
            </p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-6 px-3 space-y-1">
        {navItems.map((item, index) => (
          <motion.div
            key={item.to}
            initial={{ x: -20, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ delay: index * 0.1 }}
          >
            <NavLink
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-2.5 rounded-lg transition-all duration-200 group ${
                  isActive
                    ? isDark
                      ? 'bg-[#1a3a5c] text-white'
                      : 'bg-[#e8f5ee] text-[#2d9e6b] font-semibold'
                    : isDark
                      ? 'text-white/50 hover:bg-white/5'
                      : 'text-[#6b7c93] hover:text-[#1a2b3c] hover:bg-[#f4f6f9]'
                }`
              }
            >
              <item.icon className="w-5 h-5 flex-shrink-0" />
              <span className="font-body text-sm font-medium">{item.label}</span>
            </NavLink>
          </motion.div>
        ))}
      </nav>

      {/* Bottom section */}
      <div className={`py-6 px-3 space-y-1 ${isDark ? 'border-t border-white/[0.06]' : 'border-t border-[#e2e8f0]'}`}>
        {bottomItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-2.5 rounded-lg transition-all duration-200 ${
                isActive
                  ? isDark
                    ? 'bg-[#1a3a5c] text-white'
                    : 'bg-[#e8f5ee] text-[#2d9e6b] font-semibold'
                  : isDark
                    ? 'text-white/50 hover:bg-white/5'
                    : 'text-[#6b7c93] hover:text-[#1a2b3c] hover:bg-[#f4f6f9]'
              }`
            }
          >
            <item.icon className="w-5 h-5 flex-shrink-0" />
            <span className="font-body text-sm font-medium">{item.label}</span>
          </NavLink>
        ))}
      </div>
    </motion.aside>
  );
}