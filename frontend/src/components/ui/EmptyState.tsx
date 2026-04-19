import { FileX } from 'lucide-react';
import Button from './Button';
import { useThemeStore } from '../../stores/themeStore';

interface EmptyStateProps {
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export default function EmptyState({ title, description, action }: EmptyStateProps) {
  const { theme } = useThemeStore();
  const isDark = theme === 'dark';

  return (
    <div className="flex flex-col items-center justify-center py-12 px-6 text-center">
      <div className={`w-16 h-16 rounded-full flex items-center justify-center mb-4 ${
        isDark ? 'bg-white/5' : 'bg-white border border-[#e2e8f0]'
      }`}>
        <FileX className="w-8 h-8" style={{ color: isDark ? 'rgba(255,255,255,0.4)' : '#9ca3af' }} />
      </div>
      <h3 className={`text-lg font-display mb-2 ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>{title}</h3>
      {description && (
        <p className={`text-sm max-w-sm mb-4 ${isDark ? 'text-white/55' : 'text-[#6b7c93]'}`}>{description}</p>
      )}
      {action && (
        <Button variant="secondary" onClick={action.onClick}>
          {action.label}
        </Button>
      )}
    </div>
  );
}