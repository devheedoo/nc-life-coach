"""Streamlit session persistence: SQLite session wrapper and store versioning."""

from __future__ import annotations

from typing import Any, cast

from agents import SQLiteSession
from agents.items import TResponseInputItem


def _strip_image_generation_action_for_session(item: Any) -> Any:
    """Drop output-only `action` on image_generation_call items before persisting to SQLite."""
    if isinstance(item, dict):
        if item.get("type") == "image_generation_call" and "action" in item:
            out = dict(item)
            out.pop("action", None)
            return out
        return item
    model_dump = getattr(item, "model_dump", None)
    if not callable(model_dump):
        return item
    try:
        d = model_dump(exclude_unset=True, warnings=False)
    except TypeError:
        try:
            d = model_dump(exclude_unset=True)
        except Exception:
            return item
    except Exception:
        return item
    if isinstance(d, dict) and d.get("type") == "image_generation_call" and "action" in d:
        out = dict(d)
        out.pop("action", None)
        return out
    return item


class LifeCoachSQLiteSession(SQLiteSession):
    async def get_items(self, limit: int | None = None) -> list[TResponseInputItem]:
        """Normalize items loaded from DB (legacy rows may still include output-only `action`)."""
        items = await super().get_items(limit)
        return [
            cast(TResponseInputItem, _strip_image_generation_action_for_session(i)) for i in items
        ]

    async def add_items(self, items: list[TResponseInputItem]) -> None:
        sanitized = [
            cast(TResponseInputItem, _strip_image_generation_action_for_session(i)) for i in items
        ]
        await super().add_items(sanitized)

    async def pop_item(self) -> TResponseInputItem | None:
        item = await super().pop_item()
        if item is None:
            return None
        return cast(TResponseInputItem, _strip_image_generation_action_for_session(item))


# Bump when session wrapper behavior changes so Streamlit session_state picks up the new class.
SESSION_STORE_VERSION = 2
