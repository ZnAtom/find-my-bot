from retrieval import (
    bm25_recall,
    build_search_text,
    filter_vector_recall,
    hybrid_match_score,
    lexical_relevance,
)


def item(item_id, name, description="", similarity=None):
    row = {
        "id": item_id,
        "item_name": name,
        "item_type": "其他",
        "description": description,
        "location": "",
        "storage_location": "",
    }
    if similarity is not None:
        row["similarity"] = similarity
    return row


def test_bm25_recall_rejects_unrelated_single_character_overlap():
    rows = [
        item(1, "蓝色运动水杯"),
        item(2, "白色膳魔师保温杯", "白色不锈钢保温水杯"),
        item(3, "银色华为手机"),
    ]

    results = bm25_recall("水杯", rows, 10)

    assert {row["id"] for row in results} == {1, 2}


def test_bm25_recall_prioritizes_complete_campus_card_phrase():
    rows = [
        item(1, "一串钥匙（含宿舍卡）"),
        item(2, "上海科技大学校园一卡通"),
        item(3, "黑色拉链卡包"),
        item(4, "灰色保温水杯", "杯身贴有卡通贴纸"),
    ]

    results = bm25_recall("一卡通", rows, 10)

    assert [row["id"] for row in results] == [2]
    assert lexical_relevance("一卡通", rows[1]) == 1.0


def test_campus_card_query_expands_to_all_in_one_card_without_generic_card_hits():
    rows = [
        item(1, "一串钥匙（含宿舍卡）"),
        item(2, "上海科技大学校园一卡通"),
        item(3, "黑色拉链卡包"),
        item(4, "蓝色学生校园卡"),
    ]

    results = bm25_recall("校园卡", rows, 10)

    assert [row["id"] for row in results] == [4, 2]
    assert hybrid_match_score("校园卡", rows[1]) >= 0.9


def test_vector_recall_applies_absolute_and_relative_cutoffs():
    rows = [
        item(1, "相关物品", similarity=0.68),
        item(2, "次相关物品", similarity=0.61),
        item(3, "低相关物品", similarity=0.47),
    ]

    results = filter_vector_recall(rows, minimum_similarity=0.48, maximum_drop=0.08)

    assert [row["id"] for row in results] == [1, 2]


def test_exact_name_gets_calibrated_display_score():
    row = item(1, "上海科技大学校园一卡通", similarity=0.69)

    assert hybrid_match_score("一卡通", row) >= 0.95


def test_book_query_uses_content_aliases_and_ignores_location_and_bookbag():
    rows = [
        item(1, "牛津高阶英语词典"),
        item(2, "《线性代数》教材"),
        item(3, "灰色双肩书包"),
        {
            **item(4, "透明长柄雨伞"),
            "location": "图书馆一楼入口",
            "storage_location": "图书馆前台",
        },
    ]

    results = bm25_recall("书", rows, 10)

    assert {row["id"] for row in results} == {1, 2}
    assert "图书馆" not in build_search_text(rows[3])
