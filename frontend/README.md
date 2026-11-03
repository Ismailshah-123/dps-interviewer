# DPS Interview Documentation — Frontend

React 19 + Vite + TypeScript + Tailwind CSS v4 + shadcn/ui. See the repository README for setup.

- `src/lib/api.ts` — typed API client. Access token in memory only; refresh via the backend's HttpOnly cookie.
- `src/features/recording/` — MediaRecorder capture, IndexedDB chunk persistence, upload with progress.
- `src/features/interviews/` — interview workspace: consent, processing, transcript, AI summary, form, review.
- `e2e/` — Playwright workflow test (starts an isolated test backend and a fake microphone).

Navigation and hidden buttons are conveniences only. The backend authorizes every request.

| Command | Purpose |
|---|---|
| `npm run dev` | Dev server on :5173, proxies `/api` to :8000 |
| `npm run typecheck` / `npm run lint` | `tsc -b`, oxlint |
| `npm test` | Vitest unit/component tests |
| `npm run build` | Production build to `dist/` |
| `npm run test:e2e` | Playwright end-to-end workflow |
