import { describeMediaError, detectRecorderSupport, fileExtension, rmsLevel, uploadMimeType } from './recorder'

describe('detectRecorderSupport', () => {
  const mediaDevices = {}

  it('requires a secure context', () => {
    expect(detectRecorderSupport({ isSecureContext: false, mediaDevices, MediaRecorder: { isTypeSupported: () => true } })).toMatchObject({ supported: false })
  })

  it('reports a browser without MediaRecorder', () => {
    const r = detectRecorderSupport({ isSecureContext: true, mediaDevices })
    expect(r.supported).toBe(false)
    expect(r.reason).toMatch(/cannot record/i)
  })

  it('prefers Opus in WebM when available', () => {
    expect(detectRecorderSupport({ isSecureContext: true, mediaDevices, MediaRecorder: { isTypeSupported: () => true } }).mimeType).toBe('audio/webm;codecs=opus')
  })

  it('falls back to MP4 for Safari-like browsers', () => {
    const r = detectRecorderSupport({ isSecureContext: true, mediaDevices, MediaRecorder: { isTypeSupported: (t: string) => t === 'audio/mp4' } })
    expect(r).toEqual({ supported: true, mimeType: 'audio/mp4' })
  })

  it('refuses when no server-accepted format is recordable', () => {
    expect(detectRecorderSupport({ isSecureContext: true, mediaDevices, MediaRecorder: { isTypeSupported: () => false } }).supported).toBe(false)
  })
})

describe('format helpers', () => {
  it('strips codec parameters for upload', () => {
    expect(uploadMimeType('audio/webm;codecs=opus')).toBe('audio/webm')
    expect(fileExtension('audio/mp4')).toBe('m4a')
    expect(fileExtension('audio/ogg;codecs=opus')).toBe('ogg')
  })

  it('explains permission and device errors in plain language', () => {
    expect(describeMediaError(new DOMException('x', 'NotAllowedError'))).toMatch(/permission was denied/i)
    expect(describeMediaError(new DOMException('x', 'NotFoundError'))).toMatch(/no microphone/i)
    expect(describeMediaError(new DOMException('x', 'NotReadableError'))).toMatch(/in use/i)
  })

  it('computes a bounded level from silence and loud input', () => {
    expect(rmsLevel(new Uint8Array(512).fill(128))).toBe(0)
    const loud = new Uint8Array(512).map((_, i) => (i % 2 ? 255 : 0))
    expect(rmsLevel(loud)).toBe(1)
  })
})
