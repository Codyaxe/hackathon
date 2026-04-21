import { useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { Sparkles, ArrowRight, BookOpen, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import Button from '../ui/Button';
import { useThemeStore } from '../../stores/themeStore';
import { getStoredCompanyProfile, toOnboardingContext } from '../../lib/companyProfile';
import { getOnboardingQuiz, submitOnboarding } from '../../lib/workflowApi';
import { formatAiText } from '../../lib/aiText';
import type {
  OnboardingQuizResponse,
  OnboardingRecommendationResponse,
  WorkflowQuestion,
} from '../../types/workflow';

interface OnboardingCardProps {
  onDismiss?: () => void;
  onComplete?: () => void;
}

function normalizeAnswer(question: WorkflowQuestion, value: unknown): unknown {
  if (question.input_type === 'number') {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : undefined;
  }
  if (question.input_type === 'multi_choice') {
    return Array.isArray(value) ? value : [];
  }
  if (question.input_type === 'boolean') {
    if (typeof value === 'boolean') {
      return value;
    }
    return value === 'true';
  }
  return value;
}

export default function OnboardingCard({ onDismiss, onComplete }: OnboardingCardProps) {
  const navigate = useNavigate();
  const [quiz, setQuiz] = useState<OnboardingQuizResponse | null>(null);
  const [recommendation, setRecommendation] = useState<OnboardingRecommendationResponse | null>(null);
  const [answersByQuestionId, setAnswersByQuestionId] = useState<Record<string, unknown>>({});
  const [isLoadingQuiz, setIsLoadingQuiz] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const { theme } = useThemeStore();
  const isDark = theme === 'dark';
  const profile = useMemo(() => getStoredCompanyProfile(), []);
  const formattedRecommendationSummary = recommendation
    ? formatAiText(recommendation.recommendation_summary)
    : '';

  const startOnboarding = async () => {
    try {
      setErrorMessage(null);
      setIsLoadingQuiz(true);
      const response = await getOnboardingQuiz(toOnboardingContext(profile));
      setQuiz(response);
      setRecommendation(null);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Could not load onboarding quiz.');
    } finally {
      setIsLoadingQuiz(false);
    }
  };

  const submitQuiz = async () => {
    if (!quiz) {
      return;
    }

    try {
      setErrorMessage(null);
      setIsSubmitting(true);
      const answers = quiz.questions
        .map((question) => ({
          question_id: question.question_id,
          value: normalizeAnswer(question, answersByQuestionId[question.question_id]),
        }))
        .filter((item) => item.value !== undefined && !(Array.isArray(item.value) && item.value.length === 0));

      const response = await submitOnboarding({
        context: quiz.context,
        answers,
      });
      setRecommendation(response);
      onComplete?.();
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Could not submit onboarding answers.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const toggleMultiChoice = (questionId: string, option: string) => {
    setAnswersByQuestionId((prev) => {
      const existing = Array.isArray(prev[questionId]) ? prev[questionId] as string[] : [];
      const next = existing.includes(option)
        ? existing.filter((item) => item !== option)
        : [...existing, option];
      return {
        ...prev,
        [questionId]: next,
      };
    });
  };

  const renderQuestionInput = (question: WorkflowQuestion) => {
    const answer = answersByQuestionId[question.question_id];

    if (question.input_type === 'boolean') {
      return (
        <div className="flex gap-2 mt-2">
          {[true, false].map((option) => (
            <button
              key={`${question.question_id}-${String(option)}`}
              type="button"
              onClick={() => setAnswersByQuestionId((prev) => ({ ...prev, [question.question_id]: option }))}
              className={`px-3 py-1.5 rounded-md text-xs border transition-colors ${
                answer === option
                  ? 'text-white border-transparent'
                  : isDark
                    ? 'text-white/60 border-white/20 hover:border-white/35'
                    : 'text-[#6b7c93] border-[#d4dde8] hover:border-[#9fb0c2]'
              }`}
              style={answer === option ? { background: 'linear-gradient(135deg, #2d9e6b 0%, #1B4332 100%)' } : undefined}
            >
              {option ? 'Yes' : 'No'}
            </button>
          ))}
        </div>
      );
    }

    if (question.input_type === 'single_choice') {
      return (
        <select
          value={typeof answer === 'string' ? answer : ''}
          onChange={(event) => setAnswersByQuestionId((prev) => ({ ...prev, [question.question_id]: event.target.value }))}
          className={`mt-2 w-full border rounded-lg px-3 py-2 text-sm ${
            isDark
              ? 'bg-[#0f2040] border-white/15 text-white'
              : 'bg-white border-[#e2e8f0] text-[#1a2b3c]'
          }`}
        >
          <option value="">Select an option</option>
          {question.options.map((option) => (
            <option key={option} value={option}>{option}</option>
          ))}
        </select>
      );
    }

    if (question.input_type === 'multi_choice') {
      const selected = Array.isArray(answer) ? answer as string[] : [];
      return (
        <div className="mt-2 flex flex-wrap gap-2">
          {question.options.map((option) => (
            <button
              key={`${question.question_id}-${option}`}
              type="button"
              onClick={() => toggleMultiChoice(question.question_id, option)}
              className={`px-3 py-1.5 rounded-md text-xs border transition-colors ${
                selected.includes(option)
                  ? 'text-white border-transparent'
                  : isDark
                    ? 'text-white/60 border-white/20 hover:border-white/35'
                    : 'text-[#6b7c93] border-[#d4dde8] hover:border-[#9fb0c2]'
              }`}
              style={selected.includes(option) ? { background: 'linear-gradient(135deg, #2d9e6b 0%, #1B4332 100%)' } : undefined}
            >
              {option.replaceAll('_', ' ')}
            </button>
          ))}
        </div>
      );
    }

    if (question.input_type === 'number') {
      return (
        <input
          type="number"
          value={typeof answer === 'number' || typeof answer === 'string' ? String(answer) : ''}
          onChange={(event) => setAnswersByQuestionId((prev) => ({ ...prev, [question.question_id]: event.target.value }))}
          className={`mt-2 w-full border rounded-lg px-3 py-2 text-sm ${
            isDark
              ? 'bg-[#0f2040] border-white/15 text-white placeholder:text-white/40'
              : 'bg-white border-[#e2e8f0] text-[#1a2b3c]'
          }`}
          placeholder="Enter a value"
        />
      );
    }

    return (
      <input
        type="text"
        value={typeof answer === 'string' ? answer : ''}
        onChange={(event) => setAnswersByQuestionId((prev) => ({ ...prev, [question.question_id]: event.target.value }))}
        className={`mt-2 w-full border rounded-lg px-3 py-2 text-sm ${
          isDark
            ? 'bg-[#0f2040] border-white/15 text-white placeholder:text-white/40'
            : 'bg-white border-[#e2e8f0] text-[#1a2b3c]'
        }`}
        placeholder="Your answer"
      />
    );
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5 }}
      className={`rounded-xl shadow-sm p-6 relative overflow-hidden ${
        isDark
          ? 'bg-[#0d2540] border border-white/[0.08]'
          : 'bg-[#f0faf5] border border-[#c6e8d5]'
      }`}
    >
      {/* Background decoration */}
      <div
        className="absolute top-0 right-0 w-32 h-32 rounded-full blur-3xl transform translate-x-16 -translate-y-16"
        style={{ background: 'linear-gradient(135deg, #2d9e6b 0%, #1B4332 100%)', opacity: 0.1 }}
      />

      {/* Close button */}
      {onDismiss && (
        <button
          onClick={onDismiss}
          className={`absolute top-4 right-4 w-8 h-8 rounded-lg flex items-center justify-center transition-colors border ${
            isDark
              ? 'bg-white/5 hover:bg-white/10 border-white/10'
              : 'bg-white hover:bg-gray-100 border-[#e2e8f0]'
          }`}
          aria-label="Dismiss welcome card"
        >
          <X className="w-4 h-4" style={{ color: isDark ? 'rgba(255,255,255,0.55)' : '#6b7c93' }} />
        </button>
      )}

      <div className="relative flex items-start gap-4">
        <div
          className="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0"
          style={{ background: 'linear-gradient(135deg, #2d9e6b 0%, #1B4332 100%)', boxShadow: '0 4px 14px rgba(45, 158, 107, 0.3)' }}
        >
          <Sparkles className="w-6 h-6 text-white" />
        </div>
        <div className="flex-1">
          <h3 className={`font-display text-lg mb-1 ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>
            Welcome to ESG Hub
          </h3>
          {!quiz && !recommendation && (
            <>
              <p className={`text-sm mb-4 max-w-lg ${isDark ? 'text-white/55' : 'text-[#6b7c93]'}`}>
                Run onboarding to personalize your ESG priorities, then auto-generate an action plan and monthly update prompts.
              </p>
              <div className="flex flex-wrap gap-3">
                <Button icon={<ArrowRight className="w-4 h-4" />} onClick={startOnboarding} loading={isLoadingQuiz}>
                  Start Onboarding Quiz
                </Button>
                <Button variant="outline" icon={<BookOpen className="w-4 h-4" />} onClick={() => navigate('/data-input')}>
                  Upload ESG Files
                </Button>
              </div>
            </>
          )}

          {quiz && !recommendation && (
            <div className="mt-4 space-y-3">
              {quiz.questions.map((question) => (
                <div
                  key={question.question_id}
                  className={`rounded-lg p-3 ${isDark ? 'bg-white/5 border border-white/10' : 'bg-white border border-[#e2e8f0]'}`}
                >
                  <p className={`text-sm font-medium ${isDark ? 'text-white' : 'text-[#1a2b3c]'}`}>
                    {question.prompt}
                  </p>
                  {renderQuestionInput(question)}
                </div>
              ))}
              <div className="flex flex-wrap gap-3 pt-1">
                <Button onClick={submitQuiz} loading={isSubmitting}>
                  Submit Onboarding
                </Button>
                <Button variant="ghost" onClick={() => setQuiz(null)}>
                  Cancel
                </Button>
              </div>
            </div>
          )}

          {recommendation && (
            <div className="mt-4 space-y-3">
              <p className={`text-sm whitespace-pre-line ${isDark ? 'text-white/70' : 'text-[#3a4d63]'}`}>
                {formattedRecommendationSummary}
              </p>
              <div className="flex flex-wrap gap-2">
                {recommendation.focus_areas.map((focus) => (
                  <span
                    key={`${focus.area}-${focus.priority}`}
                    className="text-xs px-2 py-1 rounded-full text-white"
                    style={{ background: 'linear-gradient(135deg, #2d9e6b 0%, #1B4332 100%)' }}
                  >
                    {focus.area.replaceAll('_', ' ')} ({focus.priority})
                  </span>
                ))}
              </div>
              <ul className={`text-sm space-y-1 ${isDark ? 'text-white/70' : 'text-[#3a4d63]'}`}>
                {recommendation.next_steps.map((step, index) => (
                  <li key={`${index}-${step}`}>• {formatAiText(step)}</li>
                ))}
              </ul>
              <div className="flex flex-wrap gap-3">
                <Button onClick={() => navigate('/reports')}>
                  Generate ESG Plan
                </Button>
                <Button variant="outline" onClick={() => setRecommendation(null)}>
                  Re-run Onboarding
                </Button>
              </div>
            </div>
          )}

          {errorMessage && (
            <p className="text-sm mt-3 text-red-500">{errorMessage}</p>
          )}
        </div>
      </div>
    </motion.div>
  );
}