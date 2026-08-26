"""One org name from Rostender customer column chrome."""
from __future__ import annotations

import re

_PUA_CTRL = re.compile(r"[\u0000-\u001f\u007f-\u009f\ue000-\uf8ff\ufffd]+")
_WS = re.compile(r"\s+")
_TAIL = re.compile(
    r"\s+(?:Организатор|Закупки заказчика|Закупки организатора|Отрасль|Закупки)\b",
    re.IGNORECASE,
)
_PREFIX = re.compile(r"^Заказчик\s+", re.IGNORECASE)
_LABELS = frozenset({"заказчик", "наименование", "организатор"})
_MAX_LEN = 160


def clean_customer_name(value: object) -> str | None:
    if value is None:
        return None
    text = _PUA_CTRL.sub("", str(value))
    text = _WS.sub(" ", text).strip()
    if not text:
        return None
    text = _PREFIX.sub("", text).strip()
    cut = _TAIL.search(text)
    if cut:
        text = text[: cut.start()].strip()
    if text.lower() in _LABELS:
        return None
    if len(text) > _MAX_LEN:
        clipped = text[:_MAX_LEN]
        if " " in clipped:
            clipped = clipped.rsplit(" ", 1)[0]
        text = clipped.strip()
    return text or None
