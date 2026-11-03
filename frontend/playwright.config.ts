import path from 'node:path'
import { defineConfig, devices } from '@playwright/test'

const root = path.resolve(import.meta.dirname, '..')
const python = process.platform === 'win32' ? path.join(root, 'backend/.venv/Scripts/python.exe') : path.join(root, 'backend/.venv/bin/python')
// The synthetic interview plays through Chromium's fake microphone so MediaRecorder captures real audio.
const fakeAudio = path.join(root, 'samples/synthetic/english_interview.wav')

export default defineConfig({
  testDir: './e2e',
  timeout: 120_000,
  workers: 1,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: 'http://localhost:5174',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    permissions: ['microphone'],
    launchOptions: {
      args: ['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream', `--use-file-for-fake-audio-capture=${fakeAudio}`],
    },
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: [
    { command: `"${python}" ${path.join(root, 'scripts/e2e_backend.py')}`, url: 'http://127.0.0.1:8001/api/v1/health/live', reuseExistingServer: false, timeout: 60_000 },
    { command: 'npx vite --port 5174 --strictPort', url: 'http://localhost:5174', env: { VITE_API_PROXY_TARGET: 'http://127.0.0.1:8001' }, reuseExistingServer: false, timeout: 60_000 },
  ],
})
