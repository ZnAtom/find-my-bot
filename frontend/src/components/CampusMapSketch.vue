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
      title="点击地图任意位置，将自动选择附近的校园地点"
      @click="handleStageClick"
    >
      <svg
        class="map-svg"
        :viewBox="`0 0 ${viewBox.width} ${viewBox.height}`"
        preserveAspectRatio="none"
        role="img"
        aria-label="校园示意图"
      >
        <defs>
          <linearGradient id="campus-bg" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="rgba(37, 99, 235, 0.11)" />
            <stop offset="100%" stop-color="rgba(20, 184, 166, 0.09)" />
          </linearGradient>
          <pattern id="campus-grid" width="48" height="48" patternUnits="userSpaceOnUse">
            <path d="M 48 0 L 0 0 0 48" fill="none" stroke="rgba(148, 163, 184, 0.16)" stroke-width="1" />
          </pattern>
          <filter id="campus-shadow" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="10" stdDeviation="14" flood-color="rgba(15, 23, 42, 0.18)" />
          </filter>
        </defs>

        <rect x="0" y="0" :width="viewBox.width" :height="viewBox.height" fill="url(#campus-bg)" />
        <rect x="0" y="0" :width="viewBox.width" :height="viewBox.height" fill="url(#campus-grid)" />
        <rect x="22" y="22" :width="viewBox.width - 44" :height="viewBox.height - 44" rx="28" fill="none" stroke="rgba(148, 163, 184, 0.2)" />
        <polygon
          :points="boundaryPoints"
          class="campus-boundary"
        />

        <g
          v-for="region in regions"
          :key="region.group.id"
          class="campus-region"
          @click.stop="handleRegionClick(region.group.id, $event)"
        >
          <rect
            :x="region.box.x"
            :y="region.box.y"
            :width="region.box.width"
            :height="region.box.height"
            :rx="18"
            :fill="region.theme.fill"
            :stroke="region.theme.stroke"
            :class="['region-box', { active: isActiveGroup(region.group.id) }]"
          />
          <text
            :x="region.labelX"
            :y="region.labelY"
            class="region-label"
          >
            {{ region.group.label }}
          </text>
          <text
            :x="region.labelX"
            :y="region.labelY + 24"
            class="region-count"
          >
            {{ region.count }} 个地点
          </text>
        </g>
      </svg>

      <div
        v-for="point in points"
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
        <span v-if="point.showLabel" class="map-point-label">
          {{ point.entry.label }}
        </span>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import {
  campusBoundary,
  campusMapViewBox,
  campusLocationGroups,
  getCampusBounds,
  getCampusGroupEntries,
  getCampusGroupTheme,
  projectCampusBoundary,
  projectCampusPoint,
} from '../data/campusLocations'

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
    default: '点击区域或地点标记即可选择。',
  },
})

const emit = defineEmits(['select', 'select-group'])

const viewBox = campusMapViewBox

const mapBounds = computed(() => getCampusBounds(props.entries, campusBoundary))

const boundaryPoints = computed(() => projectCampusBoundary(campusBoundary, mapBounds.value, viewBox))

const highlightIdSet = computed(() => new Set(props.highlightedIds))

const regions = computed(() => campusLocationGroups.map((group) => {
  const groupEntries = getCampusGroupEntries(group.id).filter((entry) => props.entries.some((item) => item.id === entry.id))
  const groupBounds = getCampusBounds(groupEntries.length ? groupEntries : props.entries.filter((entry) => entry.groupId === group.id), [])
  const padded = expandBox(groupBounds, 0.16)
  const topLeft = projectCampusPoint([padded.minLng, padded.maxLat], mapBounds.value, viewBox)
  const bottomRight = projectCampusPoint([padded.maxLng, padded.minLat], mapBounds.value, viewBox)
  return {
    group,
    count: groupEntries.length,
    theme: getCampusGroupTheme(group.id),
    box: {
      x: Math.max(0, topLeft.x),
      y: Math.max(0, topLeft.y),
      width: Math.max(88, bottomRight.x - topLeft.x),
      height: Math.max(78, bottomRight.y - topLeft.y),
    },
    labelX: Math.max(48, Math.min(viewBox.width - 48, topLeft.x + 18)),
    labelY: Math.max(48, topLeft.y + 28),
  }
}))

const points = computed(() => props.entries.map((entry) => {
  const point = projectCampusPoint(entry.coords, mapBounds.value, viewBox)
  const highlighted = highlightIdSet.value.has(entry.id)
  const isSelected = entry.id === props.selectedId
  const isActiveGroup = props.activeGroupId === 'all' || entry.groupId === props.activeGroupId
  const hasSearchHighlight = highlightIdSet.value.size > 0
  const isDimmed = !isSelected && (
    (hasSearchHighlight && !highlighted) ||
    (props.activeGroupId !== 'all' && !isActiveGroup && !highlighted)
  )
  const showLabel = isSelected || highlighted || (props.activeGroupId !== 'all' && isActiveGroup)
  return {
    entry,
    x: Number(((point.x / viewBox.width) * 100).toFixed(2)),
    y: Number(((point.y / viewBox.height) * 100).toFixed(2)),
    theme: getCampusGroupTheme(entry.groupId),
    isHighlighted: highlighted,
    isSelected,
    isActiveGroup,
    isDimmed,
    showLabel,
  }
}))

const selectedLabel = computed(() => {
  if (!props.selectedId) return '未选择地点'
  const entry = props.entries.find((item) => item.id === props.selectedId)
  return entry?.pathLabel || '已选择地点'
})

function emitSelect(entry) {
  emit('select', entry)
}

function emitGroup(groupId) {
  emit('select-group', groupId)
}

function handleStageClick(event) {
  selectNearestFromEvent(event)
}

function handleRegionClick(groupId, event) {
  emitGroup(groupId)
  selectNearestFromEvent(event, groupId)
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

function expandBox(bounds, ratio = 0.1) {
  const lngSpan = Math.max(bounds.maxLng - bounds.minLng, 0.0001)
  const latSpan = Math.max(bounds.maxLat - bounds.minLat, 0.0001)
  return {
    minLng: bounds.minLng - lngSpan * ratio,
    maxLng: bounds.maxLng + lngSpan * ratio,
    minLat: bounds.minLat - latSpan * ratio,
    maxLat: bounds.maxLat + latSpan * ratio,
  }
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

.map-svg {
  width: 100%;
  height: 100%;
  display: block;
}

.campus-boundary {
  fill: rgba(255, 255, 255, 0.28);
  stroke: rgba(37, 99, 235, 0.55);
  stroke-width: 3;
  filter: url(#campus-shadow);
}

.campus-region {
  cursor: pointer;
}

.region-box {
  stroke-width: 2.4;
  opacity: 0.92;
}

.region-box.active {
  opacity: 1;
  stroke-width: 3;
}

.region-label {
  fill: var(--text-primary);
  font-size: 15px;
  font-weight: 800;
  paint-order: stroke;
  stroke: rgba(255, 255, 255, 0.8);
  stroke-width: 3px;
}

.region-count {
  fill: var(--text-secondary);
  font-size: 11px;
  font-weight: 700;
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
