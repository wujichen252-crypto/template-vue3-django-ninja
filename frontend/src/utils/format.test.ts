import { describe, it, expect } from 'vitest'
import { formatDate, formatFileSize } from './format'

describe('formatDate', () => {
  it('should format date correctly', () => {
    const date = new Date('2024-01-15T10:30:00')
    expect(formatDate(date)).toBe('2024-01-15 10:30:00')
  })

  it('should handle string date input', () => {
    expect(formatDate('2024-01-15T10:30:00')).toBe('2024-01-15 10:30:00')
  })

  it('should return empty string for invalid date', () => {
    expect(formatDate('invalid')).toBe('')
  })
})

describe('formatFileSize', () => {
  it('should format bytes correctly', () => {
    expect(formatFileSize(500)).toBe('500 B')
  })

  it('should format KB correctly', () => {
    expect(formatFileSize(1024)).toBe('1.00 KB')
  })

  it('should format MB correctly', () => {
    expect(formatFileSize(1024 * 1024)).toBe('1.00 MB')
  })

  it('should format GB correctly', () => {
    expect(formatFileSize(1024 * 1024 * 1024)).toBe('1.00 GB')
  })

  it('should handle zero bytes', () => {
    expect(formatFileSize(0)).toBe('0 B')
  })
})
