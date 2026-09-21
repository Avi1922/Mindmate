import { GoogleGenAI, Modality, type LiveServerMessage, type Session } from '@google/genai'
import {
  Bot,
  CheckCircle2,
  Clock3,
  LoaderCircle,
  Mic2,
  ShieldCheck,
  Square,
  UserRound,
  Volume2,
  Waves,
} from 'lucide-react'
import { useCallback, useEffect, useRef, useState } from 'react'

import PageHeader from '../components/PageHeader'
import { analyzeText, type AnalysisResult } from '../lib/analysis'
import { ApiError } from '../lib/api'
import {
  createConversation,
  type ConversationRecord,
} from '../lib/conversation'
import { createLiveToken, MicrophoneStreamer, PcmPlayer } from '../lib/live'
import {
  appendTranscriptTurn,
  finalizeTranscript,
  formatDuration,
  type TranscriptTurn,
} from '../lib/transcript'

type SessionStatus = 'idle' | 'connecting' | 'listening' | 'speaking' | 'ended' | 'error'

const statusText: Record<SessionStatus, string> = {
  idle: 'Ready to start',
  connecting: 'Connecting securely…',
  listening: 'Listening',
  speaking: 'MindMate is responding',
  ended: 'Conversation ended',
  error: 'Connection needs attention',
}

function microphoneError(error: unknown): string {
  if (error instanceof DOMException && error.name === 'NotAllowedError') {
    return 'Microphone access was blocked. Allow microphone permission for this site and try again.'
  }
  if (error instanceof DOMException && error.name === 'NotFoundError') {
    return 'No microphone was found on this device.'
  }
  if (error instanceof ApiError) return error.message
  if (error instanceof Error && error.message) return error.message
  return 'The voice conversation could not be started.'
}

export default function AssistantPage() {
  const [status, setStatus] = useState<SessionStatus>('idle')
  const [error, setError] = useState('')
  const [transcript, setTranscript] = useState<TranscriptTurn[]>([])
  const [elapsedSeconds, setElapsedSeconds] = useState(0)
  const [saving, setSaving] = useState(false)
  const [savedConversation, setSavedConversation] = useState<ConversationRecord | null>(null)
  const [conversationAnalysis, setConversationAnalysis] = useState<AnalysisResult | null>(null)
  const [saveMessage, setSaveMessage] = useState('')
  const sessionRef = useRef<Session | null>(null)
  const microphoneRef = useRef<MicrophoneStreamer | null>(null)
  const playerRef = useRef<PcmPlayer | null>(null)
  const endingRef = useRef(false)
  const turnIdRef = useRef(0)
  const startedAtRef = useRef<string | null>(null)
  const endedAtRef = useRef<string | null>(null)

  const appendTranscript = useCallback((role: TranscriptTurn['role'], fragment: string) => {
    if (!fragment.trim()) return
    setTranscript((current) => {
      const nextId = turnIdRef.current + 1
      const updated = appendTranscriptTurn(current, role, fragment, nextId)
      if (updated.length > current.length) {
        turnIdRef.current = nextId
      }
      return updated
    })
  }, [])

  const finishStreamingTurns = useCallback(() => {
    setTranscript(finalizeTranscript)
  }, [])

  const releaseMedia = useCallback(async () => {
    await microphoneRef.current?.stop()
    microphoneRef.current = null
    await playerRef.current?.close()
    playerRef.current = null
  }, [])

  const handleMessage = useCallback((message: LiveServerMessage) => {
    const content = message.serverContent
    if (!content) return

    if (content.interrupted) {
      playerRef.current?.stop()
      setStatus('listening')
    }
    if (content.inputTranscription?.text) {
      appendTranscript('user', content.inputTranscription.text)
    }
    if (content.outputTranscription?.text) {
      appendTranscript('assistant', content.outputTranscription.text)
    }
    for (const part of content.modelTurn?.parts ?? []) {
      if (part.inlineData?.data) {
        setStatus('speaking')
        playerRef.current?.play(
          part.inlineData.data,
          part.inlineData.mimeType ?? 'audio/pcm;rate=24000',
        )
      }
    }
    if (content.turnComplete) {
      finishStreamingTurns()
      setStatus('listening')
    }
  }, [appendTranscript, finishStreamingTurns])

  const endConversation = useCallback(async () => {
    endingRef.current = true
    try {
      sessionRef.current?.sendRealtimeInput({ audioStreamEnd: true })
    } catch {
      // The socket may already be closed.
    }
    sessionRef.current?.close()
    sessionRef.current = null
    await releaseMedia()
    finishStreamingTurns()
    endedAtRef.current = new Date().toISOString()
    setStatus('ended')
  }, [finishStreamingTurns, releaseMedia])

  const startConversation = useCallback(async () => {
    setError('')
    setTranscript([])
    setElapsedSeconds(0)
    setSavedConversation(null)
    setConversationAnalysis(null)
    setSaveMessage('')
    setStatus('connecting')
    endingRef.current = false
    startedAtRef.current = new Date().toISOString()
    endedAtRef.current = null

    const microphone = new MicrophoneStreamer()
    const player = new PcmPlayer()
    microphoneRef.current = microphone
    playerRef.current = player

    try {
      await player.resume()
      await microphone.start((base64Pcm) => {
        sessionRef.current?.sendRealtimeInput({
          audio: { data: base64Pcm, mimeType: 'audio/pcm;rate=16000' },
        })
      })

      const credential = await createLiveToken()
      const ai = new GoogleGenAI({
        apiKey: credential.token,
        httpOptions: { apiVersion: 'v1beta' },
      })
      sessionRef.current = await ai.live.connect({
        model: credential.model,
        config: {
          responseModalities: [Modality.AUDIO],
          inputAudioTranscription: {},
          outputAudioTranscription: {},
        },
        callbacks: {
          onopen: () => setStatus('listening'),
          onmessage: handleMessage,
          onerror: () => {
            endingRef.current = true
            sessionRef.current?.close()
            sessionRef.current = null
            void releaseMedia()
            endedAtRef.current = new Date().toISOString()
            setError('The Gemini Live connection encountered an error. Start a new conversation to try again.')
            setStatus('error')
          },
          onclose: () => {
            if (!endingRef.current) {
              sessionRef.current = null
              void releaseMedia()
              endedAtRef.current = new Date().toISOString()
              setError('The live session closed. You can start a new conversation.')
              setStatus('error')
            }
          },
        },
      })
    } catch (caughtError) {
      await microphone.stop()
      await player.close()
      microphoneRef.current = null
      playerRef.current = null
      setError(microphoneError(caughtError))
      endedAtRef.current = new Date().toISOString()
      setStatus('error')
    }
  }, [handleMessage, releaseMedia])

  const saveAndAnalyze = useCallback(async () => {
    const finalizedTurns = transcript
      .filter((turn) => turn.text.trim())
      .map(({ role, text }) => ({ role, text }))
    const userText = finalizedTurns
      .filter((turn) => turn.role === 'user')
      .map((turn) => turn.text)
      .join('\n')
    const startedAt = startedAtRef.current
    const endedAt = endedAtRef.current ?? new Date().toISOString()
    if (!finalizedTurns.some((turn) => turn.role === 'user') || !startedAt) {
      setError('A user transcript is required before this conversation can be saved.')
      return
    }

    setSaving(true)
    setError('')
    setSaveMessage('')
    let record = savedConversation
    try {
      if (!record) {
        record = await createConversation(finalizedTurns, startedAt, endedAt)
        setSavedConversation(record)
      }
      if (!conversationAnalysis) {
        const analysis = await analyzeText(userText, 'conversation', record.id)
        setConversationAnalysis(analysis)
      }
      setSaveMessage('Conversation saved, analyzed, and added to your daily mood record.')
    } catch (caughtError) {
      const message = caughtError instanceof ApiError
        ? caughtError.message
        : 'The conversation could not be saved and analyzed.'
      setError(
        record
          ? `The conversation is saved, but analysis failed: ${message}`
          : message,
      )
    } finally {
      setSaving(false)
    }
  }, [conversationAnalysis, savedConversation, transcript])

  useEffect(() => {
    if (!['connecting', 'listening', 'speaking'].includes(status)) return
    const timer = window.setInterval(() => {
      setElapsedSeconds((seconds) => seconds + 1)
    }, 1000)
    return () => window.clearInterval(timer)
  }, [status])

  useEffect(() => () => {
    endingRef.current = true
    sessionRef.current?.close()
    void microphoneRef.current?.stop()
    void playerRef.current?.close()
  }, [])

  const active = ['connecting', 'listening', 'speaking'].includes(status)
  const hasTranscript = transcript.some((turn) => turn.role === 'user' && turn.text.trim())

  return (
    <section className="space-y-8">
      <PageHeader
        description="Talk naturally with a live AI reflection companion and review the transcript as it develops."
        eyebrow="Voice check-in"
        title="AI mood assistant"
      />

      {error && <div className="form-error" role="alert">{error}</div>}

      <div className="grid gap-5 xl:grid-cols-[0.85fr_1.15fr]">
        <article className="card flex min-h-[32rem] flex-col items-center justify-center text-center">
          <div className={`relative grid size-28 place-items-center rounded-full text-pine ring-8 transition ${active ? 'bg-sage/25 ring-sage/10' : 'bg-mist ring-mist/50'}`}>
            {status === 'connecting' ? (
              <LoaderCircle aria-hidden="true" className="animate-spin" size={42} />
            ) : status === 'speaking' ? (
              <Volume2 aria-hidden="true" size={42} />
            ) : (
              <Mic2 aria-hidden="true" size={42} />
            )}
            {status === 'listening' && <span className="absolute inset-0 animate-ping rounded-full border border-sage/40" />}
          </div>

          <div className="mt-7 flex items-center gap-2 text-sm font-semibold text-pine">
            {active && <Waves aria-hidden="true" size={18} />}
            {statusText[status]}
          </div>
          <div className="mt-2 flex items-center gap-2 text-xs tabular-nums text-muted">
            <Clock3 aria-hidden="true" size={15} />
            {formatDuration(elapsedSeconds)}
          </div>

          <p className="mx-auto mt-5 max-w-sm text-sm leading-6 text-muted">
            {active
              ? 'Speak naturally. Gemini detects pauses automatically and may respond in the language you use.'
              : 'Start when you are ready. Your browser will ask for microphone permission.'}
          </p>

          {active ? (
            <button className="mt-7 inline-flex items-center gap-2 rounded-xl bg-rose-600 px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-rose-700" onClick={() => void endConversation()} type="button">
              <Square aria-hidden="true" fill="currentColor" size={15} />
              End conversation
            </button>
          ) : (
            <button className="button-primary mt-7" disabled={saving} onClick={() => void startConversation()} type="button">
              <Mic2 aria-hidden="true" size={18} />
              {hasTranscript && !savedConversation
                ? 'Discard and start new'
                : status === 'ended' || status === 'error'
                  ? 'Start a new conversation'
                  : 'Start conversation'}
            </button>
          )}

          <div className="mt-8 flex items-start gap-2 border-t border-line pt-5 text-left text-xs leading-5 text-muted">
            <ShieldCheck aria-hidden="true" className="mt-0.5 shrink-0" size={16} />
            <span>Your permanent Gemini key stays on the backend. Audio streams directly using a short-lived, single-use credential.</span>
          </div>
        </article>

        <article className="card flex h-[36rem] min-h-[32rem] flex-col" aria-labelledby="transcript-heading">
          <div className="flex items-center justify-between border-b border-line pb-4">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.16em] text-sage">Live transcript</p>
              <h2 className="mt-1 font-display text-2xl font-semibold" id="transcript-heading">Conversation</h2>
            </div>
            <span className={`rounded-full px-3 py-1 text-xs font-medium ${savedConversation ? 'bg-emerald-100 text-emerald-800' : 'bg-mist text-pine'}`}>
              {conversationAnalysis ? 'Saved and analyzed' : savedConversation ? 'Saved' : 'Not saved'}
            </span>
          </div>

          <div className="mt-5 min-h-0 flex-1 space-y-4 overflow-y-auto pr-1" aria-live="polite">
            {transcript.length === 0 ? (
              <div className="grid min-h-72 place-items-center rounded-2xl bg-canvas px-6 text-center">
                <div>
                  <Bot className="mx-auto text-sage" size={30} />
                  <p className="mt-3 text-sm font-semibold">Transcript will appear here</p>
                  <p className="mt-2 text-xs leading-5 text-muted">End a conversation to review it before choosing whether to save and analyze it.</p>
                </div>
              </div>
            ) : transcript.map((turn) => (
              <div className={`flex gap-3 ${turn.role === 'user' ? 'flex-row-reverse' : ''}`} key={turn.id}>
                <div className={`grid size-8 shrink-0 place-items-center rounded-full ${turn.role === 'user' ? 'bg-pine text-white' : 'bg-mist text-pine'}`}>
                  {turn.role === 'user' ? <UserRound size={16} /> : <Bot size={16} />}
                </div>
                <div className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-6 ${turn.role === 'user' ? 'bg-pine text-white' : 'bg-canvas text-ink'}`}>
                  <p className="mb-1 text-[0.65rem] font-bold uppercase tracking-wider opacity-60">{turn.role === 'user' ? 'You' : 'MindMate'}</p>
                  <p>{turn.text}</p>
                </div>
              </div>
            ))}
          </div>

          {!active && hasTranscript && (
            <div className="mt-5 rounded-2xl border border-line bg-canvas p-4">
              {saveMessage && (
                <div className="mb-4 flex items-start gap-2 text-sm text-emerald-800" role="status">
                  <CheckCircle2 className="mt-0.5 shrink-0" size={17} />
                  <span>{saveMessage}</span>
                </div>
              )}
              {conversationAnalysis && (
                <div className="mb-4 grid grid-cols-2 gap-3 text-sm sm:grid-cols-3">
                  <div>
                    <p className="text-xs text-muted">Mood estimate</p>
                    <p className="mt-1 font-display text-2xl font-semibold">{conversationAnalysis.mood_score}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted">Dominant emotion</p>
                    <p className="mt-1 font-semibold capitalize">{conversationAnalysis.dominant_emotion}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted">Language</p>
                    <p className="mt-1 font-semibold uppercase">{conversationAnalysis.language}</p>
                  </div>
                </div>
              )}
              {!conversationAnalysis && (
                <button className="button-primary" disabled={saving} onClick={() => void saveAndAnalyze()} type="button">
                  {saving ? <LoaderCircle className="animate-spin" size={18} /> : <ShieldCheck size={18} />}
                  {saving
                    ? savedConversation ? 'Analyzing…' : 'Saving and analyzing…'
                    : savedConversation ? 'Retry analysis' : 'Save and analyze'}
                </button>
              )}
              <p className="mt-3 text-xs leading-5 text-muted">
                Saving stores the transcript in your private Firestore account and sends a PII-masked version through emotion analysis. Audio is not stored.
              </p>
            </div>
          )}

          <p className="mt-5 border-t border-line pt-4 text-xs leading-5 text-muted">
            Transcription can contain mistakes. This assistant offers reflective conversation, not medical advice or diagnosis.
          </p>
        </article>
      </div>
    </section>
  )
}
