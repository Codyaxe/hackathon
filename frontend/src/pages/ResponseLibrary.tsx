import { useState } from 'react';
import { motion } from 'framer-motion';
import { Search, Copy, Check, MessageSquare } from 'lucide-react';
import AppLayout from '../components/layout/AppLayout';
import Input from '../components/ui/Input';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';
import { useThemeStore } from '../stores/themeStore';

const templates = [
  {
    id: '1',
    title: 'Carbon Reduction Commitment',
    category: 'Carbon',
    content: 'Our company is committed to reducing carbon emissions by 40% by 2030, baseline 2020. This includes investments in renewable energy, process optimization, and supply chain sustainability initiatives.',
  },
  {
    id: '2',
    title: 'Renewable Energy Statement',
    category: 'Energy',
    content: 'We source 85% of our operational energy from certified renewable sources, including solar and wind power. Our facilities are equipped with LED lighting and smart energy management systems.',
  },
  {
    id: '3',
    title: 'Waste Diversion Policy',
    category: 'Waste',
    content: 'Our zero-waste initiative has achieved 78% diversion rate from landfill. We partner with certified recycling facilities and have implemented comprehensive sorting and composting programs.',
  },
  {
    id: '4',
    title: 'ESG Reporting Cadence',
    category: 'Governance',
    content: 'We publish comprehensive ESG reports quarterly, with annual verification by independent third-party auditors. Our next report will be published in Q1 2025.',
  },
  {
    id: '5',
    title: 'Supply Chain Sustainability',
    category: 'Carbon',
    content: 'We require all suppliers with contracts exceeding $500K to complete our Supplier Sustainability Assessment. 92% of our top 50 suppliers have certified compliance.',
  },
];

const categories = ['All', 'Carbon', 'Energy', 'Waste', 'Governance'];

export default function ResponseLibrary() {
  const [search, setSearch] = useState('');
  const [activeCategory, setActiveCategory] = useState('All');
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const { theme } = useThemeStore();
  const isDark = theme === 'dark';

  const filteredTemplates = templates.filter(t => {
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
    Carbon: 'sage',
    Energy: 'sand',
    Waste: 'forest',
    Governance: 'slate',
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
        <div className="grid gap-4">
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
                    <Badge variant={categoryColors[template.category]} size="sm">
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
                <p className={`text-sm leading-relaxed ${isDark ? 'text-white/55' : 'text-[#6b7c93]'}`}>{template.content}</p>
              </Card>
            </motion.div>
          ))}
        </div>

        {filteredTemplates.length === 0 && (
          <div className="text-center py-12">
            <p className={isDark ? 'text-white/40' : 'text-[#6b7c93]'}>No templates match your search.</p>
          </div>
        )}
      </div>
    </AppLayout>
  );
}