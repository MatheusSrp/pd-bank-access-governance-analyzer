const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080').replace(/\/$/, '')
const API_KEY = import.meta.env.VITE_API_KEY?.trim()
const REQUEST_TIMEOUT_MS = 30_000

export class ApiError extends Error {
  constructor(message: string, public readonly status?: number, public readonly causeValue?: unknown) {
    super(message)
    this.name = 'ApiError'
  }
}

export interface RequestOptions {
  method?: 'GET' | 'POST'
  body?: unknown
  file?: File
  signal?: AbortSignal
}
export interface ApiResponse<T> { data: T; headers: Headers }
interface ActiveResponse { response: Response; controller: AbortController; dispose: () => void }

function friendlyMessage(status: number, detail?: string): string {
  if (detail) return detail
  if (status === 400 || status === 422) return 'Os dados enviados não foram aceitos. Revise o arquivo e tente novamente.'
  if (status === 401 || status === 403) return 'A API recusou a solicitação. Verifique a configuração de acesso do backend.'
  if (status === 404) return 'O registro solicitado não foi encontrado.'
  if (status === 413) return 'O arquivo excede o limite aceito pelo backend.'
  if (status >= 500) return 'O backend encontrou um erro ao processar a solicitação.'
  return `Não foi possível concluir a solicitação (HTTP ${status}).`
}

async function decodeError(response: Response): Promise<string> {
  try {
    const payload: unknown = await response.json()
    if (payload && typeof payload === 'object') {
      const record = payload as Record<string, unknown>
      const detail = record.message ?? record.error ?? record.detail
      if (typeof detail === 'string' && detail.trim()) return friendlyMessage(response.status, detail)
    }
  } catch { /* Corpo vazio, timeout ou não JSON. */ }
  return friendlyMessage(response.status)
}

function readFailure(controller: AbortController, error: unknown): ApiError {
  if (controller.signal.aborted) {
    const timedOut = controller.signal.reason instanceof DOMException && controller.signal.reason.name === 'TimeoutError'
    return new ApiError(timedOut ? 'A solicitação excedeu o tempo limite. Tente novamente.' : 'A solicitação foi cancelada.', undefined, error)
  }
  return new ApiError('Não foi possível ler a resposta da API. Tente novamente.', undefined, error)
}

async function fetchResponse(path: string, options: RequestOptions = {}): Promise<ActiveResponse> {
  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(new DOMException('Tempo limite excedido', 'TimeoutError')), REQUEST_TIMEOUT_MS)
  const abortFromCaller = () => controller.abort(options.signal?.reason)
  options.signal?.addEventListener('abort', abortFromCaller, { once: true })
  const headers = new Headers()
  if (API_KEY) headers.set('X-API-Key', API_KEY)
  let body: BodyInit | undefined
  if (options.file) {
    const form = new FormData()
    form.append('file', options.file)
    body = form
  } else if (options.body !== undefined) {
    headers.set('Content-Type', 'application/json')
    body = JSON.stringify(options.body)
  }
  const dispose = () => {
    window.clearTimeout(timeout)
    options.signal?.removeEventListener('abort', abortFromCaller)
  }
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, { method: options.method ?? 'GET', headers, body, signal: controller.signal })
    if (!response.ok) throw new ApiError(await decodeError(response), response.status)
    return { response, controller, dispose }
  } catch (error) {
    dispose()
    if (error instanceof ApiError) throw error
    throw readFailure(controller, error)
  }
}

export async function requestWithHeaders<T>(path: string, options: RequestOptions = {}): Promise<ApiResponse<T>> {
  const { response, controller, dispose } = await fetchResponse(path, options)
  try {
    if (response.status === 204) return { data: undefined as T, headers: response.headers }
    let text: string
    try { text = await response.text() } catch (error) { throw readFailure(controller, error) }
    if (!text) return { data: undefined as T, headers: response.headers }
    try { return { data: JSON.parse(text) as T, headers: response.headers } }
    catch (error) { throw new ApiError('A resposta do backend não está em um formato JSON válido.', response.status, error) }
  } finally { dispose() }
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  return (await requestWithHeaders<T>(path, options)).data
}

export async function download(path: string, fallbackName: string): Promise<void> {
  const { response, controller, dispose } = await fetchResponse(path)
  try {
    const disposition = response.headers.get('Content-Disposition')
    const encodedName = disposition?.match(/filename\*=UTF-8''([^;]+)/i)?.[1]
    const plainName = disposition?.match(/filename="?([^";]+)"?/i)?.[1]
    const filename = encodedName ? decodeURIComponent(encodedName) : plainName || fallbackName
    let blob: Blob
    try { blob = await response.blob() } catch (error) { throw readFailure(controller, error) }
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = filename
    document.body.appendChild(anchor)
    anchor.click()
    anchor.remove()
    window.setTimeout(() => URL.revokeObjectURL(url), 1000)
  } finally { dispose() }
}

export function apiBaseUrl(): string { return API_BASE_URL }
