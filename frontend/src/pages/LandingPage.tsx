import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Upload, FileText, Download, BarChart3, ArrowRight } from 'lucide-react';

import ThemeToggle from '../components/ui/ThemeToggle';
import { totalEnergy, totalCarbon, recyclingRate } from '../data/mock/esg-data';

const features = [
  { icon: Upload, title: 'Upload Data', desc: 'Import energy bills and sustainability reports automatically' },
  { icon: FileText, title: 'Generate Reports', desc: 'Create comprehensive ESG reports in minutes' },
  { icon: Download, title: 'Export Data', desc: 'Download reports in multiple formats for stakeholders' },
  { icon: BarChart3, title: 'View Analytics', desc: 'Track progress with interactive charts and dashboards' },
];

const statItems = [
  { value: totalEnergy, unit: 'kWh', label: 'Energy Tracked' },
  { value: totalCarbon.toFixed(1), unit: 'tons', label: 'CO₂ Reduced' },
  { value: `${recyclingRate.toFixed(1)}%`, unit: '', label: 'Recycling Rate' },
];

const dashboardKPIs = [
  { label: 'Total Energy', value: `${totalEnergy.toLocaleString()} kWh`, color: 'text-sage' },
  { label: 'Carbon Emissions', value: `${totalCarbon.toFixed(1)} tons CO₂e`, color: 'text-sand' },
  { label: 'Recycling Rate', value: `${recyclingRate.toFixed(1)}%`, color: 'text-moss' },
  { label: 'ESG Score', value: '87.5/100', color: 'text-sage' },
];

export default function LandingPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-charcoal text-cloud overflow-x-hidden">
      {/* Navbar */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-charcoal/80 backdrop-blur-md border-b border-slate-700/50 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6 }}
            className="flex items-center gap-3"
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-sage flex items-center justify-center">
              <span className="text-cloud font-display text-lg">E</span>
            </div>
            <span className="font-display text-lg text-cloud">ESG Hub</span>
          </motion.div>
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <ThemeToggle />
          </motion.div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
        {/* Background gradient */}
        <div className="absolute inset-0 bg-gradient-to-br from-forest/20 via-charcoal to-charcoal" />
        <div className="absolute inset-0 opacity-30">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-sage/20 rounded-full blur-3xl" />
          <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-moss/20 rounded-full blur-3xl" />
        </div>

        <div className="relative z-10 text-center px-6 max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.1 }}
          >
            <h1 className="font-display text-4xl md:text-6xl lg:text-7xl text-cloud mb-6 leading-tight">
              Sustainability Tracking for{' '}
              <span className="bg-gradient-sage bg-clip-text text-transparent">Modern Manufacturers</span>
            </h1>
          </motion.div>
          <motion.p
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.3 }}
            className="font-body text-lg md:text-xl text-cloud/70 mb-10 max-w-2xl mx-auto"
          >
            Track energy, carbon, and waste. Generate ESG reports in minutes.
            Empower your team with real-time sustainability insights.
          </motion.p>
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.5 }}
            className="flex flex-col sm:flex-row gap-4 justify-center"
          >
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => navigate('/login')}
              className="inline-flex items-center gap-2 px-8 py-4 bg-gradient-sage text-cloud font-body font-medium rounded-lg shadow-glow-sage/30 hover:shadow-glow-sage transition-shadow duration-300"
            >
              Get Started
              <ArrowRight className="w-5 h-5" />
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => navigate('/dashboard')}
              className="inline-flex items-center gap-2 px-8 py-4 bg-slate-800/50 backdrop-blur-sm text-cloud font-body font-medium rounded-lg border border-slate-700/50 hover:bg-slate-700/50 transition-colors duration-200"
            >
              View Demo
            </motion.button>
          </motion.div>
        </div>

        {/* Scroll indicator */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.2, duration: 0.6 }}
          className="absolute bottom-8 left-1/2 -translate-x-1/2"
        >
          <div className="w-6 h-10 border-2 border-cloud/30 rounded-full flex items-start justify-center p-2">
            <motion.div
              animate={{ y: [0, 12, 0] }}
              transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut' }}
              className="w-1.5 h-1.5 bg-cloud/50 rounded-full"
            />
          </div>
        </motion.div>
      </section>

      {/* Stats Bar */}
      <section className="bg-slate-800/30 backdrop-blur-sm border-y border-slate-700/30 py-16">
        <div className="max-w-6xl mx-auto px-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {statItems.map((stat, index) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                className="text-center"
              >
                <div className="font-mono text-4xl md:text-5xl font-semibold text-sage mb-2">
                  {typeof stat.value === 'number' ? (
                    <span>{stat.value.toLocaleString()}</span>
                  ) : (
                    <span>{stat.value}</span>
                  )}
                  {stat.unit && <span className="text-cloud/50 text-xl ml-1">{stat.unit}</span>}
                </div>
                <p className="text-cloud/60 font-body">{stat.label}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="font-display text-3xl md:text-4xl text-cloud mb-4">
              Everything You Need for ESG Tracking
            </h2>
            <p className="text-cloud/60 font-body text-lg max-w-2xl mx-auto">
              Streamline your sustainability reporting with powerful tools designed for modern manufacturers.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
              >
                <div className="group h-full p-6 bg-slate-800/30 backdrop-blur-sm border border-slate-700/30 rounded-xl hover:border-sage/30 transition-all duration-300 hover:shadow-glow-sage/10">
                  <div className="w-12 h-12 rounded-lg bg-gradient-sage flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300">
                    <feature.icon className="w-6 h-6 text-cloud" />
                  </div>
                  <h3 className="font-display text-xl text-cloud mb-2">{feature.title}</h3>
                  <p className="text-cloud/60 text-sm font-body">{feature.desc}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Dashboard Preview */}
      <section className="py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-12"
          >
            <h2 className="font-display text-3xl md:text-4xl text-cloud mb-4">
              See It In Action
            </h2>
            <p className="text-cloud/60 font-body text-lg">
              A glimpse of what your sustainability dashboard looks like.
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.98 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="bg-slate-800/40 backdrop-blur-sm border border-slate-700/40 rounded-2xl p-8 shadow-glass"
          >
            <div className="flex items-center gap-3 mb-6">
              <div className="w-3 h-3 rounded-full bg-red-500/80" />
              <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
              <div className="w-3 h-3 rounded-full bg-green-500/80" />
            </div>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              {dashboardKPIs.map((kpi) => (
                <div
                  key={kpi.label}
                  className="bg-slate-900/50 rounded-lg p-4 border border-slate-700/30"
                >
                  <p className="text-cloud/50 text-xs font-body mb-1 uppercase tracking-wider">
                    {kpi.label}
                  </p>
                  <p className={`font-mono text-lg font-semibold ${kpi.color}`}>{kpi.value}</p>
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      </section>

      {/* CTA Banner */}
      <section className="relative py-24 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-forest/30 via-moss/20 to-forest/30" />
        <div className="absolute inset-0 bg-charcoal/60" />

        <div className="relative z-10 max-w-3xl mx-auto text-center px-6">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="font-display text-3xl md:text-5xl text-cloud mb-6"
          >
            Ready to track your ESG performance?
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
            className="text-cloud/70 font-body text-lg mb-8"
          >
            Join Apex Manufacturing and hundreds of other companies making sustainability simple.
          </motion.p>
          <motion.button
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => navigate('/login')}
            className="inline-flex items-center gap-2 px-8 py-4 bg-cloud text-charcoal font-body font-semibold rounded-lg hover:bg-cloud/90 transition-colors"
          >
            Get Started Free
            <ArrowRight className="w-5 h-5" />
          </motion.button>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-800/40 backdrop-blur-sm border-t border-slate-700/30 py-12 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col md:flex-row items-center justify-between gap-8">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-sage flex items-center justify-center">
                <span className="text-cloud font-display text-lg">E</span>
              </div>
              <div>
                <h3 className="font-display text-lg text-cloud">ESG Hub</h3>
                <p className="text-cloud/50 text-sm font-body">Sustainability Made Simple</p>
              </div>
            </div>

            <nav className="flex gap-8 text-sm font-body">
              <a
                href="/dashboard"
                className="text-cloud/60 hover:text-sage transition-colors"
              >
                Dashboard
              </a>
              <a
                href="/login"
                className="text-cloud/60 hover:text-sage transition-colors"
              >
                Login
              </a>
              <a
                href="/reports"
                className="text-cloud/60 hover:text-sage transition-colors"
              >
                Reports
              </a>
            </nav>

            <p className="text-sm text-cloud/40 font-body">
              © 2024 Apex Manufacturing Co.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}