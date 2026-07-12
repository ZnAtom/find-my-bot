import { describe, expect, it } from 'vitest'
import {
  campusBoundary,
  campusLocationEntries,
  campusLocationTree,
  findNearestCampusLocation,
  getCampusBounds,
  projectCampusBoundary,
  projectCampusPoint,
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

  it('returns enough entries for the visual picker', () => {
    const results = searchCampusLocations('', 'academic', 20)
    expect(results.length).toBeGreaterThan(12)
  })

  it('searches residential and dining locations from the campus map', () => {
    expect(searchCampusLocations('宿舍')[0].label).toBe('学生公寓8号楼')
    expect(searchCampusLocations('白玉兰')[0].label).toBe('白玉兰一楼学生食堂')
    expect(campusLocationEntries.some(entry => entry.groupLabel === '住宿公共区')).toBe(true)
  })

  it('finds the nearest known campus place', () => {
    const nearest = findNearestCampusLocation([121.6032, 31.1812])
    expect(nearest.entry.label).toBe('图书馆')
    expect(nearest.distanceMeters).toBeLessThan(80)
  })

  it('projects campus coordinates into the visual map', () => {
    const bounds = getCampusBounds()
    const point = projectCampusPoint([121.6032, 31.1812], bounds)
    const boundary = projectCampusBoundary(campusBoundary, bounds)

    expect(point.x).toBeGreaterThan(0)
    expect(point.y).toBeGreaterThan(0)
    expect(boundary.split(' ').length).toBeGreaterThan(8)
  })
})
