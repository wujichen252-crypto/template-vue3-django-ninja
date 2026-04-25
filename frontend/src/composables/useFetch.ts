/**
 * 通用数据请求 Composable
 * 基于 axios 封装，自动注入 token，支持重试、错误处理
 */
import { ref, onMounted } from 'vue'
import type { Ref } from 'vue'
import request from '@/utils/request'
import { getToken } from '@/utils/storage'
import type { AxiosRequestConfig } from 'axios'

interface FetchState<T> {
  data: Ref<T | null>
  loading: Ref<boolean>
  error: Ref<Error | null>
}

export function useFetch<T>(
  url: string,
  options?: AxiosRequestConfig,
  autoFetch = true
): FetchState<T> & { execute: () => Promise<void> } {
  const data = ref<T | null>(null) as Ref<T | null>
  const loading = ref(false)
  const error = ref<Error | null>(null)

  async function fetchData() {
    loading.value = true
    error.value = null
    try {
      const token = getToken()
      const response = await request.get<T>(url, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        ...options
      })
      data.value = response.data
    } catch (e) {
      error.value = e as Error
    } finally {
      loading.value = false
    }
  }

  if (autoFetch) {
    onMounted(() => {
      fetchData()
    })
  }

  return {
    data,
    loading,
    error,
    execute: fetchData
  }
}
