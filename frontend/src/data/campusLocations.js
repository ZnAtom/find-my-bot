const CAMPUS_NAME = '上海科技大学浦东校区'
const CAMPUS_CODE = 'pudong-campus'

export const campusMapViewBox = { width: 1000, height: 680 }
export const campusBoundary = [
  [121.595651, 31.18312],
  [121.597811, 31.1839],
  [121.599931, 31.184364],
  [121.599482, 31.186279],
  [121.600513, 31.18643],
  [121.604933, 31.186677],
  [121.607192, 31.181757],
  [121.605517, 31.18005],
  [121.599211, 31.179193],
  [121.598106, 31.179726],
  [121.597378, 31.180692],
]

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
      { id: 'magnolia-canteen', label: '白玉兰一楼学生食堂', aliases: ['白玉兰餐厅', '白玉兰食堂'], coords: [121.603167, 31.182079], note: '学生餐饮' },
      { id: 'faculty-canteen', label: '教工餐厅与点餐区', aliases: ['教工餐厅'], coords: [121.60303, 31.181904], note: '教工餐饮' },
      { id: 'barber', label: '校园理发中心', aliases: ['理发店'], coords: [121.603924, 31.183769], note: '理发服务' },
      { id: 'souvenir', label: '纪念品专卖', aliases: ['纪念品店'], coords: [121.603138, 31.182528], note: '纪念品' },
      { id: 'print', label: '自助打印', aliases: ['打印机'], coords: [121.601714, 31.181641], note: '自助打印' },
      { id: 'shuttle', label: '学校班车', aliases: ['班车'], coords: [121.605343, 31.181877], note: '校内交通' },
    ],
  },
  {
    id: 'residential',
    label: '住宿公共区',
    summary: '学生公寓与日常公共空间',
    items: [
      { id: 'student-apartment-8', label: '学生公寓8号楼', aliases: ['学生公寓', '宿舍', '寝室'], coords: [121.60485, 31.183098], note: '学生住宿' },
    ],
  },
  {
    id: 'sports',
    label: '运动休闲区',
    summary: '体育馆、运动场与户外场地',
    items: [
      { id: 'gym', label: '体育馆', aliases: ['体育馆'], coords: [121.604703, 31.182366], note: '室内运动' },
      { id: 'track', label: '运动场', aliases: ['操场'], coords: [121.606044, 31.182016], note: '户外运动' },
      { id: 'swimming', label: '游泳馆', aliases: ['泳池'], coords: [121.603681, 31.185629], note: '游泳' },
      { id: 'basketball', label: '篮球场', aliases: ['篮球'], coords: [121.60592, 31.183423], note: '球类运动' },
      { id: 'tennis', label: '网球场', aliases: ['网球'], coords: [121.602653, 31.185292], note: '球类运动' },
      { id: 'volleyball', label: '排球场', aliases: ['排球'], coords: [121.605705, 31.183995], note: '球类运动' },
      { id: 'fitness', label: '健身场', aliases: ['健身区'], coords: [121.606204, 31.183183], note: '健身' },
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
  'student-apartment-8': '住宿',
  'metro-13': '公共交通',
  'bus-25': '公共交通',
  'bus-58-1': '公共交通',
  'bus-58-2': '公共交通',
  'bus-58-3': '公共交通',
  'bus-nanchuan': '公共交通',
  garage: '车行出入口',
}

const campusLocationShapeOverrides = {
  library: [[121.602868, 31.181827], [121.602765, 31.181633], [121.602725, 31.181606], [121.602716, 31.181158], [121.602747, 31.181143], [121.602756, 31.181023], [121.603034, 31.180703], [121.603034, 31.180637], [121.603322, 31.180517], [121.60343, 31.180734], [121.603497, 31.180718], [121.60369, 31.181066], [121.603677, 31.181294], [121.603641, 31.181321], [121.603726, 31.181471], [121.603713, 31.181618], [121.6036, 31.18161]],
  'info-1': [[121.600802, 31.183873], [121.600856, 31.183885], [121.600838, 31.18402], [121.600515, 31.183962], [121.60051, 31.183819], [121.600614, 31.183514], [121.600775, 31.182997], [121.601494, 31.183097], [121.602275, 31.183028], [121.602302, 31.183425], [121.60179, 31.183506], [121.60153, 31.183476], [121.601534, 31.183765], [121.601166, 31.183719], [121.601103, 31.183788], [121.601031, 31.183773], [121.600991, 31.183665], [121.600879, 31.183657]],
  'info-2': [[121.600492, 31.184279], [121.600483, 31.184039], [121.600506, 31.18397], [121.600829, 31.184032], [121.600852, 31.183943], [121.60148, 31.184039], [121.601467, 31.184128], [121.601543, 31.184147], [121.601525, 31.184252], [121.601494, 31.184429]],
  'info-3': [[121.601476, 31.184449], [121.601548, 31.184093], [121.60175, 31.184066], [121.60179, 31.184016], [121.602527, 31.184105], [121.602545, 31.184151], [121.602662, 31.184178], [121.602648, 31.184364], [121.602603, 31.184576]],
  'materials-1': [[121.599937, 31.184132], [121.599672, 31.184054], [121.599645, 31.18412], [121.599524, 31.184097], [121.599533, 31.184016], [121.599255, 31.183942], [121.599219, 31.184024], [121.599066, 31.183985], [121.599057, 31.183765], [121.599129, 31.183576], [121.599574, 31.183695], [121.6, 31.183776], [121.6, 31.183958]],
  'materials-2': [[121.598929, 31.183981], [121.598453, 31.183881], [121.598008, 31.18375], [121.598013, 31.183622], [121.598067, 31.183429], [121.598116, 31.183325], [121.598543, 31.183425], [121.59901, 31.183518], [121.59901, 31.183715]],
  'materials-3': [[121.597227, 31.183537], [121.597263, 31.18334], [121.597362, 31.183101], [121.597941, 31.183259], [121.597923, 31.183317], [121.597999, 31.18334], [121.598008, 31.18346], [121.597896, 31.183746]],
  'materials-4': [[121.599706, 31.183692], [121.599814, 31.183271], [121.599944, 31.182877], [121.600209, 31.182923], [121.60003, 31.183773]],
  'materials-5': [[121.599158, 31.183433], [121.599253, 31.183197], [121.599131, 31.183151], [121.599095, 31.183055], [121.599158, 31.182958], [121.599073, 31.182908], [121.599172, 31.18278], [121.59923, 31.182595], [121.599594, 31.18273], [121.59989, 31.182815], [121.599881, 31.183004], [121.599832, 31.183178], [121.599567, 31.183116], [121.599378, 31.183468]],
  'materials-6': [[121.599145, 31.18346], [121.598161, 31.183236], [121.598372, 31.182819], [121.599033, 31.183001], [121.599042, 31.183101], [121.599244, 31.18319]],
  'materials-7': [[121.598401, 31.182985], [121.598311, 31.182977], [121.598311, 31.182977], [121.598243, 31.183155], [121.598158, 31.183267], [121.598001, 31.18319], [121.598001, 31.183016], [121.597579, 31.18278], [121.597579, 31.18261], [121.597749, 31.182359], [121.598306, 31.182645], [121.598437, 31.182749], [121.598437, 31.182896]],
  'materials-8': [[121.59826, 31.182583], [121.598633, 31.1828], [121.599037, 31.183024], [121.599104, 31.182935], [121.599064, 31.182916], [121.59919, 31.182761], [121.599203, 31.18258], [121.59844, 31.182159], [121.59826, 31.182406]],
  'life-science': [[121.60024, 31.18511], [121.60003, 31.18597], [121.600052, 31.186148], [121.600362, 31.186198], [121.600605, 31.185209], [121.601992, 31.185464], [121.602064, 31.185249], [121.602033, 31.185063], [121.60131, 31.184931], [121.600941, 31.184855], [121.600519, 31.184778], [121.600308, 31.184796]],
  art: [[121.599167, 31.182553], [121.599172, 31.182356], [121.599338, 31.18207], [121.599338, 31.181996], [121.599432, 31.18183], [121.599486, 31.181857], [121.599491, 31.181803], [121.599509, 31.181772], [121.599473, 31.181745], [121.5997, 31.181855], [121.599965, 31.181974], [121.600077, 31.182044], [121.600059, 31.182156], [121.600037, 31.182318], [121.600001, 31.182561], [121.599965, 31.182685], [121.599899, 31.182834], [121.599908, 31.182792], [121.599684, 31.182711], [121.599666, 31.182749], [121.599531, 31.182665], [121.5995, 31.182703]],
  management: [[121.600827, 31.183009], [121.600773, 31.182935], [121.600769, 31.18285], [121.600984, 31.182221], [121.601029, 31.181997], [121.601137, 31.181916], [121.601299, 31.182039], [121.601303, 31.182402], [121.60124, 31.182549], [121.601519, 31.182665], [121.602103, 31.182734], [121.602125, 31.183036], [121.60173, 31.183074], [121.601344, 31.183074], [121.601002, 31.183059]],
  ihuman: [[121.600708, 31.186016], [121.600712, 31.185854], [121.600735, 31.185754], [121.600766, 31.185626], [121.600825, 31.185576], [121.601413, 31.185646], [121.601763, 31.185418], [121.601948, 31.185611], [121.601974, 31.185932], [121.60179, 31.186063], [121.60184, 31.186144], [121.601849, 31.186441], [121.601606, 31.186569], [121.601359, 31.186217], [121.601247, 31.186159]],
  administration: [[121.599428, 31.181158], [121.599558, 31.181209], [121.599589, 31.181185], [121.599881, 31.181352], [121.600259, 31.18151], [121.600299, 31.181475], [121.60042, 31.18151], [121.600515, 31.181313], [121.600519, 31.181178], [121.60007, 31.180996], [121.599666, 31.180749], [121.599482, 31.180938], [121.599486, 31.181023]],
  'teaching-center': [[121.601229, 31.181691], [121.601229, 31.181386], [121.601269, 31.181286], [121.601701, 31.18129], [121.602239, 31.181224], [121.602316, 31.181409], [121.602311, 31.181626], [121.602064, 31.18166], [121.601822, 31.181699], [121.601503, 31.181711]],
  h2: [[121.602549, 31.182912], [121.602841, 31.182838], [121.602859, 31.182665], [121.602581, 31.182101], [121.60232, 31.18217], [121.602325, 31.182309]],
  'math-research': [[121.59945, 31.18173], [121.599482, 31.181707], [121.599459, 31.181518], [121.599598, 31.181363], [121.600236, 31.18161], [121.600398, 31.181707], [121.60038, 31.181954], [121.600182, 31.182085]],
  humanities: [[121.599899, 31.182823], [121.599908, 31.182831], [121.600052, 31.182108], [121.600349, 31.182124], [121.600254, 31.182912]],
  bioengineering: [[121.601808, 31.183997], [121.601597, 31.183993], [121.601602, 31.183827], [121.601624, 31.183727], [121.601629, 31.183541], [121.601754, 31.183518], [121.602603, 31.183483], [121.602608, 31.183692], [121.602626, 31.183947], [121.602186, 31.183978], [121.601943, 31.183989]],
  gym: [[121.604238, 31.182653], [121.604391, 31.182719], [121.604782, 31.182638], [121.605105, 31.182475], [121.605271, 31.182471], [121.605163, 31.18219], [121.605163, 31.181966], [121.604948, 31.181989], [121.604764, 31.182078], [121.604265, 31.182305], [121.604189, 31.182386], [121.604157, 31.182522]],
  basketball: [[121.60557, 31.183836], [121.605577, 31.183055], [121.606088, 31.183035], [121.606092, 31.183143], [121.606092, 31.183325], [121.606102, 31.183564], [121.605936, 31.183591], [121.605907, 31.183839]],
  swimming: [[121.603591, 31.186044], [121.604005, 31.185928], [121.603996, 31.185793], [121.603785, 31.185225], [121.603349, 31.185318], [121.603362, 31.185464]],
  tennis: [[121.602289, 31.185438], [121.60233, 31.185141], [121.602999, 31.185137], [121.602994, 31.18545]],
  volleyball: [[121.605572, 31.184101], [121.605572, 31.183889], [121.605846, 31.183896], [121.605828, 31.184093]],
  fitness: [[121.606116, 31.183294], [121.606125, 31.183066], [121.606282, 31.183066], [121.606291, 31.183306]],
  'magnolia-canteen': [[121.603106, 31.181784], [121.602882, 31.181838], [121.602891, 31.181919], [121.603026, 31.182232], [121.603126, 31.182472], [121.603243, 31.182448], [121.603232, 31.182394], [121.603443, 31.182317], [121.603385, 31.182163], [121.603133, 31.182224], [121.603075, 31.182116], [121.60307, 31.18195], [121.603295, 31.181892], [121.603331, 31.181857], [121.603313, 31.181796], [121.60312, 31.181861]],
}

export function createLocationEntry(group, item) {
  const sectionLabel = getCampusLocationSectionLabel(group, item)
  const sectionCode = getCampusLocationSectionCode(group.id, sectionLabel)
  const polygon = campusLocationShapeOverrides[item.id] || null
  const mapCoords = polygon ? getCampusPolygonCenter(polygon) : item.coords
  const pathLabels = [CAMPUS_NAME, group.label, sectionLabel, item.label]
  return {
    ...item,
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
