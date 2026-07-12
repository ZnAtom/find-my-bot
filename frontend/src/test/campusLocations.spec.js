import { describe, expect, it } from 'vitest'
import {
  campusLocationTree,
  findNearestCampusLocation,
  searchCampusLocations,
} from '../data/campusLocations'

describe('campus location data', () => {
  it('provides a hierarchical campus tree', () => {
    expect(campusLocationTree[0].label).toContain('浦东校区')
    expect(campusLocationTree[0].children.length).toBeGreaterThan(2)
    expect(campusLocationTree[0].children.some(group => group.label === '生活服务区')).toBe(true)
  })

  it('searches by building and alias', () => {
    const results = searchCampusLocations('图书信息中心')
    expect(results[0].label).toBe('图书馆')
  })

  it('finds the nearest known campus place', () => {
    const nearest = findNearestCampusLocation([121.6032, 31.1812])
    expect(nearest.entry.label).toBe('图书馆')
    expect(nearest.distanceMeters).toBeLessThan(80)
  })
})
