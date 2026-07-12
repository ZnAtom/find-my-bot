import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import CampusMapSketch from '../components/CampusMapSketch.vue'
import {
  campusBoundary,
  campusLocationEntries,
  campusMapViewBox,
  getCampusBounds,
  projectCampusPoint,
} from '../data/campusLocations'

describe('CampusMapSketch', () => {
  it('selects the nearest place when the map stage is clicked', async () => {
    const wrapper = mount(CampusMapSketch, {
      props: {
        entries: campusLocationEntries,
        activeGroupId: 'all',
      },
    })
    const library = campusLocationEntries.find((entry) => entry.id === 'library')
    const stage = wrapper.find('.map-stage')
    const bounds = getCampusBounds(campusLocationEntries, campusBoundary)
    const point = projectCampusPoint(library.coords, bounds, campusMapViewBox)

    stage.element.getBoundingClientRect = () => ({
      left: 0,
      top: 0,
      right: campusMapViewBox.width,
      bottom: campusMapViewBox.height,
      width: campusMapViewBox.width,
      height: campusMapViewBox.height,
      x: 0,
      y: 0,
      toJSON: () => ({}),
    })

    await stage.trigger('click', {
      clientX: point.x,
      clientY: point.y,
    })

    expect(wrapper.emitted('select')?.[0]?.[0].id).toBe('library')
  })

  it('selects a building directly when the polygon is clicked', async () => {
    const wrapper = mount(CampusMapSketch, {
      props: {
        entries: campusLocationEntries,
        activeGroupId: 'all',
      },
    })

    const libraryPolygon = wrapper.findAll('polygon.campus-building').find((node) =>
      node.element.textContent?.includes('图书馆'),
    )

    expect(libraryPolygon).toBeTruthy()

    await libraryPolygon.trigger('click')

    expect(wrapper.emitted('select')?.at(-1)?.[0].id).toBe('library')
  })

  it('dims places outside the active group', () => {
    const wrapper = mount(CampusMapSketch, {
      props: {
        entries: campusLocationEntries,
        activeGroupId: 'service',
      },
    })

    expect(wrapper.find('polygon.campus-building').classes()).toContain('filtered')
    expect(wrapper.find('[title*="尚科餐厅"]').classes()).not.toContain('filtered')
  })
})
