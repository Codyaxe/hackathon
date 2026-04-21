import { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { Search, Copy, Check, MessageSquare } from 'lucide-react';
import AppLayout from '../components/layout/AppLayout';
import Input from '../components/ui/Input';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';
import { useThemeStore } from '../stores/themeStore';
import { getStoredCompanyProfile } from '../lib/companyProfile';
import { getResponseLibrary } from '../lib/workflowApi';
import { formatAiText } from '../lib/aiText';
import type { ResponseLibraryEntry } from '../types/workflow';

type LibraryTemplate = {
  id: string;
  title: string;
  category: string;
  content: string;
};

function toTemplate(entry: ResponseLibraryEntry): LibraryTemplate {
  const payload = entry.payload as {
    recommendation_summary?: string;
    one_page_summary?: string;
    ai_summary?: string;
    month?: string;
    change_summary?: string[];
  };

  if (entry.entry_type === 'onboarding') {
    return {
      id: entry.entry_id,
      title: 'Onboarding Recommendation',
      category: 'Onboarding',
      content: formatAiText(payload.recommendation_summary ?? JSON.stringify(entry.payload, null, 2)),
    };
  }

  if (entry.entry_type === 'plan') {
    return {
      id: entry.entry_id,
      title: 'Auto-generated ESG Plan',
      category: 'Plan',
      content: formatAiText(payload.one_page_summary ?? JSON.stringify(entry.payload, null, 2)),
    };
  }

  if (entry.entry_type === 'upload_extraction') {
    return {
      id: entry.entry_id,
      title: 'File Extraction Summary',
      category: 'Upload',
      content: formatAiText(payload.ai_summary ?? JSON.stringify(entry.payload, null, 2)),
    };
  }

  return {
    id: entry.entry_id,
    title: payload.month ? `Monthly Update ${payload.month}` : 'Monthly Update',
    category: 'Monthly',
    content: formatAiText(payload.change_summary?.join('\n') ?? JSON.stringify(entry.payload, null, 2)),
  };
}

const categories = ['All', 'Onboarding', 'Plan', 'Upload', 'Monthly'];

export default function ResponseLibrary() {
  const company = useMemo(() => getStoredCompanyProfile(), []);
  const [search, setSearch] = useState('');
  const [activeCategory, setActiveCategory] = useState('All');
  const [entries, setEntries] = useState<LibraryTemplate[]>([]);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const { theme } = useThemeStore();
  const isDark = theme === 'dark';

  useEffect(() => {
    const load = async () => {
      try {
        setIsLoading(true);
        setErrorMessage(null);
        const response = await getResponseLibrary(company.companyId, 100);
        setEntries(response.entries.map(toTemplate));
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : 'Could not load response library.');
      } finally {
        setIsLoading(false);
      }
    };

    void load();
  }, [company.companyId]);

  const filteredTemplates = entries.filter((t) => {
    const matchesSearch = t.title.toLowerCase().includes(search.toLowerCase()) ||
      t.content.toLowerCase().includes(search.toLowerCase());
    const matchesCategory = activeCategory === 'All' || t.category === activeCategory;
    return matchesSearch && matchesCategory;
  });

  const copyToClipboard = (id: string, content: string) => {
    navigator.clipboard.writeText(content);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const categoryColors: Record<string, 'sage' | 'sand' | 'forest' | 'slate'> = {
    Onboarding: 'sage',
    Plan: 'sand',
    Upload: 'forest',
    Monthly: 'slate',
  };

  return (
    <AppLayout title="Response Library" subtitle="Reusable ESG response templates">
      <div className="space-y-6">
        {/* Search and Filter */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col sm:flex-row gap-4"
        >
          <div className="flex-1">
            <Input
              placeholder="Search templates..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              icon={<Search className="w-4 h-4" />}
            />
          </div>
          <div className="flex gap-2">
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setActiveCategory(cat)}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                  activeCategory === cat
                    ? 'text-white'
                    : isDark
                      ? 'bg-[#111e33] text-white/55 hover:text-white border border-white/10'
                      : 'bg-white text-[#6b7c93] hover:text-[#1a2b3c] border border-[#e2e8f0]'
                }`}
                style={activeCategory === cat ? { background: 'linear-gradient(135deg, #2d9e6b 0%, #1B4332 100%)' } : undefined}
              >
                {cat}
              </button>
            ))}
          </div>
        </motion.div>

        {/* Templates */}
        {errorMessage && (
          <div className={`rounded-lg p-3 text-sm ${isDark ? 'bg-red-500/10 text-red-300' : 'bg-red-50 text-red-600'}`}>
            {errorMessage}
          </div>
        )}

        <div className="grid gap-4">
          {isLoading && (
            <Card>
              <p className={isDark ? 'text-white/55' : 'text-[#6b7c93]'}>Loading library entries...</p>
            </Card>
          )}

          {filteredTemplates.map((template, index) => (
            <motion.div
              key={template.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
            >
              <Card className="group">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <MessageSquare className="w-4 h-4" style={{ color: '#2d9e6b' }} />
                    <h4 className={`font-body font-medium ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>{template.title}</h4>
                    <Badge variant={categoryColors[template.category] ?? 'slate'} size="sm">
                      {template.category}
                    </Badge>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => copyToClipboard(template.id, template.content)}
                    icon={copiedId === template.id
                      ? <Check className="w-4 h-4" style={{ color: '#2d9e6b' }} />
                      : <Copy className="w-4 h-4" style={{ color: isDark ? 'rgba(255,255,255,0.4)' : '#6b7c93' }} />
                    }
                  >
                    {copiedId === template.id ? 'Copied' : 'Copy'}
                  </Button>
                </div>
                <p className={`text-sm leading-relaxed whitespace-pre-line ${isDark ? 'text-white/55' : 'text-[#6b7c93]'}`}>{template.content}</p>
              </Card>
            </motion.div>
          ))}
        </div>

        {filteredTemplates.length === 0 && (
          <div className="text-center py-12">
            <p className={isDark ? 'text-white/40' : 'text-[#6b7c93]'}>
              {isLoading ? 'Loading templates...' : 'No templates match your search.'}
            </p>
          </div>
        )}
      </div>
    </AppLayout>
  );
}