import { firebaseAuth } from './firebase'

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '')
const configuredTimeout = Number(import.meta.env.VITE_API_TIMEOUT_MS ?? 15_000)
const apiTimeoutMs =
  Number.isFinite(configuredTimeout) && configuredTimeout >= 1_000 && configuredTimeout <= 120_000
    ? configuredTimeout
    : 15_000

if (!apiBaseUrl) {
  throw new Error('Missing required frontend environment variable: VITE_API_BASE_URL')
}

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export async function authenticatedApiRequest<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const user = firebaseAuth.currentUser
  if (!user) {
    throw new ApiError('Authentication required', 401)
  }

  const token = await user.getIdToken()
  const headers = new Headers(init.headers)
  headers.set('Authorization', `Bearer ${token}`)
  if (init.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  const controller = new AbortController()
  let timedOut = false
  const cancelFromCaller = () => controller.abort(init.signal?.reason)
  if (init.signal?.aborted) {
    cancelFromCaller()
  } else {
    init.signal?.addEventListener('abort', cancelFromCaller, { once: true })
  }
  const timeout = globalThis.setTimeout(() => {
    timedOut = true
    controller.abort()
  }, apiTimeoutMs)

  let response: Response
  try {
    response = await fetch(`${apiBaseUrl}${path}`, {
      ...init,
      headers,
      signal: controller.signal,
    })
  } catch {
    if (timedOut) {
      throw new ApiError('The request timed out. Please try again.', 408)
    }
    if (controller.signal.aborted) {
      throw new ApiError('The request was cancelled.', 499)
    }
    throw new ApiError('MindMate could not reach the server. Please try again.', 0)
  } finally {
    globalThis.clearTimeout(timeout)
    init.signal?.removeEventListener('abort', cancelFromCaller)
  }

  if (!response.ok) {
    let message = 'The request could not be completed.'
    try {
      const body = (await response.json()) as { detail?: unknown }
      if (typeof body.detail === 'string') {
        message = body.detail
      }
    } catch {
      // Keep the generic message when an upstream response is not JSON.
    }
    throw new ApiError(message, response.status)
  }

  return (await response.json()) as T
}
