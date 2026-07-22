"""Insert idempotent local records for hybrid-search testing."""

import argparse

from db import get_db_connection, release_db_connection
from embedding import VECTOR_DIM, encode_text


SEED_MARKER = "[SEARCH_SEED_V1]"
SEED_OWNER = f"搜索测试数据 {SEED_MARKER}"

# item_name, item_type, description, location, storage_location, lost_time, direction
SEED_ITEMS = [
    ("蓝色卡套校园一卡通", "证件卡片", "蓝色透明卡套，里面是校园一卡通，挂有白色短挂绳。", "图书馆二楼自习区", None, "2026-07-18 19:20:00", "lost"),
    ("上海科技大学校园一卡通", "证件卡片", "捡到一张学生校园卡，卡面有照片，放在红色卡套中。", "学生餐厅一楼", "学生餐厅失物招领处", "2026-07-18 12:35:00", "found"),
    ("黑色 iPhone 15 手机", "电子产品", "黑色苹果手机，透明手机壳，锁屏壁纸是校园风景。", "体育馆篮球场", None, "2026-07-19 20:10:00", "lost"),
    ("银色华为手机", "电子产品", "银色华为手机，后置三摄，深蓝色硅胶保护壳。", "第二教学楼 205", "二教值班室", "2026-07-19 16:40:00", "found"),
    ("白色膳魔师保温杯", "其他", "白色不锈钢保温水杯，杯盖有浅蓝色贴纸，容量约 500ml。", "图书馆三楼靠窗座位", None, "2026-07-20 14:15:00", "lost"),
    ("蓝色运动水杯", "其他", "蓝色塑料运动水壶，带黑色提环，杯身印有英文标志。", "操场东侧看台", "体育馆前台", "2026-07-20 18:30:00", "found"),
    ("宿舍钥匙和门禁卡", "钱包钥匙", "两把银色钥匙和一张蓝色门禁卡，挂有黄色笑脸挂件。", "学生宿舍 3 号楼", None, "2026-07-17 22:00:00", "lost"),
    ("黑色汽车钥匙", "钱包钥匙", "黑色遥控汽车钥匙，金属钥匙环上有一个红色小挂件。", "学校南门停车场", "南门保安室", "2026-07-17 10:25:00", "found"),
    ("AirPods Pro 无线耳机", "电子产品", "白色苹果无线耳机和充电盒，保护套右侧有轻微划痕。", "第一教学楼 101", None, "2026-07-21 09:50:00", "lost"),
    ("黑色索尼蓝牙耳机", "电子产品", "黑色入耳式蓝牙耳机，只有充电盒，盒盖贴有字母贴纸。", "科创中心一楼大厅", "科创中心前台", "2026-07-21 15:05:00", "found"),
    ("藏青色折叠雨伞", "其他", "藏青色三折自动伞，木质伞柄，伞套可能遗失。", "学校公交站", None, "2026-07-16 08:30:00", "lost"),
    ("透明长柄雨伞", "其他", "透明塑料长柄伞，白色弯柄，伞面边缘有蓝色包边。", "图书馆一楼入口", "图书馆前台", "2026-07-16 17:45:00", "found"),
    ("灰色双肩书包", "其他", "灰色双肩背包，内有笔记本和文具，侧袋放着折叠伞。", "信息学院 1 号楼", None, "2026-07-18 21:10:00", "lost"),
    ("黑色联想电脑包", "其他", "黑色单肩电脑包，拉链处有绿色挂绳，包内没有电脑。", "学生餐厅二楼", "餐厅服务台", "2026-07-18 13:20:00", "found"),
    ("高等数学教材", "学习用品", "同济版高等数学上册，封面有透明书皮，书内有大量蓝色笔记。", "第一教学楼 302", None, "2026-07-20 11:30:00", "lost"),
    ("牛津高阶英语词典", "学习用品", "红色封面的英语词典，扉页写有姓名缩写，书角有磨损。", "图书馆四楼阅览区", "图书馆前台", "2026-07-20 16:10:00", "found"),
    ("银色 MacBook Air 笔记本电脑", "电子产品", "银色苹果笔记本电脑，13 英寸，外壳贴有学校徽标贴纸。", "物质学院实验室", None, "2026-07-21 19:40:00", "lost"),
    ("卡西欧科学计算器", "学习用品", "黑色卡西欧 fx-991CN X 计算器，背面贴有白色标签。", "第二教学楼 305", "二教值班室", "2026-07-21 12:00:00", "found"),
    ("棕色短款钱包", "钱包钥匙", "棕色皮质短钱包，内有若干会员卡，没有现金和身份证件。", "西餐厅靠窗座位", None, "2026-07-19 13:15:00", "lost"),
    ("黑色拉链卡包", "钱包钥匙", "黑色小卡包，带银色拉链，内有交通卡和几张收据。", "校医院候诊区", "校医院前台", "2026-07-19 10:05:00", "found"),
    ("蓝色户外冲锋衣", "衣物鞋帽", "深蓝色薄款冲锋衣，左胸有白色品牌标志，尺码 L。", "体育馆更衣室", None, "2026-07-17 20:30:00", "lost"),
    ("白色棒球帽", "衣物鞋帽", "白色鸭舌帽，帽檐内侧有黑色签名，后部可调节。", "操场主席台附近", "体育馆前台", "2026-07-17 18:10:00", "found"),
    ("小米 10000mAh 充电宝", "电子产品", "银灰色小米移动电源，带一根白色 Type-C 短线。", "校园咖啡厅", None, "2026-07-22 10:20:00", "lost"),
    ("白色 Type-C 充电器", "电子产品", "白色充电头和一米长 Type-C 数据线，充电头功率 65W。", "信息学院机房", "机房管理员处", "2026-07-22 11:45:00", "found"),
    ("绿色研究生证卡套", "证件卡片", "绿色软质卡套，内有研究生证，外侧挂有深蓝色伸缩扣。", "生命学院报告厅", None, "2026-07-15 14:20:00", "lost"),
    ("白色临时校园访客证", "证件卡片", "白色塑料访客证，蓝色挂绳，证件信息已遮挡。", "行政中心一楼", "行政中心前台", "2026-07-15 16:35:00", "found"),
    ("深灰色 Apple Watch 智能手表", "电子产品", "深灰色苹果智能手表，黑色运动表带，表盘约 45mm。", "体育馆健身房", None, "2026-07-16 20:15:00", "lost"),
    ("黑色小米智能手环", "电子产品", "黑色小米手环，长方形屏幕，硅胶表带有轻微磨损。", "操场西侧跑道", "体育馆前台", "2026-07-16 19:05:00", "found"),
    ("黑框近视眼镜", "其他", "黑色方框近视眼镜，透明鼻托，装在深蓝色硬壳眼镜盒中。", "信息学院咖啡区", None, "2026-07-17 15:40:00", "lost"),
    ("茶色太阳镜", "其他", "茶色镜片太阳眼镜，金色细框，镜腿内侧有品牌字样。", "学校南门广场", "南门保安室", "2026-07-17 11:25:00", "found"),
    ("蓝色闪迪 U 盘", "电子产品", "蓝黑配色闪迪 USB 3.0 U 盘，容量 64GB，挂有银色钥匙圈。", "计算机机房 2", None, "2026-07-18 21:30:00", "lost"),
    ("黑色希捷移动硬盘", "电子产品", "黑色希捷移动硬盘，约 1TB，附带一根短 USB 数据线。", "创客空间工作台", "创客空间管理员处", "2026-07-18 18:45:00", "found"),
    ("透明大容量笔袋", "学习用品", "透明网纱笔袋，里面有自动铅笔、荧光笔和直尺。", "第一教学楼 204", None, "2026-07-19 10:10:00", "lost"),
    ("黑色实验记录本", "学习用品", "黑色硬壳实验记录本，A5 大小，内页有化学实验笔记。", "物质学院公共实验室", "实验室值班台", "2026-07-19 17:20:00", "found"),
    ("白色长袖实验服", "衣物鞋帽", "白色长袖实验服，尺码 M，胸前口袋夹着一支蓝色笔。", "生物实验室更衣区", None, "2026-07-20 18:00:00", "lost"),
    ("灰色羊绒围巾", "衣物鞋帽", "浅灰色长围巾，两端有流苏，材质柔软，无明显品牌。", "会议中心二楼", "会议中心服务台", "2026-07-20 13:50:00", "found"),
    ("尤尼克斯羽毛球拍", "其他", "蓝白配色羽毛球拍，黑色手胶，装在单肩球拍套中。", "体育馆羽毛球场", None, "2026-07-21 21:10:00", "lost"),
    ("橙色七号篮球", "其他", "橙色标准七号篮球，表面写有黑色字母缩写，气压正常。", "室外篮球场", "体育馆器材室", "2026-07-21 19:30:00", "found"),
    ("白色骑行头盔", "衣物鞋帽", "白色自行车骑行头盔，带黑色调节带，后部有反光贴。", "自行车停车棚 A 区", None, "2026-07-14 22:15:00", "lost"),
    ("黑色自行车 U 型锁", "钱包钥匙", "黑色金属 U 型自行车锁，锁梁较粗，配有一把小钥匙。", "学生宿舍 5 号楼", "5 号楼宿管处", "2026-07-14 09:40:00", "found"),
    ("藏青色 20 寸行李箱", "其他", "藏青色登机箱，四个万向轮，拉杆上系有红色行李牌。", "学生宿舍 2 号楼", None, "2026-07-15 08:25:00", "lost"),
    ("米白色帆布手提袋", "其他", "米白色帆布袋，正面印有红色校园建筑图案，袋内有文件夹。", "校车一号线", "校车调度室", "2026-07-15 18:10:00", "found"),
    ("银色星星吊坠项链", "其他", "银色细链项链，吊坠为五角星形，链扣附近有小圆牌。", "学生活动中心", None, "2026-07-16 17:35:00", "lost"),
    ("黑色素圈戒指", "其他", "黑色金属素圈戒指，内圈刻有英文字母，尺寸较小。", "西餐厅洗手台", "西餐厅服务台", "2026-07-16 12:20:00", "found"),
    ("联想 65W 笔记本电源适配器", "电子产品", "黑色联想笔记本充电器，功率 65W，圆口电源接头。", "信息学院讨论室", None, "2026-07-18 22:00:00", "lost"),
    ("灰色 HDMI 转接器", "电子产品", "灰色 USB-C 转 HDMI 转接器，短线设计，接口处有轻微划痕。", "教学中心多媒体教室", "教学中心设备室", "2026-07-18 16:55:00", "found"),
    ("黄色小鸭毛绒玩具", "其他", "黄色小鸭子毛绒挂件，约 15 厘米高，头顶有白色挂绳。", "校园咖啡厅沙发区", None, "2026-07-19 19:10:00", "lost"),
    ("三阶彩色魔方", "其他", "标准三阶魔方，彩色贴片，白色中心块上印有品牌标志。", "学生活动中心桌游区", "活动中心前台", "2026-07-19 20:40:00", "found"),
    ("深空灰 iPad Air 平板电脑", "电子产品", "深空灰苹果平板电脑，蓝色磁吸保护套，背面贴有课程表。", "图书馆研讨室", None, "2026-07-20 20:30:00", "lost"),
    ("粉色罗技无线鼠标", "电子产品", "粉色罗技无线鼠标，滚轮为浅粉色，底部没有 USB 接收器。", "文印室电脑桌", "文印室前台", "2026-07-20 11:05:00", "found"),
    ("白色耐克跑步鞋", "衣物鞋帽", "一双白色耐克运动鞋，尺码 42，鞋侧有黑色标志。", "体育馆男更衣室", None, "2026-07-21 22:20:00", "lost"),
    ("黑色保暖手套", "衣物鞋帽", "一副黑色针织手套，手腕处有灰色条纹，可触屏使用。", "学校北门公交站", "北门保安室", "2026-07-21 08:35:00", "found"),
    ("佳能微单相机", "电子产品", "黑色佳能微单相机，配有银色镜头和黑红色相机背带。", "校园湖边草坪", None, "2026-07-22 17:40:00", "lost"),
    ("蓝色 JBL 蓝牙音箱", "电子产品", "蓝色圆柱形 JBL 便携音箱，侧面有白色挂绳，能够正常开机。", "学生活动中心排练室", "活动中心前台", "2026-07-22 16:15:00", "found"),
    ("中国银行借记卡", "证件卡片", "红白配色中国银行借记卡，卡号等信息未记录。", "自动售货机附近", None, "2026-07-22 09:10:00", "lost"),
    ("居民身份证", "证件卡片", "捡到一张居民身份证，身份信息已完全遮挡，请本人凭有效证明认领。", "校医院门口", "校医院前台", "2026-07-22 14:05:00", "found"),
]


def vector_string(values: list[float]) -> str:
    return "[" + ",".join(str(value) for value in values[:VECTOR_DIM]) + "]"


def search_text(item: tuple) -> str:
    item_name, item_type, description, _, _, _, _ = item
    return f"物品：{item_name}。分类：{item_type}。描述：{description}"


def clean_seed_data() -> None:
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "DELETE FROM lost_items WHERE contact_person = %s OR description LIKE %s",
            (SEED_OWNER, f"%{SEED_MARKER}%"),
        )
        deleted = cur.rowcount
        conn.commit()
        print(f"Deleted {deleted} search seed records.")
    finally:
        cur.close()
        release_db_connection(conn)


def seed(include_vectors: bool) -> None:
    conn = get_db_connection()
    cur = conn.cursor()
    inserted = 0
    skipped = 0
    try:
        for item in SEED_ITEMS:
            item_name, item_type, description, location, storage_location, lost_time, direction = item
            cur.execute(
                """SELECT 1 FROM lost_items
                   WHERE item_name = %s AND direction = %s
                     AND (contact_person = %s OR description LIKE %s)""",
                (item_name, direction, SEED_OWNER, f"%{SEED_MARKER}%"),
            )
            if cur.fetchone():
                skipped += 1
                continue

            vector = vector_string(encode_text(search_text(item))) if include_vectors else None
            cur.execute(
                """INSERT INTO lost_items
                   (item_name, item_type, description, location, storage_location, lost_time,
                    direction, status, contact_visibility, contact_person, user_id, vector)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, 'active', 'private', %s, NULL, %s::vector)""",
                (
                    item_name,
                    item_type,
                    description,
                    location,
                    storage_location,
                    lost_time,
                    direction,
                    SEED_OWNER,
                    vector,
                ),
            )
            inserted += 1

        conn.commit()
        print(f"Inserted {inserted} search seed records; skipped {skipped} existing records.")
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        release_db_connection(conn)


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage local hybrid-search test records.")
    parser.add_argument("--clean", action="store_true", help="Delete only records created by this script.")
    parser.add_argument("--without-vectors", action="store_true", help="Insert BM25-only records without loading the embedding model.")
    args = parser.parse_args()

    if args.clean:
        clean_seed_data()
        return
    seed(include_vectors=not args.without_vectors)


if __name__ == "__main__":
    main()
