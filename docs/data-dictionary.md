# Data Dictionary

Core entities are UUID keyed and timestamped.

- User: controlled school staff account, role, activation state, failed-login state.
- RefreshSession: server-side refresh-token session record and revocation state.
- PasswordResetToken: hashed, expiring password-reset credential.
- Candidate: minimum admission/interview metadata and assigned interviewer.
- Interview: lifecycle state, candidate, interviewer, and immutable template-version association.
- ConsentRecord: recording notice version, status, confirming staff account, timestamps.
- Recording: private storage key, MIME type, size, SHA-256 checksum, duration metadata.
- ProcessingJob: durable database-backed work item with status, attempts and failure details.
- Transcript: original machine transcript and provider/model metadata.
- TranscriptSegment: timestamped editable segment retaining original machine text after edits.
- Summary: validated structured AI output plus provider/model/prompt version.
- InterviewTemplate / InterviewTemplateVersion: versioned configurable field definitions.
- InterviewForm / InterviewFormFieldValue: generated and human-reviewed form state.
- InterviewReview: reviewer action, remarks and recommendation.
- AuditEvent: protected operational audit trail without raw transcripts or secrets.
- LoginAttempt: authentication success/failure history without passwords.
