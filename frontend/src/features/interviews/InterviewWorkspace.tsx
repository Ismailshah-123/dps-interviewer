import { useQuery } from '@tanstack/react-query'
import { Link, useParams, useSearchParams } from 'react-router'
import { Download } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ErrorState, LoadingRows, PageHeader, StatusBadge } from '@/components/common'
import { useAuth } from '@/features/auth/AuthProvider'
import { RecordingPanel } from '@/features/recording/RecordingPanel'
import { api } from '@/lib/api'
import { EDITABLE_STATUSES, STATUS_META, isProcessing } from '@/lib/status'
import { ConsentCard } from './ConsentCard'
import { FormPanel, downloadPdf } from './FormPanel'
import { ProcessingCard } from './ProcessingCard'
import { ReviewPanel } from './ReviewPanel'
import { SummaryPanel } from './SummaryPanel'
import { TranscriptPanel } from './TranscriptPanel'

const TABS = ['overview', 'transcript', 'summary', 'form', 'review'] as const

export function InterviewWorkspace() {
  const { id = '' } = useParams()
  const { user } = useAuth()
  const [params, setParams] = useSearchParams()
  const interview = useQuery({
    queryKey: ['interview', id],
    queryFn: () => api.interview(id),
    refetchInterval: (q) => (q.state.data && isProcessing(q.state.data.status) ? 3000 : false),
  })
  const meta = useQuery({ queryKey: ['meta'], queryFn: api.meta, staleTime: Infinity })

  if (interview.isPending) return <LoadingRows rows={8} />
  if (interview.isError) return <ErrorState error={interview.error} onRetry={() => interview.refetch()} />
  const i = interview.data
  const isOwner = user?.role === 'administrator' || (user?.role === 'interviewer' && user.id === i.interviewer_id)
  const editable = isOwner && EDITABLE_STATUSES.includes(i.status)
  const canSubmit = isOwner && (i.status === 'needs_review' || i.status === 'correction_requested')
  // A failed interview is recovered by an administrator retrying the failed job, not by re-recording.
  const showRecorder = isOwner && ['draft', 'recording'].includes(i.status) && i.consent_status !== 'withdrawn'
  const hasOutputs = !['draft', 'recording', 'uploading', 'uploaded', 'queued', 'transcribing', 'cancelled'].includes(i.status)
  const formReady = ['needs_review', 'submitted', 'principal_review', 'correction_requested', 'reviewed', 'finalized'].includes(i.status)
  const defaultTab = formReady ? 'form' : 'overview'
  const tab = TABS.includes(params.get('tab') as (typeof TABS)[number]) ? params.get('tab')! : defaultTab

  return (
    <>
      <PageHeader
        eyebrow={<span className="font-mono">{i.candidate_reference}</span>}
        title={i.candidate_name ?? 'Interview'}
        description={
          <span className="flex flex-wrap items-center gap-2">
            <StatusBadge status={i.status} /> {STATUS_META[i.status]?.description}
          </span>
        }
        actions={
          <>
            <Button asChild variant="outline">
              <Link to={`/candidates/${i.candidate_id}`}>Candidate record</Link>
            </Button>
            {formReady && (
              <Button variant="outline" onClick={() => void downloadPdf(i)}>
                <Download /> Export PDF
              </Button>
            )}
          </>
        }
      />
      {i.status === 'correction_requested' && isOwner && (
        <div className="mb-4 rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          The principal requested a correction. See the remarks under <button className="underline" onClick={() => setParams({ tab: 'review' })}>Review</button>, update the form, then
          resubmit.
        </div>
      )}
      <Tabs value={tab} onValueChange={(v) => setParams({ tab: v }, { replace: true })}>
        <TabsList className="mb-4">
          <TabsTrigger value="overview">Recording & status</TabsTrigger>
          <TabsTrigger value="transcript" disabled={!hasOutputs}>
            Transcript
          </TabsTrigger>
          <TabsTrigger value="summary" disabled={!hasOutputs}>
            AI summary
          </TabsTrigger>
          <TabsTrigger value="form" disabled={!hasOutputs}>
            Interview form
          </TabsTrigger>
          <TabsTrigger value="review">Review</TabsTrigger>
        </TabsList>
        <TabsContent value="overview" className="grid gap-6 lg:grid-cols-5">
          <div className="space-y-6 lg:col-span-3">
            {showRecorder ? (
              <RecordingPanel interview={i} maxUploadBytes={meta.data?.upload.max_bytes} />
            ) : (
              <ProcessingCard interview={i} />
            )}
          </div>
          <div className="space-y-6 lg:col-span-2">
            <ConsentCard interview={i} canAct={isOwner} />
          </div>
        </TabsContent>
        <TabsContent value="transcript">{hasOutputs && <TranscriptPanel interview={i} editable={editable} />}</TabsContent>
        <TabsContent value="summary">{hasOutputs && <SummaryPanel interviewId={i.id} />}</TabsContent>
        <TabsContent value="form">{hasOutputs && <FormPanel interview={i} editable={editable} canSubmit={canSubmit} />}</TabsContent>
        <TabsContent value="review">
          <ReviewPanel interview={i} />
        </TabsContent>
      </Tabs>
    </>
  )
}
