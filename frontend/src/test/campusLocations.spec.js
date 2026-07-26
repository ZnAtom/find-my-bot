import { describe, expect, it } from 'vitest'
import {
  campusBoundary,
  campusLocationCategoryTree,
  campusLocationEntries,
  campusLocationTree,
  findCampusLocationByCategoryPath,
  findNearestCampusLocation,
  getCampusBounds,
  projectCampusBoundary,
  projectCampusPolygon,
  projectCampusPoint,
  searchCampusLocations,
} from '../data/campusLocations'

describe('campus location data', () => {
  it('provides a hierarchical campus tree', () => {
    expect(campusLocationTree[0].label).toContain('浦东校区')
    expect(campusLocationTree[0].children.length).toBe(5)
    const academic = campusLocationTree[0].children.find(group => group.label === '教学科研区')
    expect(academic).toBeTruthy()
    expect(academic.children.some(section => section.label === '信息科学与技术学院')).toBe(true)
    const infoSection = academic.children.find(section => section.label === '信息科学与技术学院')
    expect(infoSection.children.some(item => item.label === '信息学院1号楼')).toBe(true)
  })

  it('exposes every documented place through the categorized picker', () => {
    const pickerLeaves = campusLocationCategoryTree.flatMap(group =>
      group.children.flatMap(section => section.children)
    )

    expect(campusLocationCategoryTree).toHaveLength(5)
    expect(pickerLeaves).toHaveLength(71)
    expect(findCampusLocationByCategoryPath([
      'residential',
      'residential:学生公寓',
      'student-apartment-8',
    ])?.label).toBe('学生公寓8号楼')
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
    expect(campusLocationEntries.some(entry => entry.sectionLabel === '学生公寓')).toBe(true)
    expect(campusLocationEntries.some(entry => entry.sectionLabel === '餐饮')).toBe(true)
  })

  it('contains real building polygons for the map view', () => {
    const library = campusLocationEntries.find((entry) => entry.id === 'library')
    expect(library.sectionLabel).toBe('图书与学术服务')
    expect(Array.isArray(library.polygon)).toBe(true)
    const polygonPoints = projectCampusPolygon(library.polygon, getCampusBounds())
    expect(polygonPoints.split(' ').length).toBeGreaterThan(6)
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
