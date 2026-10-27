"""Ligningsmæssige fradrag for løn (feature 017) — ligningsloven § 9 J og § 9 K.

Grundlaget er arbejdsmarkedsbidragsgrundlaget (her: årslønnen før skat). Fradragene nedsætter
den skattepligtige indkomst, dvs. kun grundlaget for kommune- og kirkeskat (PSL §§ 6–7).
"""
from __future__ import annotations

from ..register.opslag import Regelopslag


def beskaeftigelsesfradrag(grundlag: float, o: Regelopslag) -> float:
    """LL § 9 J, stk. 1: en procentdel af grundlaget, højst et maksimum."""
    return min(max(0.0, grundlag) * o.v("skat.beskaeftigelsesfradrag.sats"), o.v("skat.beskaeftigelsesfradrag.maks"))


def jobfradrag(grundlag: float, o: Regelopslag) -> float:
    """LL § 9 K, stk. 1: en procentdel af grundlaget over en grænse, højst et maksimum."""
    over = max(0.0, grundlag - o.v("skat.jobfradrag.graense"))
    return min(over * o.v("skat.jobfradrag.sats"), o.v("skat.jobfradrag.maks"))


def seniorfradrag(grundlag: float, alder: int, folkepensionsalder: int, o: Regelopslag) -> float:
    """LL § 9 J, stk. 5–6: ekstra beskæftigelsesfradrag i de seneste indkomstår før
    folkepensionsalderen. Det bortfalder i det år, hvor folkepensionsalderen nås."""
    if not folkepensionsalder - o.v("skat.seniorfradrag.aar_foer_fp") <= alder < folkepensionsalder:
        return 0.0
    return min(max(0.0, grundlag) * o.v("skat.seniorfradrag.sats"), o.v("skat.seniorfradrag.maks"))


def ligningsmaessige_fradrag(grundlag: float, alder: int, folkepensionsalder: int, o: Regelopslag) -> float:
    return (beskaeftigelsesfradrag(grundlag, o) + jobfradrag(grundlag, o)
            + seniorfradrag(grundlag, alder, folkepensionsalder, o))
