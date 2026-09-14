import Taro from '@tarojs/taro'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { anonymousId, request } from './client'

vi.mock('@tarojs/taro', () => ({
  default: {
    getStorageSync: vi.fn(),
    setStorageSync: vi.fn(),
    request: vi.fn()
  }
}))

describe('API 客户端', () => {
  beforeEach(() => vi.clearAllMocks())

  it('生成并持久化匿名标识', () => {
    vi.mocked(Taro.getStorageSync).mockReturnValue('')
    expect(anonymousId()).toMatch(/^anon_/)
    expect(Taro.setStorageSync).toHaveBeenCalledOnce()
  })

  it('解包成功响应并传递幂等键', async () => {
    vi.mocked(Taro.getStorageSync).mockReturnValue('anon_test')
    vi.mocked(Taro.request).mockResolvedValue({
      statusCode: 200,
      data: { code: 0, message: 'ok', data: { value: 1 }, request_id: 'req_1' }
    } as never)
    await expect(request<{ value: number }>('/health', 'POST', {}, 'idem_1')).resolves.toEqual({ value: 1 })
    expect(Taro.request).toHaveBeenCalledWith(expect.objectContaining({
      header: expect.objectContaining({ 'X-Anonymous-Id': 'anon_test', 'Idempotency-Key': 'idem_1' })
    }))
  })

  it('保留业务错误码和请求 ID', async () => {
    vi.mocked(Taro.getStorageSync).mockReturnValue('anon_test')
    vi.mocked(Taro.request).mockResolvedValue({
      statusCode: 422,
      data: { code: 4220, message: '请求参数不合法', data: null, request_id: 'req_bad' }
    } as never)
    await expect(request('/bad')).rejects.toMatchObject({
      code: 4220,
      requestId: 'req_bad',
      message: '请求参数不合法'
    })
  })
})
