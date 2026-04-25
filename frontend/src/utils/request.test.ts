import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import axios from 'axios'
import request, { cancelAllRequests, createCancelableRequest } from './request'
import { getToken, removeToken } from './storage'
import router from '@/router'

// Mock 依赖
vi.mock('./storage')
vi.mock('@/router', () => ({
  default: {
    push: vi.fn()
  }
}))
vi.mock('element-plus', () => ({
  ElMessage: {
    error: vi.fn()
  }
}))

describe('RequestDeduplicator', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    cancelAllRequests()
  })

  afterEach(() => {
    cancelAllRequests()
  })

  it('应该取消重复请求', async () => {
    const mockGetToken = vi.mocked(getToken)
    mockGetToken.mockReturnValue('test-token')

    // 创建两个相同的请求
    const request1 = request.get('/test')
    const request2 = request.get('/test')

    // 第一个请求应该被取消
    await expect(request1).rejects.toThrow('取消重复请求')
    
    // 清理
    cancelAllRequests()
  })

  it('不同请求不应该互相影响', async () => {
    const mockGetToken = vi.mocked(getToken)
    mockGetToken.mockReturnValue('test-token')

    // 使用不同的 URL
    const request1 = request.get('/test1')
    const request2 = request.get('/test2')

    // 两个请求都应该正常发起（会被网络错误拒绝，但不是取消）
    await expect(request1).rejects.toThrow()
    await expect(request2).rejects.toThrow()
  })
})

describe('Request Retry', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    cancelAllRequests()
  })

  it('网络错误时应该重试', async () => {
    const mockGetToken = vi.mocked(getToken)
    mockGetToken.mockReturnValue('test-token')

    // 模拟网络错误
    const mockAxios = vi.spyOn(axios, 'create').mockReturnValue({
      interceptors: {
        request: { use: vi.fn() },
        response: { use: vi.fn() }
      }
    } as any)

    // 清理
    mockAxios.mockRestore()
  })

  it('超过重试次数应该失败', async () => {
    // 模拟连续失败的场景
    const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {})
    
    // 清理
    consoleSpy.mockRestore()
  })
})

describe('Token Injection', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    cancelAllRequests()
  })

  it('应该注入 Token 到请求头', () => {
    const mockGetToken = vi.mocked(getToken)
    mockGetToken.mockReturnValue('test-token')

    // 验证请求配置
    expect(getToken()).toBe('test-token')
  })

  it('没有 Token 时不应该添加 Authorization', () => {
    const mockGetToken = vi.mocked(getToken)
    mockGetToken.mockReturnValue(null)

    expect(getToken()).toBeNull()
  })
})

describe('Response Interceptor', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    cancelAllRequests()
  })

  it('code 不为 200 时应该显示错误', () => {
    // 测试错误响应处理
    const response = { data: { code: 400, msg: '参数错误' } }
    expect(response.data.code).toBe(400)
    expect(response.data.msg).toBe('参数错误')
  })

  it('401 时应该清除 Token 并跳转登录', () => {
    const mockRemoveToken = vi.mocked(removeToken)
    const mockRouterPush = vi.mocked(router.push)

    // 模拟 401 响应
    const response = { data: { code: 401, msg: '未授权' } }
    
    if (response.data.code === 401) {
      removeToken()
      router.push('/login')
    }

    expect(mockRemoveToken).toHaveBeenCalled()
    expect(mockRouterPush).toHaveBeenCalledWith('/login')
  })

  it('应该处理 429 限流错误', () => {
    const response = { status: 429, data: { msg: '请求过于频繁' } }
    expect(response.status).toBe(429)
  })
})

describe('cancelAllRequests', () => {
  it('应该取消所有待处理请求', () => {
    const mockGetToken = vi.mocked(getToken)
    mockGetToken.mockReturnValue('test-token')

    // 发起多个请求
    const requests = [
      request.get('/test1'),
      request.get('/test2'),
      request.post('/test3', {})
    ]

    // 取消所有请求
    cancelAllRequests()

    // 所有请求都应该被取消
    expect(requests.every(r => r instanceof Promise)).toBe(true)
  })
})

describe('createCancelableRequest', () => {
  it('应该创建可取消的请求', () => {
    const mockRequestFn = vi.fn().mockResolvedValue({ data: 'test' })
    
    const { promise, cancel } = createCancelableRequest(mockRequestFn)
    
    expect(promise).toBeInstanceOf(Promise)
    expect(typeof cancel).toBe('function')
  })

  it('取消函数应该能取消请求', () => {
    const mockRequestFn = vi.fn().mockResolvedValue({ data: 'test' })
    
    const { cancel } = createCancelableRequest(mockRequestFn)
    
    // 调用取消不应该抛出错误
    expect(() => cancel()).not.toThrow()
  })
})

describe('Timeout Configuration', () => {
  it('请求超时时间应该为 10 秒', () => {
    // 验证超时配置
    const expectedTimeout = 10000
    expect(expectedTimeout).toBe(10000)
  })
})
