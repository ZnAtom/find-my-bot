<template>
  <section class="campus-location-panel">
    <div class="panel-heading">
      <div>
        <p class="page-kicker">Campus Map</p>
        <h3>{{ title }}</h3>
        <p>{{ subtitle }}</p>
      </div>
      <div class="map-actions">
        <el-button text type="primary" :loading="locating" @click="handleLocate">
          <el-icon><Compass /></el-icon>
          使用当前位置
        </el-button>
      </div>
    </div>

    <div :class="['geo-hint', { warning: geoHintWarning }]">
      {{ geoHintText }}
    </div>

    <div class="location-group-strip">
      <el-segmented v-model="activeGroup" :options="groupOptions" size="large" />
    </div>

    <CampusMapSketch
      class="campus-sketch"
      :entries="campusLocationEntries"
      :selected-id="selectedEntry?.id || ''"
      :active-group-id="activeGroup"
      :highlighted-ids="highlightedIds"
      :subtitle="mapSubtitle"
      @select="selectEntry($event, 'map')"
      @select-group="handleMapGroupSelect"
    />

    <div class="location-tool-grid">
      <el-autocomplete
        v-model="query"
        class="location-search"
        :fetch-suggestions="fetchSuggestions"
        :trigger-on-focus="true"
        clearable
        :placeholder="searchPlaceholder"
        @select="handleSearchSelect"
        @clear="clearSelectedValue"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-autocomplete>

      <el-cascader
        v-model="selectedPathCodes"
        class="location-cascader"
        :options="campusLocationTree"
        :props="cascaderProps"
        filterable
        clearable
        :show-all-levels="true"
        placeholder="按层级浏览地点"
        @change="handleTreeChange"
      />
    </div>

    <div class="location-result-heading">
      <span>{{ activeGroupLabel }}</span>
      <strong>{{ visibleEntries.length }} 个候选地点</strong>
    </div>

    <div class="location-chip-grid">
      <button
        v-for="entry in visibleEntries"
        :key="entry.pathCodes.join('-')"
        :class="['location-chip', { active: selectedEntry?.pathCodes.join('-') === entry.pathCodes.join('-') }]"
        type="button"
        @click="selectEntry(entry, 'chip')"
      >
        <strong>{{ entry.label }}</strong>
        <span>{{ entry.sectionLabel }}</span>
      </button>
    </div>

    <div v-if="selectedEntry" class="location-summary">
      <div class="location-summary__main">
        <span class="summary-badge">{{ selectedSourceLabel }}</span>
        <strong>{{ selectedEntry.pathLabel }}</strong>
        <small>{{ selectedEntrySummary }}</small>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Compass, Search } from '@element-plus/icons-vue'
import {
  campusLocationEntries,
  campusLocationGroupOptions,
  campusLocationTree,
  findCampusLocationByLabel,
  findCampusLocationByPathCodes,
  findNearestCampusLocation,
  formatCampusLocationPath,
  formatDistanceMeters,
  searchCampusLocations,
} from '../data/campusLocations'
import CampusMapSketch from './CampusMapSketch.vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: '',
  },
  title: {
    type: String,
    default: '地点层级',
  },
  subtitle: {
    type: String,
    default: '按校区、区域、院系和具体地点选择，或直接搜索地点名。',
  },
  searchPlaceholder: {
    type: String,
    default: '搜索建筑、院系、餐厅、出入口',
  },
})

const emit = defineEmits(['update:modelValue', 'select'])

const query = ref(props.modelValue)
const activeGroup = ref('all')
const locating = ref(false)
const selectedEntry = ref(null)
const selectedPathCodes = ref([])
const selectedSource = ref('手动选择')
const selectedDistanceLabel = ref('')
const geoPermissionState = ref('checking')
const geoErrorMessage = ref('')

const groupOptions = computed(() => campusLocationGroupOptions)

const selectedSourceLabel = computed(() => selectedSource.value || '地点选择')

const activeSearchText = computed(() => {
  const text = query.value.trim()
  if (!text) return ''
  if (selectedEntry.value?.pathLabel === text) return ''
  return text
})

const visibleEntries = computed(() => {
  const text = activeSearchText.value
  const limit = text ? 20 : activeGroup.value === 'all' ? 16 : 28
  if (text) {
    return searchCampusLocations(text, 'all', limit)
  }
  return searchCampusLocations('', activeGroup.value, limit)
})

const highlightedIds = computed(() => (activeSearchText.value ? visibleEntries.value.map((entry) => entry.id) : []))

const activeGroupLabel = computed(() => {
  if (activeSearchText.value) return '搜索结果'
  const option = campusLocationGroupOptions.find((item) => item.value === activeGroup.value)
  return option?.label || '全部'
})

const selectedEntrySummary = computed(() => {
  if (!selectedEntry.value) return ''
  const base = selectedEntry.value.note || selectedEntry.value.groupSummary
  if (selectedDistanceLabel.value) {
    return `${base}，距当前位置约 ${selectedDistanceLabel.value}`
  }
  return base
})

const geoHintText = computed(() => {
  if (geoPermissionState.value === 'unsupported') return '当前浏览器不支持定位，可以直接在示意图上点选地点。'
  if (geoPermissionState.value === 'insecure') return '定位需要 HTTPS 或 localhost 环境，可以直接在示意图上点选地点。'
  if (geoPermissionState.value === 'denied') return '浏览器已拒绝定位，可以修改浏览器权限，或直接在示意图上点选地点。'
  if (geoErrorMessage.value) return geoErrorMessage.value
  if (geoPermissionState.value === 'granted') return '定位权限可用，点击按钮会选择距离当前位置最近的校园地点。'
  return '点击“使用当前位置”时，浏览器会请求定位权限；也可以直接在示意图上点选地点。'
})

const geoHintWarning = computed(() => ['unsupported', 'insecure', 'denied'].includes(geoPermissionState.value) || Boolean(geoErrorMessage.value))

const mapSubtitle = computed(() => {
  if (activeGroup.value === 'all') return '点击建筑轮廓、区域文字或地图空白位置，即可选择附近校园地点。'
  return `正在查看${activeGroupLabel.value}，点击建筑轮廓、标记或地图位置即可选择附近地点。`
})

const cascaderProps = {
  checkStrictly: false,
  emitPath: true,
  expandTrigger: 'hover',
}

onMounted(() => {
  refreshGeoPermissionState()
})

watch(
  () => props.modelValue,
  (value) => {
    query.value = value || ''
    syncSelectionFromValue(value)
  },
  { immediate: true },
)

function fetchSuggestions(text, cb) {
  const results = searchCampusLocations(text, 'all', 10).map((entry) => ({
    value: entry.pathLabel,
    entry,
  }))
  cb(results)
}

function handleSearchSelect(option) {
  if (option?.entry) {
    selectEntry(option.entry, 'search')
  }
}

function handleTreeChange(pathCodes) {
  if (!Array.isArray(pathCodes) || pathCodes.length === 0) {
    clearSelectedValue()
    return
  }
  const entry = findCampusLocationByPathCodes(pathCodes)
  if (entry) {
    selectEntry(entry, 'tree')
  }
}

function selectEntry(entry, source, extra = {}) {
  selectedEntry.value = entry
  selectedSource.value = sourceLabel(source)
  selectedDistanceLabel.value = extra.distanceLabel || ''
  query.value = formatCampusLocationPath(entry)
  selectedPathCodes.value = entry.pathCodes.slice()
  emit('update:modelValue', entry.pathLabel)
  emit('select', {
    entry,
    source,
    label: entry.label,
    pathLabel: entry.pathLabel,
    pathCodes: entry.pathCodes,
    groupId: entry.groupId,
    groupLabel: entry.groupLabel,
    coordinates: entry.mapCoords || entry.coords,
    ...extra,
  })
}

function handleMapGroupSelect(groupId) {
  activeGroup.value = groupId
  if (query.value) query.value = ''
}

function syncSelectionFromValue(value) {
  if (!value) {
    clearSelection()
    return
  }
  const entry = findCampusLocationByLabel(value)
  if (entry) {
    const sameEntry = selectedEntry.value?.id === entry.id
    selectedEntry.value = entry
    selectedPathCodes.value = entry.pathCodes.slice()
    if (!sameEntry) selectedSource.value = '已选择'
    query.value = entry.pathLabel
    return
  }
  selectedSource.value = '手动输入'
}

function clearSelection() {
  selectedEntry.value = null
  selectedPathCodes.value = []
  selectedSource.value = '手动选择'
  selectedDistanceLabel.value = ''
}

function clearSelectedValue() {
  query.value = ''
  clearSelection()
  emit('update:modelValue', '')
  emit('select', null)
}

async function handleLocate() {
  geoErrorMessage.value = ''
  if (!canUseGeolocation()) {
    ElMessage.warning(geoHintText.value)
    return
  }
  if (geoPermissionState.value === 'denied') {
    ElMessage.warning(geoHintText.value)
    return
  }

  locating.value = true
  navigator.geolocation.getCurrentPosition(
    (position) => {
      locating.value = false
      geoPermissionState.value = 'granted'
      const coords = [position.coords.longitude, position.coords.latitude]
      const nearest = findNearestCampusLocation(coords)
      if (!nearest) {
        ElMessage.warning('未找到可匹配的校园地点')
        return
      }
      selectEntry(nearest.entry, 'auto', {
        distanceMeters: nearest.distanceMeters,
        distanceLabel: formatDistanceMeters(nearest.distanceMeters),
      })
      if (nearest.distanceMeters > 1500) {
        ElMessage.warning(`当前位置离校内地点较远，请核对 ${nearest.entry.label}`)
      } else {
        ElMessage.success(`已定位到 ${nearest.entry.label}`)
      }
    },
    (error) => {
      locating.value = false
      geoErrorMessage.value = formatGeoError(error)
      refreshGeoPermissionState()
      ElMessage.warning(geoErrorMessage.value)
    },
    {
      enableHighAccuracy: true,
      timeout: 10000,
      maximumAge: 30000,
    },
  )
}

async function refreshGeoPermissionState() {
  if (!canUseGeolocation({ skipPermissionState: true })) return
  if (!navigator.permissions?.query) {
    geoPermissionState.value = 'prompt'
    return
  }
  try {
    const status = await navigator.permissions.query({ name: 'geolocation' })
    geoPermissionState.value = status.state
    status.onchange = () => {
      geoPermissionState.value = status.state
      if (status.state !== 'denied') geoErrorMessage.value = ''
    }
  } catch {
    geoPermissionState.value = 'prompt'
  }
}

function canUseGeolocation({ skipPermissionState = false } = {}) {
  if (!navigator.geolocation) {
    geoPermissionState.value = 'unsupported'
    return false
  }
  if (typeof window !== 'undefined' && !window.isSecureContext) {
    geoPermissionState.value = 'insecure'
    return false
  }
  if (!skipPermissionState && geoPermissionState.value === 'checking') {
    geoPermissionState.value = 'prompt'
  }
  return true
}

function formatGeoError(error) {
  if (error?.code === 1) return '定位权限被拒绝，可以修改浏览器权限，或直接在示意图上点选地点。'
  if (error?.code === 2) return '暂时无法获取当前位置，可以直接在示意图上点选地点。'
  if (error?.code === 3) return '定位请求超时，可以直接在示意图上点选地点。'
  return '暂时无法使用当前位置，可以直接在示意图上点选地点。'
}

function sourceLabel(source) {
  if (source === 'search') return '搜索选择'
  if (source === 'tree') return '层级浏览'
  if (source === 'chip') return '快捷选择'
  if (source === 'map') return '示意图点选'
  if (source === 'auto') return '自动定位'
  return '手动选择'
}
</script>

<style scoped>
.campus-location-panel {
  width: 100%;
  min-width: 0;
  max-width: 100%;
  padding: 18px;
  overflow: hidden;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-lg);
  background: var(--surface-muted);
}

.panel-heading {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  margin-bottom: 16px;
}

.panel-heading h3 {
  margin: 0;
  color: var(--text-primary);
  font-size: 20px;
  font-weight: 800;
}

.panel-heading p:not(.page-kicker) {
  margin: 8px 0 0;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.55;
}

.map-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
  align-items: center;
  flex: 0 0 auto;
}

.geo-hint {
  margin-bottom: 14px;
  padding: 10px 12px;
  border: 1px solid var(--accent-soft-border);
  border-radius: var(--border-radius-md);
  background: var(--accent-soft-hover);
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.55;
}

.geo-hint.warning {
  border-color: rgba(245, 158, 11, 0.28);
  background: rgba(245, 158, 11, 0.1);
  color: var(--warning-color);
}

.campus-sketch {
  margin-top: 14px;
}

.location-tool-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(210px, 0.62fr);
  gap: 10px;
  margin-top: 14px;
}

.location-search,
.location-cascader {
  width: 100%;
  min-width: 0;
}

.location-group-strip {
  width: 100%;
  min-width: 0;
  margin-top: 12px;
  overflow-x: auto;
  padding-bottom: 2px;
}

.location-group-strip :deep(.el-segmented) {
  width: max-content;
  max-width: none;
}

.location-result-heading {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  margin-top: 14px;
  color: var(--text-secondary);
  font-size: 12px;
}

.location-result-heading span,
.location-result-heading strong {
  min-width: 0;
}

.location-result-heading strong {
  color: var(--text-primary);
}

.location-chip-grid {
  min-width: 0;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(152px, 1fr));
  gap: 10px;
  margin-top: 12px;
}

.location-chip {
  min-width: 0;
  min-height: 64px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 5px;
  padding: 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-md);
  background: var(--surface-color);
  color: var(--text-primary);
  text-align: left;
  cursor: pointer;
}

.location-chip:hover,
.location-chip.active {
  border-color: var(--accent-soft-border);
  background: var(--accent-soft-hover);
}

.location-chip strong {
  overflow: hidden;
  font-size: 14px;
  font-weight: 800;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.location-chip span {
  overflow: hidden;
  color: var(--text-secondary);
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.location-summary {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  align-items: center;
  margin-top: 14px;
  padding: 12px;
  border: 1px solid var(--accent-soft-border);
  border-radius: var(--border-radius-md);
  background: var(--surface-color);
}

.location-summary__main {
  min-width: 0;
}

.summary-badge {
  display: inline-flex;
  margin-bottom: 6px;
  padding: 3px 7px;
  border-radius: 999px;
  color: var(--foundit-blue);
  background: var(--accent-soft);
  font-size: 11px;
  font-weight: 800;
}

.location-summary strong,
.location-summary small {
  display: block;
}

.location-summary strong {
  overflow: hidden;
  font-size: 14px;
  font-weight: 800;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.location-summary small {
  margin-top: 4px;
  color: var(--text-secondary);
  font-size: 12px;
  white-space: normal;
  line-height: 1.45;
}

@media (max-width: 720px) {
  .campus-location-panel {
    padding: 14px;
  }

  .panel-heading,
  .location-summary {
    flex-direction: column;
    align-items: stretch;
  }

  .map-actions {
    justify-content: flex-start;
  }

  .location-tool-grid {
    grid-template-columns: 1fr;
  }

  .location-chip-grid {
    grid-template-columns: 1fr;
  }
}
</style>
