import { authenticatedApiRequest } from './api'

export interface LiveToken {
  token: string
  model: string
  expires_at: string
  new_session_expires_at: string
}

export function createLiveToken(): Promise<LiveToken> {
  return authenticatedApiRequest<LiveToken>('/live/token', { method: 'POST' })
}

function floatToPcm16(input: Float32Array, inputRate: number): Int16Array {
  const ratio = inputRate / 16_000
  const outputLength = Math.max(1, Math.floor(input.length / ratio))
  const output = new Int16Array(outputLength)

  for (let index = 0; index < outputLength; index += 1) {
    const start = Math.floor(index * ratio)
    const end = Math.max(start + 1, Math.floor((index + 1) * ratio))
    let total = 0
    for (let sourceIndex = start; sourceIndex < end && sourceIndex < input.length; sourceIndex += 1) {
      total += input[sourceIndex]
    }
    const sample = Math.max(-1, Math.min(1, total / (end - start)))
    output[index] = sample < 0 ? sample * 0x8000 : sample * 0x7fff
  }
  return output
}

function bytesToBase64(bytes: Uint8Array): string {
  let binary = ''
  const blockSize = 0x8000
  for (let offset = 0; offset < bytes.length; offset += blockSize) {
    binary += String.fromCharCode(...bytes.subarray(offset, offset + blockSize))
  }
  return btoa(binary)
}

function base64ToBytes(value: string): Uint8Array {
  const binary = atob(value)
  const bytes = new Uint8Array(binary.length)
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index)
  }
  return bytes
}

export class MicrophoneStreamer {
  private context: AudioContext | null = null
  private stream: MediaStream | null = null
  private source: MediaStreamAudioSourceNode | null = null
  private worklet: AudioWorkletNode | null = null
  private silentGain: GainNode | null = null

  async start(onAudio: (base64Pcm: string) => void): Promise<void> {
    this.stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        autoGainControl: true,
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true,
      },
    })
    this.context = new AudioContext()
    await this.context.audioWorklet.addModule('/pcm-capture-worklet.js')
    await this.context.resume()

    this.source = this.context.createMediaStreamSource(this.stream)
    this.worklet = new AudioWorkletNode(this.context, 'pcm-capture')
    this.silentGain = this.context.createGain()
    this.silentGain.gain.value = 0
    this.worklet.port.onmessage = (event: MessageEvent<Float32Array>) => {
      const pcm = floatToPcm16(event.data, this.context?.sampleRate ?? 48_000)
      onAudio(bytesToBase64(new Uint8Array(pcm.buffer)))
    }
    this.source.connect(this.worklet)
    this.worklet.connect(this.silentGain)
    this.silentGain.connect(this.context.destination)
  }

  async stop(): Promise<void> {
    this.worklet?.disconnect()
    this.source?.disconnect()
    this.silentGain?.disconnect()
    this.stream?.getTracks().forEach((track) => track.stop())
    if (this.context && this.context.state !== 'closed') {
      await this.context.close()
    }
    this.context = null
    this.stream = null
    this.source = null
    this.worklet = null
    this.silentGain = null
  }
}

export class PcmPlayer {
  private readonly context = new AudioContext()
  private nextStartTime = 0
  private readonly sources = new Set<AudioBufferSourceNode>()

  async resume(): Promise<void> {
    if (this.context.state === 'suspended') {
      await this.context.resume()
    }
  }

  play(base64Pcm: string, mimeType = 'audio/pcm;rate=24000'): void {
    const bytes = base64ToBytes(base64Pcm)
    const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength)
    const samples = Math.floor(bytes.byteLength / 2)
    const rate = Number(/rate=(\d+)/i.exec(mimeType)?.[1] ?? 24_000)
    const buffer = this.context.createBuffer(1, samples, rate)
    const channel = buffer.getChannelData(0)
    for (let index = 0; index < samples; index += 1) {
      channel[index] = view.getInt16(index * 2, true) / 0x8000
    }

    const source = this.context.createBufferSource()
    source.buffer = buffer
    source.connect(this.context.destination)
    source.onended = () => this.sources.delete(source)
    this.sources.add(source)
    const startAt = Math.max(this.context.currentTime, this.nextStartTime)
    source.start(startAt)
    this.nextStartTime = startAt + buffer.duration
  }

  stop(): void {
    this.sources.forEach((source) => {
      try {
        source.stop()
      } catch {
        // A source may already have completed between iteration and stop().
      }
    })
    this.sources.clear()
    this.nextStartTime = this.context.currentTime
  }

  async close(): Promise<void> {
    this.stop()
    if (this.context.state !== 'closed') {
      await this.context.close()
    }
  }
}
