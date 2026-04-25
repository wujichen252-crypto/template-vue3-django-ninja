import { describe, it, expect, beforeEach } from 'vitest'
import {
  getToken,
  setToken,
  removeToken,
  getRefreshToken,
  setRefreshToken,
  getUserInfo,
  setUserInfo,
  removeUserInfo,
  clearAuth
} from './storage'

describe('Storage Utils', () => {
  beforeEach(() => {
    // 清理 localStorage
    localStorage.clear()
  })

  describe('Token Management', () => {
    it('应该正确设置和获取 Token', () => {
      const token = 'test-access-token'
      setToken(token)
      expect(getToken()).toBe(token)
    })

    it('应该正确移除 Token', () => {
      setToken('test-token')
      removeToken()
      expect(getToken()).toBeNull()
    })

    it('没有 Token 时应该返回 null', () => {
      expect(getToken()).toBeNull()
    })
  })

  describe('Refresh Token Management', () => {
    it('应该正确设置和获取 Refresh Token', () => {
      const token = 'test-refresh-token'
      setRefreshToken(token)
      expect(getRefreshToken()).toBe(token)
    })

    it('removeToken 应该同时移除 Refresh Token', () => {
      setToken('access-token')
      setRefreshToken('refresh-token')
      removeToken()
      expect(getToken()).toBeNull()
      expect(getRefreshToken()).toBeNull()
    })
  })

  describe('User Info Management', () => {
    it('应该正确设置和获取用户信息', () => {
      const userInfo = {
        id: 1,
        username: 'testuser',
        email: 'test@example.com'
      }
      setUserInfo(userInfo)
      expect(getUserInfo()).toEqual(userInfo)
    })

    it('应该正确移除用户信息', () => {
      setUserInfo({ id: 1, username: 'test' })
      removeUserInfo()
      expect(getUserInfo()).toBeNull()
    })

    it('应该返回指定类型的用户信息', () => {
      interface User {
        id: number
        username: string
      }
      const userInfo: User = { id: 1, username: 'test' }
      setUserInfo(userInfo)
      const retrieved = getUserInfo<User>()
      expect(retrieved?.id).toBe(1)
      expect(retrieved?.username).toBe('test')
    })

    it('没有用户信息时应该返回 null', () => {
      expect(getUserInfo()).toBeNull()
    })

    it('处理无效的 JSON 数据时应该返回 null', () => {
      localStorage.setItem('user_info', 'invalid-json')
      expect(getUserInfo()).toBeNull()
    })
  })

  describe('clearAuth', () => {
    it('应该清除所有认证信息', () => {
      setToken('access-token')
      setRefreshToken('refresh-token')
      setUserInfo({ id: 1, username: 'test' })

      clearAuth()

      expect(getToken()).toBeNull()
      expect(getRefreshToken()).toBeNull()
      expect(getUserInfo()).toBeNull()
    })
  })
})
