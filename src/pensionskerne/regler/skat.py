"""Indkomstskat af personlig indkomst — personskatteloven §§ 6, 7, 7 a, 8, 10 og 19.

Pensionsudbetalinger og offentlige ydelser (folkepension, ATP, ældrecheck, mediecheck)
er personlig indkomst UDEN arbejdsmarkedsbidrag: AM-bidrag betales ved indbetaling til
en pensionsordning, aldrig ved udbetaling (domænegrundlag A1).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from ..register.opslag import Regelopslag

TRIN = ("mellemskat", "topskat", "toptopskat")


@dataclass(frozen=True)
class Skatteberegning:
    personlig_indkomst: float
    flad_skat: float            # bund + kommune + kirke af hele PI
    personfradrag_vaerdi: float
    progressiv: float           # mellem + top + top-top før skatteloft
    loftnedslag: float          # skrå skatteloft (PSL § 19)
    total: float


def progressiv_skat(pi: float, kommuneskat: float, o: Regelopslag) -> tuple[float, float]:
    """Mellem-, top- og top-topskat og nedslaget efter det skrå skatteloft.

    Hvert trin rammer al personlig indkomst over trinnets grænse. I båndet mellem to
    grænser er marginalsatsen derfor summen af de ramte trinsatser. Overstiger
    bundskat + kommuneskat + den samlede trinsats trinnets skatteloft, nedsættes
    trinsatsen med det overskydende (PSL § 19). Kirkeskat indgår ikke i loftet.
    """
    bundskat = o.v("skat.bundskat")
    trin = [
        (o.v(f"skat.{navn}.graense"), o.v(f"skat.{navn}.sats"), o.v(f"skat.skatteloft.{navn}"))
        for navn in TRIN
    ]
    brutto = nedslag = 0.0
    samlet_trinsats = 0.0
    for i, (graense, sats, loft) in enumerate(trin):
        samlet_trinsats += sats
        if pi <= graense:
            break
        naeste_graense = trin[i + 1][0] if i + 1 < len(trin) else math.inf
        baand = min(pi, naeste_graense) - graense
        brutto += baand * samlet_trinsats
        overskydende = bundskat + kommuneskat + samlet_trinsats - loft
        nedslag += baand * min(samlet_trinsats, max(0.0, overskydende))
    return brutto, nedslag


def beregn_skat(pi: float, kommuneskat: float, kirkeskat: float, o: Regelopslag) -> Skatteberegning:
    """Samlet skat af årets personlige indkomst."""
    flad_sats = o.v("skat.bundskat") + kommuneskat + kirkeskat
    flad = pi * flad_sats
    personfradrag = min(o.v("skat.personfradrag"), max(0.0, pi)) * flad_sats
    progressiv, nedslag = progressiv_skat(pi, kommuneskat, o)
    total = max(0.0, flad - personfradrag + progressiv - nedslag)
    return Skatteberegning(pi, flad, personfradrag, progressiv, nedslag, total)


def fordel(total: float, brutto_pr_kilde: dict[str, float]) -> dict[str, float]:
    """Fordeler den samlede skat forholdsmæssigt på indkomstkilderne (FR-024).

    Summen af andelene er lig totalen. Fordelingen er en præsentationskonvention:
    loven beskatter den samlede indkomst, ikke de enkelte kilder.
    """
    pi = sum(brutto_pr_kilde.values())
    if pi <= 0:
        return {k: 0.0 for k in brutto_pr_kilde}
    return {k: total * b / pi for k, b in brutto_pr_kilde.items()}
