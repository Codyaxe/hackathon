import { type ReactNode } from 'react';

interface BadgeProps {
  children: ReactNode;
  variant?: 'sage' | 'sand' | 'forest' | 'slate';
  size?: 'sm' | 'md';
  className?: string;
}

const variantStyles = {
  sage: { bg: 'rgba(45, 158, 107, 0.12)', color: '#2d9e6b', border: 'rgba(45, 158, 107, 0.25)' },
  sand: { bg: 'rgba(212, 165, 116, 0.12)', color: '#D4A574', border: 'rgba(212, 165, 116, 0.25)' },
  forest: { bg: 'rgba(27, 67, 50, 0.12)', color: '#1B4332', border: 'rgba(27, 67, 50, 0.25)' },
  slate: { bg: '#e2e8f0', color: '#475569', border: '#cbd5e1' },
};

export default function Badge({ children, variant = 'sage', size = 'sm', className = '' }: BadgeProps) {
  const style = variantStyles[variant];

  return (
    <span
      className={`inline-flex items-center rounded-full font-body font-medium ${className}`}
      style={{
        backgroundColor: style.bg,
        color: style.color,
        border: `1px solid ${style.border}`,
        padding: size === 'sm' ? '2px 8px' : '4px 12px',
        fontSize: size === 'sm' ? '12px' : '14px',
      }}
    >
      {children}
    </span>
  );
}
