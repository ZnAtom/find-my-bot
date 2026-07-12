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
        <el-link :href="campusMapUrl" target="_blank" type="primary" underline="never">
          官方地图
        </el-link>
      </div>
    </div>

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
      placeholder="从层级里浏览地点"
      @change="handleTreeChange"
    />

    <div class="location-group-strip">
      <el-segmented v-model="activeGroup" :options="groupOptions" size="large" />
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
        <span>{{ entry.groupLabel }}</span>
      </button>
    </div>

    <div v-if="selectedEntry" class="location-summary">
      <div class="location-summary__main">
        <span class="summary-badge">{{ selectedSourceLabel }}</span>
        <strong>{{ selectedEntry.pathLabel }}</strong>
        <small>{{ selectedEntry.groupSummary }}</small>
      </div>
      <div class="location-summary__actions">
        <el-link :href="selectedMapLinks.official" target="_blank" type="primary" underline="never">官方地图</el-link>
        <el-link :href="selectedMapLinks.amap" target="_blank" type="primary" underline="never">高德</el-link>
        <el-link :href="selectedMapLinks.baidu" target="_blank" type="primary" underline="never">百度</el-link>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Compass, Search } from '@element-plus/icons-vue'
import {
  buildCampusMapLinks,
  campusLocationEntries,
  campusLocationGroupOptions,
  campusLocationTree,
  campusMapUrl,
  findCampusLocationByLabel,
  findCampusLocationByPathCodes,
  findNearestCampusLocation,
  formatCampusLocationPath,
  formatDistanceMeters,
  searchCampusLocations,
} from '../data/campusLocations'

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
    default: '按校区、区域和具体地点选择，或直接搜索地点名。',
  },
  searchPlaceholder: {
    type: String,
    default: '搜索建筑、餐厅、出入口',
  },
})

const emit = defineEmits(['update:modelValue', 'select'])

const query = ref(props.modelValue)
const activeGroup = ref('all')
const locating = ref(false)
const selectedEntry = ref(null)
const selectedPathCodes = ref([])
const selectedSource = ref('手动选择')

const groupOptions = computed(() => campusLocationGroupOptions)

const selectedMapLinks = computed(() => buildCampusMapLinks(selectedEntry.value))

const selectedSourceLabel = computed(() => selectedSource.value || '地点选择')

const visibleEntries = computed(() => {
  const text = query.value.trim()
  if (text) {
    return searchCampusLocations(text).slice(0, 12)
  }
  if (activeGroup.value === 'all') {
    return campusLocationEntries.slice(0, 12)
  }
  return campusLocationEntries.filter((entry) => entry.groupId === activeGroup.value).slice(0, 12)
})

const cascaderProps = {
  checkStrictly: false,
  emitPath: true,
  expandTrigger: 'hover',
}

watch(
  () => props.modelValue,
  (value) => {
    query.value = value || ''
    syncSelectionFromValue(value)
  },
  { immediate: true },
)

function fetchSuggestions(text, cb) {
  const results = searchCampusLocations(text).slice(0, 8).map((entry) => ({
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
    mapLinks: buildCampusMapLinks(entry),
    coordinates: entry.coords,
    ...extra,
  })
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
}

function clearSelectedValue() {
  query.value = ''
  clearSelection()
  emit('update:modelValue', '')
  emit('select', null)
}

async function handleLocate() {
  if (!navigator.geolocation) {
    ElMessage.warning('当前浏览器不支持定位')
    return
  }

  locating.value = true
  navigator.geolocation.getCurrentPosition(
    (position) => {
      locating.value = false
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
    () => {
      locating.value = false
      ElMessage.warning('定位未授权或不可用')
    },
    {
      enableHighAccuracy: true,
      timeout: 10000,
      maximumAge: 30000,
    },
  )
}

function sourceLabel(source) {
  if (source === 'search') return '搜索选择'
  if (source === 'tree') return '层级浏览'
  if (source === 'chip') return '快捷选择'
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

.location-search,
.location-cascader {
  width: 100%;
  min-width: 0;
}

.location-search + .location-cascader {
  margin-top: 10px;
}

.location-group-strip {
  width: 100%;
  min-width: 0;
  margin-top: 14px;
  overflow-x: auto;
  padding-bottom: 2px;
}

.location-group-strip :deep(.el-segmented) {
  width: max-content;
  max-width: none;
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
}

.location-summary__actions {
  display: flex;
  flex: 0 0 auto;
  gap: 10px;
  align-items: center;
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

  .map-actions,
  .location-summary__actions {
    justify-content: flex-start;
  }

  .location-chip-grid {
    grid-template-columns: 1fr;
  }
}
</style>
