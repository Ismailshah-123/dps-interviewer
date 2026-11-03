# DPS AI Student Interview System
# Production Frontend Master Engineering Prompt

## 1. Role

Act as a Principal Frontend Architect, Senior Next.js Engineer, Product Designer, UX Engineer, Accessibility Engineer, Security Engineer, QA Engineer, and API Integration Engineer.

You are building the production frontend for the DPS AI Student Interview System.

This is not a demo.
This is not a generic SaaS dashboard.
This is not an AI landing page.
Do not create fake workflows, fake statistics, fake AI results, or hardcoded production data.

The frontend must become a serious internal education operations application used by administrators, interviewers, reviewers, and principals.

The backend is the authoritative source of truth for authentication, authorization, workflow state, processing jobs, transcripts, AI summaries, forms, reviews, audit records, and PDFs.

Never duplicate business rules in the frontend.

---

## 2. Product Objective

Build a secure enterprise workflow application that allows DPS staff to:

1. Authenticate securely.
2. Manage candidates.
3. Assign interviewers.
4. Create and conduct student interviews.
5. Capture mandatory recording consent.
6. Record or upload interview audio.
7. Track transcription and AI processing.
8. Review and edit timestamped transcripts.
9. Review AI-generated evidence-based summaries.
10. Review an official DPS interview form.
11. Edit form fields when permitted.
12. Submit completed interviews.
13. Allow reviewer/principal review.
14. Request corrections.
15. Finalize interviews.
16. Export the finalized interview as PDF.
17. Allow administrators to monitor jobs, users, audit logs, and retention operations.

The application must make the complete lifecycle understandable at every point.

---

## 3. Mandatory Technology Stack

Use:

- Next.js 16.x Active LTS or the latest Active LTS release available when implementation begins.
- React with TypeScript.
- App Router.
- Strict TypeScript.
- Tailwind CSS.
- shadcn/ui for accessible primitives.
- Radix primitives where appropriate.
- TanStack Query v5 for server state.
- React Hook Form for complex forms.
- Zod for client-side validation and API response/input validation where appropriate.
- Lucide React for icons.
- date-fns for date formatting.
- Playwright for end-to-end tests.
- Vitest or Jest for unit/component tests.
- ESLint and TypeScript checks in CI.

Do not introduce unnecessary state-management libraries.

Use React state for local UI state.
Use TanStack Query for remote/server state.
Use URL search parameters for shareable filters, tabs, pagination, and search state where useful.

Do not use Redux unless a real architectural requirement appears and is documented.

---

## 4. Architecture

Use a feature-oriented structure similar to:

src/
  app/
    (auth)/
      login/
      forgot-password/
      reset-password/
    (app)/
      dashboard/
      candidates/
      interviews/
      review/
      processing/
      administration/
      settings/
    layout.tsx
    error.tsx
    not-found.tsx
    loading.tsx
    globals.css
  components/
    ui/
    layout/
    data-table/
    forms/
    feedback/
    audio/
    workflow/
  features/
    auth/
    dashboard/
    candidates/
    interviews/
    recording/
    transcripts/
    summaries/
    forms/
    reviews/
    processing/
    administration/
  lib/
    api/
    auth/
    query/
    permissions/
    validation/
    formatting/
    telemetry/
  hooks/
  types/
  config/
  test/

Keep domain logic close to its feature.
Keep generic UI primitives independent from business features.

---

## 5. Backend Integration Rules

The FastAPI backend is authoritative.

Never calculate or invent workflow transitions in the frontend.

Never assume an interview is complete because a button was clicked.

After every mutation:

1. Process the backend response.
2. Update or invalidate the relevant TanStack Query cache.
3. Re-fetch authoritative state when necessary.
4. Show the new server status.

Every API request must include:

- Authorization credentials according to the selected authentication strategy.
- X-Correlation-ID.
- Appropriate Content-Type.

Never expose:

- GROQ_API_KEY.
- database credentials.
- storage credentials.
- JWT signing secrets.
- provider configuration secrets.

No AI provider request is made directly from the browser.

---

## 6. Authentication

Build:

- Login.
- Logout.
- Refresh session handling.
- Current user endpoint integration.
- Password reset request.
- Password reset confirmation.
- Session expiration handling.
- Unauthorized state.
- Forbidden state.

Authentication must not rely on localStorage for long-lived sensitive tokens when a safer architecture is available.

Prefer secure, HttpOnly, SameSite cookies if the deployment architecture supports them.
If bearer tokens must be used by the existing backend contract, isolate token handling in one authentication module and never scatter token access across components.

Handle 401 globally.

A session expiration should:

1. Attempt one controlled refresh if supported.
2. Retry the original request once.
3. If refresh fails, clear session state.
4. Redirect to login.
5. Preserve a safe return URL.

Do not create redirect loops.

---

## 7. RBAC

Roles:

- Administrator
- Interviewer
- Reviewer / Principal

The frontend must hide unavailable actions for UX, but hiding UI is not security.

The backend remains the final authorization authority.

Create a centralized permission model:

canManageUsers
canManageTemplates
canManageCandidates
canCreateInterview
canRecordInterview
canEditTranscript
canEditForm
canSubmitInterview
canReviewInterview
canRequestCorrection
canFinalizeInterview
canViewAudit
canManageProcessing
canExportPdf

Never scatter role comparisons throughout the application.

---

## 8. Application Shell

Create an enterprise application shell.

Desktop:

- Fixed left navigation.
- Compact top bar.
- Main content area.
- Breadcrumbs.
- Page title.
- Contextual actions.
- User menu.
- Notifications/status area.

Navigation sections:

Dashboard
Candidates
Interviews
Review Queue
Processing
Administration
Settings

Only display sections the current user can access.

The sidebar should be compact, calm, and professional.

Do not use giant decorative graphics.
Do not use excessive gradients.
Do not use neon AI effects.
Do not use a generic startup dashboard appearance.

---

## 9. Visual Design System

Design language:

- institutional
- premium
- modern
- restrained
- trustworthy
- clean
- information-dense without being crowded

Primary visual direction:

White and very light neutral surfaces.
Deep navy text.
Professional blue as the primary action color.
Subtle borders.
Moderate shadows.
Small radii.
Strong typography hierarchy.

Avoid:

- excessive rounded cards
- glassmorphism everywhere
- neon gradients
- glowing borders
- huge empty hero sections
- cartoon illustrations
- AI robots
- brain graphics
- decorative stock photography

The product should feel closer to a high-quality enterprise operations console than a marketing website.

---

## 10. Typography

Use a highly readable modern sans-serif.

Suggested hierarchy:

Page title: 28–32px desktop.
Section title: 20–24px.
Card title: 15–18px.
Body: 14–15px.
Metadata: 12–13px.

Do not make everything large.
The interface contains substantial operational information and must remain compact.

---

## 11. Status System

Interview states:

Draft
Recording
Uploading
Uploaded
Queued
Transcribing
Transcript Ready
Summarizing
Form Draft Ready
Needs Review
Submitted
Principal Review
Correction Requested
Reviewed
Finalized
Failed
Cancelled

Create a centralized status configuration with:

- label
- description
- semantic visual treatment
- icon
- allowed UI actions

Do not hardcode status colors in individual components.

The user must always understand:

Current state
What happened
What is processing
What action is available next
Who owns the next action

---

## 12. Dashboard

Dashboard must be role-aware.

Administrator dashboard:

- total candidates
- interviews by state
- processing queue
- failed jobs
- review queue
- recently finalized interviews
- recent audit events
- system readiness

Interviewer dashboard:

- assigned interviews
- today's interviews
- drafts
- interviews awaiting review
- processing interviews
- correction requests

Reviewer dashboard:

- pending review
- correction requests
- recently reviewed
- recently finalized

Do not invent analytics that the backend does not provide.

If an aggregate endpoint does not exist, either request backend support or calculate only from a deliberately bounded dataset where the semantics are correct.

---

## 13. Candidates

Build a production data table.

Columns:

- Reference Number
- Student Name
- Application Reference
- Grade
- Interview Date
- Assigned Interviewer
- Interview Status
- Created
- Actions

Features:

- Search
- Pagination
- Sorting where supported
- Status filtering
- Interviewer filtering
- Date filtering
- Empty state
- Loading state
- Error state
- Row action menu

Candidate creation form:

- Name
- Application reference
- Grade
- Interview date/time
- Assigned interviewer
- Optional metadata

Use React Hook Form + Zod.

Never lose entered data because of a validation error.

---

## 14. Interview Detail Workspace

This is the most important screen in the product.

Layout:

Header:

- Candidate identity
- Reference number
- Interview status
- Interviewer
- Date/time
- Actions

Below header:

Workflow timeline.

Main content should use tabs or a structured workspace:

Overview
Recording
Transcript
AI Summary
Interview Form
Review
Activity

Do not hide critical workflow information behind excessive navigation.

---

## 15. Interview Workflow Timeline

Display the lifecycle visually:

Draft
↓
Consent
↓
Recording
↓
Upload
↓
Processing
↓
Transcript
↓
AI Summary
↓
Form Draft
↓
Human Review
↓
Submission
↓
Principal Review
↓
Finalization

Highlight the current step.
Completed steps should remain visible.
Failed steps should explain the failure.

The timeline is informational; the backend decides whether a transition is valid.

---

## 16. Consent UX

Before recording or uploading audio, show a dedicated consent confirmation interface.

Must clearly display:

- Consent notice.
- Notice version.
- What audio is being recorded.
- Why it is processed.
- AI processing disclosure where required by policy.
- Confirmation control.
- Confirm button.

Do not make consent a tiny checkbox hidden in a form.

The recording action must remain disabled until confirmed consent is returned by the backend.

Withdrawal should be visually prominent but not destructive without confirmation.

---

## 17. Recording Interface

Build a professional recording interface.

Components:

- microphone permission state
- recording timer
- waveform or lightweight level indicator
- recording state
- pause/resume if backend/workflow permits
- stop
- cancel
- playback preview
- re-record confirmation

Browser recording should use MediaRecorder where supported.

Handle:

- unsupported browser
- microphone denied
- microphone unavailable
- device disconnected
- recording failure
- page navigation during recording

Never silently lose audio.

Before leaving an active recording page, warn the user.

---

## 18. Upload Interface

Support audio upload through a controlled uploader.

Show:

- filename
- MIME type
- size
- upload progress
- upload state
- checksum if returned by backend
- retry
- cancel where supported
- server confirmation

Validate client-side for UX, but backend validation is authoritative.

Do not upload files directly to Groq from the browser.

---

## 19. Processing Experience

Processing must never look frozen.

Show a processing pipeline:

Audio uploaded
✓

Queued
✓

Transcribing
...

Transcript generation

AI summary

Form generation

Use polling through TanStack Query unless a production WebSocket/SSE endpoint is later added.

Polling must stop when the terminal state is reached.

Do not poll aggressively.

Use exponential backoff or sensible intervals.

If processing fails:

- show failed stage
- show safe human-readable message
- show retry action if authorized
- show correlation ID for support

Never display raw provider exceptions to normal users.

---

## 20. Transcript Workspace

Create a professional transcript editor.

Layout:

Left / main:

- audio player
- playback controls
- timeline
- transcript segments

Right:

- selected segment metadata
- editing tools
- evidence/navigation context

Transcript segments must show:

- timestamp
- speaker if available
- text
- confidence if available
- edited indicator

Clicking a segment should seek the audio player to its start timestamp.

Playing audio should highlight the active transcript segment.

Editing a segment must preserve the original transcript value in the UI where the backend provides it.

Show:

Original
Edited

Never silently replace evidence.

---

## 21. AI Summary

AI output must be presented as an assistant-generated draft, not an official decision.

Clearly label:

AI-generated
Requires human review

Show structured sections:

Parent/Guardian Statements
Student Statements
Educational Background
Interests and Activities
School Expectations
Interviewer Documented Observations
Follow-up Questions
Unclear or Missing Information

Every statement should be traceable to transcript evidence when evidence is available from the backend.

Never display unsupported inference as fact.

Do not create a score or admission recommendation unless the backend explicitly provides one.

---

## 22. Interview Form

The official DPS interview form is the operational source of truth.

Do not create a visually different generic form if the official template is supplied.

The frontend must render fields dynamically from the versioned template returned by the backend.

Field types should support:

- text
- textarea
- date
- select
- checkbox
- radio
- structured list
- evidence-linked field

Each field should show:

- label
- generated value
- current value
- review state
- evidence indicator
- edited indicator

Generated values must be visually distinguished from human-edited values.

---

## 23. Human Review

Human review must be first-class.

Reviewers should see:

- Candidate details
- Recording
- Transcript
- AI summary
- Form
- Evidence
- Review history

Reviewer actions:

- approve/review
- request correction
- finalize where authorized

Correction request must require meaningful remarks.

Show exactly what needs correction.

---

## 24. Finalization

Finalization is irreversible from the normal UI unless the backend explicitly supports reopening.

Use a strong confirmation dialog.

Display:

This interview will become read-only after finalization.

Require explicit confirmation.

After successful finalization:

- disable editing
- show finalized state
- display finalization timestamp
- display reviewer identity where available
- enable PDF export

---

## 25. PDF Export

PDF export should call the backend.

The browser must not attempt to recreate the official PDF layout.

Provide:

View PDF
Download PDF

Use a safe authenticated request.

Show progress state.

Handle PDF generation failure cleanly.

---

## 26. Review Queue

Build a high-quality review queue.

Columns:

- Candidate
- Reference
- Interviewer
- Submitted At
- Current State
- Age
- Priority if backend provides it
- Action

Filters:

- state
- interviewer
- date
- search

Provide a strong empty state:

No interviews are currently waiting for review.

Do not show fake counts.

---

## 27. Administration

Administrator screens:

Users
Templates
Processing Jobs
Audit Log
Retention
System Status

Users:

- list
- search
- role
- active/inactive
- create staff user
- activate/deactivate where backend permits

Templates:

- template list
- versions
- current version
- version metadata

Processing Jobs:

- job ID
- interview
- job type
- status
- attempts
- next attempt
- error
- created
- started
- finished
- retry action

Audit Log:

- timestamp
- actor
- action
- resource
- resource ID
- correlation ID
- metadata summary

Never expose sensitive metadata unnecessarily.

---

## 28. Error Handling

Every route must support:

Loading
Empty
Error
Success

Use:

- inline validation errors
- toast notifications for completed actions
- persistent banners for important failures
- route-level error boundaries
- retry controls

Error messages should be human-readable.

Example:

Bad:

"IntegrityError: duplicate key value violates unique constraint"

Good:

"This recording has already been uploaded for this interview."

Keep the backend correlation ID available in a support details area.

---

## 29. Loading UX

Avoid giant spinners.

Use skeletons for page content.

Use inline progress indicators for mutations.

Buttons must become disabled while their mutation is in progress when duplicate submission could be harmful.

Never disable the entire application during one small API request.

---

## 30. TanStack Query Architecture

Create query keys centrally.

Examples:

['me']
['candidates', filters]
['candidate', candidateId]
['interviews', filters]
['interview', interviewId]
['processing', interviewId]
['transcript', interviewId]
['summary', interviewId]
['form', interviewId]
['review-history', interviewId]
['admin-jobs', filters]
['audit', filters]

Mutations must invalidate only affected resources.

Use optimistic updates only when rollback is safe.

Do not optimistically change critical workflow states such as finalized/reviewed.

For processing status, use controlled polling.

---

## 31. API Client

Create one typed HTTP client.

Responsibilities:

- base URL
- authentication
- correlation ID
- JSON handling
- multipart upload
- error normalization
- timeout handling
- abort signals
- retry policy

Create domain clients:

authApi
usersApi
candidatesApi
interviewsApi
recordingsApi
processingApi
transcriptsApi
summariesApi
formsApi
reviewsApi
adminApi

Do not call fetch directly from page components.

---

## 32. Forms

All complex forms must use React Hook Form.

Use Zod schemas for:

- candidate creation
- login
- password reset
- consent
- form fields where schema permits
- review actions

Server validation remains authoritative.

Display field-level errors.

Do not erase the entire form after one invalid field.

---

## 33. Accessibility

Target WCAG 2.2 AA quality.

Requirements:

- keyboard navigation
- visible focus
- semantic HTML
- accessible dialogs
- accessible tables
- accessible form labels
- screen-reader labels
- proper error announcements
- sufficient contrast
- no color-only status indicators
- reduced-motion support

Test keyboard-only navigation through critical workflows.

---

## 34. Responsive Design

Primary target is desktop because interviews and review workflows are operational tasks.

Support:

- desktop 1440px
- laptop 1280px
- tablet
- smaller screens for monitoring and basic administration

The transcript workspace may require a specialized responsive layout.

On smaller screens:

- collapse sidebar
- stack panels
- keep audio controls accessible
- avoid horizontal overflow where possible

---

## 35. Performance

Requirements:

- route-level code splitting
- lazy-load heavy transcript/editor modules
- lazy-load PDF preview if used
- avoid unnecessary re-renders
- virtualize very long transcript lists if needed
- do not render thousands of segments at once without virtualization
- optimize icons and assets
- avoid huge client bundles

Use Server Components where appropriate.
Use Client Components only when interactivity requires them.

Do not turn the entire application into a client component.

---

## 36. Security

Frontend security requirements:

- no secrets in NEXT_PUBLIC variables
- no API keys in browser bundles
- no sensitive data in URLs
- no transcript text in analytics payloads
- no audio data in logs
- no PII in console logs
- sanitize/render trusted content safely
- secure authentication handling
- prevent accidental token exposure
- prevent duplicate destructive actions

Do not add third-party analytics until privacy requirements are approved.

---

## 37. Observability

Use correlation IDs.

For production errors capture:

- route
- action
- correlation ID
- user role
- non-sensitive error category

Never capture:

- passwords
- access tokens
- refresh tokens
- audio
- transcript contents
- student PII unless explicitly approved

---

## 38. Testing Strategy

Unit tests:

- permission functions
- status presentation
- API error normalization
- validation schemas
- query key factories
- formatting

Component tests:

- login
- consent
- recording state
- upload
- transcript editor
- form editor
- review dialog

End-to-end Playwright tests:

1. Login.
2. Create candidate.
3. Create interview.
4. Confirm consent.
5. Start recording state.
6. Upload audio test fixture.
7. Observe processing.
8. Open transcript.
9. Edit transcript segment.
10. Review AI summary.
11. Edit form field.
12. Submit interview.
13. Reviewer opens queue.
14. Reviewer requests correction.
15. Interviewer corrects.
16. Reviewer reviews.
17. Finalize.
18. Export PDF.

Do not use production student data in tests.

---

## 39. Mocking

Create a typed API mock layer for frontend development.

Mocks must reflect the actual backend OpenAPI schemas.

Do not invent fake endpoints.

Use fixtures for:

- each interview status
- processing failure
- transcript with timestamps
- summary
- form
- correction request
- finalized interview

The mock layer must be removable without rewriting UI components.

---

## 40. UX Details That Matter

The product should always answer these questions:

Where am I?
What interview am I working on?
What is the current state?
What happened?
What is processing?
What can I do now?
Why can I not do something?
Who needs to act next?
Is my change saved?
Is the information AI-generated or human-reviewed?
Can I trace this information to evidence?

If a user cannot answer these questions quickly, improve the UX.

---

## 41. Do Not Build

Do not build:

- marketing landing page inside the application
- fake AI chat assistant
- generic CRM dashboard
- fake analytics
- fake admission scoring
- invented student recommendations
- decorative AI brain graphics
- excessive glassmorphism
- unnecessary animations
- client-side business workflow engine
- direct Groq calls from frontend
- hardcoded production credentials
- localStorage-based secret dumping
- fake processing progress

---

## 42. Production Acceptance Criteria

The frontend is not complete until:

- TypeScript passes.
- ESLint passes.
- Unit tests pass.
- Component tests pass.
- Playwright critical workflows pass against a staging backend.
- No critical accessibility violations remain.
- No secrets exist in client bundles.
- All backend API errors have normalized UX.
- All role boundaries are tested.
- All workflow states render correctly.
- Finalized records are read-only.
- Processing polling terminates correctly.
- Upload failures are recoverable.
- Recording failures are recoverable.
- Session expiration is handled.
- PDF export works against staging.
- Mobile/tablet layouts have no critical overflow.
- Production build succeeds.
- Source maps and error reporting do not leak sensitive data.

---

## 43. Implementation Order

Implement in this exact order:

Phase 1
Project setup, TypeScript, Tailwind, shadcn/ui, linting, testing, environment configuration.

Phase 2
API client, authentication, session handling, RBAC, permission layer.

Phase 3
Application shell, navigation, user menu, global error/loading systems.

Phase 4
Dashboard and candidate management.

Phase 5
Interview creation and interview workspace.

Phase 6
Consent and recording/upload workflow.

Phase 7
Processing status and job UX.

Phase 8
Transcript workspace with synchronized audio.

Phase 9
AI summary and evidence presentation.

Phase 10
Dynamic DPS interview form.

Phase 11
Submission and principal/reviewer workflow.

Phase 12
Finalization and PDF export.

Phase 13
Administration console.

Phase 14
Accessibility, security, performance, testing, observability.

Phase 15
Production staging validation and deployment hardening.

---

## 44. Final Engineering Rule

Build the frontend as a real enterprise application connected to the existing FastAPI backend.

Do not fake functionality to make the UI look complete.

Do not hide backend limitations.

If the backend lacks a required endpoint, document it and add the backend contract rather than inventing a client-side workaround.

Every important screen must have loading, empty, error, success, permission-denied, and read-only states where applicable.

The finished result should feel like a polished institutional operations platform designed for real DPS staff handling real student interview workflows.
