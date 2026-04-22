import request from '@/utils/request'
import type { ApiResponse, PageResult } from '@/types/api'
import type { User, TokenData, LoginPayload, RegisterPayload } from '@/types/user'

export const userApi = {
  register(data: RegisterPayload) {
    return request.post<ApiResponse<User>>('/auth/register', data)
  },

  login(data: LoginPayload) {
    return request.post<ApiResponse<TokenData>>('/auth/login', data)
  },

  getCurrentUser() {
    return request.get<ApiResponse<User>>('/users/me')
  },

  refreshToken(refresh: string) {
    return request.post<ApiResponse<TokenData>>('/auth/refresh', { refresh })
  }
}

export default userApi
