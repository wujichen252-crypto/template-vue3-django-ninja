import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig, AxiosResponse, Canceler } from 'axios'
import { ElMessage } from 'element-plus'
import { getToken, removeToken } from './storage'
import router from '@/router'
import type { ApiResponse } from '@/types/api'

/**
 * 请求去重管理器
 * 用于取消重复的请求
 */
class RequestDeduplicator {
  private pendingRequests: Map<string, Canceler> = new Map()

  /**
   * 生成请求唯一标识
   */
  generateKey(config: InternalAxiosRequestConfig): string {
    const { method, url, params, data } = config
    return `${method?.toUpperCase()}_${url}_${JSON.stringify(params)}_${JSON.stringify(data)}`
  }

  /**
   * 添加请求到待处理队列
   */
  add(config: InternalAxiosRequestConfig): void {
    const key = this.generateKey(config)
    config.cancelToken = new axios.CancelToken((cancel) => {
      this.pendingRequests.set(key, cancel)
    })
  }

  /**
   * 移除请求从待处理队列
   */
  remove(config: InternalAxiosRequestConfig): void {
    const key = this.generateKey(config)
    if (this.pendingRequests.has(key)) {
      this.pendingRequests.delete(key)
    }
  }

  /**
   * 取消重复请求
   */
  cancel(config: InternalAxiosRequestConfig): void {
    const key = this.generateKey(config)
    if (this.pendingRequests.has(key)) {
      const cancel = this.pendingRequests.get(key)
      cancel?.(`取消重复请求: ${key}`)
      this.pendingRequests.delete(key)
    }
  }

  /**
   * 取消所有请求
   */
  cancelAll(): void {
    this.pendingRequests.forEach((cancel, key) => {
      cancel?.(`取消请求: ${key}`)
    })
    this.pendingRequests.clear()
  }
}

const deduplicator = new RequestDeduplicator()

const request: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 30000, // 30秒超时，适应复杂查询和文件上传
  headers: {
    'Content-Type': 'application/json'
  }
})

/**
 * 文件上传专用请求实例（更长超时）
 */
export const uploadRequest: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 60000, // 60秒超时
  headers: {
    'Content-Type': 'multipart/form-data'
  }
})

/**
 * 请求重试配置
 */
const retryConfig = {
  retries: 2,           // 重试次数
  retryDelay: 1000,     // 重试延迟（毫秒）
  shouldRetry: (error: AxiosError): boolean => {
    // 网络错误或 5xx 服务器错误时重试
    const status = error.response?.status
    return !status || status >= 500 || error.code === 'ECONNABORTED'
  }
}

request.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // 请求去重：取消之前的相同请求
    deduplicator.cancel(config)
    deduplicator.add(config)

    // Token 注入
    const token = getToken()
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }

    // 添加请求时间戳，用于调试
    config.headers['X-Request-Time'] = Date.now().toString()

    return config
  },
  (error: AxiosError) => {
    return Promise.reject(error)
  }
)

request.interceptors.response.use(
  (response: AxiosResponse<ApiResponse>) => {
    // 移除已完成的请求
    deduplicator.remove(response.config)

    const res = response.data
    if (res.code !== 200) {
      ElMessage.error(res.msg || '请求失败')
      if (res.code === 401) {
        removeToken()
        router.push('/login')
      }
      return Promise.reject(new Error(res.msg || '请求失败'))
    }
    return response
  },
  async (error: AxiosError<ApiResponse>) => {
    // 移除失败的请求
    if (error.config) {
      deduplicator.remove(error.config)
    }

    // 处理取消请求
    if (axios.isCancel(error)) {
      console.log('请求被取消:', error.message)
      return Promise.reject(error)
    }

    // 请求重试逻辑
    const config = error.config as InternalAxiosRequestConfig & { __retryCount?: number }
    if (config && retryConfig.shouldRetry(error)) {
      config.__retryCount = config.__retryCount || 0

      if (config.__retryCount < retryConfig.retries) {
        config.__retryCount += 1
        console.log(`请求重试 ${config.__retryCount}/${retryConfig.retries}`)

        // 延迟重试
        await new Promise(resolve => setTimeout(resolve, retryConfig.retryDelay))
        return request(config)
      }
    }

    // 错误处理
    if (error.response) {
      const status = error.response.status
      const msg = error.response.data?.msg || '请求失败'

      switch (status) {
        case 401:
          ElMessage.error('未授权，请重新登录')
          removeToken()
          router.push('/login')
          break
        case 403:
          ElMessage.error('拒绝访问')
          break
        case 404:
          ElMessage.error('请求资源不存在')
          break
        case 429:
          ElMessage.error('请求过于频繁，请稍后再试')
          break
        case 500:
          ElMessage.error('服务器内部错误')
          break
        default:
          ElMessage.error(msg)
      }
    } else if (error.code === 'ECONNABORTED') {
      ElMessage.error('请求超时，请检查网络连接')
    } else {
      ElMessage.error('网络错误，请检查网络连接')
    }

    return Promise.reject(error)
  }
)

/**
 * 取消所有待处理的请求
 * 适用于页面切换时清理请求
 */
export function cancelAllRequests(): void {
  deduplicator.cancelAll()
}

/**
 * 创建可取消的请求
 * 适用于需要手动控制取消的场景
 */
export function createCancelableRequest<T>(
  requestFn: () => Promise<T>
): { promise: Promise<T>; cancel: () => void } {
  const source = axios.CancelToken.source()

  const promise = requestFn()

  return {
    promise,
    cancel: () => {
      source.cancel('用户取消请求')
    }
  }
}

export default request
