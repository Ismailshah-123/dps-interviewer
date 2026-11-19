import { ApiError, errorMessage, fallbackMessage } from './api'
import { containsArabicScript, formatBytes, formatDuration, isProcessing, statusLabel } from './status'
import { staffSchema } from '@/features/admin/UsersPage'
import { candidateSchema } from '@/features/candidates/CandidateFormDialog'

describe('status helpers', () => {
  it('formats durations for a 40 minute interview and beyond', () => {
    expect(formatDuration(0)).toBe('0:00')
    expect(formatDuration(65)).toBe('1:05')
    expect(formatDuration(40 * 60)).toBe('40:00')
    expect(formatDuration(3725)).toBe('1:02:05')
  })

  it('labels statuses and identifies processing states', () => {
    expect(statusLabel('needs_review')).toBe('Interviewer review')
    expect(isProcessing('transcribing')).toBe(true)
    expect(isProcessing('submitted')).toBe(false)
  })

  it('detects Urdu script but not Roman Urdu', () => {
    expect(containsArabicScript('بچے کو ریاضی پسند ہے')).toBe(true)
    expect(containsArabicScript('bachay ko math pasand hai')).toBe(false)
  })

  it('formats sizes', () => {
    expect(formatBytes(19_200_000)).toBe('18.3 MB')
  })
})

describe('api error messages', () => {
  it('maps status codes to safe messages', () => {
    expect(fallbackMessage(401)).toMatch(/session/i)
    expect(fallbackMessage(403)).toMatch(/permission/i)
    expect(fallbackMessage(409)).toMatch(/current state/i)
    expect(fallbackMessage(500)).toMatch(/server/i)
  })

  it('prefers ApiError messages and hides network internals', () => {
    expect(errorMessage(new ApiError(409, 'Consent required'))).toBe('Consent required')
    expect(errorMessage(new TypeError('Failed to fetch'))).toMatch(/could not be reached/i)
  })
})

describe('form validation', () => {
  it('enforces the staff password policy', () => {
    const base = { full_name: 'Synthetic Staff', email: 'staff@dps.example.com', role: 'interviewer' as const }
    expect(staffSchema.safeParse({ ...base, password: 'short' }).success).toBe(false)
    expect(staffSchema.safeParse({ ...base, password: 'alllowercase123' }).success).toBe(false)
    expect(staffSchema.safeParse({ ...base, password: 'Synthetic-Pass-2026' }).success).toBe(true)
  })

  it('requires a candidate name', () => {
    expect(candidateSchema.safeParse({ name: '  ' }).success).toBe(false)
    expect(candidateSchema.safeParse({ name: 'Synthetic Child' }).success).toBe(true)
  })
})

import { getFormMetrics } from '@/features/interviews/formMetrics'
import type { FormField, TemplateFieldSpec } from '@/lib/types'

describe('interview form metrics', () => {
  const specs = new Map<string, TemplateFieldSpec>([
    ['name', { id: 'name', label: 'Candidate name', required: true }],
    ['notes', { id: 'notes', label: 'Interviewer notes', required: true, human_review: true }],
    ['optional', { id: 'optional', label: 'Optional notes' }],
  ])
  const field = (field_id: string, text: string, source: FormField['value']['source'] = 'ai_summary', human_edited = false, review_status: FormField['review_status'] = 'needs_review'): FormField => ({
    id: field_id, field_id, value: { text, source }, generated_value: null, evidence: [], review_status, human_edited, updated_at: '2026-11-19T00:00:00Z',
  })

  it('counts required completion, review state and AI drafts accurately', () => {
    const metrics = getFormMetrics([
      field('name', 'Synthetic Candidate'),
      field('notes', ''),
      field('optional', 'Additional detail', 'human', true, 'reviewed'),
    ], specs)
    expect(metrics).toEqual({ total: 3, required: 2, requiredComplete: 1, missingRequired: 1, awaitingReview: 2, aiDrafts: 1 })
  })

  it('handles a form with no required fields', () => {
    const metrics = getFormMetrics([field('optional', 'Some note')], specs)
    expect(metrics.required).toBe(0)
    expect(metrics.requiredComplete).toBe(0)
    expect(metrics.missingRequired).toBe(0)
  })
})
