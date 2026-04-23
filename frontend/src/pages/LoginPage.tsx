import { useState, useEffect, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Eye, EyeOff, Mail, Lock } from 'lucide-react';

import Input from '../components/ui/Input';
import { ensureCompanyProfile } from '../lib/companyProfile';
import { useThemeStore } from '../stores/themeStore';

const VALID_EMAIL = 'admin@apexmfg.com';
const VALID_PASSWORD = 'esg2024';

// Custom Aurora animated background
function AuroraBackground() {
  return (
    <div className="absolute inset-0 overflow-hidden">
      {/* Animated gradient orbs */}
      <div
        className="absolute top-0 left-0 w-full h-full"
        style={{
          background: 'linear-gradient(135deg, #0d2b1e 0%, #1a5c3a 50%, #0d2b1e 100%)',
        }}
      >
        {/* Orb 1 - large, slow moving */}
        <div
          style={{
            position: 'absolute',
            top: '10%',
            left: '20%',
            width: '500px',
            height: '500px',
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(45, 158, 107, 0.4) 0%, transparent 70%)',
            animation: 'orbFloat1 12s ease-in-out infinite',
            filter: 'blur(40px)',
          }}
        />
        {/* Orb 2 - medium */}
        <div
          style={{
            position: 'absolute',
            top: '40%',
            right: '10%',
            width: '400px',
            height: '400px',
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(45, 158, 107, 0.3) 0%, transparent 70%)',
            animation: 'orbFloat2 10s ease-in-out infinite',
            filter: 'blur(50px)',
          }}
        />
        {/* Orb 3 - small, fast */}
        <div
          style={{
            position: 'absolute',
            bottom: '20%',
            left: '30%',
            width: '350px',
            height: '350px',
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(27, 67, 50, 0.5) 0%, transparent 70%)',
            animation: 'orbFloat3 8s ease-in-out infinite',
            filter: 'blur(45px)',
          }}
        />
        {/* Subtle overlay */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: 'rgba(10, 22, 40, 0.55)',
          }}
        />
      </div>
      <style>{`
        @keyframes orbFloat1 {
          0%, 100% { transform: translate(0, 0) scale(1); }
          33% { transform: translate(50px, 30px) scale(1.1); }
          66% { transform: translate(-30px, 50px) scale(0.95); }
        }
        @keyframes orbFloat2 {
          0%, 100% { transform: translate(0, 0) scale(1); }
          50% { transform: translate(-40px, -30px) scale(1.05); }
        }
        @keyframes orbFloat3 {
          0%, 100% { transform: translate(0, 0) scale(1); }
          40% { transform: translate(30px, -40px) scale(1.08); }
          80% { transform: translate(-20px, 20px) scale(0.98); }
        }
      `}</style>
    </div>
  );
}

export default function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [shakeError, setShakeError] = useState(false);
  const { theme } = useThemeStore();
  const isDark = theme === 'dark';

  useEffect(() => {
    const isAuth = localStorage.getItem('esg_auth');
    if (isAuth === 'true') {
      navigate('/dashboard', { replace: true });
    }
  }, [navigate]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');

    if (!email || !password) {
      setError('Please enter both email and password');
      setShakeError(true);
      setTimeout(() => setShakeError(false), 500);
      return;
    }

    setIsLoading(true);

    await new Promise((resolve) => setTimeout(resolve, 800));

    if (email === VALID_EMAIL && password === VALID_PASSWORD) {
      localStorage.setItem('esg_auth', 'true');
      ensureCompanyProfile();
      navigate('/dashboard', { replace: true });
    } else {
      setError('Invalid email or password');
      setIsLoading(false);
      setShakeError(true);
      setTimeout(() => setShakeError(false), 500);
    }
  };

  return (
    <div className="min-h-screen flex" style={{ backgroundColor: isDark ? '#0a1628' : '#f4f6f9' }}>
      {/* Left Side - Dark Green Animated Background (always dark) */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden">
        <AuroraBackground />
        <div className="relative z-10 flex flex-col items-center justify-center w-full p-12">
          <motion.div
            initial={{ opacity: 0, y: 32 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
            className="text-center"
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.1, duration: 0.5 }}
            >
              <div
                className="w-20 h-20 rounded-2xl flex items-center justify-center mx-auto mb-6"
                style={{
                  background: 'linear-gradient(135deg, #2d9e6b 0%, #1B4332 100%)',
                  boxShadow: '0 8px 32px rgba(45, 158, 107, 0.4)',
                }}
              >
                <span className="text-white font-display text-3xl">E</span>
              </div>
            </motion.div>
            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2, duration: 0.5 }}
              className="font-display text-5xl text-white mb-4"
            >
              Esverdant
            </motion.h1>
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3 }}
              className="text-white/70 text-lg"
            >
              Sustainability tracking for a better tomorrow
            </motion.p>
          </motion.div>
        </div>
      </div>

      {/* Right Side - Form (Dark or Light mode) */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 md:p-12">
        <motion.div
          initial={{ opacity: 0, y: 32 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
          className="w-full max-w-md"
        >
          <motion.div
            className={`rounded-2xl shadow-lg p-8 ${
              isDark
                ? 'bg-[#1a2535] border border-white/10'
                : 'bg-white border border-[#e2e8f0] shadow-lg'
            }`}
            animate={shakeError ? { x: [-8, 8, -6, 6, -4, 4, 0] } : {}}
            transition={{ duration: 0.4 }}
          >
            <div className="text-center mb-8 lg:hidden">
              <h2 className={`font-display text-2xl mb-1 ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>
                Welcome Back
              </h2>
              <p className={`text-sm ${isDark ? 'text-white/55' : 'text-[#6b7c93]'}`}>
                Sign in to continue
              </p>
            </div>

            <AnimatePresence>
              {error && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="mb-4 p-3 rounded-lg text-sm"
                  style={{
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    border: '1px solid rgba(239, 68, 68, 0.3)',
                    color: '#ef4444',
                  }}
                >
                  {error}
                </motion.div>
              )}
            </AnimatePresence>

            <form onSubmit={handleSubmit} className="space-y-5">
              <Input
                type="email"
                label="Email"
                placeholder="Enter your email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                icon={<Mail className="w-5 h-5" />}
                autoComplete="email"
              />

              <div className="relative">
                <Input
                  type={showPassword ? 'text' : 'password'}
                  label="Password"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  icon={<Lock className="w-5 h-5" />}
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-[38px] transition-colors"
                  style={{ color: isDark ? 'rgba(255,255,255,0.4)' : '#9ca3af' }}
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>

              <div className="flex items-center justify-between">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="w-4 h-4 rounded"
                    style={{ accentColor: '#2d9e6b' }}
                  />
                  <span className={`text-sm ${isDark ? 'text-white/55' : 'text-[#6b7c93]'}`}>
                    Remember me
                  </span>
                </label>
                <a
                  href="#"
                  className="text-sm transition-colors hover:opacity-80"
                  style={{ color: '#2d9e6b' }}
                >
                  Forgot password?
                </a>
              </div>

              <motion.button
                type="submit"
                className="w-full py-3 rounded-lg text-white font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-[#2d9e6b]/50 focus:ring-offset-2"
                style={{
                  background: 'linear-gradient(135deg, #2d9e6b 0%, #1B4332 100%)',
                }}
                whileHover={{ scale: isLoading ? 1 : 1.02 }}
                whileTap={{ scale: isLoading ? 1 : 0.98 }}
                disabled={isLoading}
              >
                {isLoading ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Signing in...
                  </span>
                ) : (
                  'Sign In'
                )}
              </motion.button>
            </form>

            <div
              className="mt-6 p-4 rounded-lg text-center"
              style={{
                backgroundColor: isDark ? 'rgba(255,255,255,0.05)' : '#f4f6f9',
                border: isDark ? '1px solid rgba(255,255,255,0.08)' : '1px solid #e2e8f0',
              }}
            >
              <p className={`text-xs ${isDark ? 'text-white/40' : 'text-[#6b7c93]'}`}>
                Demo credentials: <span style={{ color: '#2d9e6b' }}>admin@apexmfg.com</span> / <span style={{ color: '#2d9e6b' }}>esg2024</span>
              </p>
            </div>
          </motion.div>
        </motion.div>
      </div>
    </div>
  );
}