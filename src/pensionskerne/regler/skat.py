"""Indkomstskat af personlig indkomst og positiv nettokapitalindkomst — personskatteloven
§§ 6, 7, 7 a, 8, 10 og 19.

Kapitalindkomst (feature 009: afkast af bufferen) indgår i grundlaget for bund-, kommune- og
kirkeskat og i personfradraget, men i mellem- og topskattegrundlaget kun over bundfradraget
(PSL § 7, stk. 1). Den del af et skattebånd, der skyldes kapitalindkomst, har skatteloftet for
kapitalindkomst (PSL § 19, stk. 2). Kapitalindkomsten lægges oven på den personlige indkomst.

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
    kapitalindkomst: float = 0.0
    skat_kapitalindkomst: float = 0.0   # merskatten af kapitalindkomsten (marginalt, oven på PI)


def progressiv_skat(pi: float, kommuneskat: float, o: Regelopslag, ki_over: float = 0.0) -> tuple[float, float]:
    """Mellem-, top- og top-topskat og nedslaget efter det skrå skatteloft.

    Grundlaget er personlig indkomst plus kapitalindkomst over bundfradraget (`ki_over`), som
    lægges øverst. Hvert trin rammer alt grundlag over trinnets grænse; i båndet mellem to
    grænser er marginalsatsen summen af de ramte trinsatser. Overstiger bundskat +
    kommuneskat + den samlede trinsats loftet, nedsættes trinsatsen med det overskydende
    (PSL § 19): trinnets loft for personlig indkomst, kapitalindkomstens loft for den del af
    båndet, der ligger over den personlige indkomst. Kirkeskat indgår ikke i loftet.
    """
    bundskat = o.v("skat.bundskat")
    trin = o.husk("skat.trin", lambda: [
        (o.v(f"skat.{navn}.graense"), o.v(f"skat.{navn}.sats"), o.v(f"skat.skatteloft.{navn}"))
        for navn in TRIN
    ])
    loft_ki = o.v("skat.skatteloft.kapitalindkomst") if ki_over > 0 else None
    grundlag = pi + ki_over
    brutto = nedslag = 0.0
    samlet_trinsats = 0.0
    for i, (graense, sats, loft) in enumerate(trin):
        samlet_trinsats += sats
        if grundlag <= graense:
            break
        naeste_graense = trin[i + 1][0] if i + 1 < len(trin) else math.inf
        fra, til = graense, min(grundlag, naeste_graense)
        brutto += (til - fra) * samlet_trinsats
        for del_fra, del_til, loft_her in ((fra, min(til, pi), loft), (max(fra, pi), til, loft_ki)):
            if del_til > del_fra:
                overskydende = bundskat + kommuneskat + samlet_trinsats - loft_her
                nedslag += (del_til - del_fra) * min(samlet_trinsats, max(0.0, overskydende))
    return brutto, nedslag


def _beregn(pi: float, ki: float, kommuneskat: float, kirkeskat: float, o: Regelopslag) -> Skatteberegning:
    flad_sats = o.v("skat.bundskat") + kommuneskat + kirkeskat
    grundlag = pi + ki
    flad = grundlag * flad_sats
    personfradrag = min(o.v("skat.personfradrag"), max(0.0, grundlag)) * flad_sats
    ki_over = max(0.0, ki - o.v("skat.kapitalindkomst.bundfradrag")) if ki > 0 else 0.0
    progressiv, nedslag = progressiv_skat(pi, kommuneskat, o, ki_over)
    total = max(0.0, flad - personfradrag + progressiv - nedslag)
    return Skatteberegning(pi, flad, personfradrag, progressiv, nedslag, total, kapitalindkomst=ki)


def beregn_skat(pi: float, kommuneskat: float, kirkeskat: float, o: Regelopslag,
                kapitalindkomst: float = 0.0) -> Skatteberegning:
    """Samlet skat af årets personlige indkomst og positive nettokapitalindkomst. Negativ
    kapitalindkomst (fradrag) er ikke modelleret og ignoreres."""
    uden = _beregn(pi, 0.0, kommuneskat, kirkeskat, o)
    ki = max(0.0, kapitalindkomst)
    if ki == 0:
        return uden
    med = _beregn(pi, ki, kommuneskat, kirkeskat, o)
    return Skatteberegning(med.personlig_indkomst, med.flad_skat, med.personfradrag_vaerdi, med.progressiv,
                           med.loftnedslag, med.total, ki, med.total - uden.total)


def fordel(total: float, brutto_pr_kilde: dict[str, float]) -> dict[str, float]:
    """Fordeler den samlede skat forholdsmæssigt på indkomstkilderne (FR-024).

    Summen af andelene er lig totalen. Fordelingen er en præsentationskonvention:
    loven beskatter den samlede indkomst, ikke de enkelte kilder.
    """
    pi = sum(brutto_pr_kilde.values())
    if pi <= 0:
        return {k: 0.0 for k in brutto_pr_kilde}
    return {k: total * b / pi for k, b in brutto_pr_kilde.items()}
