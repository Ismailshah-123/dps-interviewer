import type { FormField, TemplateFieldSpec } from '@/lib/types'

export interface FormMetrics {
  total: number
  required: number
  requiredComplete: number
  missingRequired: number
  awaitingReview: number
  aiDrafts: number
}

export function getFormMetrics(fields: FormField[], specs: Map<string, TemplateFieldSpec>): FormMetrics {
  const requiredFields = fields.filter((field) => specs.get(field.field_id)?.required)
  return {
    total: fields.length,
    required: requiredFields.length,
    requiredComplete: requiredFields.filter((field) => Boolean(field.value.text?.trim())).length,
    missingRequired: requiredFields.filter((field) => !field.value.text?.trim()).length,
    awaitingReview: fields.filter((field) => field.review_status !== 'reviewed').length,
    aiDrafts: fields.filter((field) => !field.human_edited && field.value.source === 'ai_summary').length,
  }
}
