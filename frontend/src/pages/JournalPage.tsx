import { BarChart3, BookOpenText, Clock3, LoaderCircle, ShieldCheck, Sparkles } from 'lucide-react'
import { useEffect, useState, type FormEvent } from 'react'

import PageHeader from '../components/PageHeader'
import { analyzeText, type AnalysisResult, type EmotionLabel } from '../lib/analysis'
import { ApiError } from '../lib/api'
import {
  createJournal,
  listJournals,
  type JournalEntry,
} from '../lib/journal'

const MAX_JOURNAL_LENGTH = 10_000
const emotionLabels: EmotionLabel[] = ['joy', 'sadness', 'anger', 'fear', 'neutral']

function formatJournalDate(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return 'Date unavailable'
  }
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date)
}

export default function JournalPage() {
  const [text, setText] = useState('')
  const [entries, setEntries] = useState<JournalEntry[]>([])
  const [loadingHistory, setLoadingHistory] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [latestAnalysis, setLatestAnalysis] = useState<AnalysisResult | null>(null)

  useEffect(() => {
    let active = true
    void listJournals()
      .then((items) => {
        if (active) {
          setEntries(items)
        }
      })
      .catch((caughtError: unknown) => {
        if (active) {
          setError(
            caughtError instanceof ApiError
              ? caughtError.message
              : 'Your journal history could not be loaded.',
          )
        }
      })
      .finally(() => {
        if (active) {
          setLoadingHistory(false)
        }
      })

    return () => {
      active = false
    }
  }, [])

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const normalizedText = text.trim()
    setError('')
    setSuccess('')
    setLatestAnalysis(null)

    if (!normalizedText) {
      setError('Write something before saving your journal entry.')
      return
    }

    setSaving(true)
    let entry: JournalEntry | null = null
    try {
      const savedEntry = await createJournal(normalizedText)
      entry = savedEntry
      setEntries((current) => [savedEntry, ...current.filter((item) => item.id !== savedEntry.id)])
      const analysis = await analyzeText(normalizedText, 'journal', savedEntry.id)
      setLatestAnalysis(analysis)
      setText('')
      setSuccess('Your journal entry was saved and analyzed privately.')
    } catch (caughtError) {
      const message = caughtError instanceof ApiError
        ? caughtError.message
        : 'The request could not be completed.'
      setError(
        entry
          ? `Your journal was saved, but analysis failed: ${message}`
          : `Your journal entry could not be saved: ${message}`,
      )
    } finally {
      setSaving(false)
    }
  }

  return (
    <section className="space-y-8">
      <PageHeader
        description="Put your thoughts into words. You will always be shown what is saved and analyzed."
        eyebrow="Daily reflection"
        title="How are you feeling today?"
      />
      <form className="card mx-auto max-w-3xl" onSubmit={(event) => void handleSubmit(event)}>
        <div className="flex items-center justify-between gap-4">
          <label className="text-sm font-semibold" htmlFor="journal-entry">
            Journal entry
          </label>
          <span className="text-xs tabular-nums text-muted">
            {text.length.toLocaleString()} / {MAX_JOURNAL_LENGTH.toLocaleString()}
          </span>
        </div>
        <textarea
          className="field-input mt-3 min-h-64 resize-y py-4 leading-6"
          id="journal-entry"
          maxLength={MAX_JOURNAL_LENGTH}
          onChange={(event) => setText(event.target.value)}
          placeholder="Write about your day, what stood out, or what is on your mind…"
          value={text}
        />
        {error && <p className="form-error mt-4" role="alert">{error}</p>}
        {success && (
          <p className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800" role="status">
            {success}
          </p>
        )}
        <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-xs leading-5 text-muted">Avoid including information you would not want stored.</p>
          <button className="button-primary justify-center" disabled={saving} type="submit">
            {saving ? (
              <LoaderCircle aria-hidden="true" className="animate-spin" size={17} />
            ) : (
              <Sparkles aria-hidden="true" size={17} />
            )}
            {saving ? 'Saving and analyzing…' : 'Save and analyze'}
          </button>
        </div>
      </form>

      {latestAnalysis && (
        <section aria-labelledby="latest-analysis-heading" className="card mx-auto max-w-3xl">
          <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.16em] text-sage">Latest result</p>
              <h2 className="mt-1 font-display text-2xl font-semibold" id="latest-analysis-heading">Text-derived mood estimate</h2>
              <p className="mt-2 text-sm text-muted">
                Detected {latestAnalysis.language} · {Math.round(latestAnalysis.confidence * 100)}% model confidence
              </p>
            </div>
            <div className="rounded-2xl bg-pine px-5 py-4 text-center text-white">
              <p className="text-xs text-white/70">Mood estimate</p>
              <p className="mt-1 font-display text-4xl font-semibold">{latestAnalysis.mood_score}</p>
              <p className="text-xs text-white/70">out of 100</p>
            </div>
          </div>

          <div className="mt-7 grid gap-7 md:grid-cols-[1fr_0.8fr]">
            <div>
              <div className="mb-4 flex items-center gap-2">
                <BarChart3 aria-hidden="true" className="text-sage" size={19} />
                <h3 className="text-sm font-semibold">Emotion distribution</h3>
              </div>
              <div className="space-y-3">
                {emotionLabels.map((emotion) => {
                  const percentage = Math.round(latestAnalysis.emotions[emotion] * 100)
                  return (
                    <div key={emotion}>
                      <div className="mb-1 flex justify-between text-xs">
                        <span className="capitalize text-muted">{emotion}</span>
                        <span className="font-semibold tabular-nums">{percentage}%</span>
                      </div>
                      <div className="h-2 overflow-hidden rounded-full bg-mist">
                        <div className="h-full rounded-full bg-sage" style={{ width: `${percentage}%` }} />
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            <div className="rounded-2xl bg-canvas p-5">
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">Dominant emotion</p>
              <p className="mt-2 font-display text-3xl font-semibold capitalize text-pine">{latestAnalysis.dominant_emotion}</p>
              <div className="mt-5 flex items-start gap-2 border-t border-line pt-4 text-xs leading-5 text-muted">
                <ShieldCheck aria-hidden="true" className="mt-0.5 shrink-0" size={16} />
                <p>{latestAnalysis.disclaimer}</p>
              </div>
            </div>
          </div>
        </section>
      )}

      <section aria-labelledby="journal-history-heading" className="mx-auto max-w-3xl">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.16em] text-sage">Private history</p>
            <h2 className="mt-1 font-display text-2xl font-semibold" id="journal-history-heading">Recent entries</h2>
          </div>
          <BookOpenText aria-hidden="true" className="text-sage" size={24} />
        </div>

        {loadingHistory ? (
          <div className="card flex items-center justify-center gap-2 text-sm text-muted" role="status">
            <LoaderCircle aria-hidden="true" className="animate-spin" size={18} />
            Loading your entries…
          </div>
        ) : entries.length === 0 ? (
          <div className="card text-center">
            <BookOpenText aria-hidden="true" className="mx-auto text-sage" size={28} />
            <p className="mt-3 font-semibold">No journal entries yet</p>
            <p className="mt-1 text-sm text-muted">Your saved reflections will appear here.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {entries.map((entry) => (
              <article className="card" key={entry.id}>
                <div className="flex items-center gap-2 text-xs text-muted">
                  <Clock3 aria-hidden="true" size={15} />
                  <time dateTime={entry.created_at}>{formatJournalDate(entry.created_at)}</time>
                </div>
                <p className="mt-4 whitespace-pre-wrap text-sm leading-7 text-ink">{entry.text}</p>
              </article>
            ))}
          </div>
        )}
      </section>
    </section>
  )
}
