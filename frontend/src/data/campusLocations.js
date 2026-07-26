const CAMPUS_NAME = '上海科技大学浦东校区'
const CAMPUS_CODE = 'pudong-campus'
const CAMPUS_COORD_OFFSET = {
  lng: -0.0067335444444,
  lat: -0.00020588888889,
}

export function shiftCampusPoint(point = []) {
  if (!Array.isArray(point) || point.length !== 2) return null
  const [lng, lat] = point
  if (!Number.isFinite(lng) || !Number.isFinite(lat)) return null
  return [
    Number((lng + CAMPUS_COORD_OFFSET.lng).toFixed(9)),
    Number((lat + CAMPUS_COORD_OFFSET.lat).toFixed(9)),
  ]
}

function shiftCampusPolygon(points = []) {
  if (!Array.isArray(points)) return []
  return points
    .map((point) => shiftCampusPoint(point))
    .filter((point) => Array.isArray(point) && point.length === 2)
}

export const campusMapViewBox = { width: 1000, height: 680 }
const rawCampusBoundary = [
  [121.60238460000001, 31.1833255],
  [121.6045446, 31.1841055],
  [121.6066646, 31.1845695],
  [121.6062156, 31.1864845],
  [121.60724660000001, 31.1866355],
  [121.6116666, 31.1868825],
  [121.6139256, 31.1819625],
  [121.61225060000001, 31.1802555],
  [121.6059446, 31.1793985],
  [121.6048396, 31.1799315],
  [121.60411160000001, 31.1808975],
]

export const campusBoundary = rawCampusBoundary.map((point) => shiftCampusPoint(point) || point)

const rawCampusLocationGroups = [
  {
    id: 'academic',
    label: '教学科研区',
    summary: '学院楼、图书馆、行政与研究中心',
    items: [
      { id: 'library', label: '图书馆', aliases: ['图书信息中心', 'library'], coords: [121.6099654235294, 31.181386617647057], note: '图书信息中心' },
      { id: 'info-1', label: '信息学院1号楼', aliases: ['信息科学与技术学院1号楼'], coords: [121.6079005444444, 31.18381488888889], note: '信息科学与技术学院' },
      { id: 'info-2', label: '信息学院2号楼', aliases: ['信息科学与技术学院2号楼'], coords: [121.6078007, 31.184331300000004], note: '信息科学与技术学院' },
      { id: 'info-3', label: '信息学院3号楼', aliases: ['信息科学与技术学院3号楼'], coords: [121.6089057111111, 31.184427499999995], note: '信息科学与技术学院' },
      { id: 'materials-1', label: '物质学院1号楼', aliases: ['物质科学与技术学院1号楼'], coords: [121.60624213846151, 31.184139346153852], note: '物质科学与技术学院' },
      { id: 'materials-2', label: '物质学院2号楼', aliases: ['物质科学与技术学院2号楼'], coords: [121.60519459999999, 31.183832833333334], note: '物质科学与技术学院' },
      { id: 'materials-3', label: '物质学院3号楼', aliases: ['物质科学与技术学院3号楼'], coords: [121.60443597499999, 31.183593000000002], note: '物质科学与技术学院' },
      { id: 'materials-4', label: '物质学院4号楼', aliases: ['物质科学与技术学院4号楼'], coords: [121.6066742, 31.1835127], note: '物质科学与技术学院' },
      { id: 'materials-5', label: '物质学院5号楼', aliases: ['物质科学与技术学院5号楼'], coords: [121.60612017142857, 31.183233214285714], note: '物质科学与技术学院' },
      { id: 'materials-6', label: '物质学院6号楼', aliases: ['物质科学与技术学院6号楼'], coords: [121.60556643333334, 31.183339999999998], note: '物质科学与技术学院' },
      { id: 'materials-7', label: '物质学院7号楼', aliases: ['物质科学与技术学院7号楼'], coords: [121.60484998461541, 31.18309826923077], note: '物质科学与技术学院' },
      { id: 'materials-8', label: '物质学院8号楼', aliases: ['物质科学与技术学院8号楼'], coords: [121.6055326, 31.182890388888886], note: '物质科学与技术学院' },
      { id: 'life-science', label: '生命学院', aliases: ['生命科学与技术学院'], coords: [121.60760493333333, 31.18551975], note: '生命科学与技术学院' },
      { id: 'art', label: '创意与艺术学院', aliases: ['创意与艺术学院楼'], coords: [121.60638805454545, 31.182479545454548], note: '创意与艺术学院' },
      { id: 'management', label: '创业与管理学院', aliases: ['创业与管理学院楼'], coords: [121.60801253333332, 31.182842833333332], note: '创业与管理学院' },
      { id: 'ihuman', label: '人字楼', aliases: ['iHuman研究所', '免疫化学研究所'], coords: [121.6081026, 31.186140566666666], note: 'iHuman研究所 / 免疫化学研究所' },
      { id: 'administration', label: '行政中心', aliases: ['校长办公室', '公共服务处'], coords: [121.60666990769231, 31.181405192307693], note: '校长办公室 / 行政办公室' },
      { id: 'teaching-center', label: '教学中心', aliases: ['教学事务处'], coords: [121.60850190000001, 31.1817037], note: '教学事务处' },
      { id: 'report-hall', label: '报告厅', aliases: ['教学中心报告厅'], coords: [121.60902585000001, 31.18206575], note: '公共服务处' },
      { id: 'h2', label: 'H2楼·学生科创中心', aliases: ['H2楼', '学生科创中心'], coords: [121.60931276666666, 31.18270466666667], note: '通识教育中心 / 学生事务处' },
      { id: 'math-research', label: '数学科学研究所', aliases: ['数学科学研究所楼'], coords: [121.60663172500001, 31.181914749999997], note: '数学科学研究所' },
      { id: 'humanities', label: '人文科学研究院', aliases: ['人文科学研究院楼'], coords: [121.606826, 31.1827651], note: '人文科学研究院' },
      { id: 'bioengineering', label: '生医工学院', aliases: ['生物医学工程学院'], coords: [121.60873178181822, 31.183995681818185], note: '信息科学与技术学院' },
    ],
  },
  {
    id: 'service',
    label: '生活服务区',
    summary: '餐饮、快递、银行与日常服务',
    items: [
      { id: 'service-center', label: '校园服务中心', aliases: ['公共服务中心'], coords: [121.6097816, 31.1838345], note: '日常服务' },
      { id: 'copy-room', label: '文印室', aliases: ['自助打印'], coords: [121.6102396, 31.1818345], note: '打印与复印' },
      { id: 'clinic', label: '医务室', aliases: ['校医务室'], coords: [121.61007760000001, 31.1846115], note: '医疗服务' },
      { id: 'delivery', label: '菜鸟驿站', aliases: ['快递驿站'], coords: [121.6120226, 31.1825305], note: '快递收发' },
      { id: 'bank-atm', label: '上海银行ATM', aliases: ['ATM'], coords: [121.60967260000001, 31.1814715], note: '自助取款' },
      { id: 'bank', label: '上海银行', aliases: ['上海银行网点'], coords: [121.6120226, 31.1845155], note: '银行服务' },
      { id: 'familymart', label: '全家便利店', aliases: ['全家'], coords: [121.6106346, 31.1832295], note: '便利店' },
      { id: 'kfc', label: 'KFC', aliases: ['肯德基'], coords: [121.61032060000001, 31.1835845], note: '餐饮' },
      { id: 'nice-coffee', label: '耐思咖啡', aliases: ['咖啡厅'], coords: [121.61094460000001, 31.1846425], note: '咖啡与简餐' },
      { id: 'shangke-canteen', label: '尚科餐厅', aliases: ['尚科餐厅1楼', '尚科餐厅二楼自选区'], coords: [121.61032060000001, 31.1836195], note: '餐饮' },
      { id: 'silk-road-canteen', label: '丝路餐厅', aliases: ['丝路'], coords: [121.61047760000001, 31.1840285], note: '餐饮' },
      { id: 'western-canteen', label: '西餐厅', aliases: ['西餐'], coords: [121.6105896, 31.1834145], note: '餐饮' },
      { id: 'magnolia-canteen', label: '白玉兰一楼学生食堂', aliases: ['白玉兰餐厅', '白玉兰食堂'], coords: [121.6099006, 31.1822845], note: '学生餐饮' },
      { id: 'faculty-canteen', label: '教工餐厅与点餐区', aliases: ['教工餐厅'], coords: [121.60976360000001, 31.1821095], note: '教工餐饮' },
      { id: 'barber', label: '校园理发中心', aliases: ['理发店'], coords: [121.61065760000001, 31.1839745], note: '理发服务' },
      { id: 'souvenir', label: '纪念品专卖', aliases: ['纪念品店'], coords: [121.6098716, 31.1827335], note: '纪念品' },
      { id: 'print', label: '自助打印', aliases: ['打印机'], coords: [121.6084476, 31.1818465], note: '自助打印' },
      { id: 'shuttle', label: '学校班车', aliases: ['班车'], coords: [121.61207660000001, 31.1820825], note: '校内交通' },
    ],
  },
  {
    id: 'residential',
    label: '住宿生活区',
    summary: '学生公寓、教授公寓与日常公共空间',
    items: [
      { id: 'student-apartment-1', label: '学生公寓1号楼', aliases: ['学生公寓1号楼', '宿舍1号'], coords: [121.6111199, 31.184484], note: '学生住宿' },
      { id: 'student-apartment-2', label: '学生公寓2号楼', aliases: ['学生公寓2号楼', '宿舍2号'], coords: [121.6109071, 31.1840912], note: '学生住宿' },
      { id: 'student-apartment-3', label: '学生公寓3号楼', aliases: ['学生公寓3号楼', '宿舍3号'], coords: [121.6107873, 31.1835997], note: '学生住宿' },
      { id: 'student-apartment-4', label: '学生公寓4号楼', aliases: ['学生公寓4号楼', '宿舍4号'], coords: [121.610577, 31.1832106], note: '学生住宿' },
      { id: 'student-apartment-5', label: '学生公寓5号楼', aliases: ['学生公寓5号楼', '宿舍5号'], coords: [121.6103305, 31.182609499999998], note: '学生住宿' },
      { id: 'student-apartment-6', label: '学生公寓6号楼', aliases: ['学生公寓6号楼', '宿舍6号'], coords: [121.6101694, 31.182177], note: '学生住宿' },
      { id: 'student-apartment-7', label: '学生公寓7号楼', aliases: ['学生公寓7号楼', '宿舍7号'], coords: [121.611243, 31.1821615], note: '学生住宿' },
      { id: 'student-apartment-8', label: '学生公寓8号楼', aliases: ['学生公寓8号楼', '宿舍8号', '学生公寓', '宿舍', '寝室'], coords: [121.6115832, 31.183304], note: '学生住宿' },
      { id: 'student-apartment-9', label: '学生公寓9号楼', aliases: ['学生公寓9号楼', '宿舍9号'], coords: [121.61171130000001, 31.1837693], note: '学生住宿' },
      { id: 'student-apartment-10', label: '学生公寓10号楼', aliases: ['学生公寓10号楼', '宿舍10号'], coords: [121.6118716, 31.1841044], note: '学生住宿' },
      { id: 'faculty-apartment-1', label: '教授公寓1号楼', aliases: ['教授公寓1号楼', '教工公寓1号'], coords: [121.6110812, 31.1815526], note: '教工住宿' },
      { id: 'faculty-apartment-2', label: '教授公寓2号楼', aliases: ['教授公寓2号楼', '教工公寓2号'], coords: [121.6120532, 31.1814564], note: '教工住宿' },
      { id: 'faculty-apartment-3', label: '教授公寓3号楼', aliases: ['教授公寓3号楼', '教工公寓3号'], coords: [121.61273700000001, 31.1814464], note: '教工住宿' },
      { id: 'faculty-apartment-4', label: '教授公寓4号楼', aliases: ['教授公寓4号楼', '教工公寓4号'], coords: [121.61073970000001, 31.1809971], note: '教工住宿' },
      { id: 'faculty-apartment-5', label: '教授公寓5号楼', aliases: ['教授公寓5号楼', '教工公寓5号'], coords: [121.6116331, 31.1809509], note: '教工住宿' },
      { id: 'faculty-apartment-6', label: '教授公寓6号楼', aliases: ['教授公寓6号楼', '教工公寓6号'], coords: [121.6126189, 31.1810378], note: '教工住宿' },
    ],
  },
  {
    id: 'sports',
    label: '运动休闲区',
    summary: '体育馆、运动场与户外场地',
    items: [
      { id: 'gym', label: '体育馆', aliases: ['体育馆'], coords: [121.6114366, 31.182571499999998], note: '室内运动' },
      { id: 'track', label: '运动场', aliases: ['操场'], coords: [121.6127776, 31.1822215], note: '户外运动' },
      { id: 'swimming', label: '游泳馆', aliases: ['泳池'], coords: [121.6104146, 31.1858345], note: '游泳' },
      { id: 'basketball', label: '篮球场', aliases: ['篮球'], coords: [121.6126536, 31.1836285], note: '球类运动' },
      { id: 'tennis', label: '网球场', aliases: ['网球'], coords: [121.60938660000001, 31.1854975], note: '球类运动' },
      { id: 'volleyball', label: '排球场', aliases: ['排球'], coords: [121.6124386, 31.1842005], note: '球类运动' },
      { id: 'fitness', label: '健身场', aliases: ['健身区'], coords: [121.61293760000001, 31.1833885], note: '健身' },
    ],
  },
  {
    id: 'transport',
    label: '交通出入口',
    summary: '地铁、公交、车库与校车',
    items: [
      { id: 'metro-13', label: '地铁13号线中科路站', aliases: ['中科路站', '地铁站'], coords: [121.6156296, 31.1848545], note: '地铁 13 号线' },
      { id: 'bus-25', label: '(浦东25路)金科路中科路', aliases: ['金科路中科路'], coords: [121.6153606, 31.1843605], note: '公交站点' },
      { id: 'bus-58-1', label: '(浦东58路)环科路金科路', aliases: ['环科路金科路'], coords: [121.6130966, 31.1810475], note: '公交站点' },
      { id: 'bus-58-2', label: '(浦东58路)海科路金科路', aliases: ['海科路金科路'], coords: [121.6135726, 31.1867395], note: '公交站点' },
      { id: 'bus-58-3', label: '(浦东58路)海科路科苑路', aliases: ['海科路科苑路'], coords: [121.6097366, 31.1867855], note: '公交站点' },
      { id: 'bus-nanchuan', label: '(南川线)华夏中路殷家浜路', aliases: ['华夏中路殷家浜路'], coords: [121.6084386, 31.1781855], note: '公交站点' },
      { id: 'garage', label: '车库出入口', aliases: ['车库'], coords: [121.6120046, 31.1843375], note: '车行出入口' },
    ],
  },
]

export const campusLocationGroups = rawCampusLocationGroups.map((group) => ({
  ...group,
  items: group.items.map((item) => ({
    ...item,
    coords: shiftCampusPoint(item.coords) || item.coords,
  })),
}))

export const campusLocationGroupOptions = [
  { label: '全部', value: 'all' },
  ...campusLocationGroups.map((group) => ({ label: group.label, value: group.id })),
]

export const campusGroupThemes = {
  academic: { fill: 'rgba(37, 99, 235, 0.12)', stroke: '#2563eb', dot: '#2563eb' },
  service: { fill: 'rgba(20, 184, 166, 0.12)', stroke: '#14b8a6', dot: '#0f766e' },
  residential: { fill: 'rgba(132, 204, 22, 0.13)', stroke: '#84cc16', dot: '#65a30d' },
  sports: { fill: 'rgba(249, 115, 22, 0.12)', stroke: '#f97316', dot: '#ea580c' },
  transport: { fill: 'rgba(59, 130, 246, 0.12)', stroke: '#3b82f6', dot: '#1d4ed8' },
}

export function getCampusGroupTheme(groupId) {
  return campusGroupThemes[groupId] || { fill: 'rgba(100, 116, 139, 0.10)', stroke: '#64748b', dot: '#475569' }
}

const campusLocationSectionMap = {
  'info-1': '信息科学与技术学院',
  'info-2': '信息科学与技术学院',
  'info-3': '信息科学与技术学院',
  'bioengineering': '信息科学与技术学院',
  'materials-1': '物质科学与技术学院',
  'materials-2': '物质科学与技术学院',
  'materials-3': '物质科学与技术学院',
  'materials-4': '物质科学与技术学院',
  'materials-5': '物质科学与技术学院',
  'materials-6': '物质科学与技术学院',
  'materials-7': '物质科学与技术学院',
  'materials-8': '物质科学与技术学院',
  'life-science': '生命科学与技术学院',
  'art': '创意与艺术学院',
  'management': '创业与管理学院',
  'ihuman': 'iHuman研究所',
  administration: '行政与教学',
  'teaching-center': '行政与教学',
  'report-hall': '行政与教学',
  h2: '学生科创中心',
  'math-research': '行政与教学',
  humanities: '行政与教学',
  library: '图书与学术服务',
  'service-center': '生活服务',
  'copy-room': '生活服务',
  clinic: '生活服务',
  delivery: '生活服务',
  'bank-atm': '生活服务',
  bank: '生活服务',
  familymart: '生活服务',
  barber: '生活服务',
  souvenir: '生活服务',
  print: '生活服务',
  shuttle: '生活服务',
  'shangke-canteen': '餐饮',
  'silk-road-canteen': '餐饮',
  'western-canteen': '餐饮',
  'faculty-canteen': '餐饮',
  'magnolia-canteen': '餐饮',
  kfc: '餐饮',
  'nice-coffee': '餐饮',
  gym: '运动场馆',
  basketball: '运动场馆',
  swimming: '运动场馆',
  tennis: '运动场馆',
  volleyball: '运动场馆',
  fitness: '运动场馆',
  track: '运动场馆',
  residential: '住宿',
  'student-apartment-1': '学生公寓',
  'student-apartment-2': '学生公寓',
  'student-apartment-3': '学生公寓',
  'student-apartment-4': '学生公寓',
  'student-apartment-5': '学生公寓',
  'student-apartment-6': '学生公寓',
  'student-apartment-7': '学生公寓',
  'student-apartment-8': '学生公寓',
  'student-apartment-9': '学生公寓',
  'student-apartment-10': '学生公寓',
  'faculty-apartment-1': '教授公寓',
  'faculty-apartment-2': '教授公寓',
  'faculty-apartment-3': '教授公寓',
  'faculty-apartment-4': '教授公寓',
  'faculty-apartment-5': '教授公寓',
  'faculty-apartment-6': '教授公寓',
  'metro-13': '公共交通',
  'bus-25': '公共交通',
  'bus-58-1': '公共交通',
  'bus-58-2': '公共交通',
  'bus-58-3': '公共交通',
  'bus-nanchuan': '公共交通',
  garage: '车行出入口',
}

const campusLocationShapeOverrides = {
  library: [[121.6096016, 31.1820325], [121.60949860000001, 31.1818385], [121.60945860000001, 31.1818115], [121.6094496, 31.1813635], [121.6094806, 31.1813485], [121.6094896, 31.1812285], [121.6097676, 31.1809085], [121.6097676, 31.1808425], [121.61005560000001, 31.180722499999998], [121.6101636, 31.1809395], [121.61023060000001, 31.1809235], [121.6104236, 31.1812715], [121.61041060000001, 31.1814995], [121.6103746, 31.1815265], [121.6104596, 31.1816765], [121.6104466, 31.1818235], [121.6103336, 31.1818155]],
  'info-1': [[121.6075356, 31.1840785], [121.6075896, 31.1840905], [121.6075716, 31.1842255], [121.6072486, 31.1841675], [121.6072436, 31.1840245], [121.6073476, 31.1837195], [121.6075086, 31.1832025], [121.6082276, 31.1833025], [121.60900860000001, 31.1832335], [121.6090356, 31.1836305], [121.6085236, 31.1837115], [121.6082636, 31.1836815], [121.6082676, 31.1839705], [121.60789960000001, 31.1839245], [121.6078366, 31.1839935], [121.60776460000001, 31.1839785], [121.6077246, 31.1838705], [121.60761260000001, 31.1838625]],
  'info-2': [[121.6072256, 31.1844845], [121.6072166, 31.1842445], [121.6072396, 31.1841755], [121.60756260000001, 31.1842375], [121.60758560000001, 31.1841485], [121.6082136, 31.1842445], [121.6082006, 31.1843335], [121.60827660000001, 31.1843525], [121.6082586, 31.1844575], [121.6082276, 31.1846345]],
  'info-3': [[121.60820960000001, 31.1846545], [121.6082816, 31.1842985], [121.6084836, 31.1842715], [121.6085236, 31.1842215], [121.6092606, 31.1843105], [121.60927860000001, 31.1843565], [121.6093956, 31.1843835], [121.6093816, 31.1845695], [121.6093366, 31.1847815]],
  'materials-1': [[121.6066706, 31.1843375], [121.6064056, 31.1842595], [121.6063786, 31.1843255], [121.6062576, 31.1843025], [121.6062666, 31.1842215], [121.6059886, 31.184147499999998], [121.60595260000001, 31.1842295], [121.6057996, 31.1841905], [121.6057906, 31.1839705], [121.60586260000001, 31.1837815], [121.60630760000001, 31.1839005], [121.6067336, 31.1839815], [121.6067336, 31.1841635]],
  'materials-2': [[121.6056626, 31.1841865], [121.60518660000001, 31.1840865], [121.6047416, 31.1839555], [121.6047466, 31.1838275], [121.6048006, 31.1836345], [121.60484960000001, 31.1835305], [121.60527660000001, 31.1836305], [121.60574360000001, 31.1837235], [121.60574360000001, 31.1839205]],
  'materials-3': [[121.60396060000001, 31.1837425], [121.6039966, 31.1835455], [121.60409560000001, 31.1833065], [121.60467460000001, 31.1834645], [121.6046566, 31.1835225], [121.6047326, 31.1835455], [121.6047416, 31.1836655], [121.60462960000001, 31.1839515]],
  'materials-4': [[121.6064396, 31.1838975], [121.6065476, 31.1834765], [121.6066776, 31.1830825], [121.60694260000001, 31.1831285], [121.60676360000001, 31.1839785]],
  'materials-5': [[121.6058916, 31.1836385], [121.60598660000001, 31.1834025], [121.6058646, 31.1833565], [121.60582860000001, 31.1832605], [121.6058916, 31.1831635], [121.60580660000001, 31.1831135], [121.6059056, 31.1829855], [121.60596360000001, 31.1828005], [121.6063276, 31.1829355], [121.6066236, 31.1830205], [121.6066146, 31.1832095], [121.60656560000001, 31.1833835], [121.6063006, 31.183321499999998], [121.6061116, 31.1836735]],
  'materials-6': [[121.6058786, 31.1836655], [121.60489460000001, 31.1834415], [121.6051056, 31.1830245], [121.60576660000001, 31.1832065], [121.6057756, 31.1833065], [121.6059776, 31.1833955]],
  'materials-7': [[121.6051346, 31.1831905], [121.6050446, 31.1831825], [121.6050446, 31.1831825], [121.6049766, 31.1833605], [121.6048916, 31.1834725], [121.6047346, 31.1833955], [121.6047346, 31.1832215], [121.6043126, 31.1829855], [121.6043126, 31.1828155], [121.6044826, 31.1825645], [121.6050396, 31.1828505], [121.60517060000001, 31.1829545], [121.60517060000001, 31.1831015]],
  'materials-8': [[121.6049936, 31.1827885], [121.60536660000001, 31.1830055], [121.6057706, 31.1832295], [121.6058376, 31.1831405], [121.6057976, 31.1831215], [121.6059236, 31.1829665], [121.6059366, 31.1827855], [121.6051736, 31.1823645], [121.6049936, 31.1826115]],
  'life-science': [[121.6069736, 31.1853155], [121.60676360000001, 31.1861755], [121.60678560000001, 31.1863535], [121.60709560000001, 31.1864035], [121.6073386, 31.1854145], [121.6087256, 31.1856695], [121.6087976, 31.1854545], [121.60876660000001, 31.1852685], [121.6080436, 31.1851365], [121.60767460000001, 31.1850605], [121.60725260000001, 31.1849835], [121.6070416, 31.1850015]],
  art: [[121.6059006, 31.1827585], [121.6059056, 31.1825615], [121.6060716, 31.1822755], [121.6060716, 31.1822015], [121.6061656, 31.1820355], [121.6062196, 31.1820625], [121.6062246, 31.1820085], [121.6062426, 31.1819775], [121.60620660000001, 31.1819505], [121.6064336, 31.1820605], [121.6066986, 31.1821795], [121.6068106, 31.1822495], [121.6067926, 31.1823615], [121.6067706, 31.1825235], [121.60673460000001, 31.1827665], [121.6066986, 31.1828905], [121.6066326, 31.1830395], [121.6066416, 31.1829975], [121.6064176, 31.1829165], [121.6063996, 31.1829545], [121.6062646, 31.1828705], [121.60623360000001, 31.1829085]],
  management: [[121.6075606, 31.1832145], [121.60750660000001, 31.1831405], [121.6075026, 31.1830555], [121.6077176, 31.1824265], [121.6077626, 31.1822025], [121.6078706, 31.1821215], [121.6080326, 31.1822445], [121.6080366, 31.1826075], [121.60797360000001, 31.1827545], [121.6082526, 31.1828705], [121.6088366, 31.1829395], [121.6088586, 31.1832415], [121.60846360000001, 31.1832795], [121.6080776, 31.1832795], [121.6077356, 31.1832645]],
  ihuman: [[121.6074416, 31.1862215], [121.6074456, 31.1860595], [121.6074686, 31.1859595], [121.6074996, 31.1858315], [121.6075586, 31.1857815], [121.6081466, 31.1858515], [121.60849660000001, 31.1856235], [121.6086816, 31.1858165], [121.6087076, 31.1861375], [121.6085236, 31.1862685], [121.6085736, 31.1863495], [121.6085826, 31.1866465], [121.60833960000001, 31.1867745], [121.6080926, 31.1864225], [121.6079806, 31.1863645]],
  administration: [[121.60616160000001, 31.1813635], [121.6062916, 31.1814145], [121.6063226, 31.1813905], [121.6066146, 31.1815575], [121.6069926, 31.1817155], [121.60703260000001, 31.1816805], [121.6071536, 31.1817155], [121.6072486, 31.1815185], [121.60725260000001, 31.1813835], [121.6068036, 31.1812015], [121.6063996, 31.1809545], [121.6062156, 31.1811435], [121.6062196, 31.1812285]],
  'teaching-center': [[121.60796260000001, 31.1818965], [121.60796260000001, 31.1815915], [121.6080026, 31.1814915], [121.60843460000001, 31.1814955], [121.6089726, 31.1814295], [121.6090496, 31.1816145], [121.6090446, 31.1818315], [121.6087976, 31.1818655], [121.6085556, 31.181904499999998], [121.6082366, 31.1819165]],
  h2: [[121.6092826, 31.1831175], [121.6095746, 31.1830435], [121.6095926, 31.1828705], [121.6093146, 31.1823065], [121.60905360000001, 31.1823755], [121.6090586, 31.1825145]],
  'math-research': [[121.60618360000001, 31.1819355], [121.6062156, 31.1819125], [121.6061926, 31.1817235], [121.6063316, 31.1815685], [121.6069696, 31.1818155], [121.6071316, 31.1819125], [121.6071136, 31.1821595], [121.60691560000001, 31.1822905]],
  humanities: [[121.6066326, 31.1830285], [121.6066416, 31.1830365], [121.60678560000001, 31.1823135], [121.6070826, 31.1823295], [121.60698760000001, 31.1831175]],
  bioengineering: [[121.60854160000001, 31.1842025], [121.6083306, 31.1841985], [121.6083356, 31.1840325], [121.6083576, 31.1839325], [121.6083626, 31.1837465], [121.6084876, 31.1837235], [121.6093366, 31.1836885], [121.60934160000001, 31.1838975], [121.6093596, 31.1841525], [121.60891960000001, 31.1841835], [121.60867660000001, 31.1841945]],
  gym: [[121.6109716, 31.1828585], [121.61112460000001, 31.1829245], [121.6115156, 31.1828435], [121.6118386, 31.1826805], [121.6120046, 31.1826765], [121.61189660000001, 31.1823955], [121.61189660000001, 31.1821715], [121.6116816, 31.1821945], [121.6114976, 31.1822835], [121.6109986, 31.1825105], [121.61092260000001, 31.1825915], [121.6108906, 31.1827275]],
  basketball: [[121.6123036, 31.1840415], [121.6123106, 31.1832605], [121.6128216, 31.1832405], [121.61282560000001, 31.1833485], [121.61282560000001, 31.1835305], [121.61283560000001, 31.1837695], [121.6126696, 31.1837965], [121.6126406, 31.1840445]],
  swimming: [[121.6103246, 31.1862495], [121.6107386, 31.1861335], [121.6107296, 31.1859985], [121.6105186, 31.1854305], [121.6100826, 31.1855235], [121.61009560000001, 31.1856695]],
  tennis: [[121.6090226, 31.1856435], [121.6090636, 31.1853465], [121.6097326, 31.1853425], [121.6097276, 31.1856555]],
  volleyball: [[121.6123056, 31.184306499999998], [121.6123056, 31.1840945], [121.6125796, 31.1841015], [121.6125616, 31.1842985]],
  fitness: [[121.6128496, 31.1834995], [121.61285860000001, 31.1832715], [121.6130156, 31.1832715], [121.6130246, 31.1835115]],
  'magnolia-canteen': [[121.6098396, 31.1819895], [121.6096156, 31.1820435], [121.6096246, 31.1821245], [121.6097596, 31.1824375], [121.60985960000001, 31.1826775], [121.60997660000001, 31.1826535], [121.60996560000001, 31.1825995], [121.6101766, 31.1825225], [121.6101186, 31.1823685], [121.6098666, 31.1824295], [121.60980860000001, 31.1823215], [121.6098036, 31.1821555], [121.6100286, 31.1820975], [121.6100646, 31.1820625], [121.6100466, 31.1820015], [121.60985360000001, 31.1820665]],
  // 学生公寓 1-10 (GIS 多边形数据)
  'student-apartment-1': [[121.6107566, 31.1847545], [121.61067560000001, 31.1846155], [121.6106886, 31.1844535], [121.61101260000001, 31.1843685], [121.6110166, 31.1843225], [121.6113496, 31.1842835], [121.6113496, 31.1842215], [121.6114976, 31.1842105], [121.6115066, 31.1844845], [121.61151960000001, 31.1846925], [121.6110396, 31.1847505], [121.6110256, 31.1846505]],
  'student-apartment-2': [[121.6108366, 31.1842175], [121.6108636, 31.1843225], [121.6113356, 31.1842795], [121.6113576, 31.1840095], [121.6113266, 31.1837895], [121.6108506, 31.1838545], [121.6108506, 31.1839395], [121.6105276, 31.1840205], [121.61054560000001, 31.1841835], [121.6105766, 31.1842955]],
  'student-apartment-3': [[121.6103506, 31.1835875], [121.6103506, 31.1837225], [121.61039960000001, 31.1838585], [121.6106956, 31.1837805], [121.61071360000001, 31.1838775], [121.6111856, 31.1838155], [121.6111896, 31.1835295], [121.61115860000001, 31.1833485], [121.61102360000001, 31.1833525], [121.6110146, 31.1833945], [121.6106736, 31.1834335], [121.61069160000001, 31.1834955]],
  'student-apartment-4': [[121.61020160000001, 31.1831665], [121.61020160000001, 31.1832985], [121.61024660000001, 31.1834295], [121.61051660000001, 31.1833445], [121.6105476, 31.1834485], [121.6110196, 31.1833945], [121.6110196, 31.1830785], [121.61097960000001, 31.1829085], [121.6105206, 31.1829585], [121.61051660000001, 31.1830785]],
  'student-apartment-5': [[121.60996560000001, 31.1825845], [121.6099706, 31.1827315], [121.6100066, 31.1828585], [121.6102846, 31.1827775], [121.6103336, 31.1828935], [121.6107696, 31.1826765], [121.6107786, 31.1824145], [121.61067560000001, 31.1822215], [121.6102666, 31.1824295], [121.61025360000001, 31.1825075]],
  'student-apartment-6': [[121.6098296, 31.1821665], [121.60980260000001, 31.1823175], [121.6098566, 31.1824325], [121.6101076, 31.1823635], [121.6101756, 31.1824565], [121.6106066, 31.1822555], [121.6106106, 31.1819195], [121.6105206, 31.1817845], [121.6100986, 31.1819775], [121.6100856, 31.1820965]],
  'student-apartment-7': [[121.61087760000001, 31.1825725], [121.6114026, 31.1823215], [121.61141160000001, 31.1822675], [121.6115736, 31.1821595], [121.6116006, 31.1818085], [121.61147960000001, 31.1816965], [121.6108016, 31.1820245], [121.6107966, 31.1824415]],
  'student-apartment-8': [[121.6112476, 31.1835865], [121.6117646, 31.1835405], [121.6117736, 31.1834555], [121.6119176, 31.1834665], [121.6119086, 31.1829605], [121.6116166, 31.1829565], [121.6112166, 31.1830145], [121.61122060000001, 31.1834515]],
  'student-apartment-9': [[121.61141160000001, 31.1840095], [121.6114166, 31.1840015], [121.6113756, 31.1838585], [121.6113806, 31.1838505], [121.6113756, 31.1835995], [121.6117626, 31.1835345], [121.6117756, 31.1834605], [121.6120676, 31.1834455], [121.6120676, 31.1837425], [121.6120586, 31.1838855], [121.6119236, 31.1838775], [121.61191960000001, 31.1839665]],
  'student-apartment-10': [[121.61156960000001, 31.1844375], [121.6115426, 31.1842955], [121.6115336, 31.1841635], [121.6115336, 31.1840095], [121.6116856, 31.1839785], [121.6119326, 31.1839665], [121.6119286, 31.1838855], [121.6120456, 31.1838775], [121.61209960000001, 31.183874499999998], [121.61212160000001, 31.1838705], [121.61212660000001, 31.1840515], [121.61212660000001, 31.1843255], [121.6119826, 31.1843185], [121.6119736, 31.1844075]],
  // 教授公寓 1-6 (GIS 多边形数据)
  'faculty-apartment-1': [[121.6107246, 31.1817265], [121.61067560000001, 31.1815995], [121.61069760000001, 31.1813905], [121.6110666, 31.1812635], [121.61151960000001, 31.1812515], [121.6115156, 31.1815335], [121.6115066, 31.1816305], [121.6112906, 31.1816495], [121.6111106, 31.1816455], [121.6109046, 31.1817115], [121.6108816, 31.1816765]],
  'faculty-apartment-2': [[121.6116796, 31.1816615], [121.6116746, 31.1812675], [121.6120566, 31.1812475], [121.6122806, 31.1811865], [121.6123216, 31.1815145], [121.6122146, 31.1815585], [121.61211060000001, 31.1815775], [121.61208760000001, 31.1816375]],
  'faculty-apartment-3': [[121.61245860000001, 31.1813565], [121.61245860000001, 31.1813485], [121.6124626, 31.1812445], [121.6128766, 31.1812285], [121.6131096, 31.1812985], [121.6131096, 31.1815295], [121.6130606, 31.1816265], [121.6128676, 31.1815495], [121.6126696, 31.1815605], [121.6125706, 31.1816035], [121.6124626, 31.1815645]],
  'faculty-apartment-4': [[121.6104866, 31.1810545], [121.61047760000001, 31.1808275], [121.61054060000001, 31.1807305], [121.6109046, 31.1808465], [121.6111156, 31.1808695], [121.6111106, 31.1810825], [121.6110926, 31.1811905], [121.6108636, 31.1811665], [121.6105716, 31.1811015], [121.6104866, 31.1810515], [121.6104866, 31.1810475]],
  'faculty-apartment-5': [[121.61128860000001, 31.1811455], [121.61124360000001, 31.1810175], [121.61124360000001, 31.1808135], [121.61164860000001, 31.1806975], [121.6118596, 31.1806625], [121.61209260000001, 31.1806625], [121.6120886, 31.1810525], [121.6118816, 31.1810525], [121.6116756, 31.1811145], [121.61149060000001, 31.1811535], [121.6114506, 31.1810875]],
  'faculty-apartment-6': [[121.61221160000001, 31.1811785], [121.61221160000001, 31.1807765], [121.61263360000001, 31.1807695], [121.6128626, 31.1808735], [121.6128446, 31.1810825], [121.6128066, 31.1811845], [121.61273560000001, 31.1811765], [121.6126366, 31.1811225], [121.61262760000001, 31.1811765]],
}

export function createLocationEntry(group, item) {
  const sectionLabel = getCampusLocationSectionLabel(group, item)
  const sectionCode = getCampusLocationSectionCode(group.id, sectionLabel)
  const polygon = shiftCampusPolygon(campusLocationShapeOverrides[item.id] || null)
  const coords = item.coords
  const mapCoords = polygon.length ? getCampusPolygonCenter(polygon) : coords
  const pathLabels = [CAMPUS_NAME, group.label, sectionLabel, item.label]
  return {
    ...item,
    coords,
    groupId: group.id,
    groupLabel: group.label,
    groupSummary: group.summary,
    sectionLabel,
    sectionCode,
    campusName: CAMPUS_NAME,
    polygon,
    mapCoords,
    pathLabels,
    pathLabel: pathLabels.join(' · '),
    pathCodes: [CAMPUS_CODE, group.id, sectionCode, item.id],
    searchText: normalizeCampusText([CAMPUS_NAME, group.label, sectionLabel, item.label, item.note, ...(item.aliases || [])].join(' ')),
  }
}

export const campusLocationEntries = campusLocationGroups.flatMap((group) =>
  group.items.map((item) => createLocationEntry(group, item))
)

export const campusLocationTree = buildCampusLocationTree(campusLocationEntries)
export const campusLocationCategoryTree = campusLocationTree[0]?.children || []

function buildCampusLocationTree(entries) {
  return [
    {
      value: CAMPUS_CODE,
      label: CAMPUS_NAME,
      children: campusLocationGroups.map((group) => {
        const sectionMap = new Map()
        for (const entry of entries.filter((item) => item.groupId === group.id)) {
          if (!sectionMap.has(entry.sectionCode)) {
            sectionMap.set(entry.sectionCode, {
              value: entry.sectionCode,
              label: entry.sectionLabel,
              children: [],
            })
          }
          sectionMap.get(entry.sectionCode).children.push({
            value: entry.id,
            label: entry.label,
          })
        }
        return {
          value: group.id,
          label: group.label,
          children: Array.from(sectionMap.values()),
        }
      }),
    },
  ]
}

function getCampusLocationSectionLabel(group, item) {
  return campusLocationSectionMap[item.id] || group.label
}

function getCampusLocationSectionCode(groupId, sectionLabel) {
  return `${groupId}:${normalizeCampusText(sectionLabel || groupId)}`
}

function getCampusPolygonCenter(polygon = []) {
  const validPoints = polygon.filter((point) => Array.isArray(point) && point.length === 2)
  if (!validPoints.length) return null
  const lng = validPoints.reduce((sum, point) => sum + point[0], 0) / validPoints.length
  const lat = validPoints.reduce((sum, point) => sum + point[1], 0) / validPoints.length
  return [Number(lng.toFixed(9)), Number(lat.toFixed(9))]
}

export function findCampusLocationByPathCodes(pathCodes = []) {
  const key = pathCodes.join('>')
  return campusLocationEntries.find((entry) => entry.pathCodes.join('>') === key) || null
}

export function findCampusLocationByCategoryPath(pathCodes = []) {
  if (!Array.isArray(pathCodes) || pathCodes.length === 0) return null
  return findCampusLocationByPathCodes([CAMPUS_CODE, ...pathCodes])
}

export function findCampusLocationByLabel(label = '') {
  const normalized = normalizeCampusText(label)
  if (!normalized) return null
  return campusLocationEntries.find((entry) =>
    normalizeCampusText(entry.pathLabel) === normalized ||
    normalizeCampusText(entry.label) === normalized ||
    (entry.aliases || []).some((alias) => normalizeCampusText(alias) === normalized) ||
    entry.searchText.includes(normalized),
  ) || null
}

export function searchCampusLocations(query = '', groupId = 'all', limit = 24) {
  const normalized = normalizeCampusText(query)
  const source = groupId === 'all'
    ? campusLocationEntries
    : campusLocationEntries.filter((entry) => entry.groupId === groupId)

  if (!normalized) {
    return source.slice(0, limit)
  }

  return source
    .map((entry) => ({ entry, score: scoreCampusLocation(entry, normalized) }))
    .filter((item) => item.score > 0)
    .sort((a, b) => b.score - a.score || a.entry.pathLabel.length - b.entry.pathLabel.length)
    .slice(0, limit)
    .map((item) => item.entry)
}

export function findNearestCampusLocation(coords) {
  if (!coords || coords.length !== 2) return null
  let best = null
  for (const entry of campusLocationEntries) {
    const target = entry.mapCoords || entry.coords
    if (!target) continue
    const distanceMeters = getDistanceMeters(coords, target)
    if (!best || distanceMeters < best.distanceMeters) {
      best = { entry, distanceMeters }
    }
  }
  return best
}

export function formatCampusLocationPath(entry) {
  return entry?.pathLabel || ''
}

export function getCampusBounds(entries = campusLocationEntries, boundary = campusBoundary) {
  const coords = []
  for (const point of boundary) {
    if (Array.isArray(point) && point.length === 2) coords.push(point)
  }
  for (const entry of entries) {
    if (Array.isArray(entry.coords) && entry.coords.length === 2) coords.push(entry.coords)
    if (Array.isArray(entry.mapCoords) && entry.mapCoords.length === 2) coords.push(entry.mapCoords)
    if (Array.isArray(entry.polygon)) {
      for (const point of entry.polygon) {
        if (Array.isArray(point) && point.length === 2) coords.push(point)
      }
    }
  }
  if (coords.length === 0) {
    return {
      minLng: 0,
      maxLng: 1,
      minLat: 0,
      maxLat: 1,
    }
  }
  const lngs = coords.map((point) => point[0])
  const lats = coords.map((point) => point[1])
  return {
    minLng: Math.min(...lngs),
    maxLng: Math.max(...lngs),
    minLat: Math.min(...lats),
    maxLat: Math.max(...lats),
  }
}

export function expandCampusBounds(bounds, ratio = 0.08) {
  const lngSpan = Math.max(bounds.maxLng - bounds.minLng, 0.0001)
  const latSpan = Math.max(bounds.maxLat - bounds.minLat, 0.0001)
  return {
    minLng: bounds.minLng - lngSpan * ratio,
    maxLng: bounds.maxLng + lngSpan * ratio,
    minLat: bounds.minLat - latSpan * ratio,
    maxLat: bounds.maxLat + latSpan * ratio,
  }
}

export function projectCampusPoint(coords, bounds = getCampusBounds(), viewBox = campusMapViewBox) {
  if (!Array.isArray(coords) || coords.length !== 2) {
    return { x: viewBox.width / 2, y: viewBox.height / 2 }
  }
  const [lng, lat] = coords
  const safeBounds = expandCampusBounds(bounds)
  const lngSpan = Math.max(safeBounds.maxLng - safeBounds.minLng, 0.0001)
  const latSpan = Math.max(safeBounds.maxLat - safeBounds.minLat, 0.0001)
  const x = ((lng - safeBounds.minLng) / lngSpan) * viewBox.width
  const y = ((safeBounds.maxLat - lat) / latSpan) * viewBox.height
  return {
    x: Number(x.toFixed(2)),
    y: Number(y.toFixed(2)),
  }
}

export function projectCampusBoundary(boundary = campusBoundary, bounds = getCampusBounds(), viewBox = campusMapViewBox) {
  return boundary
    .map((point) => projectCampusPoint(point, bounds, viewBox))
    .map((point) => `${point.x},${point.y}`)
    .join(' ')
}

export function projectCampusPolygon(polygon = [], bounds = getCampusBounds(), viewBox = campusMapViewBox) {
  return polygon
    .map((point) => projectCampusPoint(point, bounds, viewBox))
    .map((point) => `${point.x},${point.y}`)
    .join(' ')
}

export function getCampusGroupEntries(groupId) {
  return campusLocationEntries.filter((entry) => entry.groupId === groupId)
}

export function getCampusGroupBounds(groupId) {
  return getCampusBounds(getCampusGroupEntries(groupId))
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
  const aliases = (entry.aliases || []).map((alias) => normalizeCampusText(alias))
  if (label === normalizedQuery || pathLabel === normalizedQuery) return 300
  if (aliases.some((alias) => alias === normalizedQuery)) return 280
  if (label.startsWith(normalizedQuery)) return 250
  if (aliases.some((alias) => alias.startsWith(normalizedQuery))) return 230
  if (pathLabel.startsWith(normalizedQuery)) return 220
  if (pathLabel.includes(normalizedQuery)) return 180
  if (aliases.some((alias) => alias.includes(normalizedQuery))) return 160
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
