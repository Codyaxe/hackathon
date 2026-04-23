/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // ESG Theme tokens with dark/light variants
        // dark: prefix applies the 'dark' key value when dark mode is active
        'esg-bg': {
          DEFAULT: '#0a1628', // dark mode default (matches current dark theme)
          light: '#f4f6f9',
        },
        'esg-surface': {
          DEFAULT: '#0f2040',
          light: '#ffffff',
        },
        'esg-card': {
          DEFAULT: '#162d52',
          light: '#ffffff',
        },
        'esg-border': {
          DEFAULT: 'rgba(255,255,255,0.08)',
          light: '#e2e8f0',
        },
        'esg-sidebar': {
          DEFAULT: '#0f2040',
          light: '#ffffff',
        },
        'esg-text': {
          DEFAULT: '#ffffff',
          light: '#1a2b3c',
        },
        'esg-text-muted': {
          DEFAULT: 'rgba(255,255,255,0.55)',
          light: '#6b7c93',
        },
        'esg-accent': '#2d9e6b',
        sage: {
          DEFAULT: '#4A7C59',
          50: '#E8F0E9',
          100: '#D1E1D3',
          200: '#A3C3A7',
          300: '#75A57B',
          400: '#5A8F62',
          500: '#4A7C59',
          600: '#3B6347',
          700: '#2C4A35',
          800: '#1D3123',
          900: '#0E1811',
        },
        forest: {
          DEFAULT: '#1B4332',
          50: '#E3EBE7',
          100: '#C7D7CF',
          200: '#8FAFB9',
          300: '#57877A',
          400: '#3D6A5F',
          500: '#1B4332',
          600: '#163828',
          700: '#112D1E',
          800: '#0C2214',
          900: '#07170A',
        },
        moss: {
          DEFAULT: '#2D6A4F',
          50: '#E7F0ED',
          100: '#CFE1DB',
          200: '#9FC3B7',
          300: '#6FA593',
          400: '#4F8A72',
          500: '#2D6A4F',
          600: '#245540',
          700: '#1B4030',
          800: '#122B20',
          900: '#091610',
        },
        sand: {
          DEFAULT: '#D4A574',
          50: '#FCF5EE',
          100: '#F9EBDD',
          200: '#F3D7BB',
          300: '#EDC399',
          400: '#D4A574',
          500: '#BE8A5A',
          600: '#A87040',
          700: '#7A522C',
          800: '#4C341C',
          900: '#1E160C',
        },
        slate: {
          DEFAULT: '#1E293B',
          50: '#F1F5F9',
          100: '#E2E8F0',
          200: '#CBD5E1',
          300: '#94A3B8',
          400: '#64748B',
          500: '#475569',
          600: '#334155',
          700: '#1E293B',
          800: '#0F172A',
          900: '#020617',
        },
        charcoal: '#0F172A',
        cloud: '#F1F5F9',
      },
      fontFamily: {
        display: ['"DM Serif Display"', 'Georgia', 'serif'],
        body: ['"IBM Plex Sans"', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      backgroundImage: {
        'gradient-sage': 'linear-gradient(135deg, #4A7C59 0%, #2D6A4F 50%, #1B4332 100%)',
        'gradient-sand': 'linear-gradient(135deg, #D4A574 0%, #BE8A5A 100%)',
        'gradient-moss': 'linear-gradient(135deg, #2D6A4F 0%, #1B4332 100%)',
      },
      animation: {
        'gradient-shift': 'gradient-shift 8s ease infinite',
        'fade-in': 'fade-in 0.5s ease-out',
        'slide-up': 'slide-up 0.6s ease-out',
        'scale-in': 'scale-in 0.4s ease-out',
      },
      keyframes: {
        'gradient-shift': {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        'slide-up': {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'scale-in': {
          '0%': { opacity: '0', transform: 'scale(0.95)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
      },
      boxShadow: {
        'glass': '0 4px 30px rgba(0, 0, 0, 0.1)',
        'glass-sm': '0 2px 10px rgba(0, 0, 0, 0.08)',
        'glow-sage': '0 0 20px rgba(74, 124, 89, 0.3)',
        'glow-sand': '0 0 20px rgba(212, 165, 116, 0.3)',
      },
    },
  },
  plugins: [],
}