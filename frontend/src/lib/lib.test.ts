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
