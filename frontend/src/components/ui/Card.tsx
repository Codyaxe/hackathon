import { motion } from 'framer-motion';
import { type ReactNode } from 'react';
import { useThemeStore } from '../../stores/themeStore';

interface CardProps {
  children: ReactNode;
  className?: string;
  hover?: boolean;
  onClick?: () => void;
}

export default function Card({ children, className = '', hover = false, onClick }: CardProps) {
  const { theme } = useThemeStore();
  const isDark = theme === 'dark';

  const cardContent = (
    <div className={`rounded-xl shadow-sm p-5 ${className} ${
      isDark
        ? 'bg-[#111e33] border border-white/[0.08]'
        : 'bg-white border border-[#e2e8f0]'
    }`}>
      {children}
    </div>
  );

  if (hover) {
    return (
      <motion.div
        whileHover={{ y: -4, transition: { type: 'spring', stiffness: 300, damping: 20 } }}
        className="cursor-pointer transition-shadow duration-300 hover:shadow-md"
        onClick={onClick}
      >
        {cardContent}
      </motion.div>
    );
  }

  return cardContent;
}