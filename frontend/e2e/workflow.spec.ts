import { expect, test, type APIRequestContext, type Page } from '@playwright/test'

// Synthetic accounts and data for the isolated E2E backend (scripts/e2e_backend.py) only.
const ADMIN = { email: 'admin@dps.example.com', password: 'E2E-Admin-Pass-2026!' }
const PASSWORD = 'Synthetic-Pass-2026!'
const INTERVIEWER = 'e2e.interviewer@dps.example.com'
const OTHER = 'e2e.other@dps.example.com'
const PRINCIPAL = 'e2e.principal@dps.example.com'
const API = 'http://127.0.0.1:8001/api/v1'

async function apiToken(request: APIRequestContext, email: string, password: string) {
  const r = await request.post(`${API}/auth/login`, { data: { email, password } })
  expect(r.ok()).toBeTruthy()
  return { Authorization: `Bearer ${(await r.json()).access_token}` }
}

async function signIn(page: Page, email: string, password = PASSWORD) {
  await page.goto('/login')
  await page.getByLabel('Email').fill(email)
  await page.getByLabel('Password').fill(password)
  await page.getByRole('button', { name: 'Sign in', exact: true }).click()
  await expect(page).toHaveURL(/\/dashboard/)
}

async function signOut(page: Page) {
  await page.getByRole('button', { name: 'Sign out' }).click()
  await expect(page.getByRole('heading', { name: 'Sign in' })).toBeVisible()
}

test('interviewer to principal workflow with real browser recording, correction loop, PDF and access control', async ({ page, request }) => {
  // 1. Administrator creates an interviewer through the UI.
  await signIn(page, ADMIN.email, ADMIN.password)
  await page.getByRole('navigation', { name: 'Main navigation' }).getByRole('link', { name: 'Staff accounts' }).click()
  await page.getByRole('button', { name: 'New account' }).click()
  await page.getByLabel('Full name').fill('E2E Interviewer')
  await page.getByLabel('Email').fill(INTERVIEWER)
  await page.getByLabel('Initial password').fill(PASSWORD)
  await page.getByRole('button', { name: 'Create account' }).click()
  await expect(page.getByText('Account created for E2E Interviewer')).toBeVisible()
  await signOut(page)

  // Supporting accounts via the API to keep the test focused.
  const admin = await apiToken(request, ADMIN.email, ADMIN.password)
  for (const [email, role] of [
    [OTHER, 'interviewer'],
    [PRINCIPAL, 'reviewer'],
  ]) {
    const r = await request.post(`${API}/auth/users`, { headers: admin, data: { email, full_name: `E2E ${role}`, password: PASSWORD, role } })
    expect(r.ok()).toBeTruthy()
  }

  // 2-3. Interviewer signs in and creates a candidate.
  await signIn(page, INTERVIEWER)
  await page.getByRole('navigation', { name: 'Main navigation' }).getByRole('link', { name: 'Candidates' }).click()
  await page.getByRole('button', { name: 'New candidate' }).first().click()
  await page.getByLabel('Candidate name').fill('Synthetic E2E Child')
  await page.getByLabel('Class / grade applied for').fill('Class 3')
  await page.getByRole('button', { name: 'Create candidate' }).click()
  await expect(page.getByRole('heading', { name: 'Synthetic E2E Child' })).toBeVisible()

  // 4. Start the interview; recording is blocked until consent is confirmed.
  await page.getByRole('button', { name: 'Start interview' }).click()
  await expect(page).toHaveURL(/\/interviews\//)
  const interviewUrl = page.url().split('?')[0]
  await expect(page.getByRole('button', { name: 'Start recording' })).toBeDisabled()
  for (const label of [/read or showed this notice/, /parent or guardian agreed/, /student was told/]) await page.getByLabel(label).check()
  await page.getByRole('button', { name: 'Confirm consent' }).click()
  await expect(page.getByText('Confirmed', { exact: true })).toBeVisible()

  // 5-6. Record from the (fake) microphone, stop, then save to the server.
  await page.getByRole('button', { name: 'Start recording' }).click()
  await expect(page.getByText('Recording', { exact: true })).toBeVisible()
  await page.waitForTimeout(6500)
  await page.getByRole('button', { name: 'Pause' }).click()
  await page.getByRole('button', { name: 'Resume' }).click()
  await page.waitForTimeout(1500)
  await page.getByRole('button', { name: 'Stop' }).click()
  await expect(page.getByText('Not yet saved to server')).toBeVisible()
  await page.getByRole('button', { name: 'Save to server' }).click()
  await expect(page.getByText('Recording saved to the school server')).toBeVisible()
  await expect(page.getByText('Audio stored')).toBeVisible()

  // 7. Processing with the deterministic test provider (no paid or external AI).
  const run = await request.post(`${API}/processing/run-once`, { headers: admin })
  expect(run.ok()).toBeTruthy()
  await request.post(`${API}/processing/run-once`, { headers: admin })
  await page.reload()
  await expect(page.getByText('Interviewer review', { exact: true }).first()).toBeVisible()

  // 8-10. Transcript, summary and form are present and labelled as AI output.
  await page.getByRole('tab', { name: 'Transcript' }).click()
  await expect(page.getByText('Machine transcription')).toBeVisible()
  await page.getByRole('tab', { name: 'AI summary' }).click()
  await expect(page.getByText('AI-generated draft')).toBeVisible()
  await page.getByRole('tab', { name: 'Interview form' }).click()
  await expect(page.getByText('Interviewer entry required')).toBeVisible()
  await expect(page.getByRole('button', { name: 'Submit for review' })).toBeDisabled()

  // 11. Interviewer writes the manual field, confirms the rest, submits.
  await page.getByRole('textbox', { name: 'Interviewer Observations' }).fill('Synthetic observation written by the interviewer.')
  await page.getByRole('button', { name: 'Save field: Interviewer Observations' }).click()
  await expect(page.getByText('Entered / edited by staff')).toBeVisible()
  const confirmButtons = page.getByRole('button', { name: /^Confirm field: / })
  while ((await confirmButtons.count()) > 0) {
    const before = await confirmButtons.count()
    await confirmButtons.first().click()
    await expect(confirmButtons).toHaveCount(before - 1)
  }
  await page.getByRole('button', { name: 'Submit for review' }).click()
  await page.getByRole('button', { name: 'Submit', exact: true }).click()
  await expect(page.getByText('Submitted', { exact: true }).first()).toBeVisible()
  await signOut(page)

  // 12-13. Principal reviews and requests a correction.
  await signIn(page, PRINCIPAL)
  await page.getByRole('navigation', { name: 'Main navigation' }).getByRole('link', { name: 'Review queue' }).click()
  await page.getByRole('link', { name: 'Open' }).first().click()
  await page.getByRole('tab', { name: 'Review' }).click()
  await page.getByRole('button', { name: 'Begin review' }).click()
  await expect(page.getByRole('button', { name: 'Request correction' })).toBeDisabled()
  await page.getByLabel('Review remarks').fill('Please expand the interview overview.')
  await page.getByRole('button', { name: 'Request correction' }).click()
  await expect(page.getByText('Correction requested', { exact: true }).first()).toBeVisible()
  await signOut(page)

  // 14. Interviewer corrects and resubmits.
  await signIn(page, INTERVIEWER)
  await page.goto(`${interviewUrl}?tab=form`)
  await page.getByRole('textbox', { name: 'Interview Overview' }).fill('Expanded synthetic overview after principal feedback.')
  await page.getByRole('button', { name: 'Save field: Interview Overview' }).click()
  await expect(page.getByRole('button', { name: 'Resubmit' })).toBeEnabled()
  await page.getByRole('button', { name: 'Resubmit' }).click()
  await page.getByRole('button', { name: 'Submit', exact: true }).click()
  await expect(page.getByText('Submitted', { exact: true }).first()).toBeVisible()
  await signOut(page)

  // 15-16. Principal finalizes and exports the PDF.
  await signIn(page, PRINCIPAL)
  await page.goto(`${interviewUrl}?tab=review`)
  await page.getByRole('button', { name: 'Begin review' }).click()
  await page.getByRole('button', { name: 'Mark documentation reviewed' }).click()
  await page.getByRole('button', { name: 'Finalize record' }).click()
  await expect(page.getByText('Finalized', { exact: true }).first()).toBeVisible()
  await expect(page.getByText('Please expand the interview overview.')).toBeVisible()
  const download = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Export PDF' }).click()
  const pdf = await download
  expect(pdf.suggestedFilename()).toMatch(/interview-form\.pdf$/)
  await signOut(page)

  // 17. Another interviewer is denied the same record (UI and API).
  await signIn(page, OTHER)
  await page.goto(interviewUrl)
  await expect(page.getByText(/interview not found/i)).toBeVisible()
  const other = await apiToken(request, OTHER, PASSWORD)
  const id = interviewUrl.split('/').pop()
  expect((await request.get(`${API}/forms/${id}/pdf`, { headers: other })).status()).toBe(404)
  expect((await request.get(`${API}/recordings/${id}/download`, { headers: other })).status()).toBe(404)
  await page.goto('/admin/users')
  await expect(page.getByRole('heading', { name: 'Access denied' })).toBeVisible()
})
