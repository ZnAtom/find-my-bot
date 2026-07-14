import { describe, expect, it } from 'vitest'
import { firstSafeImageUrl, resolveImageUrl } from '../api'

describe('image URL helpers', () => {
  it('allows uploaded images from the app path', () => {
    expect(resolveImageUrl('/uploads/item.jpg')).toBe('/uploads/item.jpg')
    expect(resolveImageUrl('uploads/item.jpg')).toBe('/uploads/item.jpg')
  })

  it('blocks external image URLs', () => {
    expect(resolveImageUrl('https://example.com/tracker.jpg')).toBe('')
    expect(firstSafeImageUrl('https://example.com/tracker.jpg,/uploads/item.jpg')).toBe('/uploads/item.jpg')
  })
})
