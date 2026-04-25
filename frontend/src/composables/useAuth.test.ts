import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import { userApi } from '@/api/user'
import * as storage from '@/utils/storage'

// Mock API 和 storage
vi.mock('@/api/user', () => ({
  userApi: {
    login: vi.fn(),
    register: vi.fn(),
    getCurrentUser: vi.fn(),
    refreshToken: vi.fn()
  }
}))

vi.mock('@/utils/storage', () => ({
  setToken: vi.fn(),
  setRefreshToken: vi.fn(),
  removeToken: vi.fn(),
  removeUserInfo: vi.fn(),
  setUserInfo: vi.fn(),
  getUserInfo: vi.fn(),
  clearAuth: vi.fn()
}))

describe('useAuthStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('login', () => {
    it('应该成功登录并保存 Token', async () => {
      const mockLogin = vi.mocked(userApi.login)
      const mockSetToken = vi.mocked(storage.setToken)
      const mockSetRefreshToken = vi.mocked(storage.setRefreshToken)

      const mockResponse = {
        data: {
          data: {
            access_token: 'test-access-token',
            refresh_token: 'test-refresh-token',
            expires_in: 7200
          }
        }
      }
      mockLogin.mockResolvedValue(mockResponse as any)

      const authStore = useAuthStore()
      const result = await authStore.login({
        username: 'testuser',
        password: 'password123'
      })

      expect(mockLogin).toHaveBeenCalledWith({
        username: 'testuser',
        password: 'password123'
      })
      expect(mockSetToken).toHaveBeenCalledWith('test-access-token')
      expect(mockSetRefreshToken).toHaveBeenCalledWith('test-refresh-token')
      expect(authStore.token).toBe('test-access-token')
      expect(result.access_token).toBe('test-access-token')
    })

    it('登录失败时应该抛出错误', async () => {
      const mockLogin = vi.mocked(userApi.login)
      mockLogin.mockRejectedValue(new Error('登录失败'))

      const authStore = useAuthStore()

      await expect(
        authStore.login({ username: 'test', password: 'wrong' })
      ).rejects.toThrow('登录失败')
    })
  })

  describe('register', () => {
    it('应该成功注册', async () => {
      const mockRegister = vi.mocked(userApi.register)
      const mockUser = {
        id: 1,
        username: 'newuser',
        email: 'new@example.com'
      }
      mockRegister.mockResolvedValue({ data: { data: mockUser } } as any)

      const authStore = useAuthStore()
      const result = await authStore.register('newuser', 'password123', 'new@example.com')

      expect(mockRegister).toHaveBeenCalledWith({
        username: 'newuser',
        password: 'password123',
        email: 'new@example.com'
      })
      expect(result).toEqual(mockUser)
    })
  })

  describe('fetchCurrentUser', () => {
    it('应该获取当前用户信息', async () => {
      const mockGetCurrentUser = vi.mocked(userApi.getCurrentUser)
      const mockSetUserInfo = vi.mocked(storage.setUserInfo)
      const mockUser = {
        id: 1,
        username: 'testuser',
        email: 'test@example.com'
      }
      mockGetCurrentUser.mockResolvedValue({ data: { data: mockUser } } as any)

      const authStore = useAuthStore()
      const result = await authStore.fetchCurrentUser()

      expect(mockGetCurrentUser).toHaveBeenCalled()
      expect(mockSetUserInfo).toHaveBeenCalledWith(mockUser)
      expect(authStore.user).toEqual(mockUser)
      expect(result).toEqual(mockUser)
    })

    it('获取失败时应该登出', async () => {
      const mockGetCurrentUser = vi.mocked(userApi.getCurrentUser)
      const mockClearAuth = vi.mocked(storage.clearAuth)
      mockGetCurrentUser.mockRejectedValue(new Error('获取失败'))

      const authStore = useAuthStore()
      const result = await authStore.fetchCurrentUser()

      expect(mockClearAuth).toHaveBeenCalled()
      expect(result).toBeNull()
    })
  })

  describe('refreshToken', () => {
    it('应该成功刷新 Token', async () => {
      const mockRefreshToken = vi.mocked(userApi.refreshToken)
      const mockSetToken = vi.mocked(storage.setToken)

      // Mock localStorage
      const mockLocalStorage = {
        getItem: vi.fn().mockReturnValue('old-refresh-token'),
        setItem: vi.fn(),
        removeItem: vi.fn()
      }
      Object.defineProperty(window, 'localStorage', {
        value: mockLocalStorage,
        writable: true
      })

      const mockResponse = {
        data: {
          data: {
            access_token: 'new-access-token',
            refresh_token: 'new-refresh-token',
            expires_in: 7200
          }
        }
      }
      mockRefreshToken.mockResolvedValue(mockResponse as any)

      const authStore = useAuthStore()
      const result = await authStore.refreshToken()

      expect(mockRefreshToken).toHaveBeenCalledWith('old-refresh-token')
      expect(mockSetToken).toHaveBeenCalledWith('new-access-token')
      expect(authStore.token).toBe('new-access-token')
      expect(result?.access_token).toBe('new-access-token')
    })

    it('没有 refresh_token 时应该返回 null', async () => {
      const mockLocalStorage = {
        getItem: vi.fn().mockReturnValue(null)
      }
      Object.defineProperty(window, 'localStorage', {
        value: mockLocalStorage,
        writable: true
      })

      const authStore = useAuthStore()
      const result = await authStore.refreshToken()

      expect(result).toBeNull()
    })

    it('刷新失败时应该登出', async () => {
      const mockRefreshToken = vi.mocked(userApi.refreshToken)
      const mockClearAuth = vi.mocked(storage.clearAuth)

      const mockLocalStorage = {
        getItem: vi.fn().mockReturnValue('invalid-refresh-token')
      }
      Object.defineProperty(window, 'localStorage', {
        value: mockLocalStorage,
        writable: true
      })

      mockRefreshToken.mockRejectedValue(new Error('刷新失败'))

      const authStore = useAuthStore()
      const result = await authStore.refreshToken()

      expect(mockClearAuth).toHaveBeenCalled()
      expect(result).toBeNull()
    })
  })

  describe('logout', () => {
    it('应该清除所有认证状态', () => {
      const mockClearAuth = vi.mocked(storage.clearAuth)

      const authStore = useAuthStore()
      authStore.user = { id: 1, username: 'test' } as any
      authStore.token = 'test-token'

      authStore.logout()

      expect(mockClearAuth).toHaveBeenCalled()
      expect(authStore.user).toBeNull()
      expect(authStore.token).toBeNull()
    })
  })

  describe('初始化状态', () => {
    it('应该从 localStorage 恢复用户信息', () => {
      const mockGetUserInfo = vi.mocked(storage.getUserInfo)
      const mockUser = { id: 1, username: 'testuser' }
      mockGetUserInfo.mockReturnValue(mockUser)

      const authStore = useAuthStore()

      expect(mockGetUserInfo).toHaveBeenCalled()
      expect(authStore.user).toEqual(mockUser)
    })
  })
})
