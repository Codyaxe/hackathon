import { motion } from 'framer-motion';
import { forwardRef, type ReactNode, type MouseEventHandler } from 'react';
import { Loader2 } from 'lucide-react';

interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  icon?: ReactNode;
  children?: ReactNode;
  className?: string;
  disabled?: boolean;
  type?: 'button' | 'submit' | 'reset';
  onClick?: MouseEventHandler<HTMLButtonElement>;
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(({
  variant = 'primary',
  size = 'md',
  loading = false,
  icon,
  children,
  className = '',
  disabled,
  type = 'button',
  onClick,
}, ref) => {
  const baseStyles = 'inline-flex items-center justify-center font-body font-medium rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-[#2d9e6b]/50 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed';

  const variants = {
    primary: 'text-white hover:opacity-90 active:scale-[0.98]',
    secondary: 'text-[#1a2b3c] hover:bg-gray-100 active:scale-[0.98] border border-[#e2e8f0] bg-white',
    ghost: 'text-[#6b7c93] hover:text-[#1a2b3c] hover:bg-gray-100',
    danger: 'bg-red-600/90 text-white hover:bg-red-600 active:scale-[0.98]',
    outline: 'text-[#2d9e6b] hover:bg-[#f0faf5] active:scale-[0.98] border border-[#2d9e6b] bg-transparent',
  };

  const sizes = {
    sm: 'px-3 py-1.5 text-sm gap-1.5',
    md: 'px-4 py-2 text-sm gap-2',
    lg: 'px-6 py-3 text-base gap-2',
  };

  const getBackground = () => {
    if (variant === 'primary') return 'linear-gradient(135deg, #2d9e6b 0%, #1B4332 100%)';
    if (variant === 'danger') return '#dc2626';
    return undefined;
  };

  return (
    <motion.button
      ref={ref}
      whileHover={{ scale: disabled || loading ? 1 : 1.02 }}
      whileTap={{ scale: disabled || loading ? 1 : 0.98 }}
      className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
      disabled={disabled || loading}
      type={type}
      onClick={onClick}
      style={variant === 'primary' || variant === 'danger' ? { background: getBackground() } : undefined}
    >
      {loading ? (
        <Loader2 className="w-4 h-4 animate-spin" />
      ) : icon ? (
        <span className="flex-shrink-0">{icon}</span>
      ) : null}
      {children}
    </motion.button>
  );
});

Button.displayName = 'Button';

export default Button;
