import { motion } from 'framer-motion';
import { Bell, Search, User } from 'lucide-react';
import { company } from '../../data/mock/esg-data';
import { useThemeStore } from '../../stores/themeStore';
import ThemeToggle from '../ui/ThemeToggle';

interface TopbarProps {
  title: string;
  subtitle?: string;
}

export default function Topbar({ title, subtitle }: TopbarProps) {
  const { theme } = useThemeStore();
  const isDark = theme === 'dark';

  return (
    <motion.header
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      className={`
        h-20 backdrop-blur-md flex items-center justify-between px-6 sticky top-0 z-10
        ${isDark
          ? 'bg-[#0f2040] border-b border-white/[0.08]'
          : 'bg-white border-b border-[#e2e8f0] shadow-sm'
        }
      `}
    >
      <div>
        <h2 className={`font-display text-xl ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>
          {title}
        </h2>
        {subtitle && (
          <p className={`text-sm mt-0.5 ${isDark ? 'text-white/55' : 'text-[#6b7c93]'}`}>
            {subtitle}
          </p>
        )}
      </div>

      <div className="flex items-center gap-4">
        {/* Search */}
        <div className="relative hidden md:block">
          <Search className={`absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 ${isDark ? 'text-white/30' : 'text-[#9ca3af]'}`} />
          <input
            type="text"
            placeholder="Search..."
            className={`
              w-64 border rounded-lg pl-10 pr-4 py-2 text-sm transition-all focus:outline-none focus:ring-2 focus:ring-[#2d9e6b]/40 focus:border-[#2d9e6b]
              ${isDark
                ? 'bg-white/8 border-white/10 text-white placeholder-white/30'
                : 'bg-[#f4f6f9] border-[#e2e8f0] text-[#1a2b3c] placeholder:text-[#9ca3af]'
              }
            `}
          />
        </div>

        {/* Theme Toggle */}
        <ThemeToggle />

        {/* Notifications */}
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className={`relative w-10 h-10 rounded-lg flex items-center justify-center transition-all ${
            isDark
              ? 'text-white/60 hover:bg-white/5'
              : 'text-[#6b7c93] hover:bg-[#f4f6f9]'
          }`}
        >
          <Bell className="w-5 h-5" />
          <span className="absolute top-2 right-2 w-2 h-2 bg-[#D4A574] rounded-full" />
        </motion.button>

        {/* Company Badge */}
        <div className={`hidden lg:flex items-center gap-3 ${isDark ? 'pl-4 border-l border-white/10' : 'pl-4 border-l border-[#e2e8f0]'}`}>
          <div className="text-right">
            <p className={`text-sm font-medium ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>
              {company.name}
            </p>
            <p className={`text-xs ${isDark ? 'text-white/55' : 'text-[#6b7c93]'}`}>
              {company.industry}
            </p>
          </div>
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#2d9e6b] to-[#1B4332] flex items-center justify-center">
            <User className="w-5 h-5 text-white" />
          </div>
        </div>
      </div>
    </motion.header>
  );
}