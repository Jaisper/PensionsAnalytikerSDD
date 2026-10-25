"""Personlig tillægsprocent, ældrecheck og mediecheck.

Tillægsprocenten er en selvstændig regel (lov om social pension § 14 a) og må ikke
afledes af pensionstillæggets aftrapning (golden G-42). Begge checks er skattepligtige.
"""
from __future__ import annotations

from ..register.opslag import Regelopslag
from .folkepension import fradrag_forhoejelse

FULD = 100


def tillaegsprocent(indtaegtsgrundlag: float, gift: bool, o: Regelopslag) -> int:
    """100 op til bundgrænsen, derefter 1 procentpoint mindre for hvert fulde trin (§ 31, stk. 2)."""
    praefiks = "tp.gift" if gift else "tp.enlig"
    bund = o.v(f"{praefiks}.bund") + fradrag_forhoejelse(gift, o)
    trin = o.v(f"{praefiks}.trin")
    if indtaegtsgrundlag <= bund:
        return FULD
    return max(0, FULD - int((indtaegtsgrundlag - bund) // trin))


def aeldrecheck(tillaegsprocent: int, likvid_formue: float, o: Regelopslag) -> float:
    """Ældrecheck: satsen × tillægsprocenten. Formuegrænsen er en hård tærskel, og
    beløb under minimum udbetales ikke."""
    if tillaegsprocent <= 0:
        return 0.0
    if likvid_formue > o.v("yd.aeldrecheck.formuegraense"):
        return 0.0
    beloeb = o.v("yd.aeldrecheck") * tillaegsprocent / FULD
    return beloeb if beloeb >= o.v("yd.aeldrecheck.minimum") else 0.0


def mediecheck(tillaegsprocent: int, o: Regelopslag) -> float:
    """Mediecheck kræver tillægsprocent 100. Afhænger ikke af formue."""
    return o.v("yd.mediecheck") if tillaegsprocent == FULD else 0.0
