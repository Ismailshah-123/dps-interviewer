
import type {
  AdminJob,
  AppMeta,
  AuditEntry,
  Candidate,
  CandidateInput,
  FormField,
  Interview,
  InterviewForm,
  InterviewStats,
  Page,
  ProcessingStatus,
  Recording,
  ReviewAction,
  ReviewEntry,
  Role,
  Summary,
  StorageAsset,
  TemplateSummary,
  TemplateVersion,
  Transcript,
  TranscriptSegment,
  User,
} from './types'

const API_ORIGIN = (
  import.meta.env.VITE_API_BASE_URL ?? ''
).replace(/\/+$/, '')

const BASE = `${API_ORIGIN}/api/v1`

/**
 * Session model: the refresh token lives in an HttpOnly, SameSite=Strict cookie set by the
 * backend, so page scripts never see it. The short-lived access token is held only in this
 * module's memory and is lost on reload, after which `restoreSession` silently refreshes it.
 */
let accessToken: string | null = null
let refreshing: Promise<boolean> | null = null
let onSessionExpired: (() => void) | null = null

export function setSessionExpiredHandler(handler: (() => void) | null) {
  onSessionExpired = handler
}

export function hasAccessToken() {
  return accessToken !== null
}

export class ApiError extends Error {
  readonly status: number
  readonly correlationId?: string
  readonly detail: unknown

  constructor(status: number, message: string, detail?: unknown, correlationId?: string) {
    super(message)
    this.status = status
    this.detail = detail
    this.correlationId = correlationId
  }
}

/** A safe, user-facing message. Server detail strings are shown only when they are plain text. */
export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message
  if (error instanceof TypeError) return 'The server could not be reached. Check your connection and try again.'
  if (error instanceof Error && error.message) return error.message
  return 'Something went wrong. Please try again.'
}

export function fallbackMessage(status: number): string {
  if (status === 401) return 'Your session has ended. Please sign in again.'
  if (status === 403) return 'You do not have permission to perform this action.'
  if (status === 404) return 'The requested record was not found or is not available to you.'
  if (status === 409) return 'This action is not allowed in the record’s current state.'
  if (status === 413) return 'The file is larger than the permitted upload size.'
  if (status === 415) return 'This file type is not accepted.'
  if (status === 422) return 'Some of the information entered is not valid.'
  if (status === 429) return 'Too many attempts. Please wait and try again.'
  if (status >= 500) return 'The server encountered an error. Please try again later.'
  return 'The request could not be completed.'
}

async function toApiError(res: Response): Promise<ApiError> {
  const correlationId = res.headers.get('X-Correlation-ID') ?? undefined
  let detail: unknown
  try {
    const body = await res.json()
    detail = body?.detail
  } catch {
    detail = undefined
  }
  const message = typeof detail === 'string' && res.status < 500 ? detail : fallbackMessage(res.status)
  return new ApiError(res.status, message, detail, correlationId)
}

export async function refreshAccessToken(): Promise<boolean> {
  refreshing ??= (async () => {
    try {
      const res = await fetch(`${BASE}/auth/refresh`, { method: 'POST', credentials: 'include' })
      if (!res.ok) {
        accessToken = null
        return false
      }
      accessToken = (await res.json()).access_token
      return true
    } catch {
      return false
    } finally {
      refreshing = null
    }
  })()
  return refreshing
}

type Query = Record<string, string | number | boolean | string[] | null | undefined>

interface RequestOptions {
  method?: string
  body?: unknown
  query?: Query
  form?: FormData
  raw?: boolean
}

function buildUrl(path: string, query?: Query) {
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(query ?? {})) {
    if (value === undefined || value === null || value === '') continue
    if (Array.isArray(value)) value.forEach((v) => params.append(key, v))
    else params.set(key, String(value))
  }
  const qs = params.toString()
  return `${BASE}${path}${qs ? `?${qs}` : ''}`
}

async function send(path: string, options: RequestOptions, retry = true): Promise<Response> {
  const headers: Record<string, string> = { 'X-Correlation-ID': crypto.randomUUID() }
  if (accessToken) headers.Authorization = `Bearer ${accessToken}`
  let body: BodyInit | undefined
  if (options.form) body = options.form
  else if (options.body !== undefined) {
    headers['Content-Type'] = 'application/json'
    body = JSON.stringify(options.body)
  }
  const res = await fetch(buildUrl(path, options.query), {
    method: options.method ?? 'GET',
    headers,
    body,
    credentials: 'include',
  })
  if (res.status === 401 && retry && !path.startsWith('/auth/')) {
    if (await refreshAccessToken()) return send(path, options, false)
    onSessionExpired?.()
  }
  if (!res.ok) throw await toApiError(res)
  return res
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const res = await send(path, options)
  if (res.status === 204) return undefined as T
  return (await res.json()) as T
}

export async function requestBlob(path: string): Promise<Blob> {
  return (await send(path, {})).blob()
}

/** Multipart upload with progress. Uses XHR because fetch cannot report upload progress. */
export function uploadWithProgress<T>(path: string, form: FormData, onProgress: (fraction: number) => void, signal?: AbortSignal): Promise<T> {
  const attempt = (retry: boolean): Promise<T> =>
    new Promise<T>((resolve, reject) => {
      const xhr = new XMLHttpRequest()
      xhr.open('POST', buildUrl(path))
      xhr.withCredentials = true
      if (accessToken) xhr.setRequestHeader('Authorization', `Bearer ${accessToken}`)
      xhr.setRequestHeader('X-Correlation-ID', crypto.randomUUID())
      xhr.upload.onprogress = (e) => e.lengthComputable && onProgress(e.loaded / e.total)
      xhr.onerror = () => reject(new ApiError(0, 'The upload was interrupted. Your recording is still saved in this browser; retry when the connection is back.'))
      xhr.onabort = () => reject(new ApiError(0, 'Upload cancelled.'))
      xhr.onload = async () => {
        if (xhr.status === 401 && retry) {
          if (await refreshAccessToken()) return attempt(false).then(resolve, reject)
          onSessionExpired?.()
        }
        if (xhr.status >= 200 && xhr.status < 300) return resolve(JSON.parse(xhr.responseText) as T)
        let detail: unknown
        try {
          detail = JSON.parse(xhr.responseText)?.detail
        } catch {
          detail = undefined
        }
        const message = typeof detail === 'string' && xhr.status < 500 ? detail : fallbackMessage(xhr.status)
        reject(new ApiError(xhr.status, message, detail, xhr.getResponseHeader('X-Correlation-ID') ?? undefined))
      }
      signal?.addEventListener('abort', () => xhr.abort())
      xhr.send(form)
    })
  return attempt(true)
}

export interface ListParams {
  skip?: number
  limit?: number
}

export const api = {
  async login(email: string, password: string) {
    const res = await fetch(`${BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
      credentials: 'include',
    })
    if (!res.ok) {
      const err = await toApiError(res)
      if (res.status === 401 || res.status === 422) throw new ApiError(res.status, 'Email or password is incorrect.', undefined, err.correlationId)
      throw err
    }
    accessToken = (await res.json()).access_token
  },
  async logout() {
    try {
      await fetch(`${BASE}/auth/logout`, { method: 'POST', credentials: 'include' })
    } finally {
      accessToken = null
    }
  },
  me: () => request<User>('/auth/me'),
  requestPasswordReset: (email: string) => request<{ message: string; demo_token?: string }>('/auth/password-reset/request', { method: 'POST', body: { email } }),
  confirmPasswordReset: (token: string, new_password: string) => request<{ message: string }>('/auth/password-reset/confirm', { method: 'POST', body: { token, new_password } }),
  meta: () => request<AppMeta>('/meta'),

  candidates: (params: ListParams & { q?: string } = {}) => request<Page<Candidate>>('/candidates', { query: { ...params } }),
  candidate: (id: string) => request<Candidate>(`/candidates/${id}`),
  createCandidate: (body: CandidateInput) => request<Candidate>('/candidates', { method: 'POST', body }),
  updateCandidate: (id: string, body: Partial<CandidateInput>) => request<Candidate>(`/candidates/${id}`, { method: 'PATCH', body }),

  interviews: (params: ListParams & { status?: string[]; candidate_id?: string } = {}) => request<Page<Interview>>('/interviews', { query: { ...params } }),
  interviewStats: () => request<InterviewStats>('/interviews/stats'),
  interview: (id: string) => request<Interview>(`/interviews/${id}`),
  createInterview: (candidate_id: string) => request<Interview>('/interviews', { method: 'POST', body: { candidate_id } }),
  confirmConsent: (id: string, notice_version: string) => request<{ status: string }>(`/interviews/${id}/consent`, { method: 'POST', body: { notice_version, confirmed: true } }),
  withdrawConsent: (id: string) => request<{ status: string; interview_status: string }>(`/interviews/${id}/consent/withdraw`, { method: 'POST' }),
  startRecording: (id: string) => request<{ status: string }>(`/interviews/${id}/recording-start`, { method: 'POST' }),
  submitInterview: (id: string) => request<Interview>(`/interviews/${id}/submit`, { method: 'POST' }),

  uploadRecording: (id: string, file: File, onProgress: (f: number) => void, signal?: AbortSignal) => {
    const form = new FormData()
    form.append('file', file, file.name)
    return uploadWithProgress<Recording>(`/recordings/${id}`, form, onProgress, signal)
  },
  recordingBlob: (id: string) => requestBlob(`/recordings/${id}/download`),
  processing: (id: string) => request<ProcessingStatus>(`/processing/${id}`),
  runProcessingOnce: () => request<{ message: string }>('/processing/run-once', { method: 'POST' }),

  transcript: (id: string) => request<Transcript>(`/transcriptions/${id}`),
  editSegment: (segmentId: string, text: string, speaker_label: string | null) =>
    request<TranscriptSegment>(`/transcriptions/segments/${segmentId}`, { method: 'PATCH', body: { text, speaker_label } }),
  summary: (id: string) => request<Summary>(`/summaries/${id}`),

  form: (interviewId: string) => request<InterviewForm>(`/forms/${interviewId}`),
  updateField: (formId: string, fieldId: string, text: string) => request<FormField>(`/forms/${formId}/fields/${fieldId}`, { method: 'PATCH', body: { value: { text } } }),
  confirmField: (formId: string, fieldId: string) => request<FormField>(`/forms/${formId}/fields/${fieldId}/confirm`, { method: 'POST' }),
  formPdf: (interviewId: string) => requestBlob(`/forms/${interviewId}/pdf`),
  templateVersion: (versionId: string) => request<TemplateVersion>(`/templates/versions/${versionId}`),
  templates: () => request<TemplateSummary[]>('/templates'),
  templateVersions: (templateId: string) => request<TemplateVersion[]>(`/templates/${templateId}/versions`),

  reviews: (interviewId: string) => request<ReviewEntry[]>(`/reviews/${interviewId}`),
  review: (interviewId: string, action: ReviewAction, remarks?: string, recommendation?: string) =>
    request<{ status: string; action: string }>(`/reviews/${interviewId}`, { method: 'POST', body: { action, remarks: remarks || null, recommendation: recommendation || null } }),

  users: (params: ListParams & { role?: Role } = {}) => request<Page<User>>('/users', { query: { ...params } }),
  createUser: (body: { email: string; full_name: string; password: string; role: Role }) => request<User>('/auth/users', { method: 'POST', body }),
  updateUser: (id: string, body: Partial<Pick<User, 'full_name' | 'role' | 'is_active'>>) => request<User>(`/users/${id}`, { method: 'PATCH', body }),
  storageAssets: (params: ListParams & { kind?: 'all' | 'recording' | 'pdf'; q?: string } = {}) =>
    request<Page<StorageAsset>>('/admin/storage', { query: { ...params } }),
  storageAssetBlob: (asset: StorageAsset, disposition: 'inline' | 'attachment' = 'inline') =>
    requestBlob(`/admin/storage/${asset.kind}/${asset.id}?disposition=${disposition}`),
  adminJobs: (params: ListParams & { status?: string } = {}) => request<Page<AdminJob>>('/admin/jobs', { query: { ...params } }),
  retryJob: (id: string) => request<{ status: string }>(`/admin/jobs/${id}/retry`, { method: 'POST' }),
  cancelJob: (id: string) => request<{ status: string }>(`/processing/jobs/${id}/cancel`, { method: 'POST' }),
  audit: (params: ListParams & { action?: string } = {}) => request<Page<AuditEntry>>('/admin/audit', { query: { ...params } }),
  healthReady: () => request<{ status: string; checks: Record<string, string> }>('/health/ready'),
  healthAi: async () => {
    // 503 is an expected "degraded" answer here, so read the body either way.
    const res = await fetch(`${BASE}/health/ai`, {
      credentials: 'include',
    })
    const body = await res.json()
    return (res.ok ? body : body.detail) as { status: string; checks: Record<string, { status: string; provider?: string; model?: string; error?: string }> }
  },
}
