"""Scoring rules from fit-tiers (P10): services L1/L2; supply → L3 on board."""
from __future__ import annotations

import re

# Service / method signals
RE_UZK = re.compile(
    r"\b(узк|ультразвуков\w*\s+контрол|узт|толщинометр\w*\s+ультразвуков)",
    re.I,
)
RE_SERVICE_NDT = re.compile(
    r"(неразрушающ\w*\s+контрол|\bнк\b|радиограф|рентген|цифров\w*\s+радиограф|\bцр\b|"
    r"\bвик\b|визуальн\w*\s+и\s+измерительн|капилляр|\bпвк\b|"
    r"дефектоскоп\w*\s+(?:свар|соединен|труб|метал)|"
    r"проведен\w*\s+неразрушающ|оказан\w*\s+услуг\w*\s+.*контрол|"
    r"контрол\w*\s+сварн|толщин\w*\s+стенок)",
    re.I,
)
RE_RK = re.compile(r"(радиограф|рентген|гаммаграф|\bцр\b|цифров\w*\s+радиограф)", re.I)
RE_VIK_PVK = re.compile(r"(\bвик\b|визуальн\w*\s+и\s+измерительн|\bпвк\b|капиллярн|проникающ\w*\s+веществ)", re.I)
RE_OBJECT = re.compile(
    r"(сварн\w*\s+соединен|гидрокрекинг|нефте|газ|энерг|трубопровод|резервуар|"
    r"строитель|объект|секци|комплекс)",
    re.I,
)
RE_SECTOR = re.compile(r"(нефте|газ|энерг|строитель|\bвпк\b|атом|промплощад)", re.I)

# Supply / equipment → L3 (on board), not noise
RE_BUY_DEVICE = re.compile(
    r"(закупк\w*|поставк\w*|приобретен\w*).{0,60}(прибор|дефектоскоп|толщиномер|"
    r"оборудован|рентген.?аппарат|панел\w*\s+цр|ультразвуков\w*\s+дефектоскоп)|"
    r"(прибор|дефектоскоп|толщиномер|оборудован).{0,60}(закупк|поставк|приобретен)",
    re.I,
)
RE_DEVICE_ONLY = re.compile(
    r"\b(дефектоскоп|толщиномер|рентген.?аппарат|кристалл\w*\s+детектор)\b",
    re.I,
)
RE_VERIFY = re.compile(r"(поверк\w*|калибровк\w*|ремонт\w*\s+(прибор|средств\w*\s+измерен))", re.I)
RE_CONSUMABLE = re.compile(r"(плёнк|пленк|химия\s+пвк|реактив|расходн)", re.I)
RE_TRAINING = re.compile(r"(обучен\w*|аттестац\w*\s+персонал|повышен\w*\s+квалификац)", re.I)


def score_title(title: str) -> tuple[int, list[str], bool]:
    """Return score, reasons, uzk_service flag."""
    t = title or ""
    score = 0
    reasons: list[str] = []
    uzk_service = False

    if RE_BUY_DEVICE.search(t):
        score -= 3
        reasons.append("buy_device:-3")
    elif RE_DEVICE_ONLY.search(t) and not RE_SERVICE_NDT.search(t):
        score -= 3
        reasons.append("device_only:-3")

    if RE_VERIFY.search(t) and not RE_SERVICE_NDT.search(t):
        score -= 2
        reasons.append("verify_only:-2")
    if RE_CONSUMABLE.search(t) and not RE_SERVICE_NDT.search(t):
        score -= 2
        reasons.append("consumable:-2")
    if RE_TRAINING.search(t) and not RE_SERVICE_NDT.search(t):
        score -= 2
        reasons.append("training:-2")

    if RE_UZK.search(t) and not RE_BUY_DEVICE.search(t):
        if not (RE_DEVICE_ONLY.search(t) and re.search(r"(закупк|поставк|приобретен)", t, re.I)):
            score += 4
            uzk_service = True
            reasons.append("uzk_service:+4")

    if RE_SERVICE_NDT.search(t) or RE_RK.search(t) or RE_VIK_PVK.search(t):
        score += 3
        reasons.append("ndt_service:+3")

    if re.search(r"проведен\w*\s+неразрушающ", t, re.I):
        score += 2
        reasons.append("conduct_ndt:+2")

    if (RE_RK.search(t) or RE_VIK_PVK.search(t) or RE_UZK.search(t) or RE_SERVICE_NDT.search(t)) and RE_OBJECT.search(
        t
    ):
        score += 2
        reasons.append("method_object:+2")

    if RE_SECTOR.search(t):
        score += 1
        reasons.append("sector:+1")

    if re.search(r"неразрушающ", t, re.I) and score == 0:
        score -= 1
        reasons.append("generic_ndt:-1")

    return score, reasons, uzk_service


def is_supply_watch(title: str) -> bool:
    """Поставка / приборы / калибровка / расходники → L3 Смотреть (на доске)."""
    t = title or ""
    if RE_BUY_DEVICE.search(t):
        return True
    if RE_DEVICE_ONLY.search(t) and not RE_SERVICE_NDT.search(t):
        return True
    if RE_VERIFY.search(t) and not RE_SERVICE_NDT.search(t):
        return True
    if RE_CONSUMABLE.search(t) and not RE_SERVICE_NDT.search(t):
        return True
    return False


def is_noise(title: str, score: int, reasons: list[str]) -> bool:
    """Только явный оффтоп (обучение и т.п.) — вне доски. Поставка → не noise."""
    t = title or ""
    if is_supply_watch(t):
        return False
    # Обучение / аттестация как предмет закупки — вне доски (даже если есть слова НК).
    if RE_TRAINING.search(t) and not re.search(
        r"проведен\w*\s+неразрушающ|оказан\w*\s+услуг\w*\s+.*контрол|контрол\w*\s+сварн",
        t,
        re.I,
    ):
        return True
    if any(r.startswith("training") for r in reasons) and score < 2:
        return True
    return False
