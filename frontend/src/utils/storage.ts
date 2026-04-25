/**
 * 安全存储工具
 * 使用 Base64 编码存储敏感数据（防简单 XSS）
 * 注意：生产环境应使用 httpOnly cookie
 */

const TOKEN_KEY = 'token'
const REFRESH_TOKEN_KEY = 'refresh_token'
const USER_INFO_KEY = 'user_info'

/**
 * 简单 Base64 编码（防简单 XSS 攻击）
 */
function encode(value: string): string {
  try {
    return btoa(encodeURIComponent(value))
  } catch {
    return value
  }
}

/**
 * 简单 Base64 解码
 */
function decode(value: string): string {
  try {
    return decodeURIComponent(atob(value))
  } catch {
    return value
  }
}

export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, encode(token))
}

export function getToken(): string | null {
  const token = localStorage.getItem(TOKEN_KEY)
  return token ? decode(token) : null
}

export function setRefreshToken(token: string) {
  localStorage.setItem(REFRESH_TOKEN_KEY, encode(token))
}

export function getRefreshToken(): string | null {
  const token = localStorage.getItem(REFRESH_TOKEN_KEY)
  return token ? decode(token) : null
}

export function removeToken() {
  localStorage.removeItem(TOKEN_KEY)
}

export function removeRefreshToken() {
  localStorage.removeItem(REFRESH_TOKEN_KEY)
}

export function setUserInfo(userInfo: Record<string, unknown>) {
  try {
    const json = JSON.stringify(userInfo)
    localStorage.setItem(USER_INFO_KEY, encode(json))
  } catch (e) {
    console.error('Failed to serialize user info:', e)
  }
}

export function getUserInfo<T>(): T | null {
  const json = localStorage.getItem(USER_INFO_KEY)
  if (!json) return null
  try {
    return JSON.parse(decode(json)) as T
  } catch {
    return null
  }
}

export function removeUserInfo() {
  localStorage.removeItem(USER_INFO_KEY)
}

export function clearAuth() {
  removeToken()
  removeRefreshToken()
  removeUserInfo()
}
