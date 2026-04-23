import { forwardRef, type InputHTMLAttributes } from 'react';
import { useThemeStore } from '../../stores/themeStore';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  icon?: React.ReactNode;
}

const Input = forwardRef<HTMLInputElement, InputProps>(({
  label,
  error,
  icon,
  className = '',
  ...props
}, ref) => {
  const { theme } = useThemeStore();
  const isDark = theme === 'dark';

  return (
    <div className="w-full">
      {label && (
        <label className={`block text-sm font-medium mb-1.5 ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>
          {label}
        </label>
      )}
      <div className="relative">
        {icon && (
          <div className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: isDark ? 'rgba(255,255,255,0.4)' : '#9ca3af' }}>
            {icon}
          </div>
        )}
        <input
          ref={ref}
          className={`
            w-full border rounded-lg px-4 py-2.5 text-sm transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-[#2d9e6b]/40 focus:border-[#2d9e6b]
            ${isDark
              ? 'bg-[#0f2040] border-white/15 text-white placeholder:text-white/30'
              : 'bg-white border-[#e2e8f0] text-[#1a2b3c] placeholder:text-[#9ca3af]'
            }
            ${icon ? 'pl-10' : ''}
            ${error ? 'border-red-500 focus:ring-red-500/50 focus:border-red-500' : ''}
            ${className}
          `}
          {...props}
        />
      </div>
      {error && (
        <p className="mt-1 text-xs text-red-500">{error}</p>
      )}
    </div>
  );
});

Input.displayName = 'Input';

export default Input;