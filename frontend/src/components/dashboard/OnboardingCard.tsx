import { motion } from 'framer-motion';
import { Sparkles, ArrowRight, BookOpen, X } from 'lucide-react';
import Button from '../ui/Button';
import { useThemeStore } from '../../stores/themeStore';

interface OnboardingCardProps {
  onDismiss?: () => void;
}

export default function OnboardingCard({ onDismiss }: OnboardingCardProps) {
  const { theme } = useThemeStore();
  const isDark = theme === 'dark';

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5 }}
      className={`rounded-xl shadow-sm p-6 relative overflow-hidden ${
        isDark
          ? 'bg-[#0d2540] border border-white/[0.08]'
          : 'bg-[#f0faf5] border border-[#c6e8d5]'
      }`}
    >
      {/* Background decoration */}
      <div
        className="absolute top-0 right-0 w-32 h-32 rounded-full blur-3xl transform translate-x-16 -translate-y-16"
        style={{ background: 'linear-gradient(135deg, #2d9e6b 0%, #1B4332 100%)', opacity: 0.1 }}
      />

      {/* Close button */}
      {onDismiss && (
        <button
          onClick={onDismiss}
          className={`absolute top-4 right-4 w-8 h-8 rounded-lg flex items-center justify-center transition-colors border ${
            isDark
              ? 'bg-white/5 hover:bg-white/10 border-white/10'
              : 'bg-white hover:bg-gray-100 border-[#e2e8f0]'
          }`}
          aria-label="Dismiss welcome card"
        >
          <X className="w-4 h-4" style={{ color: isDark ? 'rgba(255,255,255,0.55)' : '#6b7c93' }} />
        </button>
      )}

      <div className="relative flex items-start gap-4">
        <div
          className="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0"
          style={{ background: 'linear-gradient(135deg, #2d9e6b 0%, #1B4332 100%)', boxShadow: '0 4px 14px rgba(45, 158, 107, 0.3)' }}
        >
          <Sparkles className="w-6 h-6 text-white" />
        </div>
        <div className="flex-1">
          <h3 className={`font-display text-lg mb-1 ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>
            Welcome to ESG Hub
          </h3>
          <p className={`text-sm mb-4 max-w-lg ${isDark ? 'text-white/55' : 'text-[#6b7c93]'}`}>
            Track your company&apos;s environmental impact, carbon footprint, and sustainability progress.
            Start by uploading your energy bills, fuel invoices, or expense reports.
          </p>
          <div className="flex flex-wrap gap-3">
            <Button icon={<ArrowRight className="w-4 h-4" />}>
              Get Started
            </Button>
            <Button variant="outline" icon={<BookOpen className="w-4 h-4" />}>
              View Guide
            </Button>
          </div>
        </div>
      </div>
    </motion.div>
  );
}