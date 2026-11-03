import type { InterviewStatus, Role } from './types'

export type Tone = 'neutral' | 'info' | 'progress' | 'attention' | 'success' | 'danger'

export const STATUS_META: Record<InterviewStatus, { label: string; tone: Tone; description: string }> = {
  draft: { label: 'Draft', tone: 'neutral', description: 'Interview created. Consent and recording have not started.' },
  recording: { label: 'Recording', tone: 'info', description: 'Recording is in progress or has not yet been uploaded.' },
  uploading: { label: 'Uploading', tone: 'progress', description: 'Audio is being uploaded to secure storage.' },
  uploaded: { label: 'Uploaded', tone: 'progress', description: 'Audio is stored. Waiting for transcription to begin.' },
  queued: { label: 'Queued', tone: 'progress', description: 'Waiting for the processing worker.' },
  transcribing: { label: 'Transcribing', tone: 'progress', description: 'Speech recognition is running.' },
  transcript_ready: { label: 'Transcript ready', tone: 'progress', description: 'Transcript produced; summary pending.' },
  summarizing: { label: 'Summarizing', tone: 'progress', description: 'Structured summary and form draft are being prepared.' },
  form_draft_ready: { label: 'Form draft ready', tone: 'attention', description: 'Form draft generated.' },
  needs_review: { label: 'Interviewer review', tone: 'attention', description: 'The interviewer must review, edit and confirm every field.' },
  submitted: { label: 'Submitted', tone: 'info', description: 'Submitted for principal review.' },
  principal_review: { label: 'Principal review', tone: 'info', description: 'The principal is reviewing the documentation.' },
  correction_requested: { label: 'Correction requested', tone: 'attention', description: 'The principal has asked the interviewer for corrections.' },
  reviewed: { label: 'Reviewed', tone: 'success', description: 'Reviewed by the principal; awaiting finalization.' },
  finalized: { label: 'Finalized', tone: 'success', description: 'Documentation is final and read-only.' },
  failed: { label: 'Failed', tone: 'danger', description: 'Processing failed. An administrator can retry the job.' },
  cancelled: { label: 'Cancelled', tone: 'neutral', description: 'The interview was cancelled.' },
}

export const PROCESSING_STATUSES: InterviewStatus[] = ['uploading', 'uploaded', 'queued', 'transcribing', 'transcript_ready', 'summarizing', 'form_draft_ready']
export const EDITABLE_STATUSES: InterviewStatus[] = ['transcript_ready', 'form_draft_ready', 'needs_review', 'correction_requested']
export const REVIEW_QUEUE_STATUSES: InterviewStatus[] = ['submitted', 'principal_review', 'correction_requested', 'reviewed']

export const ROLE_LABEL: Record<Role, string> = {
  administrator: 'Administrator',
  interviewer: 'Interviewer',
  reviewer: 'Principal / Reviewer',
}

export function statusLabel(status: string): string {
  return STATUS_META[status as InterviewStatus]?.label ?? status.replace(/_/g, ' ')
}

export function isProcessing(status: InterviewStatus) {
  return PROCESSING_STATUSES.includes(status)
}

export function formatDuration(totalSeconds: number): string {
  const s = Math.max(0, Math.floor(totalSeconds))
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  const sec = s % 60
  const mm = String(m).padStart(h ? 2 : 1, '0')
  return h ? `${h}:${mm}:${String(sec).padStart(2, '0')}` : `${mm}:${String(sec).padStart(2, '0')}`
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return '—'
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return '—'
  return d.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
}

/** Perso-Arabic characters present: render with RTL direction and an Urdu-capable font. */
export function containsArabicScript(text: string): boolean {
  return /[؀-ۿݐ-ݿﭐ-﷿ﹰ-﻿]/.test(text)
}
