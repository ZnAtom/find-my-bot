const CAMPUS_NAME = '上海科技大学浦东校区'
const CAMPUS_CODE = 'pudong-campus'

export const campusMapUrl = 'https://map.shanghaitech.edu.cn/'

export const campusLocationGroups = [
  {
    id: 'academic',
    label: '教学科研区',
    summary: '学院楼、图书馆、行政与研究中心',
    items: [
      { id: 'library', label: '图书馆', aliases: ['图书信息中心', 'library'], coords: [121.6032318235294, 31.181181117647057], note: '图书信息中心' },
      { id: 'info-1', label: '信息学院1号楼', aliases: ['信息科学与技术学院1号楼'], coords: [121.6011669444444, 31.18360938888889], note: '信息科学与技术学院' },
      { id: 'info-2', label: '信息学院2号楼', aliases: ['信息科学与技术学院2号楼'], coords: [121.6010671, 31.184125800000004], note: '信息科学与技术学院' },
      { id: 'info-3', label: '信息学院3号楼', aliases: ['信息科学与技术学院3号楼'], coords: [121.6021721111111, 31.184221999999995], note: '信息科学与技术学院' },
      { id: 'materials-1', label: '物质学院1号楼', aliases: ['物质科学与技术学院1号楼'], coords: [121.5995085384615, 31.183933846153852], note: '物质科学与技术学院' },
      { id: 'materials-2', label: '物质学院2号楼', aliases: ['物质科学与技术学院2号楼'], coords: [121.59846099999999, 31.183627333333334], note: '物质科学与技术学院' },
      { id: 'materials-3', label: '物质学院3号楼', aliases: ['物质科学与技术学院3号楼'], coords: [121.59770237499998, 31.183387500000002], note: '物质科学与技术学院' },
      { id: 'materials-4', label: '物质学院4号楼', aliases: ['物质科学与技术学院4号楼'], coords: [121.5999406, 31.1833072], note: '物质科学与技术学院' },
      { id: 'materials-5', label: '物质学院5号楼', aliases: ['物质科学与技术学院5号楼'], coords: [121.59938657142857, 31.183027714285714], note: '物质科学与技术学院' },
      { id: 'materials-6', label: '物质学院6号楼', aliases: ['物质科学与技术学院6号楼'], coords: [121.59883283333333, 31.183134499999998], note: '物质科学与技术学院' },
      { id: 'materials-7', label: '物质学院7号楼', aliases: ['物质科学与技术学院7号楼'], coords: [121.59811638461541, 31.18289276923077], note: '物质科学与技术学院' },
      { id: 'materials-8', label: '物质学院8号楼', aliases: ['物质科学与技术学院8号楼'], coords: [121.598799, 31.182684888888886], note: '物质科学与技术学院' },
      { id: 'life-science', label: '生命学院', aliases: ['生命科学与技术学院'], coords: [121.60087133333333, 31.18531425], note: '生命科学与技术学院' },
      { id: 'art', label: '创意与艺术学院', aliases: ['创意与艺术学院楼'], coords: [121.59965445454544, 31.182274045454548], note: '创意与艺术学院' },
      { id: 'management', label: '创业与管理学院', aliases: ['创业与管理学院楼'], coords: [121.60127893333332, 31.182637333333332], note: '创业与管理学院' },
      { id: 'ihuman', label: '人字楼', aliases: ['iHuman研究所', '免疫化学研究所'], coords: [121.60136899999999, 31.185935066666666], note: 'iHuman研究所 / 免疫化学研究所' },
      { id: 'administration', label: '行政中心', aliases: ['校长办公室', '公共服务处'], coords: [121.5999363076923, 31.181199692307693], note: '校长办公室 / 行政办公室' },
      { id: 'teaching-center', label: '教学中心', aliases: ['教学事务处'], coords: [121.6017683, 31.1814982], note: '教学事务处' },
      { id: 'report-hall', label: '报告厅', aliases: ['教学中心报告厅'], coords: [121.60229225, 31.18186025], note: '公共服务处' },
      { id: 'h2', label: 'H2楼·学生科创中心', aliases: ['H2楼', '学生科创中心'], coords: [121.60257916666666, 31.18249916666667], note: '通识教育中心 / 学生事务处' },
      { id: 'math-research', label: '数学科学研究所', aliases: ['数学科学研究所楼'], coords: [121.59989812500001, 31.181709249999997], note: '数学科学研究所' },
      { id: 'humanities', label: '人文科学研究院', aliases: ['人文科学研究院楼'], coords: [121.6000924, 31.1825596], note: '人文科学研究院' },
      { id: 'bioengineering', label: '生医工学院', aliases: ['生物医学工程学院'], coords: [121.60199818181822, 31.183790181818186], note: '信息科学与技术学院' },
    ],
  },
  {
    id: 'service',
    label: '生活服务区',
    summary: '餐饮、快递、银行与日常服务',
    items: [
      { id: 'service-center', label: '校园服务中心', aliases: ['公共服务中心'], coords: [121.603048, 31.183629], note: '日常服务' },
      { id: 'copy-room', label: '文印室', aliases: ['自助打印'], coords: [121.603506, 31.181629], note: '打印与复印' },
      { id: 'clinic', label: '医务室', aliases: ['校医务室'], coords: [121.603344, 31.184406], note: '医疗服务' },
      { id: 'delivery', label: '菜鸟驿站', aliases: ['快递驿站'], coords: [121.605289, 31.182325], note: '快递收发' },
      { id: 'bank-atm', label: '上海银行ATM', aliases: ['ATM'], coords: [121.602939, 31.181266], note: '自助取款' },
      { id: 'bank', label: '上海银行', aliases: ['上海银行网点'], coords: [121.605289, 31.18431], note: '银行服务' },
      { id: 'familymart', label: '全家便利店', aliases: ['全家'], coords: [121.603901, 31.183024], note: '便利店' },
      { id: 'kfc', label: 'KFC', aliases: ['肯德基'], coords: [121.603587, 31.183379], note: '餐饮' },
      { id: 'nice-coffee', label: '耐思咖啡', aliases: ['咖啡厅'], coords: [121.604211, 31.184437], note: '咖啡与简餐' },
      { id: 'shangke-canteen', label: '尚科餐厅', aliases: ['尚科餐厅1楼', '尚科餐厅二楼自选区'], coords: [121.603587, 31.183414], note: '餐饮' },
      { id: 'silk-road-canteen', label: '丝路餐厅', aliases: ['丝路'], coords: [121.603744, 31.183823], note: '餐饮' },
      { id: 'western-canteen', label: '西餐厅', aliases: ['西餐'], coords: [121.603856, 31.183209], note: '餐饮' },
      { id: 'faculty-canteen', label: '教工餐厅与点餐区', aliases: ['教工餐厅'], coords: [121.60303, 31.181904], note: '教工餐饮' },
      { id: 'barber', label: '校园理发中心', aliases: ['理发店'], coords: [121.603924, 31.183769], note: '理发服务' },
      { id: 'souvenir', label: '纪念品专卖', aliases: ['纪念品店'], coords: [121.603138, 31.182528], note: '纪念品' },
      { id: 'print', label: '自助打印', aliases: ['打印机'], coords: [121.601714, 31.181641], note: '自助打印' },
      { id: 'shuttle', label: '学校班车', aliases: ['班车'], coords: [121.605343, 31.181877], note: '校内交通' },
    ],
  },
  {
    id: 'sports',
    label: '运动休闲区',
    summary: '体育馆、运动场与户外场地',
    items: [
      { id: 'gym', label: '体育馆', aliases: ['体育馆'], coords: [121.604238, 31.182653], note: '室内运动' },
      { id: 'track', label: '运动场', aliases: ['操场'], coords: [121.606044, 31.182016], note: '户外运动' },
      { id: 'swimming', label: '游泳馆', aliases: ['泳池'], coords: [121.605864, 31.18192], note: '游泳' },
      { id: 'basketball', label: '篮球场', aliases: ['篮球'], coords: [121.60578, 31.18175], note: '球类运动' },
      { id: 'tennis', label: '网球场', aliases: ['网球'], coords: [121.60622, 31.18222], note: '球类运动' },
      { id: 'volleyball', label: '排球场', aliases: ['排球'], coords: [121.60595, 31.18158], note: '球类运动' },
      { id: 'fitness', label: '健身场', aliases: ['健身区'], coords: [121.60562, 31.18143], note: '健身' },
    ],
  },
  {
    id: 'transport',
    label: '交通出入口',
    summary: '地铁、公交、车库与校车',
    items: [
      { id: 'metro-13', label: '地铁13号线中科路站', aliases: ['中科路站', '地铁站'], coords: [121.608896, 31.184649], note: '地铁 13 号线' },
      { id: 'bus-25', label: '(浦东25路)金科路中科路', aliases: ['金科路中科路'], coords: [121.608627, 31.184155], note: '公交站点' },
      { id: 'bus-58-1', label: '(浦东58路)环科路金科路', aliases: ['环科路金科路'], coords: [121.606363, 31.180842], note: '公交站点' },
      { id: 'bus-58-2', label: '(浦东58路)海科路金科路', aliases: ['海科路金科路'], coords: [121.606839, 31.186534], note: '公交站点' },
      { id: 'bus-58-3', label: '(浦东58路)海科路科苑路', aliases: ['海科路科苑路'], coords: [121.603003, 31.18658], note: '公交站点' },
      { id: 'bus-nanchuan', label: '(南川线)华夏中路殷家浜路', aliases: ['华夏中路殷家浜路'], coords: [121.601705, 31.17798], note: '公交站点' },
      { id: 'garage', label: '车库出入口', aliases: ['车库'], coords: [121.605271, 31.184132], note: '车行出入口' },
    ],
  },
]

export const campusLocationEntries = campusLocationGroups.flatMap((group) =>
  group.items.map((item) => createLocationEntry(group, item))
)

export const campusLocationTree = [
  {
    value: CAMPUS_CODE,
    label: CAMPUS_NAME,
    children: campusLocationGroups.map((group) => ({
      value: group.id,
      label: group.label,
      children: group.items.map((item) => ({
        value: item.id,
        label: item.label,
      })),
    })),
  },
]

export const campusLocationGroupOptions = [
  { label: '全部', value: 'all' },
  ...campusLocationGroups.map((group) => ({ label: group.label, value: group.id })),
]

export function createLocationEntry(group, item) {
  const pathLabels = [CAMPUS_NAME, group.label, item.label]
  return {
    ...item,
    groupId: group.id,
    groupLabel: group.label,
    groupSummary: group.summary,
    campusName: CAMPUS_NAME,
    pathLabels,
    pathLabel: pathLabels.join(' · '),
    pathCodes: [CAMPUS_CODE, group.id, item.id],
    searchText: normalizeCampusText([CAMPUS_NAME, group.label, item.label, item.note, ...(item.aliases || [])].join(' ')),
  }
}

export function findCampusLocationByPathCodes(pathCodes = []) {
  const key = pathCodes.join('>')
  return campusLocationEntries.find((entry) => entry.pathCodes.join('>') === key) || null
}

export function findCampusLocationByLabel(label = '') {
  const normalized = normalizeCampusText(label)
  if (!normalized) return null
  return campusLocationEntries.find((entry) =>
    normalizeCampusText(entry.pathLabel) === normalized ||
    normalizeCampusText(entry.label) === normalized ||
    normalizeCampusText(entry.aliases?.[0] || '') === normalized ||
    entry.searchText.includes(normalized),
  ) || null
}

export function searchCampusLocations(query = '', groupId = 'all') {
  const normalized = normalizeCampusText(query)
  const source = groupId === 'all'
    ? campusLocationEntries
    : campusLocationEntries.filter((entry) => entry.groupId === groupId)

  if (!normalized) {
    return source.slice(0, 12)
  }

  return source
    .map((entry) => ({ entry, score: scoreCampusLocation(entry, normalized) }))
    .filter((item) => item.score > 0)
    .sort((a, b) => b.score - a.score || a.entry.pathLabel.length - b.entry.pathLabel.length)
    .slice(0, 12)
    .map((item) => item.entry)
}

export function findNearestCampusLocation(coords) {
  if (!coords || coords.length !== 2) return null
  let best = null
  for (const entry of campusLocationEntries) {
    if (!entry.coords) continue
    const distanceMeters = getDistanceMeters(coords, entry.coords)
    if (!best || distanceMeters < best.distanceMeters) {
      best = { entry, distanceMeters }
    }
  }
  return best
}

export function buildCampusMapLinks(entry) {
  if (!entry?.coords) {
    return {
      official: campusMapUrl,
      amap: campusMapUrl,
      baidu: campusMapUrl,
    }
  }

  const [lng, lat] = entry.coords
  const title = encodeURIComponent(entry.label)
  const content = encodeURIComponent(entry.pathLabel)
  return {
    official: campusMapUrl,
    amap: `https://uri.amap.com/marker?position=${lng},${lat}&name=${title}&coordinate=gaode&callnative=0`,
    baidu: `https://api.map.baidu.com/marker?location=${lat},${lng}&title=${title}&content=${content}&output=html`,
  }
}

export function formatCampusLocationPath(entry) {
  return entry?.pathLabel || ''
}

export function formatDistanceMeters(distanceMeters) {
  if (!Number.isFinite(distanceMeters)) return ''
  if (distanceMeters < 1000) {
    return `${Math.round(distanceMeters)} 米`
  }
  return `${(distanceMeters / 1000).toFixed(1)} 公里`
}

export function normalizeCampusText(value = '') {
  return String(value)
    .toLowerCase()
    .replace(/[\s·/\\()（）【】\[\],，.。:：;；_-]+/g, '')
}

function scoreCampusLocation(entry, normalizedQuery) {
  const pathLabel = normalizeCampusText(entry.pathLabel)
  const label = normalizeCampusText(entry.label)
  if (label === normalizedQuery || pathLabel === normalizedQuery) return 300
  if (label.startsWith(normalizedQuery)) return 250
  if (pathLabel.startsWith(normalizedQuery)) return 220
  if (pathLabel.includes(normalizedQuery)) return 180
  if (entry.searchText.includes(normalizedQuery)) return 140
  return 0
}

function getDistanceMeters(origin, target) {
  const [lng1, lat1] = origin
  const [lng2, lat2] = target
  const rad = Math.PI / 180
  const dLat = (lat2 - lat1) * rad
  const dLng = (lng2 - lng1) * rad
  const sinLat = Math.sin(dLat / 2)
  const sinLng = Math.sin(dLng / 2)
  const a = sinLat * sinLat
    + Math.cos(lat1 * rad) * Math.cos(lat2 * rad) * sinLng * sinLng
  return 6371000 * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
}
