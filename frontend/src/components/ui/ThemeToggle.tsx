import { motion } from 'framer-motion';
import { Sun, Moon } from 'lucide-react';
import { useThemeStore } from '../../stores/themeStore';

export default function ThemeToggle() {
  const { theme, toggle } = useThemeStore();

  return (
    <motion.button
      onClick={toggle}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      className={`
        relative w-10 h-10 rounded-lg flex items-center justify-center
        transition-colors duration-200
        ${theme === 'dark'
          ? 'bg-[rgba(255,255,255,0.08)] hover:bg-[rgba(255,255,255,0.12)]'
          : 'bg-[#e8f5ee] hover:bg-[#d4f0df]'
        }
      `}
      aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
    >
      <motion.div
        initial={false}
        animate={{ rotate: theme === 'dark' ? 0 : 180 }}
        transition={{ type: 'spring', stiffness: 200, damping: 20 }}
        className="relative w-5 h-5"
      >
        {theme === 'dark' ? (
          <Moon className="w-5 h-5 text-white" />
        ) : (
          <Sun className="w-5 h-5 text-[#2d9e6b]" />
        )}
      </motion.div>
    </motion.button>
  );
}