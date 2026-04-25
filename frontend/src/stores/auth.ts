import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { userApi } from '@/api/user'
import type { User, TokenData, LoginPayload, RegisterPayload } from '@/types/user'
import { setToken, setRefreshToken, removeToken, removeUserInfo, setUserInfo, getUserInfo, clearAuth, getToken, getRefreshToken } from '@/utils/storage'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(getUserInfo<User>())
  const token = ref<string | null>(getToken())
  const refreshTokenValue = ref<string | null>(getRefreshToken())

  // 计算属性：是否已登录
  const isLoggedIn = computed(() => !!token.value)

  // Token 过期时间（分钟）
  const TOKEN_EXPIRE_MINUTES = 120
  const TOKEN_REFRESH_THRESHOLD = 10 // 提前 10 分钟刷新

  async function login(payload: LoginPayload) {
    const res = await userApi.login(payload)
    const data = res.data.data as TokenData
    token.value = data.access_token
    refreshTokenValue.value = data.refresh_token
    setToken(data.access_token)
    setRefreshToken(data.refresh_token)
    return data
  }

  async function register(username: string, password: string, email: string) {
    const res = await userApi.register({ username, password, email })
    return res.data.data
  }

  async function fetchCurrentUser() {
    try {
      const res = await userApi.getCurrentUser()
      user.value = res.data.data
      setUserInfo(res.data.data)
      return user.value
    } catch {
      logout()
      return null
    }
  }

  async function refreshToken() {
    const refresh = refreshTokenValue.value || getRefreshToken()
    if (!refresh) {
      return null
    }
    try {
      const res = await userApi.refreshToken(refresh)
      const data = res.data.data as TokenData
      token.value = data.access_token
      refreshTokenValue.value = data.refresh_token
      setToken(data.access_token)
      setRefreshToken(data.refresh_token)
      return data
    } catch {
      logout()
      return null
    }
  }

  /**
   * 登出并加入黑名单
   */
  async function logout() {
    try {
      // 如果有 token，尝试加入黑名单（后端接口）
      if (token.value) {
        await userApi.logout(token.value).catch(() => {
          // 忽略错误，确保本地清理
        })
      }
    } finally {
      // 清理本地状态
      user.value = null
      token.value = null
      refreshTokenValue.value = null
      clearAuth()
    }
  }

  /**
   * 检查 token 是否需要刷新
   */
  function shouldRefreshToken(): boolean {
    if (!token.value) return false

    try {
      // 解析 JWT token 获取过期时间
      const payload = JSON.parse(atob(token.value.split('.')[1]))
      const expireTime = new Date(payload.exp * 1000)
      const now = new Date()
      const diffMinutes = (expireTime.getTime() - now.getTime()) / (1000 * 60)

      return diffMinutes <= TOKEN_REFRESH_THRESHOLD
    } catch {
      return false
    }
  }

  /**
   * 初始化：检查 token 是否需要刷新
   */
  async function init() {
    if (token.value && shouldRefreshToken()) {
      await refreshToken()
    }
  }

  return {
    user,
    token,
    isLoggedIn,
    login,
    register,
    fetchCurrentUser,
    refreshToken,
    logout,
    init
  }
})
