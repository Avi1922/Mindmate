import {
  Activity,
  BookOpenText,
  ChartNoAxesCombined,
  LoaderCircle,
  MessageCircleMore,
  RefreshCw,
  Sparkles,
} from 'lucide-react'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import PageHeader from '../components/PageHeader'
import type { EmotionLabel } from '../lib/analysis'
import { ApiError } from '../lib/api'
import { getDailyMoodHistory, type DailyMoodRecord } from '../lib/mood'

const emotionLabels: EmotionLabel[] = ['joy', 'sadness', 'anger', 'fear', 'neutral']
const emotionColors: Record<EmotionLabel, string> = {
  joy: 'bg-amber-400',
  sadness: 'bg-sky-500',
  anger: 'bg-rose-500',
  fear: 'bg-violet-500',
  neutral: 'bg-sage',
}

function utcDate(): string {
  return new Date().toISOString().slice(0, 10)
}

function shortDate(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    weekday: 'short',
    timeZone: 'UTC',
  }).format(new Date(`${value}T00:00:00Z`))
}

function fullDate(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeZone: 'UTC',
  }).format(new Date(`${value}T00:00:00Z`))
}

export default function DashboardPage() {
  const [records, setRecords] = useState<DailyMoodRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadDashboard = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      setRecords(await getDailyMoodHistory(7))
    } catch (caughtError) {
      setError(
        caughtError instanceof ApiError
          ? caughtError.message
          : 'Your dashboard data could not be loaded.',
      )
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    let active = true
    void getDailyMoodHistory(7)
      .then((items) => {
        if (active) {
          setRecords(items)
        }
      })
      .catch((caughtError: unknown) => {
        if (active) {
          setError(
            caughtError instanceof ApiError
              ? caughtError.message
              : 'Your dashboard data could not be loaded.',
          )
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false)
        }
      })

    return () => {
      active = false
    }
  }, [])

  const today = records.find((record) => record.date === utcDate()) ?? null
  const activity = useMemo(
    () => records.reduce(
      (totals, record) => ({
        journals: totals.journals + record.journal_count,
        conversations: totals.conversations + record.conversation_count,
        analyses: totals.analyses + record.analysis_count,
      }),
      { journals: 0, conversations: 0, analyses: 0 },
    ),
    [records],
  )
  const chartData = records.map((record) => ({
    date: record.date,
    day: shortDate(record.date),
    mood: record.mood_score,
  }))
  const activityCards = [
    { label: 'Journal entries', value: activity.journals, icon: BookOpenText },
    { label: 'Conversations', value: activity.conversations, icon: MessageCircleMore },
    { label: 'Analyses', value: activity.analyses, icon: Sparkles },
  ]

  return (
    <section className="space-y-8">
      <PageHeader
        action={(
          <button
            className="inline-flex items-center gap-2 self-start rounded-xl border border-line bg-white px-4 py-2.5 text-sm font-semibold text-ink shadow-sm transition hover:border-sage disabled:opacity-60 md:self-auto"
            disabled={loading}
            onClick={() => void loadDashboard()}
            type="button"
          >
            <RefreshCw className={loading ? 'animate-spin' : ''} size={16} />
            Refresh
          </button>
        )}
        description="Your recent check-ins, combined into transparent text-derived emotional signals. Dates use UTC."
        eyebrow="Last 7 days"
        title="Your wellbeing dashboard"
      />

      {error && (
        <div className="form-error flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between" role="alert">
          <span>{error}</span>
          <button className="font-semibold underline" onClick={() => void loadDashboard()} type="button">Try again</button>
        </div>
      )}

      {loading && records.length === 0 ? (
        <div className="card grid min-h-72 place-items-center" role="status">
          <div className="text-center text-muted">
            <LoaderCircle className="mx-auto animate-spin text-sage" size={30} />
            <p className="mt-3 text-sm">Loading your mood history…</p>
          </div>
        </div>
      ) : records.length === 0 && !error ? (
        <div className="card mx-auto max-w-2xl py-14 text-center">
          <Activity className="mx-auto text-sage" size={34} />
          <h2 className="mt-5 font-display text-2xl font-semibold">Your dashboard is ready for a check-in</h2>
          <p className="mx-auto mt-3 max-w-lg text-sm leading-6 text-muted">
            Save and analyze a journal entry to create your first daily mood estimate and trend point.
          </p>
          <Link className="button-primary mt-6" to="/journal">Write a journal entry</Link>
        </div>
      ) : (
        <>
          <div className="grid gap-4 lg:grid-cols-[1.15fr_1fr]">
            <article className="card flex min-h-72 flex-col justify-between overflow-hidden bg-pine text-white">
              {today ? (
                <>
                  <div>
                    <p className="text-sm font-medium text-white/70">Today&apos;s mood estimate</p>
                    <div className="mt-4 flex items-end gap-3">
                      <p className="font-display text-7xl font-semibold tabular-nums">{today.mood_score}</p>
                      <p className="pb-2 text-lg text-white/60">/ 100</p>
                    </div>
                    <p className="mt-4 text-sm text-white/80">
                      Dominant emotion: <span className="font-semibold capitalize text-white">{today.dominant_emotion}</span>
                    </p>
                  </div>
                  <div className="mt-8 border-t border-white/15 pt-4 text-xs leading-5 text-white/65">
                    <p>{today.analysis_count} {today.analysis_count === 1 ? 'analysis' : 'analyses'} · Updated {fullDate(today.date)}</p>
                    <p className="mt-1">{today.disclaimer}</p>
                  </div>
                </>
              ) : (
                <>
                  <div>
                    <p className="text-sm font-medium text-white/70">Today&apos;s mood estimate</p>
                    <p className="mt-5 font-display text-5xl font-semibold">No check-in yet</p>
                    <p className="mt-4 max-w-md text-sm leading-6 text-white/70">Your earlier history is below. Add a journal entry to create today&apos;s UTC record.</p>
                  </div>
                  <Link className="mt-8 inline-flex w-fit rounded-xl bg-white px-4 py-2.5 text-sm font-semibold text-pine" to="/journal">Check in now</Link>
                </>
              )}
            </article>

            <article className="card min-h-72">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-semibold">Emotion distribution</p>
                  <p className="mt-1 text-xs text-muted">{today ? 'Today’s averaged signals' : 'Available after today’s check-in'}</p>
                </div>
                <ChartNoAxesCombined className="text-sage" size={22} />
              </div>
              {today ? (
                <div className="mt-7 space-y-4">
                  {emotionLabels.map((emotion) => {
                    const percentage = Math.round(today.emotions[emotion] * 100)
                    return (
                      <div key={emotion}>
                        <div className="mb-1.5 flex justify-between text-xs">
                          <span className="font-medium capitalize">{emotion}</span>
                          <span className="tabular-nums text-muted">{percentage}%</span>
                        </div>
                        <div
                          aria-label={`${emotion}: ${percentage}%`}
                          aria-valuemax={100}
                          aria-valuemin={0}
                          aria-valuenow={percentage}
                          className="h-2.5 overflow-hidden rounded-full bg-mist"
                          role="progressbar"
                        >
                          <div
                            className={`h-full rounded-full ${emotionColors[emotion]}`}
                            style={{ width: `${percentage}%` }}
                          />
                        </div>
                      </div>
                    )
                  })}
                </div>
              ) : (
                <div className="mt-12 rounded-2xl bg-canvas px-5 py-8 text-center text-sm text-muted">No emotion data for today.</div>
              )}
            </article>
          </div>

          <article className="card">
            <div>
              <p className="text-sm font-semibold">Seven-day mood trend</p>
              <p className="mt-1 text-xs text-muted">Only days with analyzed check-ins are plotted.</p>
            </div>
            <div className="mt-6 h-64 w-full sm:h-72" aria-label="Seven-day mood score line chart" role="img">
              <ResponsiveContainer height="100%" width="100%">
                <LineChart data={chartData} margin={{ left: -20, right: 10, top: 10, bottom: 0 }}>
                  <CartesianGrid stroke="#e2ede8" strokeDasharray="4 4" vertical={false} />
                  <XAxis axisLine={false} dataKey="day" tick={{ fill: '#667b75', fontSize: 12 }} tickLine={false} />
                  <YAxis axisLine={false} domain={[0, 100]} tick={{ fill: '#667b75', fontSize: 12 }} tickLine={false} ticks={[0, 25, 50, 75, 100]} />
                  <Tooltip
                    contentStyle={{ border: '1px solid #d7e2dd', borderRadius: 14, boxShadow: '0 12px 30px -18px rgb(23 49 43 / 0.4)' }}
                    labelFormatter={(_, payload) => payload[0]?.payload?.date ? fullDate(payload[0].payload.date as string) : ''}
                  />
                  <Line activeDot={{ r: 6 }} connectNulls={false} dataKey="mood" dot={{ fill: '#205c4f', r: 4 }} name="Mood estimate" stroke="#205c4f" strokeWidth={3} type="monotone" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </article>

          <div>
            <p className="mb-3 text-xs font-bold uppercase tracking-[0.16em] text-muted">Activity · last 7 UTC days</p>
            <div className="grid gap-4 sm:grid-cols-3">
              {activityCards.map(({ label, value, icon: Icon }) => (
                <article className="card" key={label}>
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-muted">{label}</p>
                    <Icon className="text-sage" size={19} />
                  </div>
                  <p className="mt-6 font-display text-3xl font-semibold tabular-nums">{value}</p>
                </article>
              ))}
            </div>
          </div>
        </>
      )}
    </section>
  )
}
