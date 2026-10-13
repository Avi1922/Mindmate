import { useEffect, useRef, useState } from 'react'
import PageHeader from '../components/PageHeader'
export default function WellbeingPage() {
  const [playing, setPlaying] = useState(false)
  const [breathing, setBreathing] = useState(false)
  const [seconds, setSeconds] = useState(0)
  const audio = useRef<AudioContext | null>(null)
  useEffect(
    () => () => {
      void audio.current?.close()
    },
    [],
  )
  useEffect(() => {
    if (!breathing) return
    const timer = window.setInterval(() => setSeconds((s) => s + 1), 1000)
    return () => window.clearInterval(timer)
  }, [breathing])
  async function toggleMusic() {
    if (audio.current) {
      await audio.current.close()
      audio.current = null
      setPlaying(false)
      return
    }
    const context = new AudioContext()
    audio.current = context
    await context.resume()
    const gain = context.createGain()
    gain.gain.value = 0.025
    gain.connect(context.destination)
    ;[130.81, 164.81, 196, 261.63].forEach((frequency, i) => {
      const oscillator = context.createOscillator()
      oscillator.type = 'sine'
      oscillator.frequency.value = frequency
      oscillator.detune.value = i * 2
      oscillator.connect(gain)
      oscillator.start()
    })
    setPlaying(true)
  }
  return (
    <section className="space-y-6">
      <PageHeader
        eyebrow="Small moments of care"
        title="Mood toolkit"
        description="Try one small activity, at your own pace. These are wellbeing ideas, not treatment."
      />
      <div className="grid gap-5 md:grid-cols-2">
        <article className="card space-y-4">
          <h2 className="font-display text-2xl font-semibold">Take a gentle breathing pause</h2>
          <p className="text-sm text-muted">
            Breathe comfortably without forcing or holding your breath. Stop if you feel
            uncomfortable.
          </p>
          <div className="rounded-2xl bg-mist p-8 text-center" aria-live="polite">
            {breathing
              ? seconds % 10 < 5
                ? 'Breathe in gently'
                : 'Breathe out gently'
              : 'A moment to slow down'}
            {breathing && <p className="mt-2 text-xs">{seconds} seconds</p>}
          </div>
          <button
            className="button-primary"
            onClick={() => {
              setSeconds(0)
              setBreathing((b) => !b)
            }}
          >
            {breathing ? 'Finish breathing pause' : 'Start breathing pause'}
          </button>
          <a
            className="text-link block text-sm"
            href="https://www.nhs.uk/mental-health/self-help/guides-tools-and-activities/breathing-exercises-for-stress/"
            target="_blank"
            rel="noreferrer"
          >
            NHS breathing guidance
          </a>
        </article>
        <article className="card space-y-4">
          <h2 className="font-display text-2xl font-semibold">A softer sound</h2>
          <p className="text-sm text-muted">
            Choose familiar music you enjoy, at a comfortable volume. Music-based activities may
            help with stress, but responses vary.
          </p>
          <button
            className="button-primary"
            aria-pressed={playing}
            onClick={() => void toggleMusic()}
          >
            {playing ? 'Stop gentle tones' : 'Play gentle tones'}
          </button>
          <p className="text-xs text-muted">
            These locally generated ambient tones are an optional listening aid, not a clinically
            tested track. No audio is recorded.
          </p>
          <a
            className="text-link block text-sm"
            href="https://www.nccih.nih.gov/health/music-and-health-what-you-need-to-know"
            target="_blank"
            rel="noreferrer"
          >
            Read the NIH evidence on music and health
          </a>
        </article>
        <article className="card space-y-4">
          <h2 className="font-display text-2xl font-semibold">Move or reconnect</h2>
          <p className="text-sm text-muted">
            If it feels possible, take a short walk, stretch gently, or message someone you trust.
            Pick a step that fits your energy today.
          </p>
          <a
            className="text-link text-sm"
            href="https://www.nhs.uk/mental-health/self-help/guides-tools-and-activities/five-steps-to-mental-wellbeing/"
            target="_blank"
            rel="noreferrer"
          >
            NHS: five steps to wellbeing
          </a>
        </article>
        <article className="card space-y-4">
          <h2 className="font-display text-2xl font-semibold">Notice the present</h2>
          <p className="text-sm text-muted">
            Look around and name a few things you can see or hear. You can stop or choose another
            activity if mindfulness does not suit you.
          </p>
          <a
            className="text-link text-sm"
            href="https://www.nhs.uk/mental-health/self-help/tips-and-support/mindfulness/"
            target="_blank"
            rel="noreferrer"
          >
            NHS mindfulness guidance
          </a>
        </article>
      </div>
    </section>
  )
}
