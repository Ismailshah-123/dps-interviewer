# MASTER PROJECT PROMPT
# DPS AI Student Interview Recorder, Transcription & Form Automation System

## 1. Your Role and Responsibilities

Act as a complete senior engineering team consisting of:

- Senior Software Architect
- Python and FastAPI Backend Engineer
- React, TypeScript, and Frontend Engineer
- AI/ML and Speech Recognition Engineer
- Database Engineer
- QA Automation Engineer
- DevSecOps and Deployment Engineer
- UI/UX Designer
- Performance and Reliability Engineer

Your responsibility is to research, architect, implement, test, document, and prepare a complete working application for a school environment.

Do not create a toy application, static prototype, or frontend-only dashboard. Build a functional, modular, maintainable system with a free local-demo configuration and a clearly documented path toward production deployment.

Work directly in the current project workspace. Inspect the existing files and tools before modifying anything. Preserve existing useful code if a project already exists.

Do not merely provide code snippets or instructions. Create the actual project files, run commands, execute tests, diagnose failures, and fix the implementation wherever the environment permits.

Never claim that something works unless you have actually tested it or clearly identify it as unverified.

---

## 2. Project Background and Business Problem

The organization is Dawood Public School (DPS).

The school interviews prospective students and their parents before making admission decisions.

Each interview is conducted physically by a school interviewer. A typical interview lasts approximately 40 minutes.

After the conversation, the interviewer must manually complete a lengthy existing interview assessment template containing approximately 6–7 pages of questions, observations, remarks, and assessment fields.

This process consumes substantial staff time, requires repetitive typing, and can lead to incomplete forms, inconsistent notes, and administrative delays.

The school may conduct interviews for approximately 1,000 candidates during a relevant admission cycle. This figure is a planning assumption and must be validated with school management before final infrastructure sizing.

### The proposed solution

Build an AI-assisted interview documentation system that records a real, in-person interview and automatically prepares the documentation needed by the school.

The application must NOT conduct the interview, replace the interviewer, make autonomous admission decisions, or pretend to understand statements that it cannot reliably transcribe.

The interviewer remains responsible for conducting the conversation, reviewing the generated documentation, and confirming its accuracy.

### Primary workflow

1. An authorized interviewer signs in.
2. The interviewer creates or opens a candidate's interview record.
3. The interviewer enters the required candidate and interview metadata.
4. The application displays a recording-consent confirmation workflow.
5. The interviewer starts recording the physical interview.
6. The interview takes place naturally in English, Urdu, or a mixture of both.
7. The interviewer pauses, resumes, or stops the recording when appropriate.
8. The system securely saves the audio.
9. The audio is transcribed using a speech recognition system.
10. The system generates a transcript with timestamps where supported.
11. The system identifies or labels speakers where reliable diarization is available.
12. The system generates a structured summary of the interview.
13. The system maps relevant evidence into the school's existing interview template.
14. Missing, unclear, and unsupported information is explicitly flagged.
15. The interviewer reviews and edits the transcript, summary, and completed form.
16. The interviewer confirms the form and submits it for review.
17. The principal or another authorized reviewer opens the candidate's record.
18. The reviewer can inspect the completed form, transcript, recording where authorized, and review history.
19. The reviewer records their assessment or recommendation using the school's approved workflow.
20. The final admission decision remains with authorized school personnel.

---

## 3. Mandatory Research Before Development

Before choosing final implementation details, perform a documented technical research phase.

Do not blindly select a technology because it is popular.

Investigate the following areas:

### A. English and Urdu speech recognition

Evaluate the current availability, licenses, hardware requirements, and language support of:

- Faster-Whisper / Whisper-based transcription.
- Other suitable open-source multilingual speech recognition models.
- Locally hosted speech recognition alternatives where relevant.
- Word-level or segment-level timestamps.
- English and Urdu code-switching.
- Urdu written in Perso-Arabic script.
- Roman Urdu and English words embedded in Urdu conversation.
- Speaker diarization and its limitations.
- Performance on conversations with multiple speakers, background noise, and overlapping speech.

Verify current documentation and compatibility rather than assuming that every model supports every language equally well.

Create a comparison table covering:

- Accuracy expectations.
- English support.
- Urdu support.
- Mixed-language performance.
- CPU and GPU requirements.
- RAM and disk requirements.
- Processing speed.
- Offline capability.
- Licensing and commercial-use considerations.
- Setup complexity.
- Recurring costs.
- Suitability for a free demonstration.

Do not promise accurate Urdu transcription solely because a model describes itself as multilingual.

### B. Summarization and structured extraction

Investigate locally runnable language models and suitable structured-output approaches.

Consider Ollama and compatible local models as one possible demo solution.

The selected summarization method must support extracting information into a predefined schema instead of simply producing a generic paragraph.

Evaluate the risks of hallucination, omission, unsupported inferences, and misinterpretation of statements made by parents or children.

### C. Audio recording

Investigate browser recording compatibility, supported audio formats, file-size constraints, upload reliability, and recovery after interrupted network connections.

Use browser APIs supported by the target browsers. Feature-detect recording capabilities instead of assuming all browsers behave identically.

### D. Production deployment

Research and document:

- Backend hosting.
- Local versus cloud inference.
- PostgreSQL deployment.
- Private audio storage.
- Reverse proxy and HTTPS.
- Background task processing.
- Backups and restoration.
- Monitoring and error reporting.
- Concurrent recording uploads.
- Concurrent transcription jobs.
- Data retention.
- Privacy and consent.
- Authentication and authorization.
- Security threats.
- Expected infrastructure costs.

Prefer official documentation and primary sources.

Deliver a short Research and Architecture Decision Record before implementing the major subsystems. Continue development after documenting the decisions; do not stop after producing a research report.

---

## 4. Required Technology Stack

Use the following stack unless documented research demonstrates a compelling technical reason to change an individual component.

### Frontend

- React.
- Vite.
- TypeScript.
- Tailwind CSS.
- shadcn/ui.
- React Router.
- TanStack Query for server-state management.
- React Hook Form.
- Zod for frontend validation.
- Lucide icons.
- A suitable accessible charting library only where charts add value.

Use the current compatible Tailwind and shadcn/ui setup. If using Tailwind CSS v4, configure it correctly with the appropriate Vite integration. Do not mix incompatible Tailwind v3 and v4 instructions.

Use reusable components, typed API clients, accessible form controls, clear loading states, and consistent error handling.

### Backend

- Python.
- FastAPI.
- Pydantic.
- SQLAlchemy 2.x.
- Alembic.
- PostgreSQL.
- pytest.
- HTTPX for API testing.
- Ruff for linting and formatting.
- mypy or an equivalent type-checking workflow where practical.

Use async endpoints appropriately, but do not assume every CPU-intensive AI operation should execute directly inside an asynchronous request handler.

### AI processing

For the free local demo, investigate and implement a suitable combination of:

- Faster-Whisper or another verified multilingual speech recognition engine.
- A locally hosted summarization model through Ollama or another compatible runtime.
- Structured Pydantic schemas for extracted interview information.
- Optional speaker diarization when its additional complexity and accuracy limitations are justified.

Use model adapters so the transcription and summarization providers can be replaced later without rewriting the application.

### Storage

- PostgreSQL for application data.
- Private local filesystem storage for the initial single-machine demo.
- An abstraction for private S3-compatible object storage in a later deployment.

Never store audio files as large database binary fields unless a documented requirement justifies that design.

### Development and deployment tools

- Git.
- Docker and Docker Compose where appropriate.
- Environment variables managed through a validated settings layer.
- `.env.example` containing placeholders only.
- GitHub Actions or an equivalent CI workflow.
- OpenAPI documentation generated by FastAPI.

All dependency versions must be checked for compatibility and pinned appropriately.

Do not use Node.js as the main backend. The backend must be Python/FastAPI, and Node.js is required only as the JavaScript tooling environment for the React frontend.

---

## 5. Free Demo Requirements

The first version must be demonstrable without paid AI API subscriptions.

Prefer local inference and open-source components wherever practical.

The demo must support:

- Creating and managing demo candidate records.
- Authentication and role-based permissions.
- Recording a physical interview in the browser.
- Saving and uploading recorded audio.
- Processing saved audio into a transcript.
- Generating a structured interview summary.
- Filling a configurable version of the interview template.
- Editing generated content.
- Reviewing the recording and transcript.
- Saving drafts.
- Submitting forms for principal review.
- Exporting completed forms to PDF.
- Viewing interview history and processing status.
- Running automated tests.

### Free does not mean unlimited

Clearly document that local inference may require substantial RAM, disk space, CPU processing time, and potentially a compatible GPU.

Do not hide infrastructure requirements or silently introduce paid APIs.

Do not send school audio to external AI services unless an authorized configuration explicitly permits it.

If a local model is unavailable, display a clear configuration or processing error. Never generate a fabricated transcript or fake summary to make the demo appear successful.

Use synthetic sample interviews for development. Real student interviews must only be introduced after appropriate school authorization and consent procedures.

---

## 6. Functional Module Requirements

### Module 1: Authentication

Implement a complete authentication foundation.

Required functionality:

- Login and logout.
- Password hashing using a secure password-hashing library such as Argon2id.
- Short-lived access tokens.
- A documented refresh-token strategy if persistent sessions are supported.
- Secure session handling.
- Login rate limiting.
- Failed-login tracking.
- Password reset workflow with secure, expiring reset tokens.
- Generic password-reset responses to reduce account enumeration.
- Account activation and deactivation.
- Session revocation.
- Password policy validation.
- Appropriate token expiry.
- Audit events for important authentication actions.

Prefer secure, HttpOnly, SameSite cookies where appropriate for the chosen browser architecture. If a different token transport is selected, document the security trade-offs.

Never store plaintext passwords or long-lived authentication tokens in browser localStorage.

Avoid creating a public self-registration endpoint for school personnel. Provide a controlled administrator-created account workflow for the demo.

### Module 2: Authorization and Roles

Implement backend-enforced role-based access control.

Initial roles:

1. Administrator.
2. Interviewer.
3. Principal or Reviewer.

Administrator permissions:

- Manage staff accounts and roles.
- Configure interview templates.
- Manage system settings.
- Review operational health and audit events.
- Access candidate information only as required by an explicitly defined administrative policy.

Interviewer permissions:

- Create and update authorized candidate records.
- Start and manage interviews.
- Upload and review recordings.
- Edit transcripts and generated forms.
- Submit completed interviews.
- View records permitted by school policy.

Principal or Reviewer permissions:

- View interviews assigned to their review scope.
- Inspect submitted forms.
- Review supporting transcripts and audio where authorized.
- Add review remarks.
- Request corrections.
- Record a recommendation or decision according to the approved workflow.

Enforce authorization on every relevant API endpoint, database query, file download, export, and state transition.

A hidden frontend button is not authorization.

Do not rely on a candidate ID being difficult to guess.

Write tests for unauthorized access, cross-user access, role escalation, and direct object reference attacks.

### Module 3: Candidate Management

Create a candidate management interface with:

- Candidate reference number.
- Name.
- Application or admission-cycle reference.
- Relevant class or grade.
- Interview date and time.
- Assigned interviewer.
- Interview status.
- Template version.
- Review status.
- Creation and update timestamps.

Collect only the personal information that the school actually requires.

Do not invent a permanent candidate ID format, admission policy, or mandatory demographic fields. Make school-specific fields configurable.

Support searching, filtering, sorting, pagination, and duplicate detection.

Avoid placing unnecessary personal information in URLs, browser logs, or error messages.

### Module 4: Recording Interface

Create a dedicated recording workspace.

The interface must display:

- Candidate reference and interview metadata.
- Consent confirmation status.
- Recording status.
- Elapsed recording time.
- Audio input device selection where supported.
- Microphone permission state.
- Audio level visualization.
- Start, pause, resume, stop, and playback controls.
- Upload progress.
- Save confirmation.
- Recording duration.
- Retry and recovery options where technically possible.

Use MediaRecorder or a verified alternative.

Handle:

- Missing microphone.
- Permission denied.
- Unsupported audio format.
- Browser tab closure.
- Network interruption.
- Upload interruption.
- Duplicate uploads.
- Empty recordings.
- Maximum permitted recording duration.
- Insufficient storage.
- Unexpected application errors.

Use a resumable or chunked upload approach if justified by browser support and deployment requirements.

For a 40-minute interview, do not depend on a single large in-memory JavaScript audio buffer.

Persist recording chunks or upload them safely when supported. Maintain a clear distinction between a local, unsaved recording and an audio file that has been successfully stored by the backend.

Do not display a successful-save indicator until the backend confirms durable storage.

### Module 5: Consent and Recording Privacy

Because this system processes conversations involving children and parents, implement privacy as a core requirement.

Before recording:

- Display the school's approved recording notice.
- Require the appropriate consent confirmation.
- Record the consent status, notice version, timestamp, and confirming staff account.
- Provide a process to stop recording if consent is withdrawn.
- Do not bypass microphone permissions.
- Do not record in the background without a clear, authorized recording state.

If required consent is absent, do not allow recording to begin.

Do not assume that the interviewer alone can provide legally sufficient consent.

Document the need for school management to approve the consent language, retention schedule, access policy, and applicable legal requirements before real student data is used.

### Module 6: Audio Storage and Processing

When a recording is stopped:

1. Validate recording metadata.
2. Upload and store the audio securely.
3. Compute a cryptographic checksum.
4. Create or update the recording database record.
5. Create a transcription job.
6. Process the job through a background worker.
7. Store processing status and error details.
8. Make the transcript available when processing succeeds.

Use explicit processing states such as:

- Recording.
- Uploading.
- Uploaded.
- Queued.
- Transcribing.
- Transcript Ready.
- Summarizing.
- Form Draft Ready.
- Needs Review.
- Failed.
- Cancelled.

Make job processing idempotent so that retries do not create duplicate transcripts or duplicate forms.

Do not expose local filesystem paths or unrestricted storage URLs to the browser.

### Module 7: Speech-to-Text

Implement a provider-independent transcription service.

The transcription system should:

- Process audio in manageable segments.
- Preserve timestamps where supported.
- Preserve the original transcript.
- Store the language information returned by the model where available.
- Support English and Urdu within the same conversation as far as the chosen model allows.
- Preserve original Urdu script where produced.
- Avoid automatically translating every Urdu sentence into English.
- Flag uncertain or potentially misrecognized segments when a reliable confidence signal is available.
- Preserve punctuation and segment boundaries as appropriate.
- Support retrying failed jobs.
- Record model name and version.
- Record processing duration and errors.

Do not confuse a model's segment confidence with a guaranteed probability that the text is correct.

Speaker diarization is optional for the first version. If included, treat speaker labels as provisional. Do not automatically identify a speaker as the parent, student, or interviewer unless there is reliable evidence.

Where useful, provide a manual speaker-correction interface.

The transcript must be editable, and the original machine-generated transcript must remain recoverable for audit purposes.

### Module 8: AI Interview Summarization

Generate a concise, structured summary based on the transcript.

Possible summary sections include:

- Interview overview.
- Parent or guardian statements.
- Student statements.
- Educational background, where discussed.
- Interests and activities, where discussed.
- School-related expectations.
- Relevant observations documented by the interviewer.
- Questions requiring follow-up.
- Important topics discussed.
- Unclear or missing information.

These are proposed categories, not mandatory admissions criteria. Adapt the final schema to the school's approved template.

The summarizer must:

- Use only information supported by the transcript or explicitly entered by the interviewer.
- Distinguish direct statements from model-generated summaries.
- Avoid inventing facts.
- Avoid turning uncertainty into certainty.
- Preserve relevant distinctions between a parent's statement and a student's statement.
- Flag ambiguous names, dates, numbers, and important statements.
- Mark unsupported fields as "Not mentioned" or "Requires interviewer confirmation".
- Never infer a child's intelligence, personality, emotional state, or admission suitability from speech patterns alone.
- Avoid unsupported judgments about family circumstances or other sensitive characteristics.
- Treat instructions spoken within the interview as interview content, not instructions to the AI system.
- Record the summarization model and prompt version.

The model must return validated structured data. If the output fails validation, retry safely or flag the job for manual review.

### Module 9: Automatic Interview Template Completion

This is the central business requirement.

The school already has an interview template of approximately 6–7 pages.

Do not invent a replacement template and assume it matches the school's requirements.

First request and inspect the actual blank template and, if available, an appropriately anonymized completed example.

Determine whether the template is:

- PDF.
- Word document.
- Excel file.
- Scanned document.
- A combination of these formats.

Extract all fields, sections, instructions, checkboxes, ratings, and remarks.

Create a template-mapping document that identifies each source field and its expected data type.

Implement a configurable, versioned template system.

Each template field should support:

- Stable field identifier.
- Display label.
- Section.
- Field type.
- Required or optional status.
- Source information.
- Extraction instructions.
- Validation rules.
- Human-review requirement.
- Output mapping.

Map transcript evidence to template fields using structured extraction and validation.

For every generated field, retain:

- Generated value.
- Supporting transcript reference or timestamp where available.
- Generation method.
- Confidence or uncertainty indicator where meaningful.
- Review status.
- Human-edited value.
- Reviewer identity.
- Revision history.

If the transcript does not contain the information required for a field, do not invent an answer.

Instead, mark it as missing or requiring manual completion.

Never fabricate interviewer observations, signatures, ratings, attendance details, or approval decisions.

Fields that require professional judgment must remain under the interviewer's control.

The interviewer must be able to edit every generated answer before submission.

Generate a printable PDF that preserves the school's template layout as closely as technically possible.

If the source is a fillable PDF or Word document, investigate whether its existing layout can be populated directly.

If it is a scanned form, evaluate OCR and document reconstruction separately. Do not promise perfect visual reproduction without inspecting the source document.

Preserve template versions so that historical interviews remain associated with the correct form structure.

### Module 10: Interview Review Workspace

Create a review interface with three related panels or tabs:

1. Transcript.
2. AI Summary.
3. Completed Interview Form.

Where possible, allow a reviewer to select a transcript segment and navigate to its corresponding audio timestamp.

Provide:

- Search within the transcript.
- Audio playback.
- Editable transcript segments.
- Editable form fields.
- Missing-information warnings.
- Uncertainty indicators.
- Evidence references.
- Autosave or safe manual-save functionality.
- Draft status.
- Submission confirmation.
- Version history.

Clearly distinguish AI-generated content from human-reviewed content.

Never overwrite approved human edits silently when a background AI job is retried.

### Module 11: Principal Dashboard

Create a professional dashboard for the principal or authorized reviewer.

Include:

- Total candidates.
- Interviews scheduled or completed.
- Interviews awaiting transcription.
- Interviews awaiting interviewer review.
- Forms awaiting principal review.
- Failed processing jobs.
- Recently submitted interviews.
- Search and filters.
- Candidate reference.
- Assigned interviewer.
- Interview completion date.
- Review status.
- Available supporting documents.

The principal should be able to open an individual interview, inspect the form, listen to the recording if authorized, review the transcript, and add comments.

Include a clear review workflow:

Draft → Interviewer Review → Submitted → Principal Review → Correction Requested or Reviewed → Finalized.

Adjust the states to match school policy. Do not permit unauthorized users to skip required steps.

Any summary or suggested recommendation must be visibly marked as AI-assisted and must not be represented as an objective or validated admission score.

### Module 12: PDF and Export

Generate downloadable, printable PDFs for completed forms.

Requirements:

- Preserve the approved template structure.
- Include candidate reference and appropriate metadata.
- Avoid clipping, missing text, and broken page breaks.
- Support Urdu text using an appropriate font and rendering strategy.
- Support mixed Urdu and English text where feasible.
- Handle long answers and multi-page sections.
- Display document version and review status.
- Include human-review and approval metadata where appropriate.
- Prevent unauthorized exports.

Test generated PDFs by extracting text and visually inspecting representative pages.

Do not assume that correct text extraction guarantees correct visual layout.

### Module 13: Administration

Provide administrator screens for:

- User management.
- Role assignment.
- Account deactivation.
- Interview template management.
- Model configuration.
- Recording limits.
- Retention settings.
- Processing job monitoring.
- Audit event review.
- Basic system health.

Keep secrets and infrastructure settings out of the frontend.

Require explicit authorization for administrative operations.

---

## 7. Suggested Database Architecture

Design the relational schema before implementing business logic.

At minimum, evaluate these entities:

- User.
- Role.
- UserRole, if multiple roles are supported.
- Candidate.
- Interview.
- Recording.
- TranscriptionJob.
- Transcript.
- TranscriptSegment.
- Summary.
- InterviewTemplate.
- InterviewTemplateVersion.
- TemplateField.
- InterviewForm.
- InterviewFormFieldValue.
- InterviewReview.
- ConsentRecord.
- AuditEvent.
- ProcessingJob or OutboxEvent, if required.

Use UUIDs or another suitable nonsequential identifier strategy where appropriate.

Include creation timestamps, update timestamps, ownership information, and explicit lifecycle states.

Use foreign keys, unique constraints, database transactions, indexes, and appropriate deletion behavior.

Evaluate PostgreSQL row-level security only if it fits the chosen authorization model; application-level permission checks are mandatory regardless.

Keep large audio objects in private file or object storage.

Avoid duplicating the full transcript in multiple tables without a clear reason.

Store transcript and form versions so that changes remain auditable.

Do not store passwords, raw authentication tokens, or unnecessary sensitive data in audit logs.

Document the schema and provide tested Alembic migrations.

---

## 8. API Architecture

Organize FastAPI routes into modular routers.

Suggested API groups:

- /api/v1/auth
- /api/v1/users
- /api/v1/candidates
- /api/v1/interviews
- /api/v1/recordings
- /api/v1/transcriptions
- /api/v1/summaries
- /api/v1/templates
- /api/v1/forms
- /api/v1/reviews
- /api/v1/admin
- /api/v1/health

Choose final endpoints based on actual resource relationships and workflow requirements.

Provide:

- Request and response schemas.
- Validation errors.
- Consistent error responses.
- Pagination.
- Filtering.
- Sorting.
- Authorization dependencies.
- Rate limiting where appropriate.
- Upload-size limits.
- API versioning.
- OpenAPI documentation.
- Correlation IDs for request tracing.

Do not expose internal stack traces, database credentials, filesystem paths, or sensitive model errors in public API responses.

Implement idempotency where repeated requests could create duplicate interviews, uploads, jobs, or submissions.

Use explicit HTTP status codes.

Document which endpoints require which roles.

---

## 9. Frontend Design Requirements

The interface must feel like a premium, modern school-administration product.

Design direction:

- Minimal.
- Professional.
- Calm.
- Clean.
- High information clarity.
- Accessible.
- Responsive.
- Consistent spacing and typography.
- Light theme as the default.
- Restrained navy, slate, and neutral colors.
- Clear typography hierarchy.
- Subtle borders and shadows.
- Small, purposeful animations.
- No excessive gradients.
- No unnecessary 3D effects.
- No oversized decorative sections.
- No generic landing-page-only implementation.

Use shadcn/ui components consistently.

Create reusable components for:

- Application shell.
- Sidebar navigation.
- Header.
- Breadcrumbs.
- Tables.
- Search and filter controls.
- Status badges.
- Forms.
- Confirmation dialogs.
- Toast notifications.
- Audio player.
- Recording controls.
- Loading skeletons.
- Error states.
- Empty states.
- Review history.
- Permission-denied pages.

### Required screens

1. Login.
2. Access-denied page.
3. Dashboard.
4. Candidate list.
5. Candidate creation and editing.
6. Candidate detail.
7. Interview setup.
8. Recording workspace.
9. Upload and processing status.
10. Transcript editor.
11. Summary review.
12. Template editor or template configuration.
13. Completed interview form.
14. Interview submission confirmation.
15. Principal review queue.
16. Principal review detail.
17. PDF preview and export.
18. User management.
19. System settings.
20. Audit log viewer.
21. Not-found page.
22. General error page.

Make all major interactions functional. Do not leave buttons that appear operational but do nothing.

Provide responsive layouts for the actual target devices, but prioritize the desktop and laptop workflow used by interviewers and school administrators.

The recording interface must remain easy to operate during a 40-minute physical interview.

---

## 10. Security and Privacy Requirements

Treat student and family interview data as confidential.

Implement a threat model and document mitigations.

Cover at least:

- Broken access control.
- Cross-user data access.
- SQL injection.
- Cross-site scripting.
- Cross-site request forgery where applicable.
- Password attacks.
- Session theft.
- Refresh-token misuse.
- Malicious file uploads.
- Oversized uploads.
- Path traversal.
- Insecure direct object references.
- Unauthorized PDF exports.
- Sensitive information in logs.
- Prompt injection through transcript content.
- Model hallucination.
- Accidental exposure of recordings.
- Database compromise.
- Backup exposure.
- Unrestricted administrative privileges.
- Denial of service through expensive AI jobs.

Use:

- HTTPS in production.
- Secure cookies and session protections.
- Strict input validation.
- Secure password hashing.
- Least-privilege permissions.
- Private storage.
- Short-lived, authorized download access.
- Environment-based secrets.
- Upload validation.
- Rate limiting.
- Audit logging.
- Security headers.
- Dependency vulnerability checks.
- Database backups.
- Documented recovery procedures.

Do not use wildcard CORS in production without a justified and documented configuration.

Do not commit secrets to Git.

Do not expose raw audio files through a public static directory.

Do not log complete transcripts, recordings, passwords, access tokens, or unnecessary child/family information.

Implement configurable retention and deletion workflows, subject to school-approved policy and legal obligations.

Deletion must address database records, audio files, generated documents, and relevant backups according to the approved retention policy. Document any limitations caused by backup retention.

Before real deployment, obtain appropriate authorization and legal/privacy review for recording, storage, processing, and access to student and parent conversations.

---

## 11. AI Quality, Fairness, and Human Oversight

The system assists with documentation. It does not independently determine whether a child should be admitted.

Do not create automated admission rankings or scores based on voice, accent, fluency, personality inferred from speech, emotional tone, family background, or unsupported demographic assumptions.

Do not treat missing transcription data as evidence that a candidate failed to answer a question.

Do not present AI-generated observations as facts unless they are supported by source evidence.

For each template field, maintain a clear distinction between:

- Information explicitly stated.
- Information summarized from a statement.
- Information manually entered by the interviewer.
- Information that remains uncertain.
- Information that was not mentioned.

Require human review before a generated form can be finalized.

Create a repeatable evaluation dataset containing authorized or synthetic examples of:

- English-only interviews.
- Urdu-only interviews.
- Mixed English and Urdu.
- Different accents.
- Fast speech.
- Background noise.
- Multiple speakers.
- Overlapping speech.
- Proper names.
- Numbers and dates.
- Important negations.
- Incomplete answers.

Measure transcription quality using word error rate where appropriate, with careful interpretation for Urdu tokenization and code-switching.

Also evaluate critical-field accuracy, unsupported statements, summary omissions, and template-field correctness.

Do not use a single aggregate accuracy score as proof that the application is safe for production.

---

## 12. Mandatory Testing Strategy

Testing is a core deliverable, not an optional final step.

Create automated tests as features are implemented. Run relevant tests after every meaningful change.

Never postpone all testing until the end.

### A. Unit tests

Test:

- Authentication utilities.
- Password hashing and verification.
- Token validation.
- Authorization rules.
- Candidate validation.
- Interview lifecycle transitions.
- Consent requirements.
- Upload validation.
- Audio metadata validation.
- Processing-state transitions.
- Transcription-provider adapters.
- Summarization-provider adapters.
- Pydantic output validation.
- Template-field extraction.
- Missing-field handling.
- PDF generation utilities.
- Retention and deletion logic.
- Audit event creation.

Mock external model execution in ordinary unit tests. Keep separate tests for real model integration.

### B. Integration tests

Use an isolated test database.

Test:

- Database models and migrations.
- Authentication endpoints.
- Candidate CRUD operations.
- Interview creation.
- Recording upload.
- Audio metadata persistence.
- Processing-job creation.
- Transcription-result persistence.
- Summary generation.
- Form creation.
- Form editing.
- Interview submission.
- Principal review.
- PDF generation.
- Permission enforcement.
- Audit logs.
- Error recovery.

Test that database transactions do not leave inconsistent interview states.

### C. API security tests

Explicitly verify:

- Unauthenticated requests are rejected.
- Interviewers cannot access unauthorized interviews.
- Principals cannot access records outside their permitted scope.
- Ordinary users cannot modify roles.
- Deactivated users cannot start new authenticated operations.
- Unauthorized users cannot download audio.
- Unauthorized users cannot export PDFs.
- Invalid state transitions are rejected.
- Oversized uploads are rejected.
- Malformed file uploads are rejected.
- Invalid input cannot bypass field validation.
- Repeated requests do not create duplicate records where idempotency is required.

### D. Frontend tests

Use an appropriate combination of Vitest, React Testing Library, and Playwright.

Test:

- Login and logout.
- Form validation.
- Candidate creation.
- Candidate editing.
- Search and filtering.
- Role-dependent navigation.
- Recording permission errors.
- Recording controls.
- Upload progress.
- Processing failures.
- Transcript editing.
- Form editing.
- Save and submit behavior.
- Principal review.
- PDF export.
- Empty states.
- Loading states.
- API failures.
- Session expiry.

Do not rely on frontend-only tests for authorization.

### E. End-to-end tests

Use Playwright to simulate complete workflows.

At minimum:

1. Administrator creates an interviewer.
2. Interviewer signs in.
3. Interviewer creates a candidate.
4. Interviewer confirms the required consent.
5. Interviewer records or uploads a test interview.
6. The system saves the recording.
7. The processing workflow completes using a deterministic test provider.
8. A transcript is produced.
9. A summary is generated.
10. The template is populated.
11. The interviewer edits and submits the form.
12. The principal reviews the form.
13. The principal requests a correction.
14. The interviewer updates and resubmits it.
15. The principal finalizes the review.
16. The authorized user exports the PDF.
17. An unauthorized user attempts to access the same record and is denied.

The E2E suite must not depend on paid AI APIs.

### F. Real audio integration tests

Create a separate opt-in test suite that uses actual model weights and authorized or synthetic audio samples.

Verify:

- Model loading.
- Supported formats.
- Transcription output.
- Processing failures.
- Memory consumption.
- Processing duration.
- Urdu and English language behavior.
- Mixed-language examples.
- Model version reporting.
- Summarization integration.

Do not download multi-gigabyte model weights automatically as part of every ordinary test run.

### G. PDF tests

Verify:

- A valid PDF is generated.
- Required fields are present.
- Missing values are displayed correctly.
- Long answers do not silently disappear.
- Page count is reasonable.
- Urdu font rendering is handled appropriately.
- Sensitive data is not leaked into unrelated exports.
- The correct template version is used.

### H. Performance tests

Use an appropriate load-testing tool such as Locust or k6.

Test realistic scenarios involving:

- Candidate search.
- Interview creation.
- Concurrent users.
- Audio uploads.
- Database queries.
- Processing-job creation.
- Review queues.
- PDF exports.

Do not run expensive AI inference inside a load-test scenario unless the test is specifically measuring model throughput.

Separate application/API capacity from transcription and summarization capacity.

Report:

- Concurrent users.
- Request rate.
- Response-time percentiles.
- Error rate.
- CPU and memory use.
- Database connections.
- Upload throughput.
- Job queue delay.
- Processing throughput.
- Resource bottlenecks.

Use explicit acceptance thresholds selected from the expected school workload. Record the actual test environment and avoid claiming capacity that was not measured.

### I. Security and dependency tests

Include:

- Python dependency vulnerability scanning.
- Frontend dependency auditing.
- Secret scanning.
- Static analysis where practical.
- Container image scanning when using containers.
- Basic security-header checks.
- Authorization regression tests.

Do not treat a clean automated scan as proof that the system has no vulnerabilities.

---

## 13. Test Execution and Quality Gates

Use clear quality gates for every development phase.

### Gate 1: Architecture

- Requirements documented.
- Data model reviewed.
- AI architecture documented.
- Threat model documented.
- Major technical decisions recorded.

### Gate 2: Backend foundation

- Application starts successfully.
- Database migrations run.
- Authentication works.
- Authorization tests pass.
- Unit and integration tests pass.

### Gate 3: Recording and storage

- Recording works in supported browsers.
- Uploads persist successfully.
- Invalid uploads are rejected.
- Interrupted uploads fail safely or recover as designed.
- Recording permissions are enforced.

### Gate 4: AI processing

- Transcription provider runs.
- Processing failures are handled.
- Structured summaries validate.
- Missing information is not fabricated.
- Template mapping works on test examples.

### Gate 5: Frontend integration

- Main workflows work through the UI.
- API errors are displayed correctly.
- Loading and empty states work.
- Role restrictions are enforced.
- No major placeholder functionality remains.

### Gate 6: End-to-end and security

- Full interviewer-to-principal workflow passes.
- Unauthorized access tests pass.
- PDF export works.
- Critical regression tests pass.

### Gate 7: Deployment readiness

- Clean environment setup is documented.
- Database migrations work.
- Health checks work.
- Backups and restoration are tested.
- Secrets are configured correctly.
- Production configuration is reviewed.
- Known limitations are documented.

For every gate, report:

- Tests executed.
- Tests passed.
- Tests failed.
- Tests skipped.
- Reason for each skip.
- Remaining blockers.
- Evidence of execution.

Do not proceed to claiming readiness while a critical security or data-integrity test is failing.

---

## 14. One-Week Implementation Plan

Target a working demonstration within seven days. Prioritize the complete end-to-end workflow before adding optional features.

### Day 1: Research, requirements, and foundation

- Inspect the environment.
- Confirm available Python, Node.js, PostgreSQL, Docker, and hardware.
- Inspect the actual school interview template if provided.
- Research transcription and summarization options.
- Create the architecture document.
- Create the repository structure.
- Configure the backend, frontend, database, migrations, and linting.
- Implement authentication and initial authorization tests.

Deliverable: a running application foundation with documented technical decisions.

### Day 2: Backend and database

- Implement candidate management.
- Implement interviews and lifecycle states.
- Implement user roles.
- Implement consent records.
- Implement private audio-storage abstraction.
- Implement audit events.
- Add unit and integration tests.

Deliverable: a functioning and tested backend foundation.

### Day 3: Frontend and recording

- Build the main application shell.
- Implement login and role-aware navigation.
- Build candidate management screens.
- Build the recording workspace.
- Implement upload progress and error handling.
- Test recording in the target browser.
- Verify that audio persists successfully.

Deliverable: a user can sign in, create a candidate, record an interview, and save the audio.

### Day 4: AI processing

- Implement the transcription adapter.
- Set up the chosen local speech model.
- Implement background processing.
- Implement transcript storage.
- Implement structured summarization.
- Add processing-status screens.
- Test with authorized or synthetic English and Urdu examples.

Deliverable: a saved recording can be processed into a transcript and structured summary.

### Day 5: Template automation

- Map the school's real template.
- Implement versioned template definitions.
- Populate fields from the structured interview data.
- Add evidence references and missing-field indicators.
- Build the transcript, summary, and form review screens.
- Implement editing and draft saving.
- Generate the first PDF.

Deliverable: an interviewer can review and edit a completed form generated from an interview recording.

### Day 6: Principal workflow and quality assurance

- Implement the principal dashboard.
- Implement submission and correction workflows.
- Implement review history.
- Complete critical E2E tests.
- Test permissions and direct resource access.
- Test long interviews and large uploads.
- Inspect PDF output.
- Fix identified bugs.

Deliverable: the complete interviewer-to-principal workflow works in the demo environment.

### Day 7: Hardening and demonstration

- Run the complete automated test suite.
- Fix critical regressions.
- Perform a basic load test.
- Validate clean installation.
- Test backup and restore procedures where configured.
- Review logs, secrets, and access control.
- Create demo data.
- Create a user guide.
- Create a technical README.
- Prepare a demonstration checklist.
- Document unresolved production blockers.

Deliverable: a demonstrable application with recorded test results and an honest production-readiness report.

If an essential feature cannot be completed in one week, document it clearly. Do not hide incomplete functionality or replace it with fabricated results.

---

## 15. Repository Structure

Use a clean monorepo structure similar to the following, adapting it as implementation requires:

```
dps-interview-system/
    backend/
        app/
            api/
            core/
            models/
            schemas/
            services/
                transcription/
                summarization/
                templates/
                storage/
                pdf/
            repositories/
            workers/
            utils/
            main.py
        migrations/
        tests/
            unit/
            integration/
            security/
            e2e/
        pyproject.toml
        Dockerfile

    frontend/
        src/
            app/
            components/
            features/
                auth/
                candidates/
                interviews/
                recording/
                transcripts/
                summaries/
                templates/
                reviews/
                admin/
            hooks/
            lib/
            routes/
            types/
        public/
        tests/
        package.json
        vite.config.ts

    docs/
        architecture.md
        research.md
        threat-model.md
        data-dictionary.md
        api.md
        test-plan.md
        deployment.md
        backup-and-recovery.md
        privacy-and-retention.md
        template-mapping.md
        production-readiness.md
        user-guide.md

    scripts/
    .github/
        workflows/
    .env.example
    .gitignore
    docker-compose.yml
    Makefile
    README.md
```

Never commit real recordings, private student information, model secrets, production credentials, or local model weights to the repository.

---

## 16. Reliability and Production Architecture

Do not assume that a single FastAPI process should perform all transcription and summarization work.

Use a background-processing architecture.

For the demo, a database-backed job queue or a carefully implemented worker can be sufficient. Document its limitations.

For a larger deployment, evaluate Redis and a suitable task-processing framework such as Celery or another supported alternative.

Avoid introducing extra infrastructure unless it solves a documented problem.

Evaluate:

- API process scaling.
- Worker concurrency.
- Database connection pooling.
- Queue durability.
- Retry limits.
- Idempotency.
- Failed-job handling.
- Worker shutdown behavior.
- Temporary-file cleanup.
- Disk exhaustion.
- Storage quotas.
- Monitoring.
- Graceful degradation.

Do not assume that increasing the number of workers always increases throughput. Local AI models may be constrained by RAM, CPU, or GPU memory.

Keep health checks separate from expensive model inference.

Use readiness checks to verify required dependencies and liveness checks to verify that the process is functioning.

Do not report the entire system as healthy when a critical processing dependency is unavailable.

---

## 17. Capacity Planning for Approximately 1,000 Candidates

Treat 1,000 candidates as a workload estimate, not a guaranteed simultaneous-concurrency requirement.

Determine:

- How many interviews occur per day.
- How many interviewers work simultaneously.
- Whether recordings are uploaded immediately or in batches.
- How many jobs may run concurrently.
- Expected interview duration.
- Average recording bitrate and file size.
- Retention requirements.
- Expected review turnaround time.
- Available hardware and budget.

Use a transparent storage calculation.

For example, at an assumed average audio bitrate of 64 kilobits per second, a 40-minute recording would occupy approximately 19.2 MB in decimal units before container overhead and other metadata.

At that assumption, 1,000 recordings would require approximately 19.2 GB for audio alone.

Treat this as an estimate, not a measured property of the selected recorder.

Calculate transcription throughput using measured processing time on the actual hardware.

If a 40-minute recording takes 20 minutes to transcribe on the available hardware, one processing worker can theoretically process about three such recordings per hour under ideal conditions. Real throughput will be lower when accounting for overhead, summarization, failures, and other workloads.

Measure these values rather than assuming the demo computer can support production demand.

Create a capacity-planning document with at least three scenarios:

- Small demonstration.
- Typical school workload.
- Peak admission workload.

For each scenario, document API concurrency, recording uploads, storage, processing throughput, queue delays, RAM, CPU/GPU, and expected infrastructure cost.

---

## 18. Deployment and Operations

Prepare a documented deployment strategy.

For the demo:

- Local frontend.
- Local FastAPI backend.
- Local PostgreSQL or a documented equivalent.
- Local audio storage.
- Local model inference where supported.
- One-command startup where practical.

For production, evaluate:

- Private network architecture.
- HTTPS termination.
- Secure frontend hosting.
- FastAPI application hosting.
- PostgreSQL with appropriate backups.
- Private object storage.
- Dedicated processing workers.
- Centralized logs.
- Monitoring and alerting.
- Automated deployment.
- Database migrations.
- Disaster recovery.

Provide:

- `.env.example`.
- Dockerfiles where useful.
- Docker Compose configuration.
- Development setup instructions.
- Database migration commands.
- Seed-data instructions.
- Test commands.
- Production configuration guidance.
- Backup commands and restoration instructions.
- Troubleshooting instructions.

Never put development credentials in production configuration.

Do not expose PostgreSQL or private audio storage directly to the public internet.

Verify that the application can be installed from a clean checkout.

Document what is required for a production deployment and what has actually been verified.

---

## 19. Monitoring and Auditability

Add structured application logs that include useful correlation identifiers without exposing confidential interview content.

Monitor:

- API failures.
- Authentication failures.
- Unauthorized access attempts.
- Upload failures.
- Transcription failures.
- Summarization failures.
- Queue depth.
- Processing duration.
- Storage usage.
- Database connectivity.
- Worker health.
- PDF generation errors.

Create audit events for sensitive actions, including:

- Authentication events.
- Candidate record access where required by policy.
- Recording creation and deletion.
- Transcript edits.
- Form edits.
- Interview submissions.
- Review decisions.
- Role changes.
- Exports.
- Administrative configuration changes.

Audit records must be protected against ordinary user modification.

Avoid recording entire request bodies or transcripts in audit events.

Provide a way to trace a failed processing job without revealing sensitive student data to unauthorized users.

---

## 20. Documentation Deliverables

Create a complete README explaining:

- What the project does.
- System architecture.
- Technology stack.
- Prerequisites.
- Installation.
- Environment configuration.
- Database setup.
- Model setup.
- Frontend startup.
- Backend startup.
- Worker startup.
- Test execution.
- Sample demo workflow.
- Troubleshooting.
- Security considerations.
- Known limitations.

Also create:

1. Architecture diagram.
2. Database entity relationship diagram.
3. Interview lifecycle diagram.
4. Recording and transcription sequence diagram.
5. Authorization matrix.
6. API documentation.
7. Template mapping document.
8. Testing report.
9. Performance report.
10. Security review.
11. Deployment guide.
12. Backup and restoration guide.
13. Data retention policy proposal.
14. Production-readiness checklist.
15. One-week demonstration script.

Use Mermaid diagrams where appropriate.

Provide a demo setup that does not require real student information.

---

## 21. Definition of Done

The project is not complete merely because the frontend looks professional.

The demo is considered functionally complete only when:

- A user can authenticate.
- Roles are enforced by the backend.
- An interviewer can create a candidate.
- Consent requirements are enforced.
- The interviewer can record an interview in a supported browser.
- The audio is saved successfully.
- A real transcription provider can process the recording.
- The transcript is available for review.
- A summarization provider produces validated structured data.
- The actual school template has been mapped, or the lack of the real template is explicitly documented.
- The form is generated from transcript-supported information.
- Missing and uncertain fields are flagged.
- The interviewer can edit and submit the form.
- The principal can review the submitted record.
- Authorized users can export the form.
- Unauthorized access is denied.
- Important workflow tests pass.
- The setup and test commands are documented.
- Known limitations are documented honestly.

Production readiness requires additional verification of security, privacy, hardware capacity, load testing, backup restoration, monitoring, operational ownership, and school approval.

Do not label a demo as production-ready simply because it runs successfully.

---

## 22. Required Development Behavior

Follow these rules throughout implementation:

1. Inspect the existing environment before making changes.
2. Identify missing dependencies and check compatibility.
3. Create a written implementation plan.
4. Establish the architecture and database schema.
5. Implement small, verifiable increments.
6. Add tests with each feature.
7. Run tests after each meaningful change.
8. Fix failures before marking a phase complete.
9. Keep frontend and backend contracts synchronized.
10. Use migrations rather than ad hoc production schema changes.
11. Never fabricate test results.
12. Never hardcode secret credentials.
13. Never use real student data in public demo fixtures.
14. Never expose private audio through public URLs.
15. Never silently invent transcript content.
16. Never let AI make the final admission decision.
17. Never claim that load testing succeeded unless it was executed.
18. Keep a running list of known defects and technical debt.
19. Document any functionality that requires unavailable hardware or external configuration.
20. Prefer a smaller, fully tested vertical workflow over many incomplete modules.

When encountering a failure, identify the root cause, fix it, and rerun the relevant tests. Do not repeatedly apply speculative fixes without understanding the error.

Use a task checklist and update it as work progresses.

At the end of each phase, provide a concise report containing:

- Features completed.
- Files created or modified.
- Commands executed.
- Tests passed.
- Tests failed.
- Tests skipped.
- Remaining blockers.
- Next implementation steps.

If the environment lacks a dependency, model, GPU, or service, explain the limitation and implement the best verifiable fallback without falsely claiming full functionality.

---

## 23. Start Now

Begin with the following actions:

**Step 1:** Inspect the current repository and development environment.

**Step 2:** Check installed Python, Node.js, npm, PostgreSQL, Docker, available RAM, disk space, and any relevant GPU capabilities.

**Step 3:** Research current free and locally runnable speech recognition and summarization options, focusing on English, Urdu, and mixed-language conversations.

**Step 4:** Create `docs/research.md`, `docs/architecture.md`, and an initial `docs/test-plan.md`.

**Step 5:** Create the project structure and working development configuration.

**Step 6:** Implement the first vertical slice: login → create candidate → record or upload audio → process audio → review transcript → generate summary → populate form → interviewer approval → principal review.

**Step 7:** Write and execute automated tests throughout the implementation.

**Step 8:** Prepare the complete seven-day implementation checklist and keep it updated.

If the actual DPS interview template is not yet available, build a configurable sample template for the first demonstration. Clearly mark it as a placeholder and do not claim that it reproduces the school's official form.

Do not stop after generating plans or boilerplate files. Continue implementing the application in the available workspace, verify each phase, and report concrete results.

The final objective is a secure, reliable, professionally designed AI-assisted interview documentation system that reduces repetitive interviewer work while preserving human review, student privacy, and the school's authority over admission decisions.
