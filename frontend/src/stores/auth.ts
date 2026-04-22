import { defineStore } from 'pinia'
import { ref } from 'vue'
import { userApi } from '@/api/user'
import type { User, TokenData, LoginPayload, RegisterPayload } from '@/types/user'
import { setToken, setRefreshToken, removeToken, removeUserInfo, setUserInfo, getUserInfo, clearAuth } from '@/utils/storage'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(getUserInfo<User>())
  const token = ref<string | null>(null)

  async function login(payload: LoginPayload) {
    const res = await userApi.login(payload)
    const data = res.data.data as TokenData
    token.value = data.access_token
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
    const refresh = localStorage.getItem('refresh_token')
    if (!refresh) {
      return null
    }
    try {
      const res = await userApi.refreshToken(refresh)
      const data = res.data.data as TokenData
      token.value = data.access_token
      setToken(data.access_token)
      setRefreshToken(data.refresh_token)
      return data
    } catch {
      logout()
      return null
    }
  }

  function logout() {
    user.value = null
    token.value = null
    clearAuth()
  }

  return {
    user,
    token,
    login,
    register,
    fetchCurrentUser,
    refreshToken,
    logout
  }
})
