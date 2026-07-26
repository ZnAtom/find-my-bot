import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from support import (
    _extract_llm_response_text,
    build_sources,
    detect_intent,
    make_anonymous_key,
    plain_chat_text,
    search_public_items,
)


def test_support_intent_detects_personal_data_for_logged_in_user():
    assert detect_intent("我的发布有哪些", {"id": 1}) == "personal_data"


def test_support_intent_detects_item_search():
    assert detect_intent("有没有人捡到校园卡", None) == "item_search"
    assert detect_intent("我丢了一个学生证", None) == "item_search"


def test_anonymous_key_is_hashed():
    key = make_anonymous_key("127.0.0.1")

    assert key != "127.0.0.1"
    assert len(key) == 40


def test_extract_llm_response_text_supports_openai_choices():
    data = {"choices": [{"message": {"content": "回答内容"}}]}

    assert _extract_llm_response_text(data) == "回答内容"


def test_plain_chat_text_removes_markdown_syntax():
    text = (
        "### 发布招领\n\n"
        "- **未登录也可以发布匿名招领**，但不能填写 `联系方式`。\n"
        "1. 查看 [详情页](http://foundit.geekpie.club/#/lost/1)"
    )

    result = plain_chat_text(text)

    assert "###" not in result
    assert "**" not in result
    assert "`" not in result
    assert "- " not in result
    assert "[详情页]" not in result
    assert "未登录也可以发布匿名招领" in result
    assert "联系方式" in result
    assert "详情页：http://foundit.geekpie.club/#/lost/1" in result


def test_item_sources_do_not_include_contact_fields():
    sources = build_sources(
        [],
        [
            {
                "id": 1,
                "item_name": "校园卡",
                "direction": "found",
                "status": "active",
                "item_type": "证件卡片",
                "location": "教学楼",
                "url": "/#/lost/1",
            }
        ],
        None,
        intent="item_search",
    )

    serialized = str(sources)
    assert "contact" not in serialized
    assert "phone" not in serialized
    assert "qq" not in serialized.lower()


def test_sources_hide_knowledge_and_personal_context():
    sources = build_sources(
        [
            {
                "path": "doc/support/faq.md",
                "chunk_index": 0,
                "title": "常见问题",
                "source_title": "FAQ",
                "content": "平台使用说明",
            }
        ],
        [
            {
                "id": 1,
                "item_name": "校园卡",
                "direction": "found",
                "status": "active",
                "item_type": "证件卡片",
                "location": "教学楼",
                "url": "/#/lost/1",
            }
        ],
        {"items": [{"id": 1}], "claims": []},
        intent="general",
    )

    assert sources == []


def test_item_search_sources_only_include_items():
    sources = build_sources(
        [
            {
                "path": "doc/support/faq.md",
                "chunk_index": 0,
                "title": "常见问题",
                "source_title": "FAQ",
                "content": "平台使用说明",
            }
        ],
        [
            {
                "id": 1,
                "item_name": "校园卡",
                "direction": "found",
                "status": "active",
                "item_type": "证件卡片",
                "location": "教学楼",
                "url": "/#/lost/1",
            }
        ],
        {"items": [{"id": 1}], "claims": []},
        intent="item_search",
    )

    assert [source["type"] for source in sources] == ["item"]


def test_public_support_search_masks_sensitive_item_details(monkeypatch):
    row = {
        "id": 1,
        "item_name": "王同学校园卡",
        "item_type": "证件卡片",
        "direction": "found",
        "status": "active",
        "description": "卡面有完整姓名和学号",
        "user_id": 9,
        "location": "上海科技大学 · 教学区 · 信息学院1号楼 · 101室",
        "image_url": "/uploads/private-card.jpg",
        "created_at": "2026-07-26T10:00:00",
        "updated_at": "2026-07-26T10:00:00",
    }

    class Cursor:
        def execute(self, sql, _params=None):
            self.checking_vector = "information_schema.columns" in sql

        def fetchone(self):
            return (False,)

        def fetchall(self):
            return [row]

        def close(self):
            pass

    class Connection:
        def cursor(self, **_kwargs):
            return Cursor()

        def rollback(self):
            pass

    monkeypatch.setattr("support.rrf_fuse", lambda *_args, **_kwargs: [(row, 1.0)])
    monkeypatch.setattr("support.hybrid_match_score", lambda *_args, **_kwargs: 1.0)

    results = search_public_items(Connection(), "校园卡")

    assert results[0]["item_name"] == "证件卡片"
    assert results[0]["description"] == ""
    assert results[0]["image_url"] is None
    assert results[0]["location"] == "教学区 · 信息学院1号楼"
