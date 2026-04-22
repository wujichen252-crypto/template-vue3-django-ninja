export interface ApiResponse<T = unknown> {
  code: number
  data: T
  msg: string
  request_id: string
}

export interface PageResult<T = unknown> {
  items: T[]
  total: number
}
