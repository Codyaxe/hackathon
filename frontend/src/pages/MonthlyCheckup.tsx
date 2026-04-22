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
  getMonthlyUpdateQuestions,
  submitMonthlyUpdate,
  submitMonthlyUpdateWithFiles,
} from '../lib/workflowApi';
import type {
  MonthlyUpdateQuestion,
  MonthlyUpdateQuestionsResponse,
  MonthlyUpdateResponse,
} from '../types/workflow';

function getDefaultMonth(): string {
  return new Date().toISOString().slice(0, 7);
}

export default function MonthlyCheckup() {
  const profile = useMemo(() => getStoredCompanyProfile(), []);
  const monthlyFileInputRef = useRef<HTMLInputElement>(null);

  const [month, setMonth] = useState(getDefaultMonth());
  const [monthlyQuestions, setMonthlyQuestions] = useState<MonthlyUpdateQuestionsResponse | null>(null);
  const [monthlyAnswers, setMonthlyAnswers] = useState<Record<string, unknown>>({});
  const [monthlyNotes, setMonthlyNotes] = useState('');
  const [isLoadingQuestions, setIsLoadingQuestions] = useState(false);
  const [isSubmittingMonthly, setIsSubmittingMonthly] = useState(false);
  const [monthlyError, setMonthlyError] = useState<string | null>(null);
  const [monthlyResult, setMonthlyResult] = useState<MonthlyUpdateResponse | null>(null);
  const [monthlyFiles, setMonthlyFiles] = useState<File[]>([]);

  const { theme } = useThemeStore();
  const isDark = theme === 'dark';

  const loadMonthlyQuestions = async () => {
    try {
      setIsLoadingQuestions(true);
      setMonthlyError(null);
      const response = await getMonthlyUpdateQuestions(profile.companyId, month);
      setMonthlyQuestions(response);
      setMonthlyAnswers({});
      setMonthlyResult(null);
    } catch (error) {
      setMonthlyError(error instanceof Error ? error.message : 'Could not load monthly questions.');
    } finally {
      setIsLoadingQuestions(false);
    }
  };

  useEffect(() => {
    void loadMonthlyQuestions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const setQuestionAnswer = (question: MonthlyUpdateQuestion, value: unknown) => {
    const normalized = question.input_type === 'number' ? Number(value) : value;
    setMonthlyAnswers((prev) => ({
      ...prev,
      [question.field_name]: normalized,
    }));
  };

  const submitMonthly = async () => {
    try {
      setIsSubmittingMonthly(true);
      setMonthlyError(null);
      const response = monthlyFiles.length > 0
        ? await submitMonthlyUpdateWithFiles(
            profile.companyId,
            month,
            monthlyAnswers,
            monthlyFiles,
            monthlyNotes || undefined
          )
        : await submitMonthlyUpdate(
            profile.companyId,
            month,
            monthlyAnswers,
            monthlyNotes || undefined
          );
      setMonthlyResult(response);
    } catch (error) {
      setMonthlyError(error instanceof Error ? error.message : 'Could not submit monthly update.');
    } finally {
      setIsSubmittingMonthly(false);
    }
  };

  const renderMonthlyInput = (question: MonthlyUpdateQuestion) => {
    const value = monthlyAnswers[question.field_name];

    if (question.input_type === 'single_choice') {
      return (
        <select
          value={typeof value === 'string' ? value : ''}
          onChange={(event) => setQuestionAnswer(question, event.target.value)}
          className={`mt-2 w-full border rounded-lg px-3 py-2 text-sm ${
            isDark
              ? 'bg-[#0f2040] border-white/15 text-white'
              : 'bg-white border-[#e2e8f0] text-[#1a2b3c]'
          }`}
        >
          <option value="">Select option</option>
          {question.options.map((option) => (
            <option key={option} value={option}>{option}</option>
          ))}
        </select>
      );
    }

    if (question.input_type === 'boolean') {
      return (
        <div className="mt-2 flex gap-2">
          {[true, false].map((option) => (
            <button
              key={`${question.field_name}-${String(option)}`}
              type="button"
              onClick={() => setQuestionAnswer(question, option)}
              className={`px-3 py-1.5 rounded-md text-xs border ${
                value === option
                  ? 'text-white border-transparent'
                  : isDark
                    ? 'text-white/60 border-white/20'
                    : 'text-[#6b7c93] border-[#d4dde8]'
              }`}
              style={value === option ? { background: 'linear-gradient(135deg, #2d9e6b 0%, #1B4332 100%)' } : undefined}
            >
              {option ? 'Yes' : 'No'}
            </button>
          ))}
        </div>
      );
    }

    if (question.input_type === 'number') {
      return (
        <input
          type="number"
          value={typeof value === 'number' ? String(value) : ''}
          onChange={(event) => setQuestionAnswer(question, event.target.value)}
          placeholder="Enter value"
          className={`mt-2 w-full border rounded-lg px-3 py-2 text-sm ${
            isDark
              ? 'bg-[#0f2040] border-white/15 text-white placeholder:text-white/40'
              : 'bg-white border-[#e2e8f0] text-[#1a2b3c]'
          }`}
        />
      );
    }

    return (
      <input
        type="text"
        value={typeof value === 'string' ? value : ''}
        onChange={(event) => setQuestionAnswer(question, event.target.value)}
        placeholder="Enter details"
        className={`mt-2 w-full border rounded-lg px-3 py-2 text-sm ${
          isDark
            ? 'bg-[#0f2040] border-white/15 text-white placeholder:text-white/40'
            : 'bg-white border-[#e2e8f0] text-[#1a2b3c]'
        }`}
      />
    );
  };

  return (
    <AppLayout title="Monthly Checkup" subtitle="Submit your monthly ESG changes and get updated guidance">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-3xl"
      >
        <Card className="space-y-6">
          <h3 className={`font-display text-lg ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>Monthly Update Flow</h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-end">
            <Input
              label="Month"
              type="month"
              value={month}
              onChange={(event) => setMonth(event.target.value)}
            />
            <Button variant="secondary" onClick={loadMonthlyQuestions} loading={isLoadingQuestions}>
              Load Questions
            </Button>
          </div>

          {monthlyQuestions && (
            <p className={`text-sm ${isDark ? 'text-white/55' : 'text-[#6b7c93]'}`}>
              {monthlyQuestions.context_message}
            </p>
          )}

          {monthlyQuestions?.questions.map((question) => (
            <div key={question.question_id}>
              <p className={`text-sm font-medium ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>{question.prompt}</p>
              {renderMonthlyInput(question)}
            </div>
          ))}

          <Input
            label="Additional Notes"
            value={monthlyNotes}
            onChange={(event) => setMonthlyNotes(event.target.value)}
            placeholder="Optional details for this month"
          />

          <div className="space-y-2">
            <p className={`text-sm font-medium ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>
              Attach Monthly Evidence (optional)
            </p>
            <div className="flex flex-wrap items-center gap-2">
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

          {monthlyError && (
            <div className={`rounded-lg p-3 text-sm ${isDark ? 'bg-red-500/10 text-red-300' : 'bg-red-50 text-red-600'}`}>
              {monthlyError}
            </div>
          )}

          <div className="flex justify-end gap-3 pt-2">
            <Button variant="ghost" onClick={() => setMonthlyAnswers({})}>Reset</Button>
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
