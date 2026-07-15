<template>
  <section class="campus-map-sketch">
    <div class="sketch-header">
      <div>
        <p class="page-kicker">Campus View</p>
        <h4>点选校园里的位置</h4>
        <p>{{ subtitle }}</p>
      </div>
      <div class="sketch-meta">
        <span>{{ entries.length }} 个地点</span>
        <span>{{ selectedLabel }}</span>
      </div>
    </div>

    <div
      class="map-stage"
      :class="{ 'has-official-map': officialMapReady }"
      :title="mapStageTitle"
      @click="!officialMapReady && handleStageClick($event)"
    >
      <div
        ref="officialMapEl"
        class="official-map-layer"
        :class="{ ready: officialMapReady }"
        aria-label="上海科技大学官方校园地图"
      />

      <svg
        v-if="!officialMapReady"
        class="map-svg"
        :viewBox="`0 0 ${viewBox.width} ${viewBox.height}`"
        preserveAspectRatio="none"
        role="img"
        aria-label="校园地图"
      >
        <defs>
          <linearGradient id="campus-bg" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="rgba(240, 247, 243, 0.96)" />
            <stop offset="100%" stop-color="rgba(235, 245, 255, 0.9)" />
          </linearGradient>
          <pattern id="campus-grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(148, 163, 184, 0.12)" stroke-width="1" />
          </pattern>
          <filter id="campus-shadow" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="8" stdDeviation="12" flood-color="rgba(15, 23, 42, 0.16)" />
          </filter>
        </defs>

        <rect x="0" y="0" :width="viewBox.width" :height="viewBox.height" fill="url(#campus-bg)" />
        <rect x="0" y="0" :width="viewBox.width" :height="viewBox.height" fill="url(#campus-grid)" />
        <polygon
          :points="boundaryPoints"
          class="campus-boundary"
        />

        <g
          v-for="line in campusRoads"
          :key="line.id"
          class="campus-road"
        >
          <polyline :points="line.points" />
        </g>

        <g class="campus-building-layer">
          <polygon
            v-for="building in buildings"
            :key="building.entry.id"
            :points="building.points"
            :fill="building.fill"
            :stroke="building.stroke"
            :class="[
              'campus-building',
              {
                selected: building.isSelected,
                filtered: building.isDimmed,
                active: building.isActiveGroup,
                hit: building.isHighlighted,
              },
            ]"
            @click.stop="emitSelect(building.entry)"
          >
            <title>{{ building.entry.pathLabel }}</title>
          </polygon>
        </g>

        <g
          v-for="label in areaLabels"
          :key="label.group.id"
          :class="[
            'campus-area-label',
            {
              active: label.isActive,
              filtered: label.isDimmed,
            },
          ]"
          @click.stop="emitGroup(label.group.id)"
        >
          <circle :cx="label.x" :cy="label.y - 6" r="5" :fill="label.theme.dot" />
          <text :x="label.x + 12" :y="label.y" class="area-label-text">
            {{ label.group.label }}
          </text>
          <text :x="label.x + 12" :y="label.y + 18" class="area-label-count">
            {{ label.count }} 个地点
          </text>
        </g>

        <g
          v-for="label in buildingLabels"
          :key="label.entry.id"
          class="campus-building-label"
          @click.stop="emitSelect(label.entry)"
        >
          <text :x="label.x" :y="label.y">
            {{ label.entry.label }}
          </text>
        </g>
      </svg>

      <div
        v-if="!officialMapReady"
        v-for="point in visiblePoints"
        :key="point.entry.id"
        class="map-point"
        :class="{
          selected: point.entry.id === selectedId,
          filtered: point.isDimmed,
          active: point.isActiveGroup,
          hit: point.isHighlighted,
        }"
        :style="{ left: `${point.x}%`, top: `${point.y}%` }"
        :title="point.entry.pathLabel"
        @click.stop="emitSelect(point.entry)"
      >
        <span class="map-point-dot" :style="{ background: point.theme.dot }" />
        <span v-if="point.showLabel && !point.hasPolygon" class="map-point-label">
          {{ point.entry.label }}
        </span>
      </div>

      <div v-if="officialMapError" class="map-fallback-note">
        {{ officialMapError }}
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  campusBoundary,
  campusMapViewBox,
  campusLocationGroups,
  getCampusBounds,
  getCampusGroupEntries,
  getCampusGroupTheme,
  findNearestCampusLocation,
  projectCampusBoundary,
  projectCampusPolygon,
  projectCampusPoint,
  shiftCampusPoint,
} from '../data/campusLocations'
import { apiBase } from '../api'

const props = defineProps({
  entries: {
    type: Array,
    default: () => [],
  },
  selectedId: {
    type: [Number, String],
    default: '',
  },
  activeGroupId: {
    type: String,
    default: 'all',
  },
  highlightedIds: {
    type: Array,
    default: () => [],
  },
  subtitle: {
    type: String,
    default: '点击建筑轮廓或地点标记即可选择。',
  },
})

const emit = defineEmits(['select', 'select-group'])

const viewBox = campusMapViewBox
const officialMapEl = ref(null)
const officialMapReady = ref(false)
const officialMapError = ref('')
const officialMapInstance = ref(null)
const officialMapOverlays = ref([])
const isTestMode = import.meta.env.MODE === 'test'
const OFFICIAL_MAP_AK = 'H8S40o4ZdE6hN4W4ESYvCgRY'
const OFFICIAL_TILE_ROOT = `${apiBase}/api/campus-map`
const OFFICIAL_CENTER = { lng: 121.601268, lat: 31.18331 }
const OFFICIAL_ZOOM = 18
let baiduMapPromise = null

const mapBounds = computed(() => getCampusBounds(props.entries, campusBoundary))

const boundaryPoints = computed(() => projectCampusBoundary(campusBoundary, mapBounds.value, viewBox))

const highlightIdSet = computed(() => new Set(props.highlightedIds))

const mapStageTitle = computed(() => officialMapReady.value
  ? '点击地图上的建筑轮廓、标记或者空白区域，将自动选择附近的校园地点'
  : '点击地图任意位置，将自动选择附近的校园地点')

const campusRoads = computed(() => [
  {
    id: 'north-ring',
    points: projectPolyline([
      [121.59735, 31.18405],
      [121.5992, 31.18436],
      [121.60165, 31.18455],
      [121.60475, 31.18442],
      [121.60638, 31.18405],
    ]),
  },
  {
    id: 'south-ring',
    points: projectPolyline([
      [121.59832, 31.18125],
      [121.60065, 31.18132],
      [121.6033, 31.18138],
      [121.6054, 31.18178],
    ]),
  },
  {
    id: 'center-axis',
    points: projectPolyline([
      [121.60272, 31.18575],
      [121.60248, 31.18442],
      [121.60232, 31.1833],
      [121.60272, 31.18212],
      [121.60318, 31.18104],
    ]),
  },
  {
    id: 'west-axis',
    points: projectPolyline([
      [121.5992, 31.18565],
      [121.59958, 31.1842],
      [121.59978, 31.18292],
      [121.60008, 31.18148],
    ]),
  },
])

const buildings = computed(() => props.entries
  .filter((entry) => Array.isArray(entry.polygon) && entry.polygon.length >= 3)
  .map((entry) => {
    const state = getEntryDisplayState(entry)
    const theme = getCampusGroupTheme(entry.groupId)
    return {
      entry,
      ...state,
      theme,
      points: projectCampusPolygon(entry.polygon, mapBounds.value, viewBox),
      fill: state.isSelected || state.isHighlighted ? theme.fill.replace('0.12', '0.26').replace('0.13', '0.27') : theme.fill,
      stroke: theme.stroke,
    }
  }))

const points = computed(() => props.entries.map((entry) => {
  const point = projectCampusPoint(entry.mapCoords || entry.coords, mapBounds.value, viewBox)
  const state = getEntryDisplayState(entry)
  const hasPolygon = Array.isArray(entry.polygon) && entry.polygon.length >= 3
  return {
    entry,
    hasPolygon,
    svgX: point.x,
    svgY: point.y,
    x: Number(((point.x / viewBox.width) * 100).toFixed(2)),
    y: Number(((point.y / viewBox.height) * 100).toFixed(2)),
    theme: getCampusGroupTheme(entry.groupId),
    ...state,
  }
}))

const visiblePoints = computed(() => points.value.filter((point) => {
  const hasPolygon = Array.isArray(point.entry.polygon) && point.entry.polygon.length >= 3
  return !hasPolygon || point.isSelected || point.isHighlighted
}))

const buildingLabels = computed(() => points.value
  .filter((point) => {
    const hasPolygon = Array.isArray(point.entry.polygon) && point.entry.polygon.length >= 3
    return hasPolygon && point.showLabel
  })
  .map((point) => ({
    ...point,
    x: Number(point.svgX.toFixed(2)),
    y: Number((point.svgY - 10).toFixed(2)),
  })))

const areaLabels = computed(() => campusLocationGroups
  .map((group) => {
    const groupEntries = getCampusGroupEntries(group.id).filter((entry) => props.entries.some((item) => item.id === entry.id))
    if (!groupEntries.length) return null
    const projectedPoints = groupEntries.map((entry) => projectCampusPoint(entry.mapCoords || entry.coords, mapBounds.value, viewBox))
    const x = projectedPoints.reduce((sum, point) => sum + point.x, 0) / projectedPoints.length
    const y = projectedPoints.reduce((sum, point) => sum + point.y, 0) / projectedPoints.length
    const isActive = isActiveGroup(group.id)
    return {
      group,
      count: groupEntries.length,
      theme: getCampusGroupTheme(group.id),
      x: Number(Math.max(32, Math.min(viewBox.width - 128, x)).toFixed(2)),
      y: Number(Math.max(36, Math.min(viewBox.height - 42, y)).toFixed(2)),
      isActive,
      isDimmed: props.activeGroupId !== 'all' && !isActive,
    }
  })
  .filter(Boolean))

const selectedLabel = computed(() => {
  if (!props.selectedId) return '未选择地点'
  const entry = props.entries.find((item) => item.id === props.selectedId)
  return entry?.pathLabel || '已选择地点'
})

onMounted(async () => {
  if (isTestMode) return
  await initOfficialMap()
})

onBeforeUnmount(() => {
  disposeOfficialMap()
})

watch(
  () => [props.entries, props.selectedId, props.activeGroupId, props.highlightedIds],
  () => {
    if (!officialMapReady.value) return
    refreshOfficialMapOverlays()
  },
  { deep: true },
)

function emitSelect(entry) {
  emit('select', entry)
}

function emitGroup(groupId) {
  emit('select-group', groupId)
}

function handleStageClick(event) {
  selectNearestFromEvent(event)
}

function handleOfficialMapClick(event) {
  if (!event?.point) return
  const nearest = findNearestCampusLocation([event.point.lng, event.point.lat])
  if (nearest?.entry) {
    emitSelect(nearest.entry)
  }
}

function selectNearestFromEvent(event, groupId = '') {
  const stage = event.currentTarget.classList?.contains('map-stage')
    ? event.currentTarget
    : event.currentTarget.closest?.('.map-stage')
  if (!stage) return
  const rect = stage.getBoundingClientRect()
  if (!rect.width || !rect.height) return

  const pointer = {
    x: ((event.clientX - rect.left) / rect.width) * 100,
    y: ((event.clientY - rect.top) / rect.height) * 100,
  }
  const candidates = getStageClickCandidates(groupId)
  const nearest = candidates.reduce((best, point) => {
    const distance = Math.hypot(point.x - pointer.x, point.y - pointer.y)
    return !best || distance < best.distance ? { point, distance } : best
  }, null)

  if (nearest?.point?.entry) {
    emitSelect(nearest.point.entry)
  }
}

function getStageClickCandidates(groupId = '') {
  if (groupId) {
    const groupPoints = points.value.filter((point) => point.entry.groupId === groupId)
    if (groupPoints.length) return groupPoints
  }
  const filtered = points.value.filter((point) =>
    point.isSelected ||
    point.isHighlighted ||
    props.activeGroupId === 'all' ||
    point.entry.groupId === props.activeGroupId,
  )
  return filtered.length ? filtered : points.value
}

function isActiveGroup(groupId) {
  return props.activeGroupId === 'all' || props.activeGroupId === groupId
}

async function initOfficialMap() {
  officialMapError.value = ''
  try {
    const BMap = await ensureBaiduMap()
    if (!officialMapEl.value || officialMapInstance.value) return

    const map = new BMap.Map(officialMapEl.value, {
      enableMapClick: false,
    })
    officialMapInstance.value = map
    map.centerAndZoom(new BMap.Point(OFFICIAL_CENTER.lng, OFFICIAL_CENTER.lat), OFFICIAL_ZOOM)
    map.setMinZoom(17)
    map.setMaxZoom(19)
    map.enableScrollWheelZoom(true)
    map.enableContinuousZoom?.()
    map.disableDoubleClickZoom?.()

    const tileLayer = new BMap.TileLayer({
      transparentPng: true,
      zIndex: 1000,
    })
    tileLayer.getTilesUrl = function getTilesUrl(tileCoord, zoom) {
      return `${OFFICIAL_TILE_ROOT}/tiles/${zoom}/tile${tileCoord.x}_${tileCoord.y}.png`
    }
    map.addTileLayer(tileLayer)
    map.addEventListener('click', handleOfficialMapClick)

    officialMapReady.value = true
    refreshOfficialMapOverlays()
    await nextTick()
    map.checkResize?.()
  } catch (error) {
    officialMapError.value = '官方地图暂时无法加载，可以继续使用下方地点选择。'
  }
}

function disposeOfficialMap() {
  const map = officialMapInstance.value
  if (!map || typeof window === 'undefined') return
  try {
    map.removeEventListener('click', handleOfficialMapClick)
    clearOfficialMapOverlays()
    officialMapInstance.value = null
    officialMapReady.value = false
  } catch {}
}

function refreshOfficialMapOverlays() {
  const map = officialMapInstance.value
  if (!map || typeof window === 'undefined' || !window.BMap) return
  clearOfficialMapOverlays()

  const BMap = window.BMap
  const highlights = new Set(props.highlightedIds)
  const hasSearchHighlight = highlights.size > 0

  for (const entry of props.entries) {
    const theme = getCampusGroupTheme(entry.groupId)
    const isSelected = entry.id === props.selectedId
    const isHighlighted = highlights.has(entry.id)
    const isActiveGroup = props.activeGroupId === 'all' || entry.groupId === props.activeGroupId
    const isDimmed = !isSelected && ((hasSearchHighlight && !isHighlighted) || (props.activeGroupId !== 'all' && !isActiveGroup && !isHighlighted))
    const baseOpacity = isSelected || isHighlighted ? 0.36 : isDimmed ? 0.05 : 0.14

    if (Array.isArray(entry.polygon) && entry.polygon.length >= 3) {
      const polygon = new BMap.Polygon(entry.polygon.map((point) => new BMap.Point(point[0], point[1])), {
        strokeColor: theme.stroke,
        strokeWeight: isSelected || isHighlighted ? 3 : 2,
        strokeOpacity: isDimmed ? 0.28 : 0.88,
        fillColor: theme.stroke,
        fillOpacity: baseOpacity,
        strokeStyle: 'solid',
        enableClicking: true,
      })
      polygon.addEventListener('click', () => emitSelect(entry))
      map.addOverlay(polygon)
      officialMapOverlays.value.push(polygon)
      continue
    }

    const coords = entry.mapCoords || entry.coords || [OFFICIAL_CENTER.lng, OFFICIAL_CENTER.lat]
    const point = new BMap.Point(coords[0], coords[1])
    const circle = new BMap.Circle(point, isSelected || isHighlighted ? 10 : 6, {
      strokeColor: theme.stroke,
      strokeWeight: isSelected || isHighlighted ? 2 : 1,
      strokeOpacity: isDimmed ? 0.25 : 0.85,
      fillColor: theme.dot,
      fillOpacity: isDimmed ? 0.18 : 0.78,
      enableClicking: true,
    })
    circle.addEventListener('click', () => emitSelect(entry))
    map.addOverlay(circle)
    officialMapOverlays.value.push(circle)
  }
}

function clearOfficialMapOverlays() {
  const map = officialMapInstance.value
  if (!map) return
  for (const overlay of officialMapOverlays.value) {
    try {
      map.removeOverlay(overlay)
    } catch {}
  }
  officialMapOverlays.value = []
}

function ensureBaiduMap() {
  if (typeof window === 'undefined') {
    return Promise.reject(new Error('browser unavailable'))
  }
  if (window.BMap?.Map) {
    return Promise.resolve(window.BMap)
  }
  if (baiduMapPromise) return baiduMapPromise

  baiduMapPromise = new Promise((resolve, reject) => {
    const existing = document.querySelector('script[data-foundit-baidu-map="true"]')
    if (existing) {
      const ready = () => {
        if (window.BMap?.Map) {
          cleanup()
          resolve(window.BMap)
        } else {
          requestAnimationFrame(ready)
        }
      }
      const cleanup = () => {
        existing.removeEventListener('load', ready)
        existing.removeEventListener('error', onError)
      }
      const onError = () => {
        cleanup()
        reject(new Error('Baidu map script failed'))
      }
      existing.addEventListener('load', ready)
      existing.addEventListener('error', onError)
      ready()
      return
    }

    const callbackName = '__founditBaiduMapReady'
    const cleanup = () => {
      delete window[callbackName]
    }
    window[callbackName] = () => {
      cleanup()
      resolve(window.BMap)
    }
    const script = document.createElement('script')
    script.dataset.founditBaiduMap = 'true'
    script.async = true
    script.defer = true
    script.src = `https://api.map.baidu.com/api?v=3.0&ak=${OFFICIAL_MAP_AK}&callback=${callbackName}`
    script.onerror = () => {
      cleanup()
      reject(new Error('Baidu map script failed'))
    }
    document.head.appendChild(script)
  })

  return baiduMapPromise
}

function getEntryDisplayState(entry) {
  const highlighted = highlightIdSet.value.has(entry.id)
  const isSelected = entry.id === props.selectedId
  const isActiveGroup = props.activeGroupId === 'all' || entry.groupId === props.activeGroupId
  const hasSearchHighlight = highlightIdSet.value.size > 0
  const isDimmed = !isSelected && (
    (hasSearchHighlight && !highlighted) ||
    (props.activeGroupId !== 'all' && !isActiveGroup && !highlighted)
  )
  return {
    isHighlighted: highlighted,
    isSelected,
    isActiveGroup,
    isDimmed,
    showLabel: isSelected || highlighted || (props.activeGroupId !== 'all' && isActiveGroup),
  }
}

function projectPolyline(points = []) {
  return points
    .map((point) => shiftCampusPoint(point) || point)
    .map((point) => projectCampusPoint(point, mapBounds.value, viewBox))
    .map((point) => `${point.x},${point.y}`)
    .join(' ')
}
</script>

<style scoped>
.campus-map-sketch {
  display: grid;
  gap: 14px;
}

.sketch-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
}

.sketch-header h4 {
  margin: 0;
  font-size: 18px;
  font-weight: 800;
}

.sketch-header p:not(.page-kicker) {
  margin: 8px 0 0;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.55;
}

.sketch-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
}

.sketch-meta span {
  display: inline-flex;
  min-height: 28px;
  align-items: center;
  padding: 4px 10px;
  border-radius: 999px;
  background: var(--accent-soft);
  color: var(--foundit-blue);
  font-size: 12px;
  font-weight: 800;
}

.map-stage {
  position: relative;
  width: 100%;
  aspect-ratio: 1000 / 680;
  min-height: 320px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-lg);
  overflow: hidden;
  background: var(--surface-color);
  box-shadow: var(--card-shadow);
  cursor: crosshair;
}

.map-stage.has-official-map {
  cursor: grab;
}

.official-map-layer {
  position: absolute;
  inset: 0;
  z-index: 4;
  width: 100%;
  height: 100%;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.18s ease;
}

.official-map-layer.ready {
  opacity: 1;
  pointer-events: auto;
}

.map-fallback-note {
  position: absolute;
  left: 14px;
  bottom: 14px;
  z-index: 6;
  max-width: min(360px, calc(100% - 28px));
  padding: 8px 10px;
  border: 1px solid rgba(245, 158, 11, 0.34);
  border-radius: var(--border-radius-md);
  background: rgba(255, 251, 235, 0.94);
  color: var(--warning-color);
  font-size: 12px;
  font-weight: 700;
  line-height: 1.45;
  pointer-events: none;
}

.map-svg {
  position: relative;
  z-index: 1;
  width: 100%;
  height: 100%;
  display: block;
}

.campus-boundary {
  fill: rgba(242, 247, 249, 0.82);
  stroke: rgba(100, 116, 139, 0.45);
  stroke-width: 2.5;
  filter: url(#campus-shadow);
}

.campus-road {
  pointer-events: none;
}

.campus-road polyline {
  fill: none;
  stroke: rgba(148, 163, 184, 0.36);
  stroke-width: 2.5;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.campus-building-layer {
  filter: url(#campus-shadow);
}

.campus-building {
  cursor: pointer;
  stroke-width: 1.8;
  vector-effect: non-scaling-stroke;
  transition: opacity 0.16s ease, stroke-width 0.16s ease, filter 0.16s ease, transform 0.16s ease;
}

.campus-building.active {
  stroke-width: 2.1;
}

.campus-building.hit,
.campus-building.selected {
  stroke-width: 2.8;
  filter: brightness(1.04);
}

.campus-building.filtered {
  opacity: 0.25;
}

.campus-area-label {
  cursor: pointer;
  user-select: none;
}

.campus-area-label.filtered {
  opacity: 0.42;
}

.area-label-text {
  fill: var(--text-primary);
  font-size: 13px;
  font-weight: 800;
  paint-order: stroke;
  stroke: rgba(255, 255, 255, 0.88);
  stroke-width: 3px;
}

.area-label-count {
  fill: var(--text-secondary);
  font-size: 10px;
  font-weight: 700;
}

.campus-building-label {
  cursor: pointer;
  user-select: none;
}

.campus-building-label text {
  fill: var(--text-primary);
  font-size: 11px;
  font-weight: 800;
  paint-order: stroke;
  stroke: rgba(255, 255, 255, 0.9);
  stroke-width: 3px;
  text-anchor: middle;
}

.map-point {
  position: absolute;
  transform: translate(-50%, -50%);
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--text-primary);
  cursor: pointer;
  user-select: none;
  z-index: 3;
}

.map-point.filtered {
  opacity: 0.24;
  z-index: 1;
}

.map-point.active,
.map-point.hit,
.map-point.selected {
  z-index: 5;
}

.map-point-dot {
  width: 12px;
  height: 12px;
  border: 2px solid rgba(255, 255, 255, 0.9);
  border-radius: 50%;
  box-shadow: 0 1px 6px rgba(15, 23, 42, 0.22);
  flex: 0 0 auto;
}

.map-point.active .map-point-dot {
  width: 14px;
  height: 14px;
}

.map-point.selected .map-point-dot {
  width: 18px;
  height: 18px;
  border-width: 3px;
}

.map-point-label {
  max-width: min(168px, 38vw);
  padding: 4px 8px;
  border: 1px solid var(--border-color);
  border-radius: 999px;
  background: var(--surface-color);
  color: var(--text-primary);
  font-size: 11px;
  font-weight: 800;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.14);
}

:global(html.dark) .map-fallback-note {
  background: rgba(69, 45, 12, 0.92);
}

:global(html.dark) .campus-boundary {
  fill: rgba(42, 42, 42, 0.82);
  stroke: rgba(169, 173, 181, 0.38);
}

:global(html.dark) .campus-road polyline {
  stroke: rgba(169, 173, 181, 0.24);
}

:global(html.dark) .area-label-text,
:global(html.dark) .campus-building-label text {
  stroke: rgba(27, 27, 27, 0.92);
}

:global(html.dark) .campus-building.selected,
:global(html.dark) .campus-building.hit {
  filter: brightness(1.08);
}

@media (max-width: 720px) {
  .sketch-header {
    flex-direction: column;
  }

  .sketch-meta {
    justify-content: flex-start;
  }

  .map-stage {
    min-height: 280px;
  }

  .map-point-label {
    font-size: 10px;
  }
}
</style>
