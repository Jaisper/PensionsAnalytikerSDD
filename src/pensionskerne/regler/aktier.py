"""Aktieindkomst og aktiesparekonto (feature 013b).

Aktieindkomst (her: realiseret kursgevinst ved salg fra frit depot) beskattes særskilt efter
personskatteloven § 8 a: en lav sats op til progressionsgrænsen og en høj sats over. For gifte
forhøjes grænsen med ægtefællens uudnyttede grænse, højst én grænse (§ 8 a, stk. 4); husstanden
beregner den og giver den ind her. Personfradraget bruges ikke på aktieindkomst.

Afkastet på en aktiesparekonto lagerbeskattes med en fast sats (aktiesparekontoloven). Negativt
afkast og tab er ikke modelleret.
"""
from __future__ import annotations

from ..register.opslag import Regelopslag


def aktieindkomst_skat(aktieindkomst: float, o: Regelopslag, ekstra_graense: float = 0.0) -> float:
    if aktieindkomst <= 0:
        return 0.0
    graense = o.v("skat.aktieindkomst.progressionsgraense")
    graense += min(max(0.0, ekstra_graense), graense)
    lav = min(aktieindkomst, graense)
    return lav * o.v("skat.aktieindkomst.sats_lav") + (aktieindkomst - lav) * o.v("skat.aktieindkomst.sats_hoej")


def ask_skat(afkast: float, o: Regelopslag) -> float:
    return max(0.0, afkast) * o.v("ask.sats")
