"""Private pensionsordninger — opsparing, lofter og udbetalingsformer.

- Ratepension: årsrate = værdi primo / resterende år (PBL § 11 A, stk. 2, nr. 1; A9).
  Raten udbetales primo, og restværdien forrentes resten af året.
- Livsvarig: forudbetalt annuitet over en antaget horisont (antagelse, ikke lov).
- Aldersopsparing: skattefri ved udbetaling. Kapitalpension: afgift ved udbetaling.
- Indbetalinger efter AM-bidrag, begrænset af lovens lofter (PBL § 16).
"""
from __future__ import annotations

from ..register.opslag import Regelopslag


def indbetalingsloft(type: str, alder: int, folkepensionsalder: int, o: Regelopslag) -> float | None:
    if type == "ratepension":
        return o.v("ordning.ratepension.indbetalingsloft")
    if type == "aldersopsparing":
        if folkepensionsalder - alder < o.v("ordning.aldersopsparing.forhoejet_aar_foer_fp"):
            return o.v("ordning.aldersopsparing.indbetalingsloft_forhoejet")
        return o.v("ordning.aldersopsparing.indbetalingsloft")
    return None


def rateplan(saldo: float, aar: int, afkast: float) -> list[float]:
    """Årlige rater efter PBL § 11 A: værdien primo divideret med de resterende år."""
    rater = []
    for i in range(aar):
        rate = saldo / (aar - i)
        rater.append(rate)
        saldo = (saldo - rate) * (1 + afkast)
    return rater


def livsvarig_ydelse(saldo: float, aar: int, afkast: float) -> float:
    """Konstant årlig ydelse, der netop opbruger saldoen over `aar` år (forudbetalt)."""
    if aar <= 0 or saldo <= 0:
        return 0.0
    if afkast == 0:
        return saldo / aar
    v = 1 / (1 + afkast)
    return saldo * (1 - v) / (1 - v ** aar)


def engangs_netto(type: str, beloeb: float, o: Regelopslag) -> float:
    if type == "kapitalpension":
        return beloeb * (1 - o.v("ordning.kapitalpension.afgift"))
    return beloeb  # aldersopsparing: skattefri
