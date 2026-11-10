export type Role = 'administrator' | 'interviewer' | 'reviewer' | 'principal'

export interface User {
  id: string
  email: string
  full_name: string
  role: Role
  is_active: boolean
  created_at?: string
}

export interface PageMeta {
  total: number
  skip: number
  limit: number
  has_more: boolean
}

export interface Page<T> {
  items: T[]
  meta: PageMeta
}

export interface Candidate {
  id: string
  reference_number: string
  name: string
  application_reference: string | null
  grade: string | null
  interview_datetime: string | null
  assigned_interviewer_id: string | null
  metadata_json: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface CandidateInput {
  name: string
  application_reference?: string | null
  grade?: string | null
  interview_datetime?: string | null
  assigned_interviewer_id?: string | null
}

export type InterviewStatus =
  | 'draft'
  | 'recording'
  | 'uploading'
  | 'uploaded'
  | 'queued'
  | 'transcribing'
  | 'transcript_ready'
  | 'summarizing'
  | 'form_draft_ready'
  | 'needs_review'
  | 'submitted'
  | 'principal_review'
  | 'correction_requested'
  | 'reviewed'
  | 'finalized'
  | 'failed'
  | 'cancelled'

export interface Interview {
  id: string
  candidate_id: string
  interviewer_id: string
  status: InterviewStatus
  template_version_id: string | null
  submitted_at: string | null
  finalized_at: string | null
  created_at: string
  updated_at: string
  candidate_reference: string | null
  candidate_name: string | null
  candidate_grade: string | null
  consent_status: 'confirmed' | 'withdrawn' | null
}

export interface InterviewStats {
  total: number
  by_status: Partial<Record<InterviewStatus, number>>
}

export interface Recording {
  id: string
  interview_id: string
  original_filename: string
  mime_type: string
  size_bytes: number
  sha256: string
  duration_seconds: number | null
  created_at: string
}

export interface StorageAsset {
  id: string
  kind: 'recording' | 'pdf'
  interview_id: string
  candidate_reference: string
  candidate_name: string
  filename: string
  mime_type: string
  size_bytes: number
  created_at: string
  version_number: number | null
}

export interface ProcessingJob {
  id: string
  type: string
  status: string
  attempts: number
  error: string | null
}

export interface ProcessingStatus {
  interview_status: InterviewStatus
  jobs: ProcessingJob[]
}

export interface TranscriptSegment {
  id: string
  sequence: number
  start_seconds: number
  end_seconds: number
  text: string
  speaker_label: string | null
  confidence: number | null
  is_human_edited: boolean
}

export interface Transcript {
  id: string
  interview_id: string
  original_text: string
  language: string | null
  provider: string
  model_name: string
  model_version: string | null
  processing_seconds: number | null
  created_at: string
  segments: TranscriptSegment[]
}

export interface SummaryEvidence {
  segment_sequence: number | null
  start_seconds: number | null
  end_seconds: number | null
  quote: string | null
}

export interface StructuredSummary {
  interview_overview: string | null
  parent_guardian_statements: string[]
  student_statements: string[]
  educational_background: string[]
  interests_and_activities: string[]
  school_expectations: string[]
  interviewer_documented_observations: string[]
  important_topics: string[]
  follow_up_questions: string[]
  unclear_or_missing_information: string[]
  evidence: SummaryEvidence[]
}

export interface Summary {
  id: string
  interview_id: string
  data: StructuredSummary
  provider: string
  model_name: string
  prompt_version: string
  created_at: string
  updated_at: string
}

export type FieldSource = 'ai_summary' | 'not_mentioned' | 'manual_required' | 'human'

export interface FormFieldValue {
  text: string
  source?: FieldSource
}

export interface FormField {
  id: string
  field_id: string
  value: FormFieldValue
  generated_value: FormFieldValue | null
  evidence: unknown[]
  review_status: 'needs_review' | 'reviewed'
  human_edited: boolean
  updated_at: string
}

export interface InterviewForm {
  id: string
  interview_id: string
  template_version_id: string
  status: string
  version_number: number
  created_at: string
  updated_at: string
  fields: FormField[]
}

export interface TemplateFieldSpec {
  id: string
  label: string
  section?: string
  type?: string
  required?: boolean
  human_review?: boolean
  source?: string
}

export interface TemplateVersion {
  id: string
  template_id: string
  template_name: string | null
  template_description: string | null
  version: string
  fields: TemplateFieldSpec[]
  is_current: boolean
}

export interface TemplateSummary {
  id: string
  name: string
  description: string | null
  active: boolean
}

export type ReviewAction = 'review' | 'request_correction' | 'finalize'

export interface ReviewEntry {
  id: string
  interview_id: string
  reviewer_id: string
  reviewer_name?: string | null
  action: ReviewAction
  remarks: string | null
  recommendation: string | null
  status_from?: string | null
  status_to?: string | null
  created_at: string
}

export interface AdminJob {
  id: string
  interview_id: string
  type: string
  status: string
  attempts: number
  max_attempts: number
  next_attempt_at: string | null
  error: string | null
}

export interface AuditEntry {
  id: string
  actor_user_id: string | null
  action: string
  resource_type: string
  resource_id: string | null
  created_at: string
}

export interface AppMeta {
  application: string
  api_version: string
  environment: string
  features: Record<string, boolean>
  external_ai: string[]
  upload: { max_bytes: number; allowed_mime_types: string[] }
}
