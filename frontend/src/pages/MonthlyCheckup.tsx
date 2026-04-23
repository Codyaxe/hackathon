import { useEffect, useMemo, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { Upload } from 'lucide-react';

import AppLayout from '../components/layout/AppLayout';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import Card from '../components/ui/Card';
import { useThemeStore } from '../stores/themeStore';
import { getStoredCompanyProfile } from '../lib/companyProfile';
import { formatAiText } from '../lib/aiText';
import {
  getQuickWins,
  getResponseLibrary,
  submitMonthlyUpdate,
  submitMonthlyUpdateWithFiles,
} from '../lib/workflowApi';
import type {
  MonthlyUpdateResponse,
} from '../types/workflow';

function getDefaultMonth(): string {
  return new Date().toISOString().slice(0, 7);
}

function getPreviousMonth(month: string): string {
  const [yearString, monthString] = month.split('-');
  const year = Number(yearString);
  const monthIndex = Number(monthString);
  if (!Number.isFinite(year) || !Number.isFinite(monthIndex) || monthIndex < 1 || monthIndex > 12) {
    return getDefaultMonth();
  }

  if (monthIndex === 1) {
    return `${year - 1}-12`;
  }

  return `${year}-${String(monthIndex - 1).padStart(2, '0')}`;
}

export default function MonthlyCheckup() {
  const profile = useMemo(() => getStoredCompanyProfile(), []);
  const monthlyFileInputRef = useRef<HTMLInputElement>(null);

  const [month, setMonth] = useState(getDefaultMonth());
  const [q1UnusualChanges, setQ1UnusualChanges] = useState<boolean | null>(null);
  const [q1Details, setQ1Details] = useState('');
  const [q2SafetyIssues, setQ2SafetyIssues] = useState<boolean | null>(null);
  const [q2Details, setQ2Details] = useState('');
  const [quickWinOptions, setQuickWinOptions] = useState<string[]>([]);
  const [selectedQuickWins, setSelectedQuickWins] = useState<string[]>([]);
  const [isLoadingQuickWins, setIsLoadingQuickWins] = useState(false);
  const [monthlyNotes, setMonthlyNotes] = useState('');
  const [isSubmittingMonthly, setIsSubmittingMonthly] = useState(false);
  const [monthlyError, setMonthlyError] = useState<string | null>(null);
  const [monthlyResult, setMonthlyResult] = useState<MonthlyUpdateResponse | null>(null);
  const [monthlyFiles, setMonthlyFiles] = useState<File[]>([]);

  const { theme } = useThemeStore();
  const isDark = theme === 'dark';
  const naQuickWinLabel = 'N/A - No Quick Wins generated yet';

  const loadQuickWins = async () => {
    try {
      setIsLoadingQuickWins(true);
      setMonthlyError(null);

      const previousMonth = getPreviousMonth(month);
      const library = await getResponseLibrary(profile.companyId, 100);
      const previousMonthlyEntry = library.entries
        .filter((entry) => entry.entry_type === 'monthly_update')
        .find((entry) => {
          if (!entry.payload || typeof entry.payload !== 'object') {
            return false;
          }
          const payload = entry.payload as Record<string, unknown>;
          return payload.month === previousMonth;
        });

      const storedSnapshot = previousMonthlyEntry && typeof previousMonthlyEntry.payload === 'object'
        ? (previousMonthlyEntry.payload as Record<string, unknown>).generated_quick_wins_snapshot
        : undefined;

      if (Array.isArray(storedSnapshot) && storedSnapshot.every((item) => typeof item === 'string')) {
        setQuickWinOptions(storedSnapshot);
      } else {
        const response = await getQuickWins(profile.companyId);
        setQuickWinOptions(response.quick_wins.map((item) => item.title));
      }

      setSelectedQuickWins([]);
    } catch (error) {
      setMonthlyError(error instanceof Error ? error.message : 'Could not load Quick Wins.');
      setQuickWinOptions([]);
    } finally {
      setIsLoadingQuickWins(false);
    }
  };

  useEffect(() => {
    const timerId = window.setTimeout(() => {
      void loadQuickWins();
    }, 0);
    return () => window.clearTimeout(timerId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [month]);

  const toggleQuickWinSelection = (option: string) => {
    setSelectedQuickWins((prev) => {
      if (option === naQuickWinLabel) {
        return prev.includes(naQuickWinLabel) ? [] : [naQuickWinLabel];
      }

      const withoutNA = prev.filter((item) => item !== naQuickWinLabel);
      if (withoutNA.includes(option)) {
        return withoutNA.filter((item) => item !== option);
      }
      return [...withoutNA, option];
    });
  };

  const submitMonthly = async () => {
    if (q1UnusualChanges === null || q2SafetyIssues === null) {
      setMonthlyError('Please answer all required Yes/No questions.');
      return;
    }

    if (q1UnusualChanges && !q1Details.trim()) {
      setMonthlyError('Please add one line for unusual changes this month.');
      return;
    }

    if (q2SafetyIssues && !q2Details.trim()) {
      setMonthlyError('Please add one line for safety or workforce issues.');
      return;
    }

    if (selectedQuickWins.length === 0) {
      setMonthlyError('Please select the Quick Wins you acted on, or choose N/A.');
      return;
    }

    try {
      setIsSubmittingMonthly(true);
      setMonthlyError(null);
      const actedQuickWins = selectedQuickWins.filter((item) => item !== naQuickWinLabel);
      const payload = {
        company_id: profile.companyId,
        month,
        changes: {
          unusual_changes_this_month: q1UnusualChanges ? 'yes' : 'no',
          unusual_changes_details: q1UnusualChanges ? q1Details.trim() : 'none',
          safety_or_workforce_issues: q2SafetyIssues ? 'yes' : 'no',
          safety_or_workforce_details: q2SafetyIssues ? q2Details.trim() : 'none',
          quick_wins_acted_on: actedQuickWins,
          quick_wins_na_selected: selectedQuickWins.includes(naQuickWinLabel),
        },
        notes: monthlyNotes || undefined,
      };
      const response = monthlyFiles.length > 0
        ? await submitMonthlyUpdateWithFiles(payload, monthlyFiles)
        : await submitMonthlyUpdate(payload);
      setMonthlyResult(response);
    } catch (error) {
      setMonthlyError(error instanceof Error ? error.message : 'Could not submit monthly update.');
    } finally {
      setIsSubmittingMonthly(false);
    }
  };

  return (
    <AppLayout title="Monthly Checkup" subtitle="A 3-step monthly update that takes around 11 minutes">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-3xl"
      >
        <Card className="space-y-6">
          <h3 className={`font-display text-lg ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>Monthly Checkup Flow</h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="Month"
              type="month"
              value={month}
              onChange={(event) => setMonth(event.target.value)}
            />
          </div>

          <div className={`rounded-xl p-4 border ${isDark ? 'bg-white/[0.02] border-white/10' : 'bg-[#f8fafc] border-[#e2e8f0]'}`}>
            <p className={`font-semibold ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>STEP 1 - Upload (5 mins)</p>
            <p className={`mt-2 text-sm ${isDark ? 'text-white/70' : 'text-[#3a4d63]'}`}>Drop your bills and receipts.</p>
            <p className={`text-sm ${isDark ? 'text-white/70' : 'text-[#3a4d63]'}`}>Electricity, fuel, waste invoices.</p>
            <p className={`text-sm ${isDark ? 'text-white/70' : 'text-[#3a4d63]'}`}>Same as last month? Just upload again.</p>

            <div className="mt-3 flex flex-wrap items-center gap-2">
              <Button
                variant="secondary"
                icon={<Upload className="w-4 h-4" />}
                onClick={() => monthlyFileInputRef.current?.click()}
              >
                Add Files
              </Button>
              <input
                ref={monthlyFileInputRef}
                type="file"
                multiple
                className="hidden"
                accept=".pdf,.jpg,.jpeg,.png,.webp,.csv,.xlsx,.xls"
                onChange={(event) => setMonthlyFiles(Array.from(event.target.files ?? []))}
              />
              {monthlyFiles.length > 0 && (
                <span className={`text-xs ${isDark ? 'text-white/55' : 'text-[#6b7c93]'}`}>
                  {monthlyFiles.length} file(s) selected
                </span>
              )}
            </div>
          </div>

          <div className={`rounded-xl p-4 border space-y-5 ${isDark ? 'bg-white/[0.02] border-white/10' : 'bg-[#f8fafc] border-[#e2e8f0]'}`}>
            <p className={`font-semibold ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>STEP 2 - 3 Quick Questions (5 mins)</p>

            <div>
              <p className={`text-sm font-medium ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>
                1. Any unusual changes this month?
              </p>
              <p className={`text-xs ${isDark ? 'text-white/55' : 'text-[#6b7c93]'}`}>
                (power outage, extra deliveries, big waste disposal)
              </p>
              <div className="mt-2 flex gap-2">
                {[true, false].map((option) => (
                  <button
                    key={`q1-${String(option)}`}
                    type="button"
                    onClick={() => setQ1UnusualChanges(option)}
                    className={`px-3 py-1.5 rounded-md text-xs border ${
                      q1UnusualChanges === option
                        ? 'text-white border-transparent'
                        : isDark
                          ? 'text-white/60 border-white/20'
                          : 'text-[#6b7c93] border-[#d4dde8]'
                    }`}
                    style={q1UnusualChanges === option ? { background: 'linear-gradient(135deg, #2d9e6b 0%, #1B4332 100%)' } : undefined}
                  >
                    {option ? 'Yes' : 'No'}
                  </button>
                ))}
              </div>
              {q1UnusualChanges && (
                <input
                  type="text"
                  value={q1Details}
                  onChange={(event) => setQ1Details(event.target.value)}
                  placeholder="If yes, add one line"
                  className={`mt-2 w-full border rounded-lg px-3 py-2 text-sm ${
                    isDark
                      ? 'bg-[#0f2040] border-white/15 text-white placeholder:text-white/40'
                      : 'bg-white border-[#e2e8f0] text-[#1a2b3c]'
                  }`}
                />
              )}
            </div>

            <div>
              <p className={`text-sm font-medium ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>
                2. Any safety or workforce issues?
              </p>
              <div className="mt-2 flex gap-2">
                {[true, false].map((option) => (
                  <button
                    key={`q2-${String(option)}`}
                    type="button"
                    onClick={() => setQ2SafetyIssues(option)}
                    className={`px-3 py-1.5 rounded-md text-xs border ${
                      q2SafetyIssues === option
                        ? 'text-white border-transparent'
                        : isDark
                          ? 'text-white/60 border-white/20'
                          : 'text-[#6b7c93] border-[#d4dde8]'
                    }`}
                    style={q2SafetyIssues === option ? { background: 'linear-gradient(135deg, #2d9e6b 0%, #1B4332 100%)' } : undefined}
                  >
                    {option ? 'Yes' : 'No'}
                  </button>
                ))}
              </div>
              {q2SafetyIssues && (
                <input
                  type="text"
                  value={q2Details}
                  onChange={(event) => setQ2Details(event.target.value)}
                  placeholder="If yes, add one line"
                  className={`mt-2 w-full border rounded-lg px-3 py-2 text-sm ${
                    isDark
                      ? 'bg-[#0f2040] border-white/15 text-white placeholder:text-white/40'
                      : 'bg-white border-[#e2e8f0] text-[#1a2b3c]'
                  }`}
                />
              )}
            </div>

            <div>
              <p className={`text-sm font-medium ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>
                3. Did you act on any of last month's Quick Wins?
              </p>
              <p className={`text-xs ${isDark ? 'text-white/55' : 'text-[#6b7c93]'}`}>
                Shows only last month's generated Quick Wins as options. Check what you did.
              </p>
              {isLoadingQuickWins ? (
                <p className={`mt-2 text-xs ${isDark ? 'text-white/55' : 'text-[#6b7c93]'}`}>Loading Quick Wins...</p>
              ) : (
                <div className="mt-2 space-y-2">
                  {quickWinOptions.map((option) => (
                    <label key={option} className="flex items-center gap-2 text-sm">
                      <input
                        type="checkbox"
                        checked={selectedQuickWins.includes(option)}
                        onChange={() => toggleQuickWinSelection(option)}
                        className="rounded border-[#d4dde8]"
                      />
                      <span className={isDark ? 'text-white/80' : 'text-[#1a2b3c]'}>{option}</span>
                    </label>
                  ))}
                  <label className="flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={selectedQuickWins.includes(naQuickWinLabel)}
                      onChange={() => toggleQuickWinSelection(naQuickWinLabel)}
                      className="rounded border-[#d4dde8]"
                    />
                    <span className={isDark ? 'text-white/80' : 'text-[#1a2b3c]'}>{naQuickWinLabel}</span>
                  </label>
                </div>
              )}
            </div>
          </div>

          <Input
            label="Additional Notes"
            value={monthlyNotes}
            onChange={(event) => setMonthlyNotes(event.target.value)}
            placeholder="Optional details for this month"
          />

          <div className={`rounded-xl p-4 border ${isDark ? 'bg-white/[0.02] border-white/10' : 'bg-[#f8fafc] border-[#e2e8f0]'}`}>
            <p className={`font-semibold ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>STEP 3 - Submit (1 min)</p>
            <p className={`mt-2 text-sm ${isDark ? 'text-white/70' : 'text-[#3a4d63]'}`}>
              System handles everything else.
            </p>
          </div>

          {monthlyError && (
            <div className={`rounded-lg p-3 text-sm ${isDark ? 'bg-red-500/10 text-red-300' : 'bg-red-50 text-red-600'}`}>
              {monthlyError}
            </div>
          )}

          <div className="flex justify-end gap-3 pt-2">
            <Button
              variant="ghost"
              onClick={() => {
                setQ1UnusualChanges(null);
                setQ1Details('');
                setQ2SafetyIssues(null);
                setQ2Details('');
                setSelectedQuickWins([]);
                setMonthlyNotes('');
                setMonthlyFiles([]);
                setMonthlyResult(null);
                setMonthlyError(null);
              }}
            >
              Reset
            </Button>
            <Button onClick={submitMonthly} loading={isSubmittingMonthly}>Submit Monthly Checkup</Button>
          </div>

          {monthlyResult && (
            <div className={`rounded-lg p-4 ${isDark ? 'bg-white/5' : 'bg-[#f4f6f9]'}`}>
              <h4 className={`font-medium mb-2 ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>Checkup submitted</h4>
              <ul className={`space-y-1 text-sm ${isDark ? 'text-white/70' : 'text-[#3a4d63]'}`}>
                {monthlyResult.change_summary.map((line, index) => (
                  <li key={`${index}-${line}`}>• {formatAiText(line)}</li>
                ))}
              </ul>
              {monthlyResult.recommended_next_actions.length > 0 && (
                <div className="mt-3">
                  <p className={`text-sm font-medium ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>Recommended Next Actions</p>
                  <ul className={`mt-1 space-y-1 text-sm ${isDark ? 'text-white/70' : 'text-[#3a4d63]'}`}>
                    {monthlyResult.recommended_next_actions.map((action, index) => (
                      <li key={`${index}-${action}`}>• {formatAiText(action)}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </Card>
      </motion.div>
    </AppLayout>
  );
}
