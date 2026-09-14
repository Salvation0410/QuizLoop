import Taro from '@tarojs/taro'

interface Envelope<T> { code: number; message: string; data: T; request_id: string }

declare const QUIZELOOP_API_BASE: string

const API_BASE = QUIZELOOP_API_BASE

export class ApiError extends Error {
  constructor (
    message: string,
    public readonly code: number,
    public readonly requestId: string,
    public readonly statusCode: number
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export function anonymousId (): string {
  let value = Taro.getStorageSync('quizeloop_anonymous_id') as string
  if (!value) {
    value = `anon_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`
    Taro.setStorageSync('quizeloop_anonymous_id', value)
  }
  return value
}

export async function request<T> (path: string, method: 'GET' | 'POST' = 'GET', data?: unknown, idempotencyKey?: string): Promise<T> {
  const response = await Taro.request<Envelope<T>>({
    url: `${API_BASE}${path}`, method, data, timeout: 35000,
    header: {
      'Content-Type': 'application/json',
      'X-Anonymous-Id': anonymousId(),
      ...(idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : {})
    }
  })
  if (response.statusCode >= 400 || response.data.code !== 0) {
    throw new ApiError(
      response.data.message || '请求失败，请稍后重试',
      response.data.code,
      response.data.request_id,
      response.statusCode
    )
  }
  return response.data.data
}
