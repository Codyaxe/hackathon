export type WorkflowInputType = "single_choice" | "multi_choice" | "boolean" | "number" | "text";

export interface CompanyProfile {
  companyId: string;
  companyName: string;
  industry: string;
  employeeCount: number;
  annualRevenue?: number;
  primaryCountry?: string;
  location?: string;
}

export interface OnboardingQuizContext {
  company_id: string;
  company_name: string;
  industry: string;
  employee_count: number;
  annual_revenue?: number;
  primary_country?: string;
  location?: string;
}

export interface WorkflowQuestion {
  question_id: string;
  prompt: string;
  field_name: string;
  input_type: WorkflowInputType;
  options: string[];
  required: boolean;
}

export interface QuestionAnswer {
  question_id: string;
  value: unknown;
}

export interface FocusArea {
  area: "energy" | "emissions" | "waste" | "workforce" | "governance" | "data_foundation" | "supply_chain";
  priority: "high" | "medium" | "low";
  reason: string;
}

export interface OnboardingQuizResponse {
  context: OnboardingQuizContext;
  questions: WorkflowQuestion[];
}

export interface OnboardingRecommendationResponse {
  company_id: string;
  focus_areas: FocusArea[];
  recommendation_summary: string;
  next_steps: string[];
}

export interface OnboardingQuizSubmission {
  context: OnboardingQuizContext;
  answers: QuestionAnswer[];
}

export interface ESGPlanAction {
  title: string;
  why_it_matters: string;
  effort: "low" | "medium" | "high";
  timeline_weeks: number;
  owner: string;
  success_metric: string;
}

export interface ESGPlanResponse {
  company_id: string;
  generated_at: string;
  one_page_summary: string;
  priority_themes: string[];
  actions: ESGPlanAction[];
  monthly_check_in_questions: string[];
  kpis: string[];
  ready_for_pdf: boolean;
}

export interface ExtractedMetric {
  metric_name: string;
  value: string;
  unit?: string | null;
  category: string;
  confidence: number;
  evidence?: string | null;
}

export interface UploadedFileRecord {
  file_id: string;
  filename: string;
  media_type: string;
  size_bytes: number;
  uploaded_at: string;
}

export interface FileExtractionResponse {
  company_id: string;
  files: UploadedFileRecord[];
  extracted_metrics: ExtractedMetric[];
  ai_summary: string;
  follow_up_questions: string[];
  fixed_extraction?: FixedExtractionMetrics | null;
}

export interface FixedExtractionMetrics {
  electricity_kwh?: number | null;
  diesel_liters?: number | null;
  waste_kg?: number | null;
  headcount?: number | null;
  new_hires?: number | null;
  turnover_count?: number | null;
  missing_fields: string[];
}

export interface ResponseLibraryEntry {
  entry_id: string;
  entry_type: "onboarding" | "plan" | "upload_extraction" | "monthly_update";
  created_at: string;
  payload: Record<string, unknown>;
}

export interface ResponseLibraryResponse {
  company_id: string;
  entries: ResponseLibraryEntry[];
}

export interface ProgressStep {
  step_id: string;
  title: string;
  completed: boolean;
  score: number;
  improvement_tip: string;
}

export interface ProgressTrackerResponse {
  company_id: string;
  completion_percentage: number;
  maturity_stage: "getting_started" | "building_baseline" | "improving" | "advanced";
  steps: ProgressStep[];
  next_best_actions: string[];
  esg_score: number;
  compliance_status: "On Track" | "Needs Attention";
  kpis: DashboardKPI[];
  quick_wins_with_savings: QuickWinItem[];
}

export interface DashboardKPI {
  name: string;
  value: number | string;
  unit?: string | null;
  rating: "Good" | "Better" | "Best";
}

export interface QuickWinItem {
  title: string;
  impact_area: string;
  effort: "low" | "medium";
  expected_benefit: string;
  why_recommended: string;
  first_step: string;
  estimated_cost_savings_php?: number | null;
}

export interface QuickWinsResponse {
  company_id: string;
  generated_at: string;
  quick_wins: QuickWinItem[];
}

export interface MonthlyUpdateQuestion {
  question_id: string;
  prompt: string;
  field_name: string;
  input_type: "number" | "text" | "boolean" | "single_choice";
  options: string[];
  required: boolean;
}

export interface MonthlyUpdateQuestionsResponse {
  company_id: string;
  month: string;
  context_message: string;
  questions: MonthlyUpdateQuestion[];
}

export interface MonthlyUpdateSubmission {
  company_id: string;
  month: string;
  changes: Record<string, unknown>;
  notes?: string;
}

export interface MonthlyUpdateResponse {
  company_id: string;
  month: string;
  change_summary: string[];
  updated_focus_areas: FocusArea[];
  recommended_next_actions: string[];
  submission_id?: string | null;
  pipeline_refreshed?: boolean;
  updated_plan_ready_for_pdf?: boolean;
}

export interface EvidenceFileRecord {
  file_id: string;
  filename: string;
  media_type: string;
  size_bytes: number;
  uploaded_at: string;
  disclosure_tag?: string | null;
}

export interface EvidenceListResponse {
  company_id: string;
  evidence_files: EvidenceFileRecord[];
}

export interface ESGReportDisclosure {
  disclosure: string;
  title: string;
  computed: boolean;
  value?: unknown;
  unit?: string | null;
  reason_for_omission?: string | null;
}

export interface OmissionReason {
  disclosure: string;
  reason: string;
}

export interface ESGReportResponse {
  company_id: string;
  generated_at: string;
  disclosures: ESGReportDisclosure[];
  reasons_for_omission: OmissionReason[];
  source_submission_id?: string | null;
}
