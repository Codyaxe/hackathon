import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Building2, MapPin, Bell, Shield, Database, LogOut } from 'lucide-react';
import AppLayout from '../components/layout/AppLayout';
import Input from '../components/ui/Input';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import { company } from '../data/mock/esg-data';
import { useThemeStore } from '../stores/themeStore';

export default function Settings() {
  const navigate = useNavigate();
  const { theme } = useThemeStore();
  const isDark = theme === 'dark';

  const handleSignOut = () => {
    localStorage.removeItem('esg_auth');
    navigate('/login', { replace: true });
  };

  return (
    <AppLayout title="Settings" subtitle="Manage your account and preferences">
      <div className="max-w-3xl space-y-6">
        {/* Company Info */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <Card>
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #2d9e6b 0%, #1B4332 100%)' }}>
                <Building2 className="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 className={`font-display ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>Company Information</h3>
                <p className={`text-sm ${isDark ? 'text-white/55' : 'text-[#6b7c93]'}`}>Update your company details</p>
              </div>
            </div>

            <div className="space-y-4">
              <Input label="Company Name" defaultValue={company.name} />
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className={`block text-sm font-medium mb-1.5 ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>Industry</label>
                  <select className={`w-full border rounded-lg px-4 py-2.5 text-sm transition-all focus:outline-none focus:ring-2 focus:ring-[#2d9e6b]/40 focus:border-[#2d9e6b] ${
                    isDark
                      ? 'bg-[#0f2040] border-white/15 text-white'
                      : 'bg-white border-[#e2e8f0] text-[#1a2b3c]'
                  }`}>
                    <option>Manufacturing</option>
                    <option>Technology</option>
                    <option>Healthcare</option>
                    <option>Finance</option>
                    <option>Retail</option>
                  </select>
                </div>
                <Input label="Employee Count" defaultValue={company.employeeCount} />
              </div>
              <Input label="Location" defaultValue={company.location} icon={<MapPin className="w-4 h-4" />} />
            </div>
          </Card>
        </motion.div>

        {/* Notifications */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card>
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ backgroundColor: 'rgba(212, 165, 116, 0.2)' }}>
                <Bell className="w-5 h-5" style={{ color: '#D4A574' }} />
              </div>
              <div>
                <h3 className={`font-display ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>Notifications</h3>
                <p className={`text-sm ${isDark ? 'text-white/55' : 'text-[#6b7c93]'}`}>Configure your alerts and reminders</p>
              </div>
            </div>

            <div className="space-y-4">
              {[
                { label: 'Weekly summary email', checked: true },
                { label: 'Monthly report reminder', checked: true },
                { label: 'Data upload confirmation', checked: false },
                { label: 'ESG score changes', checked: true },
              ].map((item) => (
                <label key={item.label} className="flex items-center justify-between cursor-pointer group">
                  <span className={isDark ? 'text-white/55' : 'text-[#6b7c93]'}>{item.label}</span>
                  <div
                    className="relative w-11 h-6 rounded-full transition-colors cursor-pointer"
                    style={{ backgroundColor: item.checked ? '#2d9e6b' : isDark ? 'rgba(255,255,255,0.1)' : '#e2e8f0' }}
                  >
                    <div
                      className="absolute top-1 w-4 h-4 rounded-full bg-white transition-all"
                      style={{ left: item.checked ? '24px' : '4px' }}
                    />
                  </div>
                </label>
              ))}
            </div>
          </Card>
        </motion.div>

        {/* Data & Privacy */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card>
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ backgroundColor: 'rgba(45, 106, 79, 0.2)' }}>
                <Shield className="w-5 h-5" style={{ color: '#2D6A4F' }} />
              </div>
              <div>
                <h3 className={`font-display ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>Data & Privacy</h3>
                <p className={`text-sm ${isDark ? 'text-white/55' : 'text-[#6b7c93]'}`}>Manage your data and privacy settings</p>
              </div>
            </div>

            <div className="space-y-4">
              <Button variant="secondary" icon={<Database className="w-4 h-4" />}>
                Export All Data
              </Button>
              <p className={`text-xs ${isDark ? 'text-white/40' : 'text-[#6b7c93]'}`}>
                Download a complete copy of all your ESG data in CSV format.
              </p>
            </div>

            <div className={`mt-6 pt-6 ${isDark ? 'border-t border-white/10' : 'border-t border-[#e2e8f0]'}`}>
              <Button
                variant="danger"
                icon={<LogOut className="w-4 h-4" />}
                onClick={handleSignOut}
              >
                Sign Out
              </Button>
            </div>
          </Card>
        </motion.div>

        {/* Save Button */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="flex justify-end"
        >
          <Button>Save Changes</Button>
        </motion.div>
      </div>
    </AppLayout>
  );
}