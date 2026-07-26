from typing import Optional

from auth import has_verified_school_email


SENSITIVE_ITEM_TYPES = {"证件卡片", "钱包钥匙"}


def is_sensitive_item(item: Optional[dict]) -> bool:
    return bool(item and item.get("item_type") in SENSITIVE_ITEM_TYPES)


def is_item_owner_or_admin(item: Optional[dict], user: Optional[dict]) -> bool:
    if not item or not user:
        return False
    return user.get("role") == "admin" or item.get("user_id") == user.get("id")


def can_view_sensitive_content(item: Optional[dict], user: Optional[dict]) -> bool:
    if not is_sensitive_item(item):
        return True
    return is_item_owner_or_admin(item, user) or has_verified_school_email(user)


def approximate_campus_location(location: Optional[str]) -> Optional[str]:
    parts = [part.strip() for part in str(location or "").split("·") if part.strip()]
    if len(parts) >= 3:
        return " · ".join(parts[1:3])
    return None


def mask_sensitive_content(item: dict, user: Optional[dict]) -> dict:
    result = dict(item)
    if can_view_sensitive_content(result, user):
        return result
    result["item_name"] = result.get("item_type") or "敏感物品"
    result["description"] = None
    result["image_url"] = None
    result["location"] = approximate_campus_location(result.get("location"))
    result["user_id"] = None
    return result
